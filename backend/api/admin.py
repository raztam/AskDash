from django.contrib import admin
from .models import DatabaseConnection, TablePermission, ChatSession, ChatMessage


@admin.register(DatabaseConnection)
class DatabaseConnectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'db_type', 'database_name', 'created_by', 'created_at']
    list_filter = ['db_type', 'created_at']
    search_fields = ['name', 'database_name', 'created_by__username']


@admin.register(TablePermission)
class TablePermissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'database_connection', 'table_name', 'permission_level', 'granted_at']
    list_filter = ['permission_level', 'granted_at']
    search_fields = ['user__username', 'table_name']


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'database_connection', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['title', 'user__username']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'message_type', 'created_at']
    list_filter = ['message_type', 'created_at']
    search_fields = ['content']
