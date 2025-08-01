#settings.py

# from pathlib import Path
# from datetime import timedelta
# import os
# # import sys
# import sys
# sys.path.append('/root/DjangoReactFaceRec/Backend/Yolo/ultralytics/yolo/v8/detect/deep_sort_pytorch')

# # sys.path.append('/usr/local/lib/python3.10/dist-packages')
# # RQ_WORKERS = int(os.environ.get('RQ_WORKERS', os.cpu_count()))

# # Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR = Path(__file__).resolve().parent.parent


# # Quick-start development settings - unsuitable for production
# # See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# # SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 'django-insecure-e1#u33m#m2w1b0i_a1%rtq*zkzk$rpo7o#-(039m-d^%ky9b^='

# # SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = True

# ALLOWED_HOSTS = ["*"]


# # Application definition
# # CELERY_BROKER_URL = 'redis://:admin@redis-primary-service:6379/0'
# # CELERY_RESULT_BACKEND = 'redis://:admin@redis-primary-service:6379/0'
# CELERY_TASK_ACKS_LATE = True
# CELERY_WORKER_SEND_TASK_EVENTS = True
# CELERY_SEND_EVENTS = True
# CELERY_SEND_SENT_EVENT = True
# CELERY_TASK_TRACK_STARTED = True
# CELERY_RESULT_PERSISTENT = True
# CELERY_REDIS_SOCKET_KEEPALIVE = True
# CELERY_BROKER_POOL_LIMIT = None
# CELERY_BROKER_CONNECTION_TIMEOUT = 300
# CELERY_BROKER_MAX_RETRIES = None
# CELERY_WORKER_LOST_WAIT = 300
# CELERY_WORKER_STATE_DB = "worker.db"
# CELERY_WORKER_CANCEL_LONG_RUNNING_TASKS_ON_CONNECTION_LOSS = True
# CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
# CELERY_BROKER_CHANNEL_ERROR_RETRY = True
# CELERYBEAT_SCHEDULE = {
#     'cleanup-temp-files': {
#         'task': 'Api.task.cleanup_old_temp_files',
#         'schedule': timedelta(minutes=1),  
#     },
# }

# INSTALLED_APPS = [
#     'corsheaders',
#     'daphne',
#     'django.contrib.admin',
#     'django.contrib.auth',
#     'django.contrib.contenttypes',
#     'django.contrib.sessions',
#     'django.contrib.messages',
#     'django.contrib.staticfiles',
#     'rest_framework',
#     'rest_framework_simplejwt.token_blacklist',
#     'rest_framework_simplejwt',
#     'Api.apps.ApiConfig',
#     'Notifications.apps.NotificationsConfig',
#     'status',
#     'PeopleCounting.apps.PeoplecountingConfig',

#     'celery',
#     'redis'
# ]
# REST_FRAMEWORK = {

#    'DEFAULT_AUTHENTICATION_CLASSES': (
#         'Backend.costum_auth.BlueDoveJWTAuthentication',  # Update this path

#         'rest_framework_simplejwt.authentication.JWTAuthentication',
#     ),
#     'DEFAULT_PERMISSION_CLASSES': [
#         'rest_framework.permissions.IsAuthenticated',
#     ],
#     'DEFAULT_PERMISSION_CLASSES': [
#         'rest_framework.permissions.AllowAny',
#     ]
# }
# SIMPLE_JWT = {
#     'ACCESS_TOKEN_LIFETIME': timedelta(days=14),
#     'REFRESH_TOKEN_LIFETIME': timedelta(days=50),
#     'ROTATE_REFRESH_TOKENS': True,
#     'BLACKLIST_AFTER_ROTATION': True,
#     'UPDATE_LAST_LOGIN': False,
#     "TOKEN_OBTAIN_SERIALIZER": "Api.serializers.MyTokenObtainPairSerializer",

#     'ALGORITHM': 'HS256',

