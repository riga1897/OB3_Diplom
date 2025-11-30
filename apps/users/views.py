"""Представления (views) для приложения Users."""

from typing import TYPE_CHECKING, Any

from django.contrib.auth import logout
from django.db.models import QuerySet

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.documents.permissions import IsSelf

from .models import User
from .serializers import LogoutSerializer, UserCreateSerializer, UserSerializer

if TYPE_CHECKING:
    from rest_framework.generics import CreateAPIView
    from rest_framework.viewsets import GenericViewSet

    class _RegisterView(CreateAPIView[User]): ...

    class _UserViewSet(
        mixins.ListModelMixin,
        mixins.RetrieveModelMixin,
        mixins.UpdateModelMixin,
        GenericViewSet[User],
    ):
        request: Request

        def get_serializer(self, *args: Any, **kwargs: Any) -> BaseSerializer[User]: ...


_RegisterView = generics.CreateAPIView  # type: ignore[misc,assignment]
_UserViewSet = type(  # type: ignore[misc,assignment]
    "_UserViewSet",
    (
        mixins.ListModelMixin,
        mixins.RetrieveModelMixin,
        mixins.UpdateModelMixin,
        viewsets.GenericViewSet,
    ),
    {},
)


class RegisterView(_RegisterView):
    """
    Регистрация пользователя.

    Позволяет анонимным пользователям зарегистрироваться, указав имя пользователя,
    email и пароль. Пароль должен быть не менее 8 символов и совпадать с подтверждением.

    **POST /api/register/**

    Тело запроса:
    ```json
    {
        "username": "ivan_petrov",
        "email": "ivan@example.com",
        "password": "SecurePass123",
        "password_confirm": "SecurePass123",
        "first_name": "Иван",
        "last_name": "Петров",
        "phone": "+79991234567"
    }
    ```

    Ответ (201 Created):
    ```json
    {
        "id": 1,
        "username": "ivan_petrov",
        "email": "ivan@example.com",
        "first_name": "Иван",
        "last_name": "Петров"
    }
    ```
    """

    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]


class UserViewSet(_UserViewSet):
    """
    CRUD операции с профилем пользователя.

    Пользователь может просматривать и редактировать только свой профиль
    (обеспечивается permission IsSelf). Создание пользователей отключено —
    используйте /api/register/.

    **GET /api/users/** — Список пользователей (только текущий)
    **GET /api/users/{id}/** — Просмотр профиля
    **PATCH /api/users/{id}/** — Обновление профиля

    **GET /api/users/me/** — Получить профиль текущего пользователя (shortcut)

    Примечание: POST (создание) и DELETE отключены из соображений безопасности.
    Для регистрации используйте /api/register/.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsSelf]
    # Используем миксины вместо ModelViewSet для отключения create/destroy

    def get_queryset(self) -> QuerySet[User]:
        """Возвращает только профиль текущего пользователя."""
        return User.objects.filter(pk=self.request.user.pk)

    @action(detail=False, methods=["get"])
    def me(self, request: Request) -> Response:
        """
        Получить профиль текущего пользователя.

        **GET /api/users/me/**

        Возвращает информацию о профиле авторизованного пользователя.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LogoutView(generics.GenericAPIView):  # type: ignore[type-arg]
    """
    Выход из системы.

    Инвалидирует refresh-токен (добавляет в чёрный список) и завершает сессию.

    **POST /api/users/logout/**

    Тело запроса:
    ```json
    {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
    ```

    Ответ (205 Reset Content):
    ```json
    {
        "detail": "Выход выполнен успешно."
    }
    ```
    """

    serializer_class = LogoutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Выполнить выход из системы."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        logout(request)

        return Response(
            {"detail": "Выход выполнен успешно."},
            status=status.HTTP_205_RESET_CONTENT,
        )


class SessionTokenView(generics.GenericAPIView):  # type: ignore[type-arg]
    """
    Получение JWT токена для уже аутентифицированного пользователя.

    Позволяет пользователю, залогиненному через сессию (web-интерфейс),
    получить JWT токены без повторного ввода логина/пароля.

    **POST /api/users/token/session/**

    Требуется: активная сессия (SessionAuthentication)

    Ответ (200 OK):
    ```json
    {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
    ```

    Безопасность:
    - Токены выдаются только аутентифицированным пользователям
    - Access token короткоживущий (15 мин по умолчанию)
    - При logout refresh token добавляется в blacklist
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Получить JWT токен для сессионного пользователя",
        description="Выдаёт JWT access и refresh токены пользователю, "
        "уже аутентифицированному через сессию.",
        tags=["Аутентификация"],
        request=None,
        responses={
            200: OpenApiResponse(
                description="Токены успешно выданы",
                examples=[
                    OpenApiExample(
                        "Успешный ответ",
                        value={
                            "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        },
                    )
                ],
            ),
            401: OpenApiResponse(description="Пользователь не аутентифицирован"),
        },
    )
    def post(self, request: Request) -> Response:
        """Выдать JWT токены аутентифицированному пользователю."""
        refresh = RefreshToken.for_user(request.user)  # type: ignore[arg-type,type-var]
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )
