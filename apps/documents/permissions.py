"""Кастомные права доступа для приложения Documents."""

from typing import Any

from rest_framework import permissions
from rest_framework.request import Request


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Право доступа: только владельцы документа могут его редактировать."""

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        """Проверить, является ли пользователь владельцем объекта."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(obj.owner == request.user)


class IsOwner(permissions.BasePermission):
    """Право доступа: только владельцы документа имеют доступ."""

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        """Проверить, является ли пользователь владельцем объекта."""
        return bool(obj.owner == request.user)


class IsSelf(permissions.BasePermission):
    """
    Право доступа: пользователи могут управлять только своим профилем.

    Используется в UserViewSet для ограничения доступа к чужим профилям.
    """

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        """Проверить, обращается ли пользователь к своему профилю."""
        return bool(obj == request.user)


class IsModerator(permissions.BasePermission):
    """
    Право доступа: проверка принадлежности к группе «Модераторы».

    Модераторы имеют расширенные права для просмотра всех документов
    и выполнения административных действий.
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        """Проверить, состоит ли пользователь в группе модераторов."""
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.groups.filter(name="Модераторы").exists()  # type: ignore[attr-defined]
        )


class IsModeratorOrOwner(permissions.BasePermission):
    """
    Право доступа для модераторов ИЛИ владельцев ресурса.

    Модераторы могут обращаться ко всем объектам,
    обычные пользователи — только к своим.
    """

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        """Проверить, является ли пользователь модератором или владельцем."""
        is_moderator = bool(
            request.user
            and request.user.is_authenticated
            and request.user.groups.filter(name="Модераторы").exists()  # type: ignore[attr-defined]
        )
        is_owner = bool(obj.owner == request.user)
        return is_moderator or is_owner
