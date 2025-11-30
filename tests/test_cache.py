"""Tests for apps.core.cache module."""

from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from apps.core.cache import CacheManager


@pytest.fixture
def mock_cache() -> Generator[MagicMock, None, None]:
    """Create mock cache object."""
    with patch("apps.core.cache.cache") as mock:
        yield mock


class TestCacheManagerKeyGeneration:
    """Tests for cache key generation."""

    def test_make_key_with_integer(self) -> None:
        """Test key generation with integer identifier."""
        result = CacheManager._make_key("prefix", 123)
        assert result == "prefix:123"

    def test_make_key_with_string(self) -> None:
        """Test key generation with string identifier."""
        result = CacheManager._make_key("prefix", "abc")
        assert result == "prefix:abc"

    def test_make_key_with_uuid(self) -> None:
        """Test key generation with UUID-like string."""
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        result = CacheManager._make_key("task", uuid_str)
        assert result == f"task:{uuid_str}"


class TestCacheManagerDocumentList:
    """Tests for document list caching."""

    def test_get_document_list_returns_cached_data(self, mock_cache: MagicMock) -> None:
        """Test getting cached document list."""
        user_id = 1
        expected_data: list[dict[str, Any]] = [{"id": 1, "title": "Doc"}]
        mock_cache.get.return_value = expected_data

        result = CacheManager.get_document_list(user_id)

        assert result == expected_data
        mock_cache.get.assert_called_once_with("document_list:1")

    def test_get_document_list_returns_none_when_not_cached(
        self, mock_cache: MagicMock
    ) -> None:
        """Test getting non-existent document list."""
        mock_cache.get.return_value = None

        result = CacheManager.get_document_list(999)

        assert result is None

    def test_set_document_list(self, mock_cache: MagicMock) -> None:
        """Test setting document list cache."""
        user_id = 1
        data: list[dict[str, Any]] = [{"id": 1, "title": "Doc"}]

        CacheManager.set_document_list(user_id, data)

        mock_cache.set.assert_called_once_with(
            "document_list:1", data, CacheManager.TIMEOUT_LIST
        )

    def test_invalidate_document_list(self, mock_cache: MagicMock) -> None:
        """Test invalidating document list cache."""
        user_id = 1

        CacheManager.invalidate_document_list(user_id)

        mock_cache.delete.assert_called_once_with("document_list:1")


class TestCacheManagerDocumentDetail:
    """Tests for document detail caching."""

    def test_get_document_detail_returns_cached_data(
        self, mock_cache: MagicMock
    ) -> None:
        """Test getting cached document detail."""
        doc_id = 42
        expected_data: dict[str, Any] = {"id": 42, "title": "Test Doc"}
        mock_cache.get.return_value = expected_data

        result = CacheManager.get_document_detail(doc_id)

        assert result == expected_data
        mock_cache.get.assert_called_once_with("document_detail:42")

    def test_get_document_detail_returns_none_when_not_cached(
        self, mock_cache: MagicMock
    ) -> None:
        """Test getting non-existent document detail."""
        mock_cache.get.return_value = None

        result = CacheManager.get_document_detail(999)

        assert result is None

    def test_set_document_detail(self, mock_cache: MagicMock) -> None:
        """Test setting document detail cache."""
        doc_id = 42
        data: dict[str, Any] = {"id": 42, "title": "Test Doc"}

        CacheManager.set_document_detail(doc_id, data)

        mock_cache.set.assert_called_once_with(
            "document_detail:42", data, CacheManager.TIMEOUT_DETAIL
        )

    def test_invalidate_document_detail(self, mock_cache: MagicMock) -> None:
        """Test invalidating document detail cache."""
        doc_id = 42

        CacheManager.invalidate_document_detail(doc_id)

        mock_cache.delete.assert_called_once_with("document_detail:42")


