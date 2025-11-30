"""Factory Boy factories for testing."""

from typing import Any

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

import factory
from factory.django import DjangoModelFactory

from apps.documents.models import Document

User = get_user_model()


class UserFactory(DjangoModelFactory[Any]):
    """Factory for User model."""

    class Meta:
        model = User
        django_get_or_create = ("username",)
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    is_staff = False
    is_superuser = False

    @factory.post_generation
    def password(obj: Any, create: bool, extracted: Any, **kwargs: Any) -> None:
        """Set password after object creation."""
        if create:
            obj.set_password(extracted or "testpass123")
            obj.save()


class DocumentFactory(DjangoModelFactory[Document]):
    """Factory for Document model."""

    class Meta:
        model = Document
        skip_postgeneration_save = True

    owner = factory.SubFactory(UserFactory)
    file = factory.LazyAttribute(
        lambda _: SimpleUploadedFile(
            "test_document.pdf", b"Test PDF content", content_type="application/pdf"
        )
    )
    file_type = Document.FileType.PDF
    file_size = factory.Faker("random_int", min=1024, max=1048576)
    original_filename = factory.Faker("file_name", extension="pdf")
    status = Document.Status.PENDING

    @factory.post_generation
    def approved_status(
        obj: Document, create: bool, extracted: Any, **kwargs: Any
    ) -> None:
        """Set approved status if requested."""
        if create and extracted:
            obj.status = Document.Status.APPROVED
            obj.save()
