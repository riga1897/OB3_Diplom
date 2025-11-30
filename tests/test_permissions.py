"""Tests for custom permissions."""

from typing import Any
from unittest.mock import MagicMock

from django.contrib.auth.models import Group

import pytest
from rest_framework.test import APIRequestFactory

from apps.documents.permissions import (
    IsModerator,
    IsModeratorOrOwner,
    IsOwner,
    IsOwnerOrReadOnly,
    IsSelf,
)
from tests.factories import DocumentFactory, UserFactory


@pytest.mark.unit
class TestIsOwnerOrReadOnly:
    """Tests for IsOwnerOrReadOnly permission."""

    @pytest.fixture
    def permission(self) -> IsOwnerOrReadOnly:
        """Create permission instance."""
        return IsOwnerOrReadOnly()

    @pytest.fixture
    def factory(self) -> APIRequestFactory:
        """Create request factory."""
        return APIRequestFactory()

    def test_safe_methods_allowed(
        self, permission: IsOwnerOrReadOnly, factory: APIRequestFactory, db: Any
    ) -> None:
        """Test safe methods (GET, HEAD, OPTIONS) are allowed."""
        user = UserFactory()
        owner = UserFactory()
        document = DocumentFactory(owner=owner)

        for method in ["get", "head", "options"]:
            request = getattr(factory, method)("/")
            request.user = user
            assert permission.has_object_permission(request, MagicMock(), document)

    def test_owner_can_modify(
        self, permission: IsOwnerOrReadOnly, factory: APIRequestFactory, db: Any
    ) -> None:
        """Test owner can modify object."""
        owner = UserFactory()
        document = DocumentFactory(owner=owner)

        request = factory.put("/")
        request.user = owner
        assert permission.has_object_permission(request, MagicMock(), document)

    def test_non_owner_cannot_modify(
        self, permission: IsOwnerOrReadOnly, factory: APIRequestFactory, db: Any
    ) -> None:
        """Test non-owner cannot modify object."""
        user = UserFactory()
        owner = UserFactory()
        document = DocumentFactory(owner=owner)

        request = factory.put("/")
        request.user = user
        assert not permission.has_object_permission(request, MagicMock(), document)


@pytest.mark.unit
class TestIsOwner:
    """Tests for IsOwner permission."""

    @pytest.fixture
    def permission(self) -> IsOwner:
        """Create permission instance."""
        return IsOwner()

    @pytest.fixture
    def factory(self) -> APIRequestFactory:
        """Create request factory."""
        return APIRequestFactory()

    def test_owner_has_permission(
        self, permission: IsOwner, factory: APIRequestFactory, db: Any
    ) -> None:
        """Test owner has permission."""
        owner = UserFactory()
        document = DocumentFactory(owner=owner)

        request = factory.get("/")
        request.user = owner
        assert permission.has_object_permission(request, MagicMock(), document)

    def test_non_owner_no_permission(
        self, permission: IsOwner, factory: APIRequestFactory, db: Any
    ) -> None:
        """Test non-owner has no permission."""
        user = UserFactory()
        owner = UserFactory()
        document = DocumentFactory(owner=owner)

        request = factory.get("/")
        request.user = user
        assert not permission.has_object_permission(request, MagicMock(), document)


@pytest.mark.unit
class TestIsSelf:
    """Tests for IsSelf permission."""

    @pytest.fixture
    def permission(self) -> IsSelf:
        """Create permission instance."""
        return IsSelf()

    @pytest.fixture
    def factory(self) -> APIRequestFactory:
        """Create request factory."""
        return APIRequestFactory()

    def test_user_can_access_own_profile(
        self, permission: IsSelf, factory: APIRequestFactory, db: Any
    ) -> None:
        """Test user can access their own profile."""
        user = UserFactory()

        request = factory.get("/")
        request.user = user
        assert permission.has_object_permission(request, MagicMock(), user)

    def test_user_cannot_access_other_profile(
        self, permission: IsSelf, factory: APIRequestFactory, db: Any
    ) -> None:
        """Test user cannot access other user's profile."""
        user = UserFactory()
        other_user = UserFactory()

        request = factory.get("/")
        request.user = user
        assert not permission.has_object_permission(request, MagicMock(), other_user)


@pytest.mark.unit
class TestIsModerator:
    """Tests for IsModerator permission."""

    @pytest.fixture
    def permission(self) -> IsModerator:
        """Create permission instance."""
        return IsModerator()

    @pytest.fixture
    def factory(self) -> APIRequestFactory:
        """Create request factory."""
        return APIRequestFactory()

    @pytest.fixture
    def moderator_group(self, db: Any) -> Group:
        """Create moderator group."""
        group, _ = Group.objects.get_or_create(name="Модераторы")
        return group

    def test_moderator_has_permission(
        self,
        permission: IsModerator,
        factory: APIRequestFactory,
        moderator_group: Group,
    ) -> None:
        """Test moderator has permission."""
        user = UserFactory()
        user.groups.add(moderator_group)

        request = factory.get("/")
        request.user = user
        assert permission.has_permission(request, MagicMock())

    def test_non_moderator_no_permission(
        self, permission: IsModerator, factory: APIRequestFactory, db: Any
    ) -> None:
        """Test non-moderator has no permission."""
        user = UserFactory()

        request = factory.get("/")
        request.user = user
        assert not permission.has_permission(request, MagicMock())

    def test_anonymous_no_permission(
        self, permission: IsModerator, factory: APIRequestFactory, db: Any
    ) -> None:
        """Test anonymous user has no permission."""
        request = factory.get("/")
        request.user = MagicMock(is_authenticated=False)
        assert not permission.has_permission(request, MagicMock())


@pytest.mark.unit
class TestIsModeratorOrOwner:
    """Tests for IsModeratorOrOwner permission."""

    @pytest.fixture
    def permission(self) -> IsModeratorOrOwner:
        """Create permission instance."""
        return IsModeratorOrOwner()

    @pytest.fixture
    def factory(self) -> APIRequestFactory:
        """Create request factory."""
        return APIRequestFactory()

    @pytest.fixture
    def moderator_group(self, db: Any) -> Group:
        """Create moderator group."""
        group, _ = Group.objects.get_or_create(name="Модераторы")
        return group

    def test_moderator_has_permission(
        self,
        permission: IsModeratorOrOwner,
        factory: APIRequestFactory,
        moderator_group: Group,
    ) -> None:
        """Test moderator has permission to any object."""
        moderator = UserFactory()
        moderator.groups.add(moderator_group)
        owner = UserFactory()
        document = DocumentFactory(owner=owner)

        request = factory.get("/")
        request.user = moderator
        assert permission.has_object_permission(request, MagicMock(), document)

    def test_owner_has_permission(
        self, permission: IsModeratorOrOwner, factory: APIRequestFactory, db: Any
    ) -> None:
        """Test owner has permission to their object."""
        owner = UserFactory()
        document = DocumentFactory(owner=owner)

        request = factory.get("/")
        request.user = owner
        assert permission.has_object_permission(request, MagicMock(), document)

    def test_non_owner_non_moderator_no_permission(
        self, permission: IsModeratorOrOwner, factory: APIRequestFactory, db: Any
    ) -> None:
        """Test non-owner non-moderator has no permission."""
        user = UserFactory()
        owner = UserFactory()
        document = DocumentFactory(owner=owner)

        request = factory.get("/")
        request.user = user
        assert not permission.has_object_permission(request, MagicMock(), document)
