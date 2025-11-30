"""Тесты для management команд."""

from __future__ import annotations

from io import StringIO
from typing import Any
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command

User = get_user_model()


class TestCreateSuperuserCommand:
    """Тесты команды create_superuser."""

    def test_create_superuser_success(self, db: None) -> None:
        """Успешное создание суперпользователя."""
        out = StringIO()
        call_command(
            "create_superuser",
            "--username=testadmin",
            "--email=testadmin@example.com",
            "--password=testpass123",
            stdout=out,
        )

        assert "создан" in out.getvalue()
        assert User.objects.filter(username="testadmin").exists()

        user: Any = User.objects.get(username="testadmin")
        assert user.email == "testadmin@example.com"
        assert user.is_superuser is True
        assert user.is_staff is True
        assert user.check_password("testpass123")

    def test_create_superuser_already_exists(self, db: None) -> None:
        """Идемпотентность — если пользователь существует, пропускаем."""
        User.objects.create_superuser(
            username="existingadmin",
            email="existing@example.com",
            password="pass123",
        )

        out = StringIO()
        call_command(
            "create_superuser",
            "--username=existingadmin",
            stdout=out,
        )

        assert "уже существует" in out.getvalue()
        assert User.objects.filter(username="existingadmin").count() == 1

    def test_create_superuser_with_defaults(self, db: None) -> None:
        """Создание суперпользователя с дефолтными значениями."""
        out = StringIO()
        call_command(
            "create_superuser",
            "--username=defaultadmin",
            stdout=out,
        )

        output = out.getvalue()
        assert "создан" in output
        assert "дефолтный пароль" in output or "Смените" in output

        user: Any = User.objects.get(username="defaultadmin")
        assert user.check_password("admin123")

    def test_create_superuser_from_env(self, db: None) -> None:
        """Создание суперпользователя из переменных окружения."""
        env_vars = {
            "DJANGO_SUPERUSER_USERNAME": "envadmin",
            "DJANGO_SUPERUSER_EMAIL": "envadmin@example.com",
            "DJANGO_SUPERUSER_PASSWORD": "envpass123",
        }

        out = StringIO()
        with patch.dict("os.environ", env_vars):
            call_command("create_superuser", stdout=out)

        assert "создан" in out.getvalue()
        assert User.objects.filter(username="envadmin").exists()


