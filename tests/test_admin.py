"""Tests for Django admin functionality."""

from typing import Any, cast
from unittest.mock import MagicMock, patch

from django.contrib.admin.sites import AdminSite
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory

import pytest

from apps.documents.admin import DocumentAdmin
from apps.documents.models import Document
from tests.factories import DocumentFactory, UserFactory


@pytest.mark.unit
class TestDocumentAdminMethods:
    """Tests for DocumentAdmin display methods."""

    @pytest.fixture
    def admin(self) -> DocumentAdmin:
        """Create DocumentAdmin instance."""
        return DocumentAdmin(model=Document, admin_site=AdminSite())

    @pytest.fixture
    def user(self, db: Any) -> Any:
        """Create test user."""
        return UserFactory()

    @pytest.fixture
    def document(self, user: Any) -> Document:
        """Create test document."""
        return cast(Document, DocumentFactory(owner=user))

    def test_status_colored_pending(
        self, admin: DocumentAdmin, document: Document
    ) -> None:
        """Test status_colored returns orange for pending."""
        document.status = Document.Status.PENDING
        result = admin.status_colored(document)

        assert "#FFA500" in result
        assert "Ожидает проверки" in result

    def test_status_colored_approved(
        self, admin: DocumentAdmin, document: Document
    ) -> None:
        """Test status_colored returns green for approved."""
        document.status = Document.Status.APPROVED
        result = admin.status_colored(document)

        assert "#28A745" in result
        assert "Подтверждён" in result

    def test_status_colored_rejected(
        self, admin: DocumentAdmin, document: Document
    ) -> None:
        """Test status_colored returns red for rejected."""
        document.status = Document.Status.REJECTED
        result = admin.status_colored(document)

        assert "#DC3545" in result
        assert "Отклонён" in result

    def test_file_size_human_bytes(
        self, admin: DocumentAdmin, document: Document
    ) -> None:
        """Test file_size_human returns bytes for small files."""
        document.file_size = 500
        result = admin.file_size_human(document)

        assert result == "500 B"

    def test_file_size_human_kilobytes(
        self, admin: DocumentAdmin, document: Document
    ) -> None:
        """Test file_size_human returns KB for medium files."""
        document.file_size = 2048
        result = admin.file_size_human(document)

        assert "2.0 KB" in result

    def test_file_size_human_megabytes(
        self, admin: DocumentAdmin, document: Document
    ) -> None:
        """Test file_size_human returns MB for large files."""
        document.file_size = 2 * 1024 * 1024
        result = admin.file_size_human(document)

        assert "2.0 MB" in result

    def test_file_preview_no_file(
        self, admin: DocumentAdmin, document: Document
    ) -> None:
        """Test file_preview returns message when no file."""
        document.file = None
        result = admin.file_preview(document)

        assert result == "Файл отсутствует"

    def test_file_preview_image(self, admin: DocumentAdmin, document: Document) -> None:
        """Test file_preview returns img tag for IMAGE."""
        document.file_type = Document.FileType.IMAGE
        document.original_filename = "test.jpg"
        document.file = MagicMock()
        document.file.url = "/media/test.jpg"

        result = admin.file_preview(document)

        assert "<img" in result
        assert "/media/test.jpg" in result
        assert "max-width: 300px" in result

    def test_file_preview_pdf(self, admin: DocumentAdmin, document: Document) -> None:
        """Test file_preview returns link for PDF."""
        document.file_type = Document.FileType.PDF
        document.file = MagicMock()
        document.file.url = "/media/test.pdf"

        result = admin.file_preview(document)

        assert "Открыть PDF" in result
        assert "/media/test.pdf" in result
        assert "#dc3545" in result

    def test_file_preview_docx(self, admin: DocumentAdmin, document: Document) -> None:
        """Test file_preview returns link for DOCX."""
        document.file_type = Document.FileType.DOCX
        document.file = MagicMock()
        document.file.url = "/media/test.docx"

        result = admin.file_preview(document)

        assert "Скачать DOCX" in result
        assert "/media/test.docx" in result
        assert "#0d6efd" in result

    def test_file_preview_txt(self, admin: DocumentAdmin, document: Document) -> None:
        """Test file_preview returns link for TXT (other type)."""
        document.file_type = Document.FileType.TXT
        document.original_filename = "test.txt"
        document.file = MagicMock()
        document.file.url = "/media/test.txt"

        result = admin.file_preview(document)

        assert "Скачать файл" in result
        assert "/media/test.txt" in result
        assert "📄" in result

    def test_file_preview_dangerous_file(
        self, admin: DocumentAdmin, document: Document
    ) -> None:
        """Test file_preview blocks preview for dangerous files."""
        document.file_type = Document.FileType.TXT
        document.original_filename = "malware.exe"
        document.file = MagicMock()
        document.file.url = "/media/malware.exe"

        result = admin.file_preview(document)

        assert "Предпросмотр и скачивание заблокированы" in result
        assert "#f8d7da" in result
        assert "Заблокировано" in result

    def test_file_info_display_safe_file(
        self, admin: DocumentAdmin, document: Document
    ) -> None:
        """Test file_info_display shows category info for safe files."""
        document.original_filename = "report.pdf"

        result = admin.file_info_display(document)

        assert "report.pdf" in result
        assert "📄" in result

    def test_file_info_display_dangerous_file(
        self, admin: DocumentAdmin, document: Document
    ) -> None:
        """Test file_info_display shows warning for dangerous files."""
        document.original_filename = "virus.exe"

        result = admin.file_info_display(document)

        assert "virus.exe" in result
        assert "⚠️" in result
        assert "#dc3545" in result


