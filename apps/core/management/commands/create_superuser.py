"""
Management команда для создания суперпользователя.

Использование:
    python manage.py create_superuser
    python manage.py create_superuser --username admin --password MyPass123

Переменные окружения (опционально):
    DJANGO_SUPERUSER_USERNAME - имя пользователя (по умолчанию: admin)
    DJANGO_SUPERUSER_EMAIL - email (по умолчанию: admin@example.com)
    DJANGO_SUPERUSER_PASSWORD - пароль (по умолчанию: admin123)

Docker:
    docker compose exec web python manage.py create_superuser
"""

from __future__ import annotations

import os
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

DEFAULT_PW = "admin123"


class Command(BaseCommand):
    """Создание суперпользователя (идемпотентно)."""

    help = "Создаёт суперпользователя с дефолтными или указанными параметрами"

    def add_arguments(self, parser: Any) -> None:
        """Добавить аргументы командной строки."""
        parser.add_argument(
            "--username",
            type=str,
            default=os.getenv("DJANGO_SUPERUSER_USERNAME", "admin"),
            help="Имя пользователя (по умолчанию: admin)",
        )
        parser.add_argument(
            "--email",
            type=str,
            default=os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@example.com"),
            help="Email (по умолчанию: admin@example.com)",
        )
        parser.add_argument(
            "--password",
            type=str,
            default=os.getenv("DJANGO_SUPERUSER_PASSWORD", DEFAULT_PW),
            help=f"Пароль (по умолчанию: {DEFAULT_PW})",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Выполнить команду."""
        username: str = options["username"]
        email: str = options["email"]
        password: str = options["password"]

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(
                    f"Суперпользователь '{username}' уже существует. Пропускаем."
                )
            )
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )

        self.stdout.write(self.style.SUCCESS(f"Суперпользователь '{username}' создан!"))

        if password == DEFAULT_PW:
            self.stdout.write(
                self.style.WARNING(
                    f"Используется дефолтный пароль '{DEFAULT_PW}'. "
                    "Смените его в админке!"
                )
            )
