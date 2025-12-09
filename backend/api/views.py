"""
AskDash API Views

Contains all API endpoints for:
- Authentication (register, login, user info)
- Database connections (CRUD)
- Table permissions
- Chat sessions
- Ask/Query endpoint
"""

from rest_framework import viewsets, status, generics
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from django.db.models import Q

from .models import (
    DatabaseConnection, TablePermission, ChatSession, ChatMessage,
    PermissionGroup, PermissionGroupTable, UserGroupAssignment
)
from .serializers import (
    UserSerializer, RegisterSerializer, DatabaseConnectionSerializer,
    TablePermissionSerializer, TablePermissionCreateSerializer,
    ChatSessionSerializer, ChatSessionListSerializer, ChatMessageSerializer,
    AskQuestionSerializer, PermissionGroupSerializer, PermissionGroupListSerializer,
    PermissionGroupCreateSerializer, AddTablesSerializer, AssignUserSerializer,
    PermissionGroupTableSerializer, UserGroupAssignmentSerializer
)
from .permissions import (
    IsOwnerOrReadOnly, IsDatabaseOwner, HasDatabaseAccess,
    get_user_allowed_tables, get_user_permission_level
)
from .utils.db_connector import get_connector_from_model
from .utils.schema_extractor import extract_schema_from_connection
from .utils.sql_executor import execute_query_safely
from .services.llm_factory import get_llm_service, get_current_provider_info
from .services.prompts import build_system_prompt, build_user_prompt

import logging

logger = logging.getLogger(__name__)


# ==================== Authentication Views ====================

class RegisterView(generics.CreateAPIView):
    """User registration endpoint."""
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """Get current authenticated user info."""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_users(request):
    """Search users by username or email."""
    query = request.query_params.get('q', '')
    if len(query) < 2:
        return Response([])

    users = User.objects.filter(
        Q(username__icontains=query) | Q(email__icontains=query)
    ).exclude(id=request.user.id)[:10]

    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_users(request):
    """List all users except admins and current user."""
    users = User.objects.filter(
        is_superuser=False,
        is_staff=False
    ).exclude(id=request.user.id).order_by('username')

    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)


# ==================== Database Connection Views ====================

class DatabaseConnectionViewSet(viewsets.ModelViewSet):
    """CRUD operations for database connections."""
    serializer_class = DatabaseConnectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return connections owned by user or shared with them."""
        user = self.request.user

        # Get IDs of databases shared with the user
        shared_db_ids = TablePermission.objects.filter(
            user=user
        ).values_list('database_connection_id', flat=True)

        # Return owned + shared databases
        return DatabaseConnection.objects.filter(
            Q(created_by=user) | Q(id__in=shared_db_ids)
        ).distinct()

    def perform_create(self, serializer):
        """Save the connection and extract schema."""
        connection = serializer.save()

        # Test the connection
        connector = get_connector_from_model(connection)
        success, message = connector.test_connection()

        if not success:
            connection.delete()
            raise Exception(f"Connection failed: {message}")

        # Extract and save schema
        schema = extract_schema_from_connection(connection)
        connection.schema_json = schema
        connection.save()

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test a database connection."""
        connection = self.get_object()
        connector = get_connector_from_model(connection)
        success, message = connector.test_connection()

        return Response({
            'success': success,
            'message': message
        })

    @action(detail=True, methods=['post'])
    def refresh_schema(self, request, pk=None):
        """Refresh the database schema."""
        connection = self.get_object()

        # Only owner can refresh schema
        if connection.created_by != request.user:
            return Response(
                {'error': 'Only the owner can refresh schema'},
                status=status.HTTP_403_FORBIDDEN
            )

        schema = extract_schema_from_connection(connection)
        connection.schema_json = schema
        connection.save()

        return Response({
            'success': True,
            'schema': schema
        })

    @action(detail=True, methods=['get'])
    def tables(self, request, pk=None):
        """Get list of tables for a connection."""
        connection = self.get_object()
        schema = connection.schema_json or {}
        tables = list(schema.get('tables', {}).keys())

        # Filter by user permissions
        allowed_tables = get_user_allowed_tables(request.user, connection)
        if allowed_tables is not None:
            tables = [t for t in tables if t in allowed_tables]

        return Response({'tables': tables})


# ==================== Table Permission Views ====================

