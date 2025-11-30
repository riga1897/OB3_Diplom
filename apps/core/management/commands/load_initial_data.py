"""
Management команда для загрузки начальных данных из фикстур.

Использование:
    python manage.py load_initial_data

Действия:
    1. Очистка всех таблиц (TRUNCATE CASCADE)
    2. Сброс sequences (счётчиков)
    3. Загрузка фикстур в правильном порядке

Фикстуры:
    fixtures/users.json - пользователи (admin, user)
    fixtures/documents.json - документы (примеры)

Docker:
    docker compose exec web python manage.py load_initial_data
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    """Загрузка начальных данных из фикстур с полной очисткой базы."""

    help = "Очищает базу и загружает начальные данные из фикстур (fixtures/)"

    FIXTURES_DIR = (
        Path(__file__).resolve().parent.parent.parent.parent.parent / "fixtures"
    )

    FIXTURE_FILES = [
        "users.json",
        "documents.json",
    ]

    EXCLUDED_APPS = [
        "contenttypes",
        "auth",
        "admin",
        "sessions",
        "token_blacklist",
    ]

    def add_arguments(self, parser: Any) -> None:
        """Добавить аргументы командной строки."""
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Показать какие действия будут выполнены, но не выполнять",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Выполнить команду."""
        dry_run: bool = options["dry_run"]

        self.stdout.write(self.style.NOTICE(f"Директория фикстур: {self.FIXTURES_DIR}"))
        self.stdout.write("")

        self._truncate_tables(dry_run)
        self.stdout.write("")

        self._reset_sequences(dry_run)
        self.stdout.write("")

        self._load_fixtures(dry_run)

    def _get_app_tables(self) -> list[str]:
        """Получить список таблиц приложений для очистки."""
        tables: list[str] = []

        for model in apps.get_models():
            app_label = model._meta.app_label
            if app_label in self.EXCLUDED_APPS:
                continue
            table_name = model._meta.db_table
            tables.append(table_name)

        return tables

    def _truncate_tables(self, dry_run: bool) -> None:
        """Очистить все таблицы приложений."""
        tables = self._get_app_tables()

        if not tables:
            self.stdout.write(self.style.WARNING("Нет таблиц для очистки"))
            return

        self.stdout.write(self.style.NOTICE("Очистка таблиц:"))

        for table in tables:
            quoted_table = connection.ops.quote_name(table)
            if dry_run:
                self.stdout.write(f"  [DRY-RUN] TRUNCATE {quoted_table} CASCADE")
            else:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(f"TRUNCATE TABLE {quoted_table} CASCADE")
                    self.stdout.write(self.style.SUCCESS(f"  [OK] {table}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  [ОШИБКА] {table}: {e}"))

    def _reset_sequences(self, dry_run: bool) -> None:
        """Сбросить sequences (счётчики) для всех таблиц."""
        tables = self._get_app_tables()

        if not tables:
            return

        self.stdout.write(self.style.NOTICE("Сброс sequences:"))

        for table in tables:
            sequence_name = f"{table}_id_seq"
            quoted_sequence = connection.ops.quote_name(sequence_name)
            if dry_run:
                self.stdout.write(
                    f"  [DRY-RUN] ALTER SEQUENCE {quoted_sequence} RESTART WITH 1"
                )
            else:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            f"ALTER SEQUENCE IF EXISTS {quoted_sequence} RESTART WITH 1"
                        )
                    self.stdout.write(self.style.SUCCESS(f"  [OK] {sequence_name}"))
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f"  [ПРОПУСК] {sequence_name}: {e}")
                    )

    def _load_fixtures(self, dry_run: bool) -> None:
        """Загрузить фикстуры в правильном порядке."""
        self.stdout.write(self.style.NOTICE("Загрузка фикстур:"))

        loaded_count = 0
        skipped_count = 0

        for fixture_name in self.FIXTURE_FILES:
            fixture_path = self.FIXTURES_DIR / fixture_name

            if not fixture_path.exists():
                self.stdout.write(
                    self.style.WARNING(f"  [ПРОПУСК] {fixture_name} — файл не найден")
                )
                skipped_count += 1
                continue

            if dry_run:
                self.stdout.write(f"  [DRY-RUN] {fixture_name}")
            else:
                try:
                    call_command("loaddata", str(fixture_path), verbosity=0)
                    self.stdout.write(self.style.SUCCESS(f"  [OK] {fixture_name}"))
                    loaded_count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"  [ОШИБКА] {fixture_name}: {e}")
                    )
                    skipped_count += 1

        self.stdout.write("")
        if dry_run:
            self.stdout.write(
                self.style.NOTICE(
                    f"Dry-run завершён. Фикстур: {len(self.FIXTURE_FILES)}, "
                    f"таблиц: {len(self._get_app_tables())}"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Загрузка завершена. Загружено: {loaded_count}, пропущено: {skipped_count}"
                )
            )