class TestCacheManagerStatistics:
    """Tests for statistics caching."""

    def test_get_statistics_returns_cached_data(self, mock_cache: MagicMock) -> None:
        """Test getting cached statistics."""
        user_id = 1
        expected_data: dict[str, int] = {"total": 10, "approved": 5}
        mock_cache.get.return_value = expected_data

        result = CacheManager.get_statistics(user_id)

        assert result == expected_data
        mock_cache.get.assert_called_once_with("document_stats:1")

    def test_get_statistics_returns_none_when_not_cached(
        self, mock_cache: MagicMock
    ) -> None:
        """Test getting non-existent statistics."""
        mock_cache.get.return_value = None

        result = CacheManager.get_statistics(999)

        assert result is None

    def test_set_statistics(self, mock_cache: MagicMock) -> None:
        """Test setting statistics cache."""
        user_id = 1
        data: dict[str, int] = {"total": 10, "approved": 5}

        CacheManager.set_statistics(user_id, data)

        mock_cache.set.assert_called_once_with(
            "document_stats:1", data, CacheManager.TIMEOUT_STATS
        )

    def test_invalidate_statistics(self, mock_cache: MagicMock) -> None:
        """Test invalidating statistics cache."""
        user_id = 1

        CacheManager.invalidate_statistics(user_id)

        mock_cache.delete.assert_called_once_with("document_stats:1")


class TestCacheManagerProcessingTask:
    """Tests for processing task caching."""

    def test_get_processing_task_returns_cached_data(
        self, mock_cache: MagicMock
    ) -> None:
        """Test getting cached processing task."""
        task_id = "task-123-abc"
        expected_data: dict[str, str] = {"status": "processing"}
        mock_cache.get.return_value = expected_data

        result = CacheManager.get_processing_task(task_id)

        assert result == expected_data
        mock_cache.get.assert_called_once_with("processing_task:task-123-abc")

    def test_get_processing_task_returns_none_when_not_cached(
        self, mock_cache: MagicMock
    ) -> None:
        """Test getting non-existent processing task."""
        mock_cache.get.return_value = None

        result = CacheManager.get_processing_task("nonexistent")

        assert result is None

    def test_set_processing_task(self, mock_cache: MagicMock) -> None:
        """Test setting processing task cache."""
        task_id = "task-123-abc"
        data: dict[str, str] = {"status": "processing"}

        CacheManager.set_processing_task(task_id, data)

        mock_cache.set.assert_called_once_with(
            "processing_task:task-123-abc", data, CacheManager.TIMEOUT_TASK
        )

    def test_invalidate_processing_task(self, mock_cache: MagicMock) -> None:
        """Test invalidating processing task cache."""
        task_id = "task-123-abc"

        CacheManager.invalidate_processing_task(task_id)

        mock_cache.delete.assert_called_once_with("processing_task:task-123-abc")


class TestCacheManagerBulkInvalidation:
    """Tests for bulk cache invalidation."""

    def test_invalidate_user_caches(self, mock_cache: MagicMock) -> None:
        """Test invalidating all user caches."""
        user_id = 1

        CacheManager.invalidate_user_caches(user_id)

        assert mock_cache.delete.call_count == 2
        mock_cache.delete.assert_any_call("document_list:1")
        mock_cache.delete.assert_any_call("document_stats:1")

    def test_invalidate_document_caches(self, mock_cache: MagicMock) -> None:
        """Test invalidating all document-related caches."""
        doc_id = 42
        user_id = 1

        CacheManager.invalidate_document_caches(doc_id, user_id)

        assert mock_cache.delete.call_count == 3
        mock_cache.delete.assert_any_call("document_detail:42")
        mock_cache.delete.assert_any_call("document_list:1")
        mock_cache.delete.assert_any_call("document_stats:1")


class TestCacheManagerTimeouts:
    """Tests for cache timeout values."""

    def test_timeout_list_value(self) -> None:
        """Test list cache timeout is 5 minutes."""
        assert CacheManager.TIMEOUT_LIST == 300

    def test_timeout_detail_value(self) -> None:
        """Test detail cache timeout is 10 minutes."""
        assert CacheManager.TIMEOUT_DETAIL == 600

    def test_timeout_stats_value(self) -> None:
        """Test stats cache timeout is 3 minutes."""
        assert CacheManager.TIMEOUT_STATS == 180

    def test_timeout_task_value(self) -> None:
        """Test task cache timeout is 5 minutes."""
        assert CacheManager.TIMEOUT_TASK == 300
