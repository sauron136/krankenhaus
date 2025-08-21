import os
from pathlib import Path
from datetime import timedelta
from decouple import config  # Import python-decouple

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
    'django_filters',
    'drf_yasg',
]

LOCAL_APPS = [
    'authentication',
    'accounts',
    'medical_records',
    'appointments',
    'pharmacy',
    'inventory',
    'lab',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Middleware
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'authentication.middleware.JWTAuthenticationMiddleware',
]

# URL and WSGI configuration
ROOT_URLCONF = 'krankenhaus.urls'
WSGI_APPLICATION = 'krankenhaus.wsgi.application'

# Templates
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

# Authentication
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_USER_MODEL = 'authentication.User'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'authentication.jwt_handler.CustomJWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # For admin
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'authentication.exceptions.custom_exception_handler',
}

# JWT Settings
JWT_SETTINGS = {
    'ACCESS_TOKEN_LIFETIME': 60 * 60,  # 1 hour in seconds
    'REFRESH_TOKEN_LIFETIME': 60 * 60 * 24 * 7,  # 7 days in seconds
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': config('SECRET_KEY'),  # Load SECRET_KEY from .env
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('authentication.jwt_handler.CustomJWTHandler',),
}

# Email settings for OTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')  # Load from .env
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')  # Load from .env
DEFAULT_FROM_EMAIL = f'Hospital Management System <{config("EMAIL_HOST_USER")}>'

# Cache settings for token blacklist
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),  # Load from .env, with fallback
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Session settings
SESSION_COOKIE_AGE = 60 * 60 * 24  # 1 day
SESSION_COOKIE_SECURE = True  # Set to True in production with HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# CSRF settings
CSRF_COOKIE_SECURE = True  # Set to True in production with HTTPS
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'hospital_management.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'authentication': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'accounts': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# CORS settings for frontend
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',  # React development server
    'http://127.0.0.1:3000',
    config('PRODUCTION_DOMAIN', default='https://yourdomain.com'),  # Load from .env, with fallback
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = config('TIME_ZONE', default='Africa/Lagos')  # Load from .env, with fallback
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom settings for hospital management
HOSPITAL_SETTINGS = {
    'OTP_EXPIRY_MINUTES': 10,
    'PASSWORD_RESET_OTP_EXPIRY_MINUTES': 15,
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOGIN_LOCKOUT_DURATION_MINUTES': 30,
    'PATIENT_ID_PREFIX': 'HMS',
    'EMPLOYEE_ID_PREFIX': 'EMP',
    'APPOINTMENT_BOOKING_DAYS_ADVANCE': 30,
    'EMERGENCY_ACCESS_TIMEOUT_HOURS': 2,
}

# Environment-specific settings
DEBUG = config('DEBUG', default=False, cast=bool)  # Load DEBUG from .env, cast to boolean
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    INTERNAL_IPS = [
        '127.0.0.1',
        'localhost',
    ]
    # Django Debug Toolbar (if used)
    if 'debug_toolbar' in INSTALLED_APPS:
        MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
else:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Email settings already loaded via config() above
