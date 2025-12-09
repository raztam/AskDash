"""
API URL Configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import (
    RegisterView,
    current_user,
    search_users,
    list_users,
    DatabaseConnectionViewSet,
    TablePermissionViewSet,
    PermissionGroupViewSet,
    ChatSessionViewSet,
    ask_question,
    llm_status,
    health_check,
)

# Create router for viewsets
router = DefaultRouter()
router.register(r'databases', DatabaseConnectionViewSet, basename='database')
router.register(r'permissions', TablePermissionViewSet, basename='permission')
router.register(r'permission-groups', PermissionGroupViewSet, basename='permission-group')
router.register(r'sessions', ChatSessionViewSet, basename='session')

urlpatterns = [
    # Health check
    path('health/', health_check, name='health-check'),

    # Authentication
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/user/', current_user, name='current-user'),

    # User search
    path('users/search/', search_users, name='search-users'),
    path('users/', list_users, name='list-users'),

    # Main ask endpoint
    path('ask/', ask_question, name='ask-question'),

    # LLM status
    path('llm/status/', llm_status, name='llm-status'),

    # Router URLs
    path('', include(router.urls)),
]
