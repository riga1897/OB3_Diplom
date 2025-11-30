"""Tests for serializers."""

from typing import Any

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

import pytest
from pytest import MonkeyPatch
from rest_framework.test import APIRequestFactory

from apps.documents.models import Document
from apps.documents.serializers import (
    DocumentCreateSerializer,
    DocumentDetailSerializer,
    DocumentListSerializer,
)
from apps.users.serializers import UserCreateSerializer, UserSerializer

User = get_user_model()


@pytest.mark.unit
class TestUserSerializer:
    """Tests for UserSerializer."""

    def test_serialize_user(self, db: Any, user: Any) -> None:
        """Test serializing user."""
        serializer = UserSerializer(user)
        data = serializer.data

        assert data["id"] == user.id
        assert data["username"] == user.username
        assert data["email"] == user.email
        assert "full_name" in data

    def test_create_user_with_password_confirmation(self, db: Any) -> None:
        """Test creating user with password confirmation."""
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "first_name": "New",
            "last_name": "User",
        }
        serializer = UserCreateSerializer(data=data)
        assert serializer.is_valid()

        user = serializer.save()
        assert user.username == "newuser"
        assert user.check_password("testpass123")

    def test_create_user_password_mismatch(self, db: Any) -> None:
        """Test password confirmation validation."""
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "testpass123",
            "password_confirm": "different",
        }
        serializer = UserCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "password" in serializer.errors


@pytest.mark.unit
class TestDocumentSerializers:
    """Tests for Document serializers."""

    def test_document_list_serializer(self, db: Any, document: Document) -> None:
        """Test DocumentListSerializer."""
        serializer = DocumentListSerializer(document)
        data = serializer.data

        assert data["id"] == str(document.id)
        assert data["original_filename"] == document.original_filename
        assert data["file_type"] == document.file_type
        assert "owner" in data
        assert "file_extension" in data
        assert "is_reviewed" in data

    def test_document_detail_serializer(self, db: Any, document: Document) -> None:
        """Test DocumentDetailSerializer."""
        serializer = DocumentDetailSerializer(document)
        data = serializer.data

        assert data["id"] == str(document.id)
        assert "status" in data
        assert "rejection_reason" in data
        assert "reviewed_at" in data

    def test_document_create_serializer_file_too_large(
        self, db: Any, user: Any
    ) -> None:
        """Test file size validation."""
        from django.conf import settings

        large_file = SimpleUploadedFile(
            "large.pdf",
            b"x" * (settings.MAX_UPLOAD_SIZE + 1),
            content_type="application/pdf",
        )

        factory = APIRequestFactory()
        request = factory.post("/")
        request.user = user

        serializer = DocumentCreateSerializer(
            data={"file": large_file},
            context={"request": request},
        )
        assert not serializer.is_valid()
        assert "file" in serializer.errors

    @pytest.mark.parametrize(
        "mime_type,should_pass",
        [
            ("application/pdf", True),
            ("text/plain", True),
            ("image/jpeg", True),
            ("application/zip", False),
            ("video/mp4", False),
        ],
    )
    def test_document_create_mime_type_validation(
        self,
        db: Any,
        user: Any,
        mime_type: str,
        should_pass: bool,
        monkeypatch: MonkeyPatch,
    ) -> None:
        """Test MIME type validation."""
        import filetype

        class MockFileType:
            """Мок-объект для filetype.guess()."""

            def __init__(self, mime: str) -> None:
                self.mime = mime

        def mock_guess(*args: Any, **kwargs: Any) -> MockFileType | None:
            if mime_type == "text/plain":
                return None
            return MockFileType(mime_type)

        def mock_is_text(*args: Any, **kwargs: Any) -> bool:
            return mime_type == "text/plain"

        monkeypatch.setattr(filetype, "guess", mock_guess)
        monkeypatch.setattr(
            "apps.documents.validators._is_text_content", mock_is_text
        )

        test_file = SimpleUploadedFile(
            "test.pdf",
            b"test content",
            content_type=mime_type,
        )

        factory = APIRequestFactory()
        request = factory.post("/")
        request.user = user

        serializer = DocumentCreateSerializer(
            data={"file": test_file},
            context={"request": request},
        )

        if should_pass:
            assert serializer.is_valid(), f"Expected {mime_type} to pass validation"
        else:
            assert not serializer.is_valid(), f"Expected {mime_type} to fail validation"
            assert "file" in serializer.errors
