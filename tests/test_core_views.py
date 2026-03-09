"""Tests for core views (health check, API root)."""

from typing import Any
from unittest.mock import patch

from django.urls import reverse

import pytest
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.unit
class TestHealthCheck:
    """Tests for health_check endpoint.

    Note: Celery workers не проверяются в healthcheck, так как web контейнер
    должен быть healthy до запуска workers (зависимость в docker-compose).
    Кэш также не критичен для liveness — возвращает warning вместо ошибки.
    """

    @pytest.fixture
    def client(self) -> APIClient:
        """Create API client."""
        return APIClient()

    @pytest.fixture
    def url(self) -> str:
        """Get health check URL."""
        return reverse("health_check")

    def test_health_check_all_healthy(
        self, client: APIClient, url: str, db: Any
    ) -> None:
        """Test health check when all services are healthy."""
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "healthy"
        assert response.data["checks"]["database"] == "ok"
        assert response.data["checks"]["cache"] == "ok"

    def test_health_check_returns_database_status(
        self, client: APIClient, url: str, db: Any
    ) -> None:
        """Test health check returns database status."""
        response = client.get(url)

        assert "database" in response.data["checks"]

    def test_health_check_returns_cache_status(
        self, client: APIClient, url: str, db: Any
    ) -> None:
        """Test health check returns cache status."""
        response = client.get(url)

        assert "cache" in response.data["checks"]

    def test_health_check_database_error(
        self, client: APIClient, url: str, db: Any
    ) -> None:
        """Test health check when database connection fails."""
        with patch("django.db.connection.cursor") as mock_cursor:
            mock_cursor.side_effect = Exception("Database unavailable")

            response = client.get(url)

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.data["status"] == "unhealthy"
        assert "error" in response.data["checks"]["database"]

    def test_health_check_cache_error_returns_warning(
        self, client: APIClient, url: str, db: Any
    ) -> None:
        """Test health check returns warning (not error) when cache fails.

        Cache is not critical for liveness — only informational.
        """
        with patch("django.core.cache.cache.set") as mock_cache_set:
            mock_cache_set.side_effect = Exception("Cache unavailable")

            response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "healthy"
        assert "warning" in response.data["checks"]["cache"]


@pytest.mark.unit
class TestAPIRootExtended:
    """Extended tests for api_root endpoint."""

    @pytest.fixture
    def client(self) -> APIClient:
        """Create API client."""
        return APIClient()

    @pytest.fixture
    def url(self) -> str:
        """Get API root URL."""
        return reverse("api-root")

    def test_api_root_contains_all_endpoints(
        self, client: APIClient, url: str, db: Any
    ) -> None:
        """Test that API root contains all required endpoints."""
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK

        assert "documents" in response.data
        assert "users" in response.data
        assert "register" in response.data
        assert "health" in response.data
        assert "auth" in response.data
        assert "documentation" in response.data

    def test_api_root_auth_endpoints(
        self, client: APIClient, url: str, db: Any
    ) -> None:
        """Test that auth endpoints are correctly structured."""
        response = client.get(url)

        auth = response.data["auth"]
        assert "obtain_token" in auth
        assert "refresh_token" in auth
        assert "verify_token" in auth

    def test_api_root_documentation_endpoints(
        self, client: APIClient, url: str, db: Any
    ) -> None:
        """Test that documentation endpoints are correctly structured."""
        response = client.get(url)

        docs = response.data["documentation"]
        assert "swagger-ui" in docs
        assert "redoc" in docs
        assert "openapi-schema" in docs
