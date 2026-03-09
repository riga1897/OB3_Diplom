"""Кастомные классы ограничения частоты запросов для приложения Documents."""

from rest_framework.throttling import UserRateThrottle


class UploadRateThrottle(UserRateThrottle):
    """Ограничение частоты загрузки файлов.

    Предотвращает злоупотребление путём ограничения количества
    загрузок на пользователя в час.
    Лимит настраивается через THROTTLE_UPLOAD в settings (по умолчанию: 10/час).
    """

    scope = "upload"
