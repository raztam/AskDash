"""
Django settings for AskDash project.
"""

import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-change-this-in-production')

DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

def _parse_allowed_hosts(raw: str):
    hosts = []
    for item in raw.split(','):
        host = item.strip()
        if host.startswith('http://') or host.startswith('https://'):
            host = host.split('://', 1)[1]
        host = host.rstrip('/')
        if host:
            hosts.append(host)
    return hosts or ['localhost', '127.0.0.1']


ALLOWED_HOSTS = _parse_allowed_hosts(os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1'))

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    # Local apps
    'api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'askdash.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'askdash.wsgi.application'

# Database - prefer DATABASE_URL when provided (e.g., Render/Supabase), fallback to SQLite locally
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(default=DATABASE_URL, conn_max_age=600)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# CORS Settings
CORS_ALLOWED_ORIGINS = os.getenv(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000'
).split(',')

CORS_ALLOW_CREDENTIALS = True

# LLM Configuration
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'ollama')  # 'ollama', 'openai', 'anthropic'

# Ollama settings
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2')

# OpenAI settings
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')

# Anthropic settings
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')

# Encryption key for database credentials
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'your-encryption-key-change-in-production')

# Logging Configuration
LOG_LEVEL = 'DEBUG' if DEBUG else 'INFO'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': LOG_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': LOG_LEVEL,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'askdash.log',
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'query_file': {
            'level': LOG_LEVEL,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'queries.log',
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'llm_file': {
            'level': LOG_LEVEL,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'llm.log',
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'api': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'api.services.query_orchestrator': {
            'handlers': ['console', 'query_file'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'api.services.llm_base': {
            'handlers': ['console', 'llm_file'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'api.services.llm_openai': {
            'handlers': ['console', 'llm_file'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'api.services.llm_anthropic': {
            'handlers': ['console', 'llm_file'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'api.services.llm_ollama': {
            'handlers': ['console', 'llm_file'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': LOG_LEVEL,
    },
}
