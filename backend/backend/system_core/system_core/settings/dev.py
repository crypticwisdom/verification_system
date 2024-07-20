from .base import *
from decouple import config
from datetime import timedelta


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', None)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '89.38.135.41', 'core.tm-dev.xyz']


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
    "http://localhost:8080",
    "http://localhost:80",
    "http://localhost:3000",
    "http://localhost",
    "http://127.0.0.1"
]

CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

# from corsheaders.defaults import default_headers
CORS_ALLOW_HEADERS = list(default_headers) + [
    "x-api-key",
]

# API header key
X_API_KEY = config('X_API_KEY', None)

VERIFY_ME_BASE_URL = config('VERIFY_ME_BASE_URL', None)
VERIFY_ME_BASE_TOKEN = config('VERIFY_ME_BASE_TOKEN', None)


# Email Service
EMAIL_SERVICE_BASE_URL = config('EMAIL_SERVICE_BASE_URL', None)
CLIENT_ID = config('CLIENT_ID', None)

# Frontend URL
FRONTEND_PASSWORD_RESET_BASE_URL = config('FRONTEND_PASSWORD_RESET_BASE_URL', None)
FRONTEND_FORGOT_PASSWORD_URL = config('FRONTEND_FORGOT_PASSWORD_URL', None)
FRONTEND_ACCT_ACTIVATION_URL = config('FRONTEND_ACCT_ACTIVATION_URL', None)
FROM_EMAIL = config('FROM_EMAIL', None)
SUPPORT_EMAIL = config('SUPPORT_EMAIL', None)
PAYMENT_BASE_URL = config('PAYMENT_BASE_URL', None)

PAYMENT_REDIRECT_URL = config('PAYMENT_REDIRECT_URL', None)



