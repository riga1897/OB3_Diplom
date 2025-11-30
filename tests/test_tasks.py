"""Tests for Celery tasks."""

from datetime import timedelta
from typing import Any
from unittest.mock import patch

from django.utils import timezone

import pytest

from apps.documents.models import Document
from apps.documents.tasks import (
    cleanup_old_documents,
    generate_statistics_report,
    send_admin_notification_task,
    send_user_notification_task,
)
from tests.factories import DocumentFactory, UserFactory


@pytest.mark.unit
class TestCleanupOldDocuments:
    """Tests for cleanup_old_documents task."""

    @pytest.fixture
    def user(self, db: Any) -> Any:
        """Create test user."""
        return UserFactory()

    def test_cleanup_old_documents_deletes_old(self, user: Any) -> None:
        """Test cleanup deletes old soft-deleted documents."""
        old_doc = DocumentFactory(owner=user)
        old_doc.is_deleted = True
        old_doc.deleted_at = timezone.now() - timedelta(days=31)
        old_doc.save()

        recent_doc = DocumentFactory(owner=user)
        recent_doc.is_deleted = True
        recent_doc.deleted_at = timezone.now() - timedelta(days=10)
        recent_doc.save()

        result = cleanup_old_documents()

        assert result["deleted_count"] == 1
        assert not Document.objects.filter(id=old_doc.id).exists()
        assert Document.objects.filter(id=recent_doc.id).exists()

    def test_cleanup_old_documents_no_old_docs(self, user: Any) -> None:
        """Test cleanup with no old documents."""
        DocumentFactory(owner=user, status=Document.Status.APPROVED)

        result = cleanup_old_documents()

        assert result["deleted_count"] == 0


@pytest.mark.unit
class TestGenerateStatisticsReport:
    """Tests for generate_statistics_report task."""

    @pytest.fixture
    def user(self, db: Any) -> Any:
        """Create test user."""
        return UserFactory()

    def test_generate_statistics_report(self, user: Any) -> None:
        """Test statistics report generation."""
        DocumentFactory(owner=user, status=Document.Status.PENDING)
        DocumentFactory(owner=user, status=Document.Status.APPROVED)
        DocumentFactory(owner=user, status=Document.Status.APPROVED)
        DocumentFactory(owner=user, status=Document.Status.REJECTED)

        result = generate_statistics_report()

        assert result["total_documents"] == 4
        assert result["pending"] == 1
        assert result["approved"] == 2
        assert result["rejected"] == 1

    def test_generate_statistics_report_empty(self, db: Any) -> None:
        """Test statistics report with no documents."""
        result = generate_statistics_report()

        assert result["total_documents"] == 0
        assert result["pending"] == 0
        assert result["approved"] == 0
        assert result["rejected"] == 0


@pytest.mark.unit
class TestSendAdminNotificationTask:
    """Tests for send_admin_notification_task."""

    @pytest.fixture
    def user(self, db: Any) -> Any:
        """Create test user."""
        return UserFactory()

    @pytest.fixture
    def admin_user(self, db: Any) -> Any:
        """Create admin user."""
        return UserFactory(is_staff=True, email="admin@example.com")

    @pytest.fixture
    def document(self, user: Any) -> Document:
        """Create test document."""
        return DocumentFactory(owner=user, status=Document.Status.PENDING)

    def test_send_admin_notification_success(
        self, document: Document, admin_user: Any
    ) -> None:
        """Test successful admin notification."""
        with patch("apps.documents.tasks.send_mail") as mock_send_mail:
            result = send_admin_notification_task.apply(args=[str(document.id)]).get()

        assert result["status"] == "sent"
        assert result["recipients_count"] == 1
        mock_send_mail.assert_called_once()

        call_args = mock_send_mail.call_args
        assert document.original_filename in call_args.kwargs["subject"]
        assert "admin@example.com" in call_args.kwargs["recipient_list"]

    def test_send_admin_notification_no_admins(self, document: Document) -> None:
        """Test notification skipped when no admins."""
        result = send_admin_notification_task.apply(args=[str(document.id)]).get()

        assert result["status"] == "skipped"
        assert result["reason"] == "no_admins"

    def test_send_admin_notification_document_not_found(self, db: Any) -> None:
        """Test notification with non-existent document."""
        result = send_admin_notification_task.apply(
            args=["00000000-0000-0000-0000-000000000000"]
        ).get()

        assert result["status"] == "error"
        assert result["reason"] == "document_not_found"


