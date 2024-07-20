"""
WSGI config for system_core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""
import os
from decouple import config

from django.core.wsgi import get_wsgi_application

if config('env') == 'dev' or os.environ.get('env') == 'dev':
    print("========================== development environment wsgi ==========================")
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'system_core.settings.dev')
elif config('env') == 'prod' or os.environ.get('env') == 'prod':
    print("========================== production environment wsgi ========================")
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'system_core.settings.prod')
else:
    print("========================== You're not on any Environment ========================")

application = get_wsgi_application()
