"""Unit tests for models."""

from typing import Any

from django.contrib.auth import get_user_model

import pytest

from apps.documents.models import Document
from tests.factories import DocumentFactory, UserFactory

User = get_user_model()


@pytest.mark.unit
class TestUserModel:
    """Tests for User model."""

    def test_create_user(self, db: Any) -> None:
        """Test creating a user."""
        user: Any = UserFactory(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True

    def test_user_full_name_with_names(self, db: Any) -> None:
        """Test full_name property with first and last name."""
        user: Any = UserFactory(first_name="John", last_name="Doe")
        assert user.full_name == "John Doe"

    def test_user_full_name_fallback_to_username(self, db: Any) -> None:
        """Test full_name falls back to username."""
        user: Any = UserFactory(first_name="", last_name="", username="johndoe")
        assert user.full_name == "johndoe"

    def test_user_str_representation(self, db: Any) -> None:
        """Test user string representation."""
        user: Any = UserFactory(email="test@example.com")
        assert str(user) == "test@example.com"


@pytest.mark.unit
class TestDocumentModel:
    """Tests for Document model."""

    def test_create_document(self, db: Any, user: Any) -> None:
        """Test creating a document."""
        doc: Any = DocumentFactory(
            owner=user,
            original_filename="test.pdf",
            file_type=Document.FileType.PDF,
            status=Document.Status.PENDING,
        )
        assert doc.owner == user
        assert doc.original_filename == "test.pdf"
        assert doc.file_type == Document.FileType.PDF
        assert doc.status == Document.Status.PENDING
        assert doc.is_deleted is False

    def test_document_file_extension_property(self, db: Any, user: Any) -> None:
        """Test file_extension property."""
        doc: Any = DocumentFactory(owner=user, original_filename="document.PDF")
        assert doc.file_extension == ".pdf"

    def test_document_is_reviewed_approved(self, db: Any, user: Any) -> None:
        """Test is_reviewed property for approved status."""
        doc: Any = DocumentFactory(owner=user, status=Document.Status.APPROVED)
        assert doc.is_reviewed is True

    def test_document_is_reviewed_rejected(self, db: Any, user: Any) -> None:
        """Test is_reviewed property for rejected status."""
        doc: Any = DocumentFactory(owner=user, status=Document.Status.REJECTED)
        assert doc.is_reviewed is True

    def test_document_is_reviewed_pending(self, db: Any, user: Any) -> None:
        """Test is_reviewed property for pending status."""
        doc: Any = DocumentFactory(owner=user, status=Document.Status.PENDING)
        assert doc.is_reviewed is False

    def test_document_soft_delete(self, db: Any, user: Any) -> None:
        """Test soft delete functionality."""
        doc: Any = DocumentFactory(owner=user)
        assert doc.is_deleted is False
        assert doc.deleted_at is None

        doc.soft_delete()
        doc.refresh_from_db()

        assert doc.is_deleted is True
        assert doc.deleted_at is not None

    def test_document_restore(self, db: Any, user: Any) -> None:
        """Test restore functionality."""
        doc: Any = DocumentFactory(owner=user)
        doc.soft_delete()
        doc.refresh_from_db()
        assert doc.is_deleted is True

        doc.restore()
        doc.refresh_from_db()

        assert doc.is_deleted is False
        assert doc.deleted_at is None

    def test_document_str_representation(self, db: Any, user: Any) -> None:
        """Test document string representation."""
        doc: Any = DocumentFactory(
            owner=user,
            original_filename="test.pdf",
            status=Document.Status.APPROVED,
        )
        assert "test.pdf" in str(doc)
        assert "Подтверждён" in str(doc)

    def test_document_is_file_allowed_safe_file(self, db: Any, user: Any) -> None:
        """Test is_file_allowed returns True for safe files."""
        doc: Any = DocumentFactory(owner=user, original_filename="report.pdf")
        assert doc.is_file_allowed is True

    def test_document_is_file_allowed_dangerous_file(self, db: Any, user: Any) -> None:
        """Test is_file_allowed returns False for dangerous files."""
        doc: Any = DocumentFactory.build(owner=user, original_filename="virus.exe")
        assert doc.is_file_allowed is False

    def test_document_save_blocks_dangerous_original_filename(
        self, db: Any, user: Any
    ) -> None:
        """Test save() raises ValidationError for dangerous original_filename."""
        from unittest.mock import MagicMock

        from django.core.exceptions import ValidationError

        doc = Document(
            owner=user,
            original_filename="malware.exe",
            file_type=Document.FileType.TXT,
            file_size=100,
        )
        doc.file = MagicMock()
        doc.file.name = "safe.txt"

        with pytest.raises(ValidationError) as exc_info:
            doc.save()

        assert "запрещена" in str(exc_info.value)
        assert ".exe" in str(exc_info.value)

    def test_document_save_blocks_dangerous_file_name(self, db: Any, user: Any) -> None:
        """Test save() raises ValidationError for dangerous file.name."""
        from unittest.mock import MagicMock

        from django.core.exceptions import ValidationError

        doc = Document(
            owner=user,
            original_filename="safe.txt",
            file_type=Document.FileType.TXT,
            file_size=100,
        )
        doc.file = MagicMock()
        doc.file.name = "hidden_malware.bat"

        with pytest.raises(ValidationError) as exc_info:
            doc.save()

        assert "запрещена" in str(exc_info.value)
        assert ".bat" in str(exc_info.value)

    def test_document_save_calls_full_clean_for_new_objects(
        self, db: Any, user: Any
    ) -> None:
        """Test save() calls full_clean() for new objects without pk in DB."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        pdf_content = b"%PDF-1.4 test content"
        uploaded_file = SimpleUploadedFile(
            "document.pdf", pdf_content, content_type="application/pdf"
        )

        doc = Document(
            owner=user,
            original_filename="document.pdf",
            file_type=Document.FileType.PDF,
            file_size=len(pdf_content),
            file=uploaded_file,
        )

        assert doc._state.adding is True

        doc.save()

        assert doc._state.adding is False
        assert Document.objects.filter(pk=doc.pk).exists()