@pytest.mark.unit
class TestSendUserNotificationTask:
    """Tests for send_user_notification_task."""

    @pytest.fixture
    def user(self, db: Any) -> Any:
        """Create test user with email."""
        return UserFactory(email="user@example.com")

    @pytest.fixture
    def document(self, user: Any) -> Document:
        """Create test document."""
        return DocumentFactory(
            owner=user,
            status=Document.Status.APPROVED,
        )

    def test_send_user_notification_approved(self, document: Document) -> None:
        """Test user notification for approved document."""
        document.reviewed_at = timezone.now()
        document.save()

        with patch("apps.documents.tasks.send_mail") as mock_send_mail:
            result = send_user_notification_task.apply(
                args=[str(document.id), "approved"]
            ).get()

        assert result["status"] == "sent"
        assert result["action"] == "approved"
        assert result["recipient"] == "user@example.com"
        mock_send_mail.assert_called_once()

        call_args = mock_send_mail.call_args
        assert "подтверждён" in call_args.kwargs["subject"]

    def test_send_user_notification_rejected(self, document: Document) -> None:
        """Test user notification for rejected document."""
        document.status = Document.Status.REJECTED
        document.rejection_reason = "Invalid format"
        document.save()

        with patch("apps.documents.tasks.send_mail") as mock_send_mail:
            result = send_user_notification_task.apply(
                args=[str(document.id), "rejected"]
            ).get()

        assert result["status"] == "sent"
        assert result["action"] == "rejected"
        mock_send_mail.assert_called_once()

        call_args = mock_send_mail.call_args
        assert "отклонён" in call_args.kwargs["subject"]

    def test_send_user_notification_unknown_action(self, document: Document) -> None:
        """Test notification with unknown action."""
        result = send_user_notification_task.apply(
            args=[str(document.id), "unknown"]
        ).get()

        assert result["status"] == "error"
        assert "unknown_action" in result["reason"]

    def test_send_user_notification_document_not_found(self, db: Any) -> None:
        """Test notification with non-existent document."""
        result = send_user_notification_task.apply(
            args=["00000000-0000-0000-0000-000000000000", "approved"]
        ).get()

        assert result["status"] == "error"
        assert result["reason"] == "document_not_found"

    def test_send_user_notification_no_email(self, db: Any) -> None:
        """Test notification skipped when user has no email."""
        user_no_email = UserFactory(email="")
        document = DocumentFactory(owner=user_no_email, status=Document.Status.APPROVED)

        result = send_user_notification_task.apply(
            args=[str(document.id), "approved"]
        ).get()

        assert result["status"] == "skipped"
        assert result["reason"] == "no_user_email"


@pytest.mark.unit
class TestCleanupWithErrors:
    """Tests for cleanup_old_documents with errors."""

    @pytest.fixture
    def user(self, db: Any) -> Any:
        """Create test user."""
        return UserFactory()

    def test_cleanup_handles_file_deletion_error(self, user: Any) -> None:
        """Test cleanup continues when file deletion fails."""
        old_doc = DocumentFactory(owner=user)
        old_doc.is_deleted = True
        old_doc.deleted_at = timezone.now() - timedelta(days=31)
        old_doc.save()

        with patch.object(old_doc.file, "delete", side_effect=Exception("IO Error")):
            result = cleanup_old_documents()

        assert result["deleted_count"] == 1

    def test_cleanup_handles_document_deletion_error(self, user: Any) -> None:
        """Test cleanup logs error and continues when document deletion fails."""
        old_doc = DocumentFactory(owner=user)
        old_doc.is_deleted = True
        old_doc.deleted_at = timezone.now() - timedelta(days=31)
        old_doc.save()

        with patch(
            "apps.documents.models.Document.delete", side_effect=Exception("DB Error")
        ):
            result = cleanup_old_documents()

        assert result["deleted_count"] == 1


@pytest.mark.unit
class TestSmtpErrorHandling:
    """Tests for SMTP error handling in notification tasks."""

    @pytest.fixture
    def user(self, db: Any) -> Any:
        """Create test user."""
        return UserFactory(email="user@example.com")

    @pytest.fixture
    def admin_user(self, db: Any) -> Any:
        """Create admin user."""
        return UserFactory(is_staff=True, email="admin@example.com")

    @pytest.fixture
    def document(self, user: Any) -> Document:
        """Create test document."""
        return DocumentFactory(owner=user, status=Document.Status.PENDING)

    def test_admin_notification_smtp_error_triggers_retry(
        self, document: Document, admin_user: Any
    ) -> None:
        """Test admin notification triggers Celery retry on SMTP error."""
        from smtplib import SMTPException

        from celery.exceptions import Retry

        with (
            patch("apps.documents.tasks.send_mail") as mock_send_mail,
            patch("apps.documents.tasks.logger") as mock_logger,
        ):
            mock_send_mail.side_effect = SMTPException("SMTP connection failed")

            with pytest.raises(Retry):
                send_admin_notification_task.apply(args=[str(document.id)]).get()

            mock_logger.error.assert_called()
            call_args = mock_logger.error.call_args
            assert call_args[0][0] == "smtp_error_admin_notification"

    def test_user_notification_smtp_error_triggers_retry(
        self, document: Document
    ) -> None:
        """Test user notification triggers Celery retry on SMTP error."""
        from smtplib import SMTPException

        from celery.exceptions import Retry

        document.reviewed_at = timezone.now()
        document.save()

        with (
            patch("apps.documents.tasks.send_mail") as mock_send_mail,
            patch("apps.documents.tasks.logger") as mock_logger,
        ):
            mock_send_mail.side_effect = SMTPException("SMTP connection failed")

            with pytest.raises(Retry):
                send_user_notification_task.apply(args=[str(document.id), "approved"]).get()

            mock_logger.error.assert_called()
            call_args = mock_logger.error.call_args
            assert call_args[0][0] == "smtp_error_user_notification"
