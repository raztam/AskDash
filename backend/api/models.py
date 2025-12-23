"""
AskDash Models

Defines the database schema for:
- DatabaseConnection: User database connections
- TablePermission: Table-level access control
- ChatSession: Conversation sessions per database
- ChatMessage: Individual messages in chat sessions
"""

from django.db import models
from django.contrib.auth.models import User
from cryptography.fernet import Fernet
from django.conf import settings
import base64
import hashlib


def get_encryption_key():
    """Generate a valid Fernet key from settings."""
    key = settings.ENCRYPTION_KEY.encode()
    # Use SHA256 to create a 32-byte key, then base64 encode for Fernet
    key_hash = hashlib.sha256(key).digest()
    return base64.urlsafe_b64encode(key_hash)


class DatabaseConnection(models.Model):
    """Stores user database connections with encrypted credentials."""

    DB_TYPES = [
        ('postgresql', 'PostgreSQL'),
        ('mysql', 'MySQL'),
        ('sqlite', 'SQLite'),
        ('mariadb', 'MariaDB'),
        ('mssql', 'Microsoft SQL Server'),
    ]

    name = models.CharField(max_length=255)
    db_type = models.CharField(max_length=20, choices=DB_TYPES)
    host = models.CharField(max_length=255, blank=True, null=True)
    port = models.IntegerField(blank=True, null=True)
    database_name = models.CharField(max_length=255)
    username = models.CharField(max_length=255, blank=True, null=True)
    password_encrypted = models.TextField(blank=True, null=True)
    # For SQLite, this stores the file path
    file_path = models.CharField(max_length=500, blank=True, null=True)

    # Schema stored as JSON
    schema_json = models.JSONField(default=dict, blank=True)

    # Ownership and timestamps
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='database_connections'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.db_type})"

    def set_password(self, password):
        """Encrypt and store the database password."""
        if password:
            f = Fernet(get_encryption_key())
            self.password_encrypted = f.encrypt(password.encode()).decode()

    def get_password(self):
        """Decrypt and return the database password."""
        if self.password_encrypted:
            f = Fernet(get_encryption_key())
            return f.decrypt(self.password_encrypted.encode()).decode()
        return None


class TablePermission(models.Model):
    """Table-level access control for database connections."""

    PERMISSION_LEVELS = [
        ('read', 'Read Only'),
        ('write', 'Read & Write'),
        ('admin', 'Admin'),
    ]

    database_connection = models.ForeignKey(
        DatabaseConnection,
        on_delete=models.CASCADE,
        related_name='permissions'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='table_permissions'
    )
    table_name = models.CharField(max_length=255)
    permission_level = models.CharField(
        max_length=10,
        choices=PERMISSION_LEVELS,
        default='read'
    )
    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='granted_permissions'
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['database_connection', 'user', 'table_name']
        ordering = ['table_name']

    def __str__(self):
        return f"{self.user.username} - {self.table_name} ({self.permission_level})"


class PermissionGroup(models.Model):
    """Permission group for organizing table access by department/role."""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    database_connection = models.ForeignKey(
        DatabaseConnection,
        on_delete=models.CASCADE,
        related_name='permission_groups'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_permission_groups'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['database_connection', 'name']
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.database_connection.name}"


class PermissionGroupTable(models.Model):
    """Tables included in a permission group."""

    PERMISSION_LEVELS = [
        ('read', 'Read Only'),
        ('write', 'Read & Write'),
        ('admin', 'Admin'),
    ]

    group = models.ForeignKey(
        PermissionGroup,
        on_delete=models.CASCADE,
        related_name='tables'
    )
    table_name = models.CharField(max_length=255)
    permission_level = models.CharField(
        max_length=10,
        choices=PERMISSION_LEVELS,
        default='read'
    )

    class Meta:
        unique_together = ['group', 'table_name']
        ordering = ['table_name']

    def __str__(self):
        return f"{self.group.name} - {self.table_name}"


class UserGroupAssignment(models.Model):
    """Assignment of users to permission groups."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='group_assignments'
    )
    group = models.ForeignKey(
        PermissionGroup,
        on_delete=models.CASCADE,
        related_name='user_assignments'
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_group_memberships'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'group']
        ordering = ['-assigned_at']

    def __str__(self):
        return f"{self.user.username} - {self.group.name}"


class ChatSession(models.Model):
    """Chat session for a user with a specific database."""

    title = models.CharField(max_length=255, default='New Chat')
    database_connection = models.ForeignKey(
        DatabaseConnection,
        on_delete=models.CASCADE,
        related_name='chat_sessions'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_sessions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"


class ChatMessage(models.Model):
    """Individual message in a chat session."""

    MESSAGE_TYPES = [
        ('user', 'User Message'),
        ('assistant', 'Assistant Response'),
        ('error', 'Error Message'),
    ]

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()

    # For assistant messages, store additional data
    sql_query = models.TextField(blank=True, null=True)
    query_results = models.JSONField(default=list, blank=True)
    chart_type = models.CharField(max_length=20, blank=True, null=True)
    chart_config = models.JSONField(default=dict, blank=True)
    explanation = models.TextField(blank=True, null=True)
    insights = models.TextField(blank=True, null=True)

    # Multi-step query analysis fields
    intermediate_queries = models.JSONField(default=list, blank=True, help_text="Internal queries executed during multi-step analysis")
    reasoning_steps = models.TextField(blank=True, null=True, help_text="JSON string of reasoning process and intermediate steps")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.message_type}: {self.content[:50]}..."
