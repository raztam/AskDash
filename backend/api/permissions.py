"""
Custom Permissions

Permission classes for AskDash API.
"""

from rest_framework import permissions
from .models import DatabaseConnection, TablePermission


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        return obj.created_by == request.user


class IsDatabaseOwner(permissions.BasePermission):
    """
    Permission that only allows database owners to modify connection settings.
    """

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, DatabaseConnection):
            return obj.created_by == request.user
        return False


class HasDatabaseAccess(permissions.BasePermission):
    """
    Permission that checks if user has access to a database.
    User has access if they:
    1. Own the database connection
    2. Have explicit table permissions
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        if isinstance(obj, DatabaseConnection):
            db_connection = obj
        else:
            return False

        # Owner always has access
        if db_connection.created_by == user:
            return True

        # Check for explicit permissions
        has_permission = TablePermission.objects.filter(
            database_connection=db_connection,
            user=user
        ).exists()

        return has_permission


def get_user_allowed_tables(user, db_connection) -> list:
    """
    Get the list of tables a user is allowed to access.

    Args:
        user: The User object
        db_connection: The DatabaseConnection object

    Returns:
        List of table names the user can access, or None if they have full access
    """
    # Owners have access to all tables
    if db_connection.created_by == user:
        return None  # None means all tables

    # Get explicit permissions
    permissions = TablePermission.objects.filter(
        database_connection=db_connection,
        user=user
    ).values_list('table_name', flat=True)

    return list(permissions)


def get_user_permission_level(user, db_connection, table_name: str = None) -> str:
    """
    Get the user's permission level for a database or specific table.

    Args:
        user: The User object
        db_connection: The DatabaseConnection object
        table_name: Optional specific table name

    Returns:
        Permission level: 'admin', 'write', 'read', or None
    """
    # Owners always have admin access
    if db_connection.created_by == user:
        return 'admin'

    # Check explicit permissions
    query = TablePermission.objects.filter(
        database_connection=db_connection,
        user=user
    )

    if table_name:
        query = query.filter(table_name=table_name)

    permission = query.first()

    if permission:
        return permission.permission_level

    return None
