#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def get_settings_module() -> str:
    """
    Определяет модуль настроек на основе переменной ENVIRONMENT.

    Приоритет:
    1. DJANGO_SETTINGS_MODULE (если задан явно в окружении)
    2. ENVIRONMENT из .env (development, staging, production, test)
    3. По умолчанию: development
    """
    if "DJANGO_SETTINGS_MODULE" in os.environ:
        return os.environ["DJANGO_SETTINGS_MODULE"]

    try:
        from decouple import config

        environment = config("ENVIRONMENT", default="development")
    except ImportError:
        environment = os.getenv("ENVIRONMENT", "development")

    settings_map = {
        "development": "config.settings.development",
        "staging": "config.settings.staging",
        "production": "config.settings.production",
        "test": "config.settings.test",
    }

    return settings_map.get(environment, "config.settings.development")


def main() -> None:
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", get_settings_module())
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
