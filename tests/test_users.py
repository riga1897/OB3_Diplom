"""Tests for Users app (Register, Token Verify, UserViewSet)."""

from typing import Any

from django.urls import reverse

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User


@pytest.mark.django_db
class TestRegisterEndpoint:
    """Tests for user registration endpoint."""

    def test_register_success(self, api_client: APIClient) -> None:
        """Test successful user registration."""
        url = reverse("register")
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "SecurePass123",
            "password_confirm": "SecurePass123",
            "first_name": "New",
            "last_name": "User",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(username="newuser").exists()
        user = User.objects.get(username="newuser")
        assert user.email == "newuser@example.com"
        assert user.first_name == "New"
        assert user.check_password("SecurePass123")

    def test_register_password_mismatch(self, api_client: APIClient) -> None:
        """Test registration with mismatched passwords."""
        url = reverse("register")
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "SecurePass123",
            "password_confirm": "DifferentPass456",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data
        assert not User.objects.filter(username="newuser").exists()

    def test_register_short_password(self, api_client: APIClient) -> None:
        """Test registration with password shorter than 8 characters."""
        url = reverse("register")
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "short",
            "password_confirm": "short",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not User.objects.filter(username="newuser").exists()

    def test_register_duplicate_username(
        self, api_client: APIClient, user_factory: Any
    ) -> None:
        """Test registration with existing username."""
        user_factory(username="existinguser")

        url = reverse("register")
        data = {
            "username": "existinguser",
            "email": "newuser@example.com",
            "password": "SecurePass123",
            "password_confirm": "SecurePass123",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert User.objects.filter(username="existinguser").count() == 1


@pytest.mark.django_db
class TestTokenVerifyEndpoint:
    """Tests for JWT token verification endpoint."""

    def test_verify_valid_token(self, user_factory: Any) -> None:
        """Test verifying a valid JWT token."""
        user = user_factory()
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        client = APIClient()
        url = reverse("users:token_verify")
        data: dict[str, str] = {"token": access_token}

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK

    def test_verify_invalid_token(self) -> None:
        """Test verifying an invalid JWT token."""
        client = APIClient()
        url = reverse("users:token_verify")
        data = {"token": "invalid.token.here"}

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_verify_missing_token(self) -> None:
        """Test verifying without providing a token."""
        client = APIClient()
        url = reverse("users:token_verify")
        data: dict[str, Any] = {}

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserViewSet:
    """Tests for User ViewSet (profile CRUD)."""

    def test_list_users_returns_only_self(
        self, authenticated_client: APIClient, user: User, user_factory: Any
    ) -> None:
        """Test that users can only see their own profile in list."""
        # Create another user
        user_factory(username="otheruser")

        url = reverse("users:users-list")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["username"] == user.username

    def test_retrieve_own_profile(
        self, authenticated_client: APIClient, user: User
    ) -> None:
        """Test retrieving own user profile."""
        url = reverse("users:users-detail", kwargs={"pk": user.pk})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == user.username
        assert response.data["email"] == user.email

    def test_retrieve_other_user_profile_forbidden(
        self, authenticated_client: APIClient, user_factory: Any
    ) -> None:
        """Test that users cannot retrieve other users' profiles."""
        other_user = user_factory(username="otheruser")

        url = reverse("users:users-detail", kwargs={"pk": other_user.pk})
        response = authenticated_client.get(url)

        # Should return 404 because get_queryset filters to only own profile
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_own_profile(
        self, authenticated_client: APIClient, user: User
    ) -> None:
        """Test updating own user profile."""
        url = reverse("users:users-detail", kwargs={"pk": user.pk})
        data = {
            "first_name": "Updated",
            "last_name": "Name",
            "bio": "Updated bio",
        }

        response = authenticated_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.first_name == "Updated"
        assert user.last_name == "Name"
        assert user.bio == "Updated bio"

    def test_me_endpoint_returns_current_user(
        self, authenticated_client: APIClient, user: User
    ) -> None:
        """Test /users/me/ endpoint returns current authenticated user."""
        url = reverse("users:users-me")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == user.username
        assert response.data["email"] == user.email

    def test_unauthenticated_cannot_access_users(self, api_client: APIClient) -> None:
        """Test that unauthenticated users cannot access user endpoints."""
        url = reverse("users:users-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_user_via_viewset_forbidden(
        self, authenticated_client: APIClient
    ) -> None:
        """Test that creating users via UserViewSet is forbidden."""
        url = reverse("users:users-list")
        data = {
            "username": "hackuser",
            "email": "hack@example.com",
            "password": "Hacked123",
        }

        response = authenticated_client.post(url, data, format="json")

        # POST method should be disabled (405 Method Not Allowed)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert not User.objects.filter(username="hackuser").exists()

    def test_delete_user_via_viewset_forbidden(
        self, authenticated_client: APIClient, user: User
    ) -> None:
        """Test that deleting users via UserViewSet is forbidden."""
        url = reverse("users:users-detail", kwargs={"pk": user.pk})

        response = authenticated_client.delete(url)

        # DELETE method should be disabled (405 Method Not Allowed)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert User.objects.filter(pk=user.pk).exists()


@pytest.mark.django_db
class TestLogoutEndpoint:
    """Tests for user logout endpoint."""

    def test_logout_success_with_refresh_token(
        self, authenticated_client: APIClient, user: User
    ) -> None:
        """Test successful logout with refresh token blacklisting."""
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

        refresh = RefreshToken.for_user(user)
        refresh_token = str(refresh)

        url = reverse("users:logout")
        data = {"refresh": refresh_token}

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_205_RESET_CONTENT
        assert response.data["detail"] == "Выход выполнен успешно."
        assert BlacklistedToken.objects.filter(token__jti=refresh["jti"]).exists()

    def test_logout_success_without_refresh_token(
        self, authenticated_client: APIClient
    ) -> None:
        """Test logout without providing refresh token (session only)."""
        url = reverse("users:logout")
        data: dict[str, str] = {}

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_205_RESET_CONTENT
        assert response.data["detail"] == "Выход выполнен успешно."

    def test_logout_with_empty_refresh_token(
        self, authenticated_client: APIClient
    ) -> None:
        """Test logout with empty refresh token string."""
        url = reverse("users:logout")
        data = {"refresh": ""}

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_205_RESET_CONTENT
        assert response.data["detail"] == "Выход выполнен успешно."

    def test_logout_with_invalid_refresh_token_still_logs_out(
        self, authenticated_client: APIClient
    ) -> None:
        """Test logout with invalid refresh token still logs out (graceful handling)."""
        url = reverse("users:logout")
        data = {"refresh": "invalid.token.here"}

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_205_RESET_CONTENT
        assert response.data["detail"] == "Выход выполнен успешно."

    def test_logout_requires_authentication(self, api_client: APIClient) -> None:
        """Test that logout requires authentication."""
        url = reverse("users:logout")
        data: dict[str, str] = {}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_blacklisted_token_cannot_refresh(
        self, authenticated_client: APIClient, user: User
    ) -> None:
        """Test that blacklisted refresh token cannot be used to get new access."""
        refresh = RefreshToken.for_user(user)
        refresh_token = str(refresh)

        logout_url = reverse("users:logout")
        authenticated_client.post(logout_url, {"refresh": refresh_token}, format="json")

        refresh_url = reverse("users:token_refresh")
        client = APIClient()
        response = client.post(refresh_url, {"refresh": refresh_token}, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_already_blacklisted_token_succeeds(
        self, authenticated_client: APIClient, user: User
    ) -> None:
        """Test logout with already blacklisted token still succeeds."""
        refresh = RefreshToken.for_user(user)
        refresh_token = str(refresh)

        refresh.blacklist()

        url = reverse("users:logout")
        data = {"refresh": refresh_token}

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_205_RESET_CONTENT
        assert response.data["detail"] == "Выход выполнен успешно."


@pytest.mark.django_db
class TestSessionTokenEndpoint:
    """Tests for session-based JWT token endpoint."""

    def test_session_token_success(
        self, authenticated_client: APIClient, user: User
    ) -> None:
        """Test getting JWT token for session-authenticated user."""
        url = reverse("users:token_session")

        response = authenticated_client.post(url, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert len(response.data["access"]) > 50
        assert len(response.data["refresh"]) > 50

    def test_session_token_requires_authentication(self, api_client: APIClient) -> None:
        """Test that session token endpoint requires authentication."""
        url = reverse("users:token_session")

        response = api_client.post(url, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_session_token_returns_valid_tokens(
        self, authenticated_client: APIClient, user: User
    ) -> None:
        """Test that returned tokens are valid and can be verified."""
        url = reverse("users:token_session")
        response = authenticated_client.post(url, format="json")

        assert response.status_code == status.HTTP_200_OK

        access_token = response.data["access"]
        verify_url = reverse("users:token_verify")
        verify_response = authenticated_client.post(
            verify_url, {"token": access_token}, format="json"
        )

        assert verify_response.status_code == status.HTTP_200_OK

    def test_session_token_refresh_works(
        self, authenticated_client: APIClient, user: User
    ) -> None:
        """Test that returned refresh token can get new access token."""
        url = reverse("users:token_session")
        response = authenticated_client.post(url, format="json")

        assert response.status_code == status.HTTP_200_OK

        refresh_token = response.data["refresh"]
        refresh_url = reverse("users:token_refresh")
        client = APIClient()
        refresh_response = client.post(
            refresh_url, {"refresh": refresh_token}, format="json"
        )

        assert refresh_response.status_code == status.HTTP_200_OK
        assert "access" in refresh_response.data
