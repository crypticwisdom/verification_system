from .base import *
from decouple import config
from django.utils.timezone import timedelta

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', None)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases


DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', None),
        'NAME': config('DB_NAME', None),
        'USER': config('DB_USER', None),
        'HOST': config('DB_HOST', None),
        'PASSWORD': config('DB_PASSWORD', None),
        'PORT': config('DB_PORT', None)
    }
}

# print(config('DB_USER', None), config('DB_NAME', None))
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Simple JWT Settings for Development
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=60),
    'UPDATE_LAST_LOGIN': True,
    'AUTH_HEADER_TYPES': ('Bearer', 'Token',),
}


# CORS Development settings
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    "https://core.tm-dev.xyz",

]

CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

# from corsheaders.defaults import default_headers
CORS_ALLOW_HEADERS = list(default_headers) + [
    "x-api-key",
]

# API header key
X_API_KEY = config('X_API_KEY', None)