#     'VERIFYING_KEY': None,
#     'AUDIENCE': None,
#     'ISSUER': None,
#     'JWK_URL': None,
#     'LEEWAY': 0,

#     'AUTH_HEADER_TYPES': ('Bearer',),
#     'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
#     'USER_ID_FIELD': 'id',
#     'USER_ID_CLAIM': 'user_id',
#     'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

#     'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
#     'TOKEN_TYPE_CLAIM': 'token_type',
#     'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

#     'JTI_CLAIM': 'jti',

#     'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
#     'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
#     'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
# }
# MIDDLEWARE = [
#     "corsheaders.middleware.CorsMiddleware",
#     'django.middleware.security.SecurityMiddleware',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     'django.middleware.clickjacking.XFrameOptionsMiddleware',
# ]
# CORS_ALLOW_ALL_ORIGINS = True
# # CORS_ALLOWED_ORIGINS = [
# #     'http://localhost:9999',
# # ]
# ROOT_URLCONF = 'Backend.urls'
# AUTH_USER_MODEL = 'Api.CustomUser'
# ASGI_APPLICATION = 'Backend.asgi.application'

# CHANNEL_LAYERS = {
#     'default': {
#         'BACKEND': 'channels_redis.core.RedisChannelLayer',
#         'CONFIG': {
#             "hosts": [os.getenv('REDIS_URL', 'redis://:admin@redis-primary-service:6379/0')],
#         },
#     },
#     'status': {
#         'BACKEND': 'channels_redis.core.RedisChannelLayer',
#         'CONFIG': {
#             "hosts": [os.getenv('REDIS_CHANNEL_URL', 'redis://:admin@redis-channels-service:6380/1')],
#         },
#     },
# }
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#         'LOCATION': os.getenv('REDIS_URL', 'redis://:admin@redis-primary-service:6379/1'),
#         'TIMEOUT': 300,  # 5 minutes default
       
#     }
# }
# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.debug',
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#             ],
#         },
#     },
# ]

# # WSGI_APPLICATION = 'Backend.wsgi.application'



# # Database
# # https://docs.djangoproject.com/en/5.0/ref/settings/#databases

# DATABASES = {    
#    "default": {        
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": os.getenv('POSTGRES_DB', 'FaceApi'),
#         "USER": os.getenv('POSTGRES_USER', 'FaceApi'),
#         "PASSWORD": os.getenv('POSTGRES_PASSWORD', 'example'),
#         "HOST": os.getenv('DATABASE_HOST', 'postgres-service'),
#         "PORT": os.getenv('DATABASE_PORT', '5432'),
#     },
#    'OPTIONS': {
#             'MIN_CONNECTIONS': 8,
#             'MAX_CONNECTIONS': 32,
#             'CONN_MAX_AGE': 60,  # 1 minute connection persistence
#         }
# }

# # Password validation
# # https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

# AUTH_PASSWORD_VALIDATORS = [
#     {
#         'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
#     },
# ]


# # Internationalization
# # https://docs.djangoproject.com/en/5.0/topics/i18n/

# LANGUAGE_CODE = 'en-us'

# TIME_ZONE = 'UTC'

# USE_I18N = True

# USE_TZ = True


# # Static files (CSS, JavaScript, Images)
# # https://docs.djangoproject.com/en/5.0/howto/static-files/

# STATIC_URL = 'static/'
# MEDIA_URL = '/database/'
# MEDIA_ROOT = BASE_DIR.joinpath('database/')
# # Default primary key field type
# # https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

# DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# # GPU Configuration
# GPU_COUNT = 2  # 2 GPUs per node
# GPU_DEVICES = "0,1"  # Local GPU devices
# CUDA_VISIBLE_DEVICES = os.getenv('CUDA_VISIBLE_DEVICES', '0,1')

