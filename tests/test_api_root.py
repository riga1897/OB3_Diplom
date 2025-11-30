"""Тесты для корневого API endpoint."""

from typing import Any

import pytest
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestAPIRoot:
    """Тесты для функции api_root."""

    def test_api_root_returns_all_endpoints(self, api_client: APIClient) -> None:
        """Корневой API возвращает все доступные endpoints."""
        response = api_client.get("/api/")

        assert response.status_code == status.HTTP_200_OK
        data: dict[str, Any] = response.json()

        assert "documents" in data
        assert "users" in data
        assert "register" in data
        assert "health" in data
        assert "auth" in data
        assert "documentation" in data

    def test_api_root_documents_endpoint(self, api_client: APIClient) -> None:
        """Endpoint для документов присутствует в корневом API."""
        response = api_client.get("/api/")

        assert response.status_code == status.HTTP_200_OK
        data: dict[str, Any] = response.json()

        assert "documents" in data
        assert "/api/documents/" in data["documents"]

    def test_api_root_health_endpoint(self, api_client: APIClient) -> None:
        """Health check endpoint присутствует в корневом API."""
        response = api_client.get("/api/")

        assert response.status_code == status.HTTP_200_OK
        data: dict[str, Any] = response.json()

        assert "health" in data
        assert "/health/" in data["health"]

    def test_api_root_auth_endpoints(self, api_client: APIClient) -> None:
        """JWT аутентификация endpoints присутствуют в корневом API."""
        response = api_client.get("/api/")

        assert response.status_code == status.HTTP_200_OK
        data: dict[str, Any] = response.json()

        assert "auth" in data
        assert isinstance(data["auth"], dict)
        assert "obtain_token" in data["auth"]
        assert "refresh_token" in data["auth"]
        assert "verify_token" in data["auth"]
        assert "/api/users/token/" in data["auth"]["obtain_token"]
        assert "/api/users/token/refresh/" in data["auth"]["refresh_token"]
        assert "/api/users/token/verify/" in data["auth"]["verify_token"]

    def test_api_root_documentation_endpoints(self, api_client: APIClient) -> None:
        """API документация endpoints присутствуют в корневом API."""
        response = api_client.get("/api/")

        assert response.status_code == status.HTTP_200_OK
        data: dict[str, Any] = response.json()

        assert "documentation" in data
        assert isinstance(data["documentation"], dict)
        assert "swagger-ui" in data["documentation"]
        assert "redoc" in data["documentation"]
        assert "openapi-schema" in data["documentation"]
        assert "/api/schema/swagger-ui/" in data["documentation"]["swagger-ui"]
        assert "/api/schema/redoc/" in data["documentation"]["redoc"]
        assert "/api/schema/" in data["documentation"]["openapi-schema"]

    def test_api_root_accessible_without_auth(self, api_client: APIClient) -> None:
        """API Root доступен без аутентификации."""
        response = api_client.get("/api/")

        assert response.status_code == status.HTTP_200_OK

    def test_api_root_users_endpoint(self, api_client: APIClient) -> None:
        """Users endpoint присутствует в корневом API."""
        response = api_client.get("/api/")

        assert response.status_code == status.HTTP_200_OK
        data: dict[str, Any] = response.json()

        assert "users" in data
        assert "/api/users/" in data["users"]

    def test_api_root_register_endpoint(self, api_client: APIClient) -> None:
        """Register endpoint присутствует в корневом API."""
        response = api_client.get("/api/")

        assert response.status_code == status.HTTP_200_OK
        data: dict[str, Any] = response.json()

        assert "register" in data
        assert "/api/register/" in data["register"]

    def test_root_redirect_to_api(self, api_client: APIClient) -> None:
        """Корневой URL перенаправляет на /api/."""
        response = api_client.get("/", follow=True)

        assert response.status_code == status.HTTP_200_OK
        data: dict[str, Any] = response.json()
        assert "documents" in data
        assert "auth" in data

    def test_api_root_authenticated_user_sees_session_token(
        self, authenticated_client: APIClient
    ) -> None:
        """Аутентифицированный пользователь видит session_token в auth."""
        response = authenticated_client.get("/api/")

        assert response.status_code == status.HTTP_200_OK
        data: dict[str, Any] = response.json()

        assert "auth" in data
        assert "session_token" in data["auth"]
        assert "/api/users/token/session/" in data["auth"]["session_token"]

    def test_api_root_anonymous_user_no_session_token(
        self, api_client: APIClient
    ) -> None:
        """Анонимный пользователь не видит session_token в auth."""
        response = api_client.get("/api/")

        assert response.status_code == status.HTTP_200_OK
        data: dict[str, Any] = response.json()

        assert "auth" in data
        assert "session_token" not in data["auth"]