class TestLoadInitialDataCommand:
    """Тесты команды load_initial_data."""

    def test_load_initial_data_dry_run(self, db: None) -> None:
        """Dry-run не загружает данные и показывает план."""
        out = StringIO()
        call_command("load_initial_data", "--dry-run", stdout=out)

        output = out.getvalue()
        assert "DRY-RUN" in output
        assert "Dry-run завершён" in output

    def test_load_initial_data_success(self, db: None) -> None:
        """Успешная загрузка фикстур с очисткой."""
        out = StringIO()
        call_command("load_initial_data", stdout=out)

        output = out.getvalue()
        assert "Очистка таблиц" in output
        assert "Сброс sequences" in output
        assert "Загрузка фикстур" in output
        assert "Загрузка завершена" in output

    def test_load_initial_data_truncates_tables(self, db: None) -> None:
        """Проверка очистки таблиц перед загрузкой."""
        User.objects.create_user(
            username="olduser",
            email="old@example.com",
            password="pass123",
        )
        assert User.objects.filter(username="olduser").exists()

        out = StringIO()
        call_command("load_initial_data", stdout=out)

        assert not User.objects.filter(username="olduser").exists()
        assert User.objects.filter(username="admin").exists()

    def test_load_initial_data_loads_documents(self, db: None) -> None:
        """Проверка загрузки документов из фикстуры."""
        from apps.documents.models import Document

        out = StringIO()
        call_command("load_initial_data", stdout=out)

        assert Document.objects.count() == 6
        assert Document.objects.filter(status="approved").count() == 2
        assert Document.objects.filter(status="pending").count() == 2
        assert Document.objects.filter(status="rejected").count() == 2

    def test_load_initial_data_missing_fixture(self, db: None) -> None:
        """Обработка отсутствующих фикстур."""
        from apps.core.management.commands.load_initial_data import Command

        original_files = Command.FIXTURE_FILES.copy()
        Command.FIXTURE_FILES = ["nonexistent.json"]

        try:
            out = StringIO()
            call_command("load_initial_data", stdout=out)

            output = out.getvalue()
            assert "ПРОПУСК" in output or "пропущено: 1" in output
        finally:
            Command.FIXTURE_FILES = original_files

    def test_fixtures_directory_exists(self) -> None:
        """Проверка что директория fixtures существует."""
        from apps.core.management.commands.load_initial_data import Command

        assert Command.FIXTURES_DIR.exists()
        assert Command.FIXTURES_DIR.is_dir()

    def test_users_fixture_exists(self) -> None:
        """Проверка что фикстура users.json существует."""
        from apps.core.management.commands.load_initial_data import Command

        users_fixture = Command.FIXTURES_DIR / "users.json"
        assert users_fixture.exists()

    def test_documents_fixture_exists(self) -> None:
        """Проверка что фикстура documents.json существует."""
        from apps.core.management.commands.load_initial_data import Command

        documents_fixture = Command.FIXTURES_DIR / "documents.json"
        assert documents_fixture.exists()

    def test_load_initial_data_with_valid_fixture(self, db: None) -> None:
        """Успешная загрузка валидной фикстуры с выводом [OK]."""
        out = StringIO()
        call_command("load_initial_data", stdout=out)

        output = out.getvalue()
        assert "[OK]" in output
        assert "users.json" in output
        assert "documents.json" in output

    def test_load_initial_data_exception_handling(self, db: None) -> None:
        """Обработка исключений при загрузке невалидной фикстуры."""
        import tempfile
        from pathlib import Path

        from apps.core.management.commands.load_initial_data import Command

        with tempfile.TemporaryDirectory() as tmpdir:
            invalid_fixture = Path(tmpdir) / "invalid.json"
            invalid_fixture.write_text('{"invalid": "json structure"}')

            original_dir = Command.FIXTURES_DIR
            original_files = Command.FIXTURE_FILES.copy()
            Command.FIXTURES_DIR = Path(tmpdir)
            Command.FIXTURE_FILES = ["invalid.json"]

            try:
                out = StringIO()
                call_command("load_initial_data", stdout=out)

                output = out.getvalue()
                assert "ОШИБКА" in output or "пропущено: 1" in output
            finally:
                Command.FIXTURES_DIR = original_dir
                Command.FIXTURE_FILES = original_files

    def test_load_initial_data_idempotent(self, db: None) -> None:
        """Идемпотентность — повторная загрузка не ломает данные."""
        out1 = StringIO()
        call_command("load_initial_data", stdout=out1)

        out2 = StringIO()
        call_command("load_initial_data", stdout=out2)

        assert "Загрузка завершена" in out2.getvalue()
        assert User.objects.count() == 2

    def test_truncate_tables_no_tables(self, db: None) -> None:
        """Обработка случая когда нет таблиц для очистки."""
        from apps.core.management.commands.load_initial_data import Command

        original_excluded = Command.EXCLUDED_APPS.copy()
        Command.EXCLUDED_APPS = [
            "contenttypes",
            "auth",
            "admin",
            "sessions",
            "token_blacklist",
            "core",
            "documents",
            "users",
        ]

        try:
            cmd = Command()
            cmd.stdout = StringIO()
            cmd._truncate_tables(dry_run=False)

            output = cmd.stdout.getvalue()
            assert "Нет таблиц для очистки" in output
        finally:
            Command.EXCLUDED_APPS = original_excluded

    def test_reset_sequences_no_tables(self, db: None) -> None:
        """Обработка случая когда нет таблиц для сброса sequences."""
        from apps.core.management.commands.load_initial_data import Command

        original_excluded = Command.EXCLUDED_APPS.copy()
        Command.EXCLUDED_APPS = [
            "contenttypes",
            "auth",
            "admin",
            "sessions",
            "token_blacklist",
            "core",
            "documents",
            "users",
        ]

        try:
            cmd = Command()
            cmd.stdout = StringIO()
            cmd._reset_sequences(dry_run=False)

            output = cmd.stdout.getvalue()
            assert output == ""
        finally:
            Command.EXCLUDED_APPS = original_excluded

    def test_truncate_tables_error_handling(self, db: None) -> None:
        """Обработка ошибок при очистке таблиц."""
        from apps.core.management.commands.load_initial_data import Command

        cmd = Command()
        cmd.stdout = StringIO()

        with patch("django.db.connection.cursor") as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.execute.side_effect = (
                Exception("Test error")
            )
            cmd._truncate_tables(dry_run=False)

        output = cmd.stdout.getvalue()
        assert "ОШИБКА" in output
        assert "Test error" in output

    def test_reset_sequences_error_handling(self, db: None) -> None:
        """Обработка ошибок при сбросе sequences."""
        from apps.core.management.commands.load_initial_data import Command

        cmd = Command()
        cmd.stdout = StringIO()

        with patch("django.db.connection.cursor") as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.execute.side_effect = (
                Exception("Sequence error")
            )
            cmd._reset_sequences(dry_run=False)

        output = cmd.stdout.getvalue()
        assert "ПРОПУСК" in output
        assert "Sequence error" in output
