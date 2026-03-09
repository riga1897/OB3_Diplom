"""Pytest configuration and fixtures."""

import shutil
from collections.abc import Generator
from pathlib import Path
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model

import pytest
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client() -> APIClient:
    """Provide DRF API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client: APIClient, user: Any) -> APIClient:
    """Provide authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def user_factory(db: Any) -> Any:
    """Provide UserFactory for creating test users."""
    from tests.factories import UserFactory

    return UserFactory


@pytest.fixture
def user(db: Any) -> Any:
    """Create test user."""
    from tests.factories import UserFactory

    return UserFactory()


@pytest.fixture
def admin_user(db: Any) -> Any:
    """Create admin user."""
    from tests.factories import UserFactory

    return UserFactory(is_staff=True, is_superuser=True)


@pytest.fixture
def document(db: Any, user: Any) -> Any:
    """Create test document."""
    from tests.factories import DocumentFactory

    return DocumentFactory(owner=user)


@pytest.fixture
def documents(db: Any, user: Any) -> Any:
    """Create multiple test documents."""
    from tests.factories import DocumentFactory

    return DocumentFactory.create_batch(5, owner=user)


@pytest.fixture
def clear_cache() -> Generator[None, None, None]:
    """Clear Django cache before each test."""
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


def _clear_directory(path: Path) -> None:
    """Удалить содержимое директории, но не саму директорию.

    Совместимо с Docker volumes (нельзя удалить mount point).
    """
    if not path.exists():
        return
    for item in path.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_media(request: pytest.FixtureRequest) -> Generator[None, None, None]:
    """Очистка тестовых медиафайлов до и после тестовой сессии.

    Удаляет только содержимое MEDIA_ROOT, не саму папку
    (совместимость с Docker volumes).
    """
    media_root = Path(settings.MEDIA_ROOT)

    _clear_directory(media_root)

    yield

    _clear_directory(media_root)


@pytest.fixture
def temp_media_root(tmp_path: Path) -> Generator[Path, None, None]:
    """Временная директория для медиафайлов в рамках одного теста.

    Используется когда нужна полная изоляция файлов теста.
    """
    media_path = tmp_path / "media" / "documents"
    media_path.mkdir(parents=True, exist_ok=True)
    yield media_path
