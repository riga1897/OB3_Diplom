"""Представления для проверки здоровья сервиса и мониторинга."""

from typing import Any

from django.core.cache import cache
from django.db import connection

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response


@extend_schema(
    summary="Проверка здоровья сервиса",
    description="Эндпоинт для мониторинга и балансировщиков нагрузки. "
    "Проверяет подключение к базе данных и кэшу.",
    tags=["Мониторинг"],
    responses={
        200: OpenApiResponse(
            description="Сервис здоров",
            examples=[
                OpenApiExample(
                    "Успешная проверка",
                    value={
                        "status": "healthy",
                        "checks": {"database": "ok", "cache": "ok"},
                    },
                )
            ],
        ),
        503: OpenApiResponse(
            description="Сервис недоступен",
            examples=[
                OpenApiExample(
                    "База данных недоступна",
                    value={
                        "status": "unhealthy",
                        "checks": {
                            "database": "error: connection refused",
                            "cache": "ok",
                        },
                    },
                )
            ],
        ),
    },
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request: Request) -> Response:
    """
    Эндпоинт проверки здоровья сервиса для мониторинга и балансировщиков нагрузки.

    Проверки:
    - Подключение к базе данных
    - Подключение к кэшу (не критично для liveness)

    Возвращает 200 OK если база данных доступна, 503 Service Unavailable в противном случае.

    Примечание: Celery workers не проверяются в healthcheck, так как web контейнер
    должен быть healthy до запуска workers (зависимость в docker-compose).
    """
    health_status: dict[str, Any] = {
        "status": "healthy",
        "checks": {},
    }
    is_healthy: bool = True

    # Проверка базы данных (критично)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["checks"]["database"] = f"error: {str(e)}"
        is_healthy = False

    # Проверка кэша (не критично для liveness, только информационно)
    try:
        cache_key = "health_check"
        cache.set(cache_key, "test", 10)
        cache.get(cache_key)
        cache.delete(cache_key)
        health_status["checks"]["cache"] = "ok"
    except Exception as e:
        health_status["checks"]["cache"] = f"warning: {str(e)}"

    # Обновление общего статуса
    if not is_healthy:
        health_status["status"] = "unhealthy"
        return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    return Response(health_status, status=status.HTTP_200_OK)


@extend_schema(
    summary="Корневой эндпоинт API",
    description="Список всех доступных ресурсов API. "
    "Динамически собирает endpoints из всех приложений.",
    tags=["API"],
    responses={
        200: OpenApiResponse(
            description="Список доступных эндпоинтов",
            examples=[
                OpenApiExample(
                    "Список эндпоинтов",
                    value={
                        "documents": "http://example.com/api/documents/",
                        "processing_tasks": "http://example.com/api/documents/tasks/",
                        "health": "http://example.com/health/",
                        "auth": {
                            "obtain_token": "http://example.com/api/users/token/",
                            "refresh_token": "http://example.com/api/users/token/refresh/",
                            "verify_token": "http://example.com/api/users/token/verify/",
                        },
                        "documentation": {
                            "swagger-ui": "http://example.com/api/schema/swagger-ui/",
                            "redoc": "http://example.com/api/schema/redoc/",
                            "openapi-schema": "http://example.com/api/schema/",
                        },
                    },
                )
            ],
        ),
    },
)
@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request: Request, response_format: str | None = None) -> Response:
    """
    Корневой эндпоинт API со списком всех доступных ресурсов.

    Динамически собирает все endpoints из роутеров приложений documents и users.
    При добавлении нового ViewSet в любое приложение, он автоматически появится здесь.

    Принцип работы:
    1. Импортируем роутер из apps.documents.urls
    2. Проходим по router.registry (список зарегистрированных ViewSet-ов)
    3. Для каждого ViewSet создаём ссылку через reverse()
    4. Добавляем JWT аутентификацию и документацию

    Args:
        request: HTTP запрос
        response_format: Формат ответа (json, html и т.д.)

    Returns:
        Response: Словарь со ссылками на все доступные эндпоинты

    Пример результата:
        {
            "documents": "http://example.com/api/documents/",
            "processing_tasks": "http://example.com/api/documents/tasks/",
            "health": "http://example.com/health/",
            "auth": {
                "obtain_token": "http://example.com/api/users/token/",
                "refresh_token": "http://example.com/api/users/token/refresh/"
            },
            "documentation": {
                "swagger-ui": "http://example.com/api/schema/swagger-ui/",
                "redoc": "http://example.com/api/schema/redoc/",
                "openapi-schema": "http://example.com/api/schema/"
            }
        }
    """
    from rest_framework.reverse import reverse

    from apps.documents.urls import router as documents_router
    from apps.users.urls import router as users_router

    endpoints: dict[str, Any] = {}

    # Автоматически собираем endpoints из роутера Documents приложения
    for prefix, _viewset, basename in documents_router.registry:
        # Формируем URL в зависимости от prefix
        url_name = f"documents:{basename}-list"

        # Для пустого prefix добавляем как "documents", для остальных используем basename
        endpoint_key = "documents" if not prefix else basename.replace("-", "_")
        endpoints[endpoint_key] = reverse(
            url_name, request=request, format=response_format
        )

    # Добавляем endpoints из роутера Users приложения
    for _prefix, _viewset, basename in users_router.registry:
        url_name = f"users:{basename}-list"
        endpoint_key = basename.replace("-", "_")
        endpoints[endpoint_key] = reverse(
            url_name, request=request, format=response_format
        )

    # Добавляем регистрацию пользователей
    endpoints["register"] = reverse("register", request=request, format=response_format)

    # Добавляем health check
    endpoints["health"] = reverse(
        "health_check", request=request, format=response_format
    )

    # Добавляем JWT аутентификацию endpoints
    endpoints["auth"] = {
        "obtain_token": reverse(
            "users:token_obtain_pair", request=request, format=response_format
        ),
        "refresh_token": reverse(
            "users:token_refresh", request=request, format=response_format
        ),
        "verify_token": reverse(
            "users:token_verify", request=request, format=response_format
        ),
    }

    # Добавляем session_token только для аутентифицированных пользователей
    if request.user.is_authenticated:
        endpoints["auth"]["session_token"] = reverse(
            "users:token_session", request=request, format=response_format
        )

    # Добавляем документацию API
    endpoints["documentation"] = {
        "swagger-ui": reverse("swagger-ui", request=request, format=response_format),
        "redoc": reverse("redoc", request=request, format=response_format),
        "openapi-schema": reverse("schema", request=request, format=response_format),
    }

    return Response(endpoints)
