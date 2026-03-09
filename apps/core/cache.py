"""Cache management utilities for ensuring consistency."""

from typing import Any

from django.core.cache import cache


class CacheManager:
    """Centralized cache manager for document-related caching.

    Provides consistent cache key generation and invalidation patterns
    to prevent stale data and race conditions.

    Cache key patterns:
        - document_list:{user_id} - User's document list
        - document_detail:{doc_id} - Individual document details
        - document_stats:{user_id} - User's statistics
        - processing_task:{task_id} - Processing task details
    """

    # Cache timeouts (seconds)
    TIMEOUT_LIST = 300  # 5 minutes for lists
    TIMEOUT_DETAIL = 600  # 10 minutes for details
    TIMEOUT_STATS = 180  # 3 minutes for statistics
    TIMEOUT_TASK = 300  # 5 minutes for tasks

    @classmethod
    def _make_key(cls, prefix: str, identifier: Any) -> str:
        """Generate consistent cache key."""
        return f"{prefix}:{identifier}"

    @classmethod
    def get_document_list(cls, user_id: int) -> Any | None:
        """Get cached document list for user."""
        key = cls._make_key("document_list", user_id)
        return cache.get(key)

    @classmethod
    def set_document_list(cls, user_id: int, data: Any) -> None:
        """Cache document list for user."""
        key = cls._make_key("document_list", user_id)
        cache.set(key, data, cls.TIMEOUT_LIST)

    @classmethod
    def invalidate_document_list(cls, user_id: int) -> None:
        """Invalidate document list cache for user."""
        key = cls._make_key("document_list", user_id)
        cache.delete(key)

    @classmethod
    def get_document_detail(cls, doc_id: int) -> Any | None:
        """Get cached document details."""
        key = cls._make_key("document_detail", doc_id)
        return cache.get(key)

    @classmethod
    def set_document_detail(cls, doc_id: int, data: Any) -> None:
        """Cache document details."""
        key = cls._make_key("document_detail", doc_id)
        cache.set(key, data, cls.TIMEOUT_DETAIL)

    @classmethod
    def invalidate_document_detail(cls, doc_id: int) -> None:
        """Invalidate document detail cache."""
        key = cls._make_key("document_detail", doc_id)
        cache.delete(key)

    @classmethod
    def get_statistics(cls, user_id: int) -> Any | None:
        """Get cached statistics for user."""
        key = cls._make_key("document_stats", user_id)
        return cache.get(key)

    @classmethod
    def set_statistics(cls, user_id: int, data: Any) -> None:
        """Cache statistics for user."""
        key = cls._make_key("document_stats", user_id)
        cache.set(key, data, cls.TIMEOUT_STATS)

    @classmethod
    def invalidate_statistics(cls, user_id: int) -> None:
        """Invalidate statistics cache for user."""
        key = cls._make_key("document_stats", user_id)
        cache.delete(key)

    @classmethod
    def invalidate_user_caches(cls, user_id: int) -> None:
        """Invalidate all caches for a user (list + stats).

        Used when documents are created, updated, or deleted.
        """
        cls.invalidate_document_list(user_id)
        cls.invalidate_statistics(user_id)

    @classmethod
    def invalidate_document_caches(cls, doc_id: int, user_id: int) -> None:
        """Invalidate all caches related to a document.

        Invalidates:
        - Document detail
        - User's document list
        - User's statistics
        """
        cls.invalidate_document_detail(doc_id)
        cls.invalidate_user_caches(user_id)

    @classmethod
    def get_processing_task(cls, task_id: str) -> Any | None:
        """Get cached processing task."""
        key = cls._make_key("processing_task", task_id)
        return cache.get(key)

    @classmethod
    def set_processing_task(cls, task_id: str, data: Any) -> None:
        """Cache processing task."""
        key = cls._make_key("processing_task", task_id)
        cache.set(key, data, cls.TIMEOUT_TASK)

    @classmethod
    def invalidate_processing_task(cls, task_id: str) -> None:
        """Invalidate processing task cache."""
        key = cls._make_key("processing_task", task_id)
        cache.delete(key)