class TablePermissionViewSet(viewsets.ModelViewSet):
    """Manage table-level permissions."""
    serializer_class = TablePermissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return permissions for databases owned by user."""
        return TablePermission.objects.filter(
            database_connection__created_by=self.request.user
        )

    @action(detail=False, methods=['post'])
    def grant(self, request):
        """Grant permissions to a user for specific tables."""
        serializer = TablePermissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        db_id = request.data.get('database_id')
        try:
            db_connection = DatabaseConnection.objects.get(
                id=db_id,
                created_by=request.user
            )
        except DatabaseConnection.DoesNotExist:
            return Response(
                {'error': 'Database not found or you are not the owner'},
                status=status.HTTP_404_NOT_FOUND
            )

        username = serializer.validated_data['username']
        user = User.objects.get(username=username)
        table_name = serializer.validated_data['table_name']
        permission_level = serializer.validated_data['permission_level']

        permission, created = TablePermission.objects.update_or_create(
            database_connection=db_connection,
            user=user,
            table_name=table_name,
            defaults={
                'permission_level': permission_level,
                'granted_by': request.user
            }
        )

        return Response(TablePermissionSerializer(permission).data)

    @action(detail=False, methods=['post'])
    def revoke(self, request):
        """Revoke permissions from a user."""
        db_id = request.data.get('database_id')
        username = request.data.get('username')
        table_name = request.data.get('table_name')

        try:
            db_connection = DatabaseConnection.objects.get(
                id=db_id,
                created_by=request.user
            )
        except DatabaseConnection.DoesNotExist:
            return Response(
                {'error': 'Database not found or you are not the owner'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        deleted, _ = TablePermission.objects.filter(
            database_connection=db_connection,
            user=user,
            table_name=table_name
        ).delete()

        return Response({'deleted': deleted > 0})

    @action(detail=False, methods=['get'])
    def by_database(self, request):
        """Get all permissions for a specific database."""
        db_id = request.query_params.get('database_id')

        try:
            db_connection = DatabaseConnection.objects.get(
                id=db_id,
                created_by=request.user
            )
        except DatabaseConnection.DoesNotExist:
            return Response(
                {'error': 'Database not found or you are not the owner'},
                status=status.HTTP_404_NOT_FOUND
            )

        permissions = TablePermission.objects.filter(
            database_connection=db_connection
        )

        return Response(TablePermissionSerializer(permissions, many=True).data)


# ==================== Permission Group Views ====================

class PermissionGroupViewSet(viewsets.ModelViewSet):
    """Manage permission groups for database access control."""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return PermissionGroupListSerializer
        return PermissionGroupSerializer

    def get_queryset(self):
        """Return permission groups for databases owned by user."""
        return PermissionGroup.objects.filter(
            database_connection__created_by=self.request.user
        )

    @action(detail=False, methods=['get'])
    def by_database(self, request):
        """Get all permission groups for a specific database."""
        db_id = request.query_params.get('database_id')

        try:
            db_connection = DatabaseConnection.objects.get(
                id=db_id,
                created_by=request.user
            )
        except DatabaseConnection.DoesNotExist:
            return Response(
                {'error': 'Database not found or you are not the owner'},
                status=status.HTTP_404_NOT_FOUND
            )

        groups = PermissionGroup.objects.filter(database_connection=db_connection)
        return Response(PermissionGroupSerializer(groups, many=True).data)

    @action(detail=False, methods=['post'])
    def create_group(self, request):
        """Create a new permission group with optional tables."""
        serializer = PermissionGroupCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        db_id = serializer.validated_data['database_id']
        try:
            db_connection = DatabaseConnection.objects.get(
                id=db_id,
                created_by=request.user
            )
        except DatabaseConnection.DoesNotExist:
            return Response(
                {'error': 'Database not found or you are not the owner'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Create the group
        group = PermissionGroup.objects.create(
            name=serializer.validated_data['name'],
            description=serializer.validated_data.get('description', ''),
            database_connection=db_connection,
            created_by=request.user
        )

        # Add tables if provided
        tables_data = serializer.validated_data.get('tables', [])
        for table_data in tables_data:
            PermissionGroupTable.objects.create(
                group=group,
                table_name=table_data.get('table_name'),
                permission_level=table_data.get('permission_level', 'read')
            )

        return Response(
            PermissionGroupSerializer(group).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def add_tables(self, request, pk=None):
        """Add tables to a permission group."""
        group = self.get_object()

        serializer = AddTablesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        added = []
        for table_data in serializer.validated_data['tables']:
            table_name = table_data.get('table_name')
            permission_level = table_data.get('permission_level', 'read')

            obj, created = PermissionGroupTable.objects.update_or_create(
                group=group,
                table_name=table_name,
                defaults={'permission_level': permission_level}
            )
            added.append({
                'table_name': table_name,
                'permission_level': permission_level,
                'created': created
            })

        return Response({
            'added': added,
            'group': PermissionGroupSerializer(group).data
        })

    @action(detail=True, methods=['post'])
    def remove_table(self, request, pk=None):
        """Remove a table from a permission group."""
        group = self.get_object()
        table_name = request.data.get('table_name')

        if not table_name:
            return Response(
                {'error': 'table_name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        deleted, _ = PermissionGroupTable.objects.filter(
            group=group,
            table_name=table_name
        ).delete()

        return Response({
            'deleted': deleted > 0,
            'group': PermissionGroupSerializer(group).data
        })

    @action(detail=True, methods=['post'])
    def assign_user(self, request, pk=None):
        """Assign a user to a permission group."""
        group = self.get_object()

        serializer = AssignUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        user = User.objects.get(username=username)

        assignment, created = UserGroupAssignment.objects.get_or_create(
            user=user,
            group=group,
            defaults={'assigned_by': request.user}
        )

        # Also create TablePermission entries for each table in the group
        for group_table in group.tables.all():
            TablePermission.objects.update_or_create(
                database_connection=group.database_connection,
                user=user,
                table_name=group_table.table_name,
                defaults={
                    'permission_level': group_table.permission_level,
                    'granted_by': request.user
                }
            )

        return Response({
            'assignment': UserGroupAssignmentSerializer(assignment).data,
            'created': created,
            'group': PermissionGroupSerializer(group).data
        })

    @action(detail=True, methods=['post'])
    def remove_user(self, request, pk=None):
        """Remove a user from a permission group."""
        group = self.get_object()
        username = request.data.get('username')

        if not username:
            return Response(
                {'error': 'username is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Delete the assignment
        deleted, _ = UserGroupAssignment.objects.filter(
            user=user,
            group=group
        ).delete()

        # Also remove table permissions that were granted through this group
        # Only remove if user doesn't have the table through another group
        for group_table in group.tables.all():
            # Check if user still has this table through another group assignment
            other_assignments = UserGroupAssignment.objects.filter(
                user=user,
                group__database_connection=group.database_connection,
                group__tables__table_name=group_table.table_name
            ).exclude(group=group).exists()

            if not other_assignments:
                TablePermission.objects.filter(
                    database_connection=group.database_connection,
                    user=user,
                    table_name=group_table.table_name
                ).delete()

        return Response({
            'deleted': deleted > 0,
            'group': PermissionGroupSerializer(group).data
        })

    def destroy(self, request, *args, **kwargs):
        """Delete a permission group and clean up related permissions."""
        group = self.get_object()

        # Remove table permissions for users who only had access through this group
        for assignment in group.user_assignments.all():
            user = assignment.user
            for group_table in group.tables.all():
                # Check if user still has this table through another group
                other_assignments = UserGroupAssignment.objects.filter(
                    user=user,
                    group__database_connection=group.database_connection,
                    group__tables__table_name=group_table.table_name
                ).exclude(group=group).exists()

                if not other_assignments:
                    TablePermission.objects.filter(
                        database_connection=group.database_connection,
                        user=user,
                        table_name=group_table.table_name
                    ).delete()

        return super().destroy(request, *args, **kwargs)


# ==================== Chat Session Views ====================

class ChatSessionViewSet(viewsets.ModelViewSet):
    """Manage chat sessions."""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return ChatSessionListSerializer
        return ChatSessionSerializer

    def get_queryset(self):
        """Return sessions for the current user."""
        queryset = ChatSession.objects.filter(user=self.request.user)

        # Filter by database if specified
        db_id = self.request.query_params.get('database_id')
        if db_id:
            queryset = queryset.filter(database_connection_id=db_id)

        return queryset

    def perform_create(self, serializer):
        """Create a new chat session."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['delete'])
    def clear_messages(self, request, pk=None):
        """Clear all messages in a session."""
        session = self.get_object()
        session.messages.all().delete()
        return Response({'success': True})


