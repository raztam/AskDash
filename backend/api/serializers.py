"""
AskDash Serializers

Serializers for all API models and authentication.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import (
    DatabaseConnection, TablePermission, ChatSession, ChatMessage,
    PermissionGroup, PermissionGroupTable, UserGroupAssignment
)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError(
                {"email": "A user with this email already exists."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class DatabaseConnectionSerializer(serializers.ModelSerializer):
    """Serializer for DatabaseConnection model."""

    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = DatabaseConnection
        fields = [
            'id', 'name', 'db_type', 'host', 'port', 'database_name',
            'username', 'password', 'file_path', 'schema_json',
            'created_by', 'created_by_username', 'created_at', 'updated_at',
            'is_owner'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'schema_json']

    def get_is_owner(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.created_by == request.user
        return False

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        validated_data['created_by'] = self.context['request'].user
        connection = DatabaseConnection.objects.create(**validated_data)
        if password:
            connection.set_password(password)
            connection.save()
        return connection

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class TablePermissionSerializer(serializers.ModelSerializer):
    """Serializer for TablePermission model."""

    user_username = serializers.CharField(source='user.username', read_only=True)
    granted_by_username = serializers.CharField(source='granted_by.username', read_only=True)

    class Meta:
        model = TablePermission
        fields = [
            'id', 'database_connection', 'user', 'user_username',
            'table_name', 'permission_level', 'granted_by',
            'granted_by_username', 'granted_at'
        ]
        read_only_fields = ['id', 'granted_by', 'granted_at']


class TablePermissionCreateSerializer(serializers.Serializer):
    """Serializer for creating/updating table permissions."""

    username = serializers.CharField()
    table_name = serializers.CharField()
    permission_level = serializers.ChoiceField(choices=['read', 'write', 'admin'])

    def validate_username(self, value):
        try:
            User.objects.get(username=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        return value


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for ChatMessage model."""

    class Meta:
        model = ChatMessage
        fields = [
            'id', 'session', 'message_type', 'content',
            'sql_query', 'query_results', 'chart_type',
            'chart_config', 'explanation', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    """Serializer for ChatSession model."""

    messages = ChatMessageSerializer(many=True, read_only=True)
    database_name = serializers.CharField(source='database_connection.name', read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = [
            'id', 'title', 'database_connection', 'database_name',
            'user', 'messages', 'message_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_message_count(self, obj):
        return obj.messages.count()

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ChatSessionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing chat sessions."""

    database_name = serializers.CharField(source='database_connection.name', read_only=True)
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = [
            'id', 'title', 'database_connection', 'database_name',
            'message_count', 'last_message', 'created_at', 'updated_at'
        ]

    def get_message_count(self, obj):
        return obj.messages.count()

    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return {
                'content': last_msg.content[:100],
                'type': last_msg.message_type,
                'created_at': last_msg.created_at
            }
        return None


class AskQuestionSerializer(serializers.Serializer):
    """Serializer for the ask endpoint."""

    question = serializers.CharField(required=True)
    session_id = serializers.IntegerField(required=False)
    database_id = serializers.IntegerField(required=True)
    show_sql = serializers.BooleanField(default=False)


class AskResponseSerializer(serializers.Serializer):
    """Serializer for the ask endpoint response."""

    answer = serializers.CharField()
    sql_query = serializers.CharField(allow_null=True)
    results = serializers.ListField()
    chart_type = serializers.CharField(allow_null=True)
    chart_config = serializers.DictField()
    explanation = serializers.CharField(allow_null=True)
    session_id = serializers.IntegerField()
    message_id = serializers.IntegerField()


# ==================== Permission Group Serializers ====================

class PermissionGroupTableSerializer(serializers.ModelSerializer):
    """Serializer for tables in a permission group."""

    class Meta:
        model = PermissionGroupTable
        fields = ['id', 'table_name', 'permission_level']
        read_only_fields = ['id']


class UserGroupAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for user group assignments."""

    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    assigned_by_username = serializers.CharField(source='assigned_by.username', read_only=True)

    class Meta:
        model = UserGroupAssignment
        fields = [
            'id', 'user', 'user_username', 'user_email',
            'group', 'assigned_by', 'assigned_by_username', 'assigned_at'
        ]
        read_only_fields = ['id', 'assigned_by', 'assigned_at']


class PermissionGroupSerializer(serializers.ModelSerializer):
    """Serializer for permission groups with nested tables and users."""

    tables = PermissionGroupTableSerializer(many=True, read_only=True)
    user_assignments = UserGroupAssignmentSerializer(many=True, read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    table_count = serializers.SerializerMethodField()
    user_count = serializers.SerializerMethodField()

    class Meta:
        model = PermissionGroup
        fields = [
            'id', 'name', 'description', 'database_connection',
            'tables', 'user_assignments', 'table_count', 'user_count',
            'created_by', 'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_table_count(self, obj):
        return obj.tables.count()

    def get_user_count(self, obj):
        return obj.user_assignments.count()

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class PermissionGroupListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing permission groups."""

    table_count = serializers.SerializerMethodField()
    user_count = serializers.SerializerMethodField()

    class Meta:
        model = PermissionGroup
        fields = [
            'id', 'name', 'description', 'database_connection',
            'table_count', 'user_count', 'created_at', 'updated_at'
        ]

    def get_table_count(self, obj):
        return obj.tables.count()

    def get_user_count(self, obj):
        return obj.user_assignments.count()


class PermissionGroupCreateSerializer(serializers.Serializer):
    """Serializer for creating a permission group with tables."""

    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    database_id = serializers.IntegerField()
    tables = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list
    )


class AddTablesSerializer(serializers.Serializer):
    """Serializer for adding tables to a group."""

    tables = serializers.ListField(
        child=serializers.DictField(),
        required=True
    )


class AssignUserSerializer(serializers.Serializer):
    """Serializer for assigning a user to a group."""

    username = serializers.CharField()

    def validate_username(self, value):
        try:
            User.objects.get(username=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        return value