# # Celery GPU Configuration
# CELERY_GPU_SETTINGS = {
#     'GPU_COUNT': GPU_COUNT,
#     'GPU_DEVICES': GPU_DEVICES,
#     'CUDA_VISIBLE_DEVICES': CUDA_VISIBLE_DEVICES,
#     'PYTORCH_CUDA_ALLOC_CONF': 'max_split_size_mb:256',
#     'NCCL_DEBUG': 'INFO',
#     'NCCL_IB_DISABLE': '1',
#     'NCCL_P2P_DISABLE': '1',
#     'CUDA_VERSION': '12.6',
#     'CUDA_LAUNCH_BLOCKING': '0',
#     'OMP_NUM_THREADS': '4',
#     'MALLOC_TRIM_THRESHOLD_': '100000',
# }

# # Add GPU settings to Celery configuration
# CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://:admin@redis-primary-service:6379/0')
# CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://:admin@redis-primary-service:6379/0')
# CELERY_TASK_ACKS_LATE = True
# CELERY_WORKER_SEND_TASK_EVENTS = True
# CELERY_SEND_EVENTS = True
# CELERY_SEND_SENT_EVENT = True
# CELERY_TASK_TRACK_STARTED = True
# CELERY_RESULT_PERSISTENT = True
# CELERY_REDIS_SOCKET_KEEPALIVE = True
# CELERY_BROKER_POOL_LIMIT = None
# CELERY_BROKER_CONNECTION_TIMEOUT = 300
# CELERY_BROKER_MAX_RETRIES = None
# CELERY_WORKER_LOST_WAIT = 300
# CELERY_WORKER_STATE_DB = "worker.db"
# CELERY_WORKER_CANCEL_LONG_RUNNING_TASKS_ON_CONNECTION_LOSS = True
# CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
# CELERY_BROKER_CHANNEL_ERROR_RETRY = True

# # Add GPU settings to environment variables
# for key, value in CELERY_GPU_SETTINGS.items():
#     os.environ[key] = str(value)




# Fixed Django settings.py
from pathlib import Path
from datetime import timedelta
import os
import sys
sys.path.append('/root/DjangoReactFaceRec/Backend/Yolo/ultralytics/yolo/v8/detect/deep_sort_pytorch')

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-e1#u33m#m2w1b0i_a1%rtq*zkzk$rpo7o#-(039m-d^%ky9b^='

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

# Redis Configuration
REDIS_PRIMARY_URL = os.getenv('REDIS_URL', 'redis://:admin@redis-primary-service:6379/0')
REDIS_CHANNELS_URL = os.getenv('REDIS_CHANNEL_URL', 'redis://:admin@redis-channels-service:6380/0')

# Celery Configuration
CELERY_BROKER_URL = REDIS_PRIMARY_URL
CELERY_RESULT_BACKEND = REDIS_PRIMARY_URL
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_SEND_TASK_EVENTS = True
CELERY_SEND_EVENTS = True
CELERY_SEND_SENT_EVENT = True
CELERY_TASK_TRACK_STARTED = True
CELERY_RESULT_PERSISTENT = True
CELERY_REDIS_SOCKET_KEEPALIVE = True
CELERY_BROKER_POOL_LIMIT = None
CELERY_BROKER_CONNECTION_TIMEOUT = 300
CELERY_BROKER_MAX_RETRIES = None
CELERY_WORKER_LOST_WAIT = 300
CELERY_WORKER_STATE_DB = "worker.db"
CELERY_WORKER_CANCEL_LONG_RUNNING_TASKS_ON_CONNECTION_LOSS = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_CHANNEL_ERROR_RETRY = True

CELERYBEAT_SCHEDULE = {
    'cleanup-temp-files': {
        'task': 'Api.task.cleanup_old_temp_files',
        'schedule': timedelta(minutes=1),  
    },
}

