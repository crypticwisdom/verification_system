#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from decouple import config

with open('.env', mode="a+") as file:
    file.close()


def main():
    """Run administrative tasks."""
    try:
        if config('env') == 'dev' or os.environ.get('env') == 'dev':
            print("========================== You're running on development environment ==========================")
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'system_core.settings.dev')
        elif config('env') == 'prod' or os.environ.get('env') == 'prod':
            print("========================== You're running on production environment ========================")
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'system_core.settings.prod')
        else:
            print("========================== You're not on any Environment ========================")
    except (Exception, ) as err:
        print(f"======================= \n {err} \n=======================")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