# ==================== Ask/Query Endpoint ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ask_question(request):
    """
    Main endpoint for asking questions about data.

    Request body:
    {
        "question": "What are the top 10 customers by revenue?",
        "database_id": 1,
        "session_id": null,  // optional, creates new session if not provided
        "show_sql": false
    }

    Response:
    {
        "answer": "Here are the top 10 customers...",
        "sql_query": "SELECT ... (only if show_sql is true)",
        "results": [...],
        "chart_type": "bar",
        "chart_config": {...},
        "explanation": "...",
        "session_id": 1,
        "message_id": 1
    }
    """
    serializer = AskQuestionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    question = serializer.validated_data['question']
    database_id = serializer.validated_data['database_id']
    session_id = serializer.validated_data.get('session_id')
    show_sql = serializer.validated_data.get('show_sql', False)

    # Get database connection
    try:
        db_connection = DatabaseConnection.objects.get(id=database_id)
    except DatabaseConnection.DoesNotExist:
        return Response(
            {'error': 'Database connection not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Check access
    permission_level = get_user_permission_level(request.user, db_connection)
    if permission_level is None:
        return Response(
            {'error': 'You do not have access to this database'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Get or create chat session
    if session_id:
        try:
            session = ChatSession.objects.get(id=session_id, user=request.user)
        except ChatSession.DoesNotExist:
            return Response(
                {'error': 'Chat session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        session = ChatSession.objects.create(
            title=question[:50] + '...' if len(question) > 50 else question,
            database_connection=db_connection,
            user=request.user
        )

    # Save user message
    user_message = ChatMessage.objects.create(
        session=session,
        message_type='user',
        content=question
    )

    try:
        # Get allowed tables for user
        allowed_tables = get_user_allowed_tables(request.user, db_connection)

        # If user has no specific permissions but has some access,
        # they're the owner and can access all tables
        schema = db_connection.schema_json or {}
        if allowed_tables is None:
            allowed_tables = list(schema.get('tables', {}).keys())

        if not allowed_tables:
            return Response({
                'error': 'You do not have access to any tables in this database',
                'session_id': session.id
            }, status=status.HTTP_403_FORBIDDEN)

        # Build prompts
        system_prompt = build_system_prompt(
            db_type=db_connection.db_type,
            schema=schema,
            allowed_tables=allowed_tables
        )
        user_prompt = build_user_prompt(question, db_connection.db_type)

        # Get LLM response
        llm_service = get_llm_service()
        llm_response = llm_service.generate_sql(system_prompt, user_prompt)

        if not llm_response.sql:
            assistant_message = ChatMessage.objects.create(
                session=session,
                message_type='error',
                content="I couldn't generate a valid SQL query for your question. Please try rephrasing.",
                explanation=llm_response.explanation
            )
            return Response({
                'answer': "I couldn't generate a valid SQL query for your question. Please try rephrasing.",
                'sql_query': None,
                'results': [],
                'chart_type': None,
                'chart_config': {},
                'explanation': llm_response.explanation,
                'session_id': session.id,
                'message_id': assistant_message.id
            })

        # Execute the query
        success, results, message = execute_query_safely(
            db_connection=db_connection,
            query=llm_response.sql,
            permission_level=permission_level
        )

        if not success:
            # Log the actual error for debugging but show user-friendly message
            logger.error(f"Query execution failed: {message}")
            user_friendly_message = "Something went wrong while processing your request. Please try again or rephrase your question."

            assistant_message = ChatMessage.objects.create(
                session=session,
                message_type='error',
                content=user_friendly_message,
                sql_query=llm_response.sql,
                explanation=llm_response.explanation
            )
            return Response({
                'answer': user_friendly_message,
                'sql_query': llm_response.sql if show_sql else None,
                'results': [],
                'chart_type': None,
                'chart_config': {},
                'explanation': llm_response.explanation,
                'session_id': session.id,
                'message_id': assistant_message.id
            })

        # Process chart suggestion
        chart_suggestion = llm_response.chart_suggestion or {}
        chart_type = chart_suggestion.get('type', 'table')
        chart_config = {
            'x_column': chart_suggestion.get('x_column'),
            'y_column': chart_suggestion.get('y_column'),
            'reason': chart_suggestion.get('reason')
        }

        # Generate answer text - keep it simple
        result_count = len(results) if results else 0
        answer = f"Found {result_count} result{'s' if result_count != 1 else ''}."

        # Save assistant message
        assistant_message = ChatMessage.objects.create(
            session=session,
            message_type='assistant',
            content=answer,
            sql_query=llm_response.sql,
            query_results=results or [],
            chart_type=chart_type,
            chart_config=chart_config,
            explanation=llm_response.explanation
        )

        # Update session title if it's new
        if session.messages.count() == 2:  # First exchange
            session.title = question[:50] + ('...' if len(question) > 50 else '')
            session.save()

        return Response({
            'answer': answer,
            'sql_query': llm_response.sql if show_sql else None,
            'results': results or [],
            'chart_type': chart_type,
            'chart_config': chart_config,
            'explanation': llm_response.explanation,
            'session_id': session.id,
            'message_id': assistant_message.id
        })

    except Exception as e:
        logger.error(f"Ask question error: {str(e)}", exc_info=True)

        # Save error message with user-friendly text
        user_friendly_message = "Something went wrong. Please try again later."
        error_message = ChatMessage.objects.create(
            session=session,
            message_type='error',
            content=user_friendly_message
        )

        return Response({
            'error': user_friendly_message,
            'session_id': session.id,
            'message_id': error_message.id
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== Utility Endpoints ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def llm_status(request):
    """Get current LLM provider status."""
    return Response(get_current_provider_info())


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Simple health check endpoint."""
    return Response({'status': 'ok'})