INSTALLED_APPS = [
    'corsheaders',
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'rest_framework_simplejwt',
    'Api.apps.ApiConfig',
    'Notifications.apps.NotificationsConfig',
    'status',
    'PeopleCounting.apps.PeoplecountingConfig',
    'celery',
    'redis'
]

REST_FRAMEWORK = {
   'DEFAULT_AUTHENTICATION_CLASSES': (
        'Backend.costum_auth.BlueDoveJWTAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ]
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=14),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=50),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,
    "TOKEN_OBTAIN_SERIALIZER": "Api.serializers.MyTokenObtainPairSerializer",
    'ALGORITHM': 'HS256',
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True
ROOT_URLCONF = 'Backend.urls'
AUTH_USER_MODEL = 'Api.CustomUser'
ASGI_APPLICATION = 'Backend.asgi.application'

# FIXED: Channel Layers Configuration - Include both default and status layers
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [REDIS_CHANNELS_URL],  # Use channels Redis service
            "capacity": 1000,
            "expiry": 60,
            "group_expiry": 3600,
            "symmetric_encryption_keys": [SECRET_KEY],
            "prefix": "asgi:default:",
        },
    },
    'status': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [REDIS_CHANNELS_URL],  # Use same channels Redis service
            "capacity": 1000,
            "expiry": 60,
            "group_expiry": 3600,
            "symmetric_encryption_keys": [SECRET_KEY],
            "prefix": "asgi:status:",  # Different prefix to avoid conflicts
        },
    },
}

# FIXED: Cache Configuration - Use primary Redis with different database
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://:admin@redis-primary-service:6379/1',  # Database 1 for cache
        'TIMEOUT': 300,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
                'socket_keepalive': True,
                'socket_keepalive_options': {},
            }
        },
        'KEY_PREFIX': 'facerec',
    }
}

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

# Database
DATABASES = {    
   "default": {        
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv('POSTGRES_DB', 'FaceApi'),
        "USER": os.getenv('POSTGRES_USER', 'FaceApi'),
        "PASSWORD": os.getenv('POSTGRES_PASSWORD', 'example'),
        "HOST": os.getenv('DATABASE_HOST', 'postgres-service'),
        "PORT": os.getenv('DATABASE_PORT', '5432'),
        'OPTIONS': {
            'connect_timeout': 10,
        },
        'CONN_MAX_AGE': 60,
        'CONN_HEALTH_CHECKS': True,
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR.joinpath('staticfiles')
STATICFILES_DIRS = [
    BASE_DIR.joinpath('static'),
]

# Media files
MEDIA_URL = '/database/'
MEDIA_ROOT = BASE_DIR.joinpath('database/')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# GPU Configuration
GPU_COUNT = 2
GPU_DEVICES = "0,1"
CUDA_VISIBLE_DEVICES = os.getenv('CUDA_VISIBLE_DEVICES', '0,1')

CELERY_GPU_SETTINGS = {
    'GPU_COUNT': GPU_COUNT,
    'GPU_DEVICES': GPU_DEVICES,
    'CUDA_VISIBLE_DEVICES': CUDA_VISIBLE_DEVICES,
    'PYTORCH_CUDA_ALLOC_CONF': 'max_split_size_mb:256',
    'NCCL_DEBUG': 'INFO',
    'NCCL_IB_DISABLE': '1',
    'NCCL_P2P_DISABLE': '1',
    'CUDA_VERSION': '12.6',
    'CUDA_LAUNCH_BLOCKING': '0',
    'OMP_NUM_THREADS': '4',
    'MALLOC_TRIM_THRESHOLD_': '100000',
}

# Add GPU settings to environment variables
for key, value in CELERY_GPU_SETTINGS.items():
    os.environ[key] = str(value)

# WebSocket Configuration for Stream Status
WEBSOCKET_URL = os.getenv('WEBSOCKET_URL', 'ws://django-backend-gpu-0-service:9898/wsStatus/')

# Logging Configuration for better debugging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'channels': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'Api.helpers': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}