@pytest.mark.unit
class TestDocumentAdminActions:
    """Tests for DocumentAdmin actions."""

    @pytest.fixture
    def admin(self) -> DocumentAdmin:
        """Create DocumentAdmin instance."""
        return DocumentAdmin(model=Document, admin_site=AdminSite())

    @pytest.fixture
    def admin_user(self, db: Any) -> Any:
        """Create admin user."""
        return UserFactory(is_staff=True, is_superuser=True, email="admin@test.com")

    @pytest.fixture
    def user(self, db: Any) -> Any:
        """Create test user."""
        return UserFactory(email="user@test.com")

    @pytest.fixture
    def request_factory(self) -> RequestFactory:
        """Create request factory."""
        return RequestFactory()

    def _create_request(self, request_factory: RequestFactory, admin_user: Any) -> Any:
        """Create mock request with messages."""
        request = request_factory.post("/admin/documents/document/")
        request.user = admin_user
        request.session = "session"  # type: ignore[assignment]
        messages = FallbackStorage(request)
        request._messages = messages  # type: ignore[assignment]
        return request

    def test_approve_documents_action(
        self,
        admin: DocumentAdmin,
        admin_user: Any,
        user: Any,
        request_factory: RequestFactory,
    ) -> None:
        """Test approve_documents action updates status."""
        doc1 = DocumentFactory(owner=user, status=Document.Status.PENDING)
        doc2 = DocumentFactory(owner=user, status=Document.Status.PENDING)

        request = self._create_request(request_factory, admin_user)
        queryset = Document.objects.filter(id__in=[doc1.id, doc2.id])

        with patch("apps.documents.tasks.send_user_notification_task") as mock_task:
            admin.approve_documents(request, queryset)

        doc1.refresh_from_db()
        doc2.refresh_from_db()

        assert doc1.status == Document.Status.APPROVED
        assert doc2.status == Document.Status.APPROVED
        assert doc1.reviewed_at is not None
        assert doc2.reviewed_at is not None
        assert mock_task.delay.call_count == 2

        messages = list(get_messages(request))
        assert len(messages) == 1
        assert "Подтверждено документов: 2" in str(messages[0])

    def test_approve_documents_skips_already_approved(
        self,
        admin: DocumentAdmin,
        admin_user: Any,
        user: Any,
        request_factory: RequestFactory,
    ) -> None:
        """Test approve_documents skips already approved documents."""
        doc = DocumentFactory(owner=user, status=Document.Status.APPROVED)

        request = self._create_request(request_factory, admin_user)
        queryset = Document.objects.filter(id=doc.id)

        with patch("apps.documents.tasks.send_user_notification_task") as mock_task:
            admin.approve_documents(request, queryset)

        mock_task.delay.assert_not_called()

        messages = list(get_messages(request))
        assert "Пропущено (уже обработаны): 1" in str(messages[0])

    def test_reject_documents_action(
        self,
        admin: DocumentAdmin,
        admin_user: Any,
        user: Any,
        request_factory: RequestFactory,
    ) -> None:
        """Test reject_documents action updates status."""
        doc = DocumentFactory(owner=user, status=Document.Status.PENDING)

        request = self._create_request(request_factory, admin_user)
        queryset = Document.objects.filter(id=doc.id)

        with patch("apps.documents.tasks.send_user_notification_task") as mock_task:
            admin.reject_documents(request, queryset)

        doc.refresh_from_db()

        assert doc.status == Document.Status.REJECTED
        assert doc.rejection_reason == "Отклонено администратором"
        assert doc.reviewed_at is not None
        mock_task.delay.assert_called_once()

        messages = list(get_messages(request))
        assert "Отклонено документов: 1" in str(messages[0])

    def test_reject_documents_skips_already_rejected(
        self,
        admin: DocumentAdmin,
        admin_user: Any,
        user: Any,
        request_factory: RequestFactory,
    ) -> None:
        """Test reject_documents skips already rejected documents."""
        doc = DocumentFactory(owner=user, status=Document.Status.REJECTED)

        request = self._create_request(request_factory, admin_user)
        queryset = Document.objects.filter(id=doc.id)

        with patch("apps.documents.tasks.send_user_notification_task") as mock_task:
            admin.reject_documents(request, queryset)

        mock_task.delay.assert_not_called()

    def test_get_queryset_uses_select_related(
        self,
        admin: DocumentAdmin,
        admin_user: Any,
        request_factory: RequestFactory,
    ) -> None:
        """Test get_queryset uses select_related for optimization."""
        request = self._create_request(request_factory, admin_user)
        queryset = admin.get_queryset(request)

        select_related = queryset.query.select_related
        assert isinstance(select_related, dict)
        assert "owner" in select_related

    def test_get_actions_hides_for_non_superuser(
        self,
        admin: DocumentAdmin,
        user: Any,
        request_factory: RequestFactory,
    ) -> None:
        """Test get_actions hides approve/reject for non-superusers."""
        user.is_staff = True
        user.is_superuser = False
        user.save()

        request = self._create_request(request_factory, user)
        actions = admin.get_actions(request)

        assert "approve_documents" not in actions
        assert "reject_documents" not in actions

    def test_has_add_permission_returns_false(
        self,
        admin: DocumentAdmin,
        admin_user: Any,
        request_factory: RequestFactory,
    ) -> None:
        """Test has_add_permission always returns False."""
        request = self._create_request(request_factory, admin_user)
        assert admin.has_add_permission(request) is False

    def test_has_delete_permission_returns_false(
        self,
        admin: DocumentAdmin,
        admin_user: Any,
        request_factory: RequestFactory,
    ) -> None:
        """Test has_delete_permission always returns False."""
        request = self._create_request(request_factory, admin_user)
        assert admin.has_delete_permission(request) is False
        assert admin.has_delete_permission(request, obj=None) is False

    def test_response_change_approve_button(
        self,
        admin: DocumentAdmin,
        admin_user: Any,
        user: Any,
        request_factory: RequestFactory,
    ) -> None:
        """Test response_change handles _approve button."""
        doc = cast(
            Document, DocumentFactory(owner=user, status=Document.Status.PENDING)
        )

        request = request_factory.post("/admin/documents/document/", {"_approve": "1"})
        request.user = admin_user
        request.session = "session"  # type: ignore[assignment]
        request._messages = FallbackStorage(request)  # type: ignore[assignment]

        with patch("apps.documents.tasks.send_user_notification_task") as mock_task:
            response = admin.response_change(request, doc)

        doc.refresh_from_db()
        assert doc.status == Document.Status.APPROVED
        assert doc.reviewed_at is not None
        mock_task.delay.assert_called_once()
        assert response.status_code == 302

    def test_response_change_reject_button(
        self,
        admin: DocumentAdmin,
        admin_user: Any,
        user: Any,
        request_factory: RequestFactory,
    ) -> None:
        """Test response_change handles _reject button."""
        doc = cast(
            Document, DocumentFactory(owner=user, status=Document.Status.PENDING)
        )

        request = request_factory.post("/admin/documents/document/", {"_reject": "1"})
        request.user = admin_user
        request.session = "session"  # type: ignore[assignment]
        request._messages = FallbackStorage(request)  # type: ignore[assignment]

        with patch("apps.documents.tasks.send_user_notification_task") as mock_task:
            response = admin.response_change(request, doc)

        doc.refresh_from_db()
        assert doc.status == Document.Status.REJECTED
        assert doc.rejection_reason == "Отклонено администратором"
        mock_task.delay.assert_called_once()
        assert response.status_code == 302

    def test_response_change_non_superuser_ignored(
        self,
        admin: DocumentAdmin,
        user: Any,
        request_factory: RequestFactory,
    ) -> None:
        """Test response_change ignores buttons for non-superusers."""
        user.is_staff = True
        user.is_superuser = False
        user.save()

        doc = cast(
            Document, DocumentFactory(owner=user, status=Document.Status.PENDING)
        )

        request = request_factory.post("/admin/documents/document/", {"_approve": "1"})
        request.user = user
        request.session = "session"  # type: ignore[assignment]
        request._messages = FallbackStorage(request)  # type: ignore[assignment]

        with patch("apps.documents.tasks.send_user_notification_task") as mock_task:
            admin.response_change(request, doc)

        doc.refresh_from_db()
        assert doc.status == Document.Status.PENDING
        mock_task.delay.assert_not_called()

    def test_approve_documents_empty_queryset(
        self,
        admin: DocumentAdmin,
        admin_user: Any,
        request_factory: RequestFactory,
    ) -> None:
        """Test approve_documents with empty queryset."""
        request = self._create_request(request_factory, admin_user)
        queryset = Document.objects.none()

        with patch("apps.documents.tasks.send_user_notification_task") as mock_task:
            admin.approve_documents(request, queryset)

        mock_task.delay.assert_not_called()
        messages = list(get_messages(request))
        assert "Нет документов для подтверждения" in str(messages[0])

    def test_reject_documents_empty_queryset(
        self,
        admin: DocumentAdmin,
        admin_user: Any,
        request_factory: RequestFactory,
    ) -> None:
        """Test reject_documents with empty queryset."""
        request = self._create_request(request_factory, admin_user)
        queryset = Document.objects.none()

        with patch("apps.documents.tasks.send_user_notification_task") as mock_task:
            admin.reject_documents(request, queryset)

        mock_task.delay.assert_not_called()
        messages = list(get_messages(request))
        assert "Нет документов для отклонения" in str(messages[0])

    def test_render_change_form_hides_submit_row(
        self,
        admin: DocumentAdmin,
        admin_user: Any,
        user: Any,
        request_factory: RequestFactory,
    ) -> None:
        """Test render_change_form sets submit_row to False."""
        doc = cast(Document, DocumentFactory(owner=user))

        request = request_factory.get(f"/admin/documents/document/{doc.id}/change/")
        request.user = admin_user
        request.session = "session"  # type: ignore[assignment]
        request._messages = FallbackStorage(request)  # type: ignore[assignment]

        context: dict[str, Any] = {
            "adminform": MagicMock(),
            "object_id": str(doc.id),
            "original": doc,
            "is_popup": False,
            "save_as": False,
            "has_add_permission": False,
            "has_change_permission": True,
            "has_delete_permission": False,
            "has_view_permission": True,
            "has_editable_inline_admin_formsets": False,
            "inline_admin_formsets": [],
            "errors": [],
            "media": MagicMock(),
            "add": False,
            "change": True,
            "opts": Document._meta,
            "app_label": "documents",
            "title": "Change Document",
            "subtitle": None,
        }

        with patch.object(
            admin.__class__.__bases__[0],
            "render_change_form",
            return_value=MagicMock(),
        ):
            admin.render_change_form(request, context, change=True, obj=doc)

        assert context["submit_row"] is False

    def test_response_change_no_action_buttons(
        self,
        admin: DocumentAdmin,
        admin_user: Any,
        user: Any,
        request_factory: RequestFactory,
    ) -> None:
        """Test response_change with no action buttons calls super."""
        doc = cast(
            Document, DocumentFactory(owner=user, status=Document.Status.PENDING)
        )

        request = request_factory.post("/admin/documents/document/", {"_save": "1"})
        request.user = admin_user
        request.session = "session"  # type: ignore[assignment]
        request._messages = FallbackStorage(request)  # type: ignore[assignment]

        with patch.object(
            admin.__class__.__bases__[0],
            "response_change",
            return_value=MagicMock(status_code=302),
        ) as mock_super:
            response = admin.response_change(request, doc)

        mock_super.assert_called_once()
        assert response.status_code == 302
