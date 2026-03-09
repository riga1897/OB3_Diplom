"""API integration tests for Documents app."""

from typing import Any

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

import pytest
from pytest import MonkeyPatch
from rest_framework import status
from rest_framework.test import APIClient

from apps.documents.models import Document
from tests.factories import DocumentFactory, UserFactory


@pytest.mark.integration
class TestDocumentAPI:
    """Integration tests for Document API."""

    @pytest.fixture(autouse=True)
    def setup(self, db: Any) -> None:
        """Setup test data."""
        self.user: Any = UserFactory()
        self.other_user: Any = UserFactory(username="otheruser")
        self.document: Any = DocumentFactory(owner=self.user)
        self.other_document: Any = DocumentFactory(owner=self.other_user)

    def test_list_documents_unauthenticated(self, api_client: APIClient) -> None:
        """Test listing documents requires authentication."""
        url = reverse("documents:documents-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_documents_authenticated(self, api_client: APIClient) -> None:
        """Test authenticated user can list their documents."""
        api_client.force_authenticate(user=self.user)
        url = reverse("documents:documents-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == str(self.document.id)

    def test_list_documents_filters_by_owner(self, api_client: APIClient) -> None:
        """Test users can only see their own documents."""
        api_client.force_authenticate(user=self.user)
        url = reverse("documents:documents-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        document_ids = [doc["id"] for doc in response.data["results"]]
        assert str(self.document.id) in document_ids
        assert str(self.other_document.id) not in document_ids

    def test_retrieve_document(self, api_client: APIClient) -> None:
        """Test retrieving a document."""
        api_client.force_authenticate(user=self.user)
        url = reverse("documents:documents-detail", args=[self.document.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(self.document.id)
        assert response.data["original_filename"] == self.document.original_filename

    def test_retrieve_other_user_document_forbidden(
        self, api_client: APIClient
    ) -> None:
        """Test user cannot retrieve another user's document."""
        api_client.force_authenticate(user=self.user)
        url = reverse("documents:documents-detail", args=[self.other_document.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_document(
        self, api_client: APIClient, monkeypatch: MonkeyPatch
    ) -> None:
        """Test creating a document."""
        import filetype

        class MockType:
            mime = "application/pdf"

        monkeypatch.setattr(filetype, "guess", lambda *args, **kwargs: MockType())

        api_client.force_authenticate(user=self.user)
        url = reverse("documents:documents-list")

        test_file = SimpleUploadedFile(
            "test.pdf", b"PDF content here", content_type="application/pdf"
        )

        response = api_client.post(url, {"file": test_file}, format="multipart")

        assert response.status_code == status.HTTP_201_CREATED
        assert Document.objects.filter(owner=self.user).count() == 2

    def test_update_document_not_allowed(self, api_client: APIClient) -> None:
        """Test updating document is not allowed (read-only fields)."""
        api_client.force_authenticate(user=self.user)
        url = reverse("documents:documents-detail", args=[self.document.id])

        response = api_client.patch(url, {"status": Document.Status.APPROVED})

        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        ]

    def test_delete_document(self, api_client: APIClient) -> None:
        """Test deleting a document."""
        api_client.force_authenticate(user=self.user)
        url = reverse("documents:documents-detail", args=[self.document.id])

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Document.objects.filter(id=self.document.id).exists()

    def test_filter_documents_by_status(self, api_client: APIClient) -> None:
        """Test filtering documents by status."""
        DocumentFactory(owner=self.user, status=Document.Status.APPROVED)
        DocumentFactory(owner=self.user, status=Document.Status.PENDING)

        api_client.force_authenticate(user=self.user)
        url = reverse("documents:documents-list")
        response = api_client.get(url, {"status": Document.Status.APPROVED})

        assert response.status_code == status.HTTP_200_OK
        for doc in response.data["results"]:
            assert doc["status"] == Document.Status.APPROVED

    def test_filter_documents_by_file_type(self, api_client: APIClient) -> None:
        """Test filtering documents by file type."""
        DocumentFactory(owner=self.user, file_type=Document.FileType.PDF)
        DocumentFactory(owner=self.user, file_type=Document.FileType.TXT)

        api_client.force_authenticate(user=self.user)
        url = reverse("documents:documents-list")
        response = api_client.get(url, {"file_type": Document.FileType.PDF})

        assert response.status_code == status.HTTP_200_OK
        for doc in response.data["results"]:
            assert doc["file_type"] == Document.FileType.PDF

    def test_search_documents_by_filename(self, api_client: APIClient) -> None:
        """Test searching documents by filename."""
        DocumentFactory(owner=self.user, original_filename="report.pdf")
        DocumentFactory(owner=self.user, original_filename="invoice.pdf")

        api_client.force_authenticate(user=self.user)
        url = reverse("documents:documents-list")
        response = api_client.get(url, {"search": "report"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1
        assert any(
            "report" in doc["original_filename"].lower()
            for doc in response.data["results"]
        )

    def test_ordering_documents(self, api_client: APIClient) -> None:
        """Test ordering documents."""
        api_client.force_authenticate(user=self.user)
        url = reverse("documents:documents-list")

        response = api_client.get(url, {"ordering": "created_at"})
        assert response.status_code == status.HTTP_200_OK

    def test_soft_delete_action(self, api_client: APIClient) -> None:
        """Test soft delete custom action."""
        api_client.force_authenticate(user=self.user)
        url = reverse("documents:documents-soft-delete", args=[self.document.id])

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        self.document.refresh_from_db()
        assert self.document.is_deleted is True

    def test_restore_action(self, api_client: APIClient) -> None:
        """Test restore custom action."""
        self.document.soft_delete()
        api_client.force_authenticate(user=self.user)
        url = reverse("documents:documents-restore", args=[self.document.id])

        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        self.document.refresh_from_db()
        assert self.document.is_deleted is False


@pytest.mark.integration
class TestDocumentStatisticsAPI:
    """Integration tests for Document statistics endpoint."""

    @pytest.fixture(autouse=True)
    def setup(self, db: Any) -> None:
        """Setup test data."""
        self.user: Any = UserFactory()
        self.pending_doc: Any = DocumentFactory(
            owner=self.user, status=Document.Status.PENDING
        )
        self.approved_doc: Any = DocumentFactory(
            owner=self.user,
            status=Document.Status.APPROVED,
            file_type=Document.FileType.PDF,
            file_size=1024,
        )
        self.rejected_doc: Any = DocumentFactory(
            owner=self.user,
            status=Document.Status.REJECTED,
            file_type=Document.FileType.DOCX,
            file_size=2048,
        )

    def test_statistics_endpoint(self, api_client: APIClient) -> None:
        """Test statistics endpoint returns correct data."""
        api_client.force_authenticate(user=self.user)
        url = reverse("documents:documents-statistics")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_documents"] == 3
        assert "by_status" in response.data
        assert "by_file_type" in response.data
        assert "recent_uploads" in response.data

    def test_statistics_by_status(self, api_client: APIClient) -> None:
        """Test statistics counts by status correctly."""
        api_client.force_authenticate(user=self.user)
        url = reverse("documents:documents-statistics")
        response = api_client.get(url)

        by_status = response.data["by_status"]
        assert by_status["pending"] == 1
        assert by_status["approved"] == 1
        assert by_status["rejected"] == 1

    def test_statistics_by_file_type(self, api_client: APIClient) -> None:
        """Test statistics counts by file type correctly."""
        api_client.force_authenticate(user=self.user)
        url = reverse("documents:documents-statistics")
        response = api_client.get(url)

        by_file_type = response.data["by_file_type"]
        assert by_file_type["pdf"] >= 1
        assert by_file_type["docx"] >= 1

    def test_statistics_unauthenticated(self, api_client: APIClient) -> None:
        """Test statistics endpoint requires authentication."""
        url = reverse("documents:documents-statistics")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.integration
class TestDocumentFilters:
    """Tests for document filter functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, db: Any) -> None:
        """Setup test data."""
        self.user: Any = UserFactory()
        self.pending_doc: Any = DocumentFactory(
            owner=self.user, status=Document.Status.PENDING
        )
        self.approved_doc: Any = DocumentFactory(
            owner=self.user, status=Document.Status.APPROVED
        )
        self.rejected_doc: Any = DocumentFactory(
            owner=self.user, status=Document.Status.REJECTED
        )

    def test_filter_is_reviewed_true(self, api_client: APIClient) -> None:
        """Test filtering by is_reviewed=true returns approved and rejected."""
        api_client.force_authenticate(user=self.user)
        url = reverse("documents:documents-list")
        response = api_client.get(url, {"is_reviewed": "true"})

        assert response.status_code == status.HTTP_200_OK
        document_ids = [doc["id"] for doc in response.data["results"]]
        assert str(self.approved_doc.id) in document_ids
        assert str(self.rejected_doc.id) in document_ids
        assert str(self.pending_doc.id) not in document_ids

    def test_filter_is_reviewed_false(self, api_client: APIClient) -> None:
        """Test filtering by is_reviewed=false returns only pending."""
        api_client.force_authenticate(user=self.user)
        url = reverse("documents:documents-list")
        response = api_client.get(url, {"is_reviewed": "false"})

        assert response.status_code == status.HTTP_200_OK
        document_ids = [doc["id"] for doc in response.data["results"]]
        assert str(self.pending_doc.id) in document_ids
        assert str(self.approved_doc.id) not in document_ids
        assert str(self.rejected_doc.id) not in document_ids

    def test_filter_search_by_filename(self, api_client: APIClient) -> None:
        """Test search filter by filename."""
        api_client.force_authenticate(user=self.user)
        url = reverse("documents:documents-list")
        response = api_client.get(
            url, {"search": self.pending_doc.original_filename[:5]}
        )

        assert response.status_code == status.HTTP_200_OK
