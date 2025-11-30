"""Базовые настройки для OB3 Document Processing Service."""

import os
from datetime import timedelta
from pathlib import Path
from typing import TypeVar

import dj_database_url
from decouple import UndefinedValueError, config
from django.core.exceptions import ImproperlyConfigured

T = TypeVar("T")


def require_env(var_name: str, cast: type[T] = str) -> T:  # type: ignore[assignment]
    """
    Получить обязательную переменную окружения.

    Бросает ImproperlyConfigured если переменная не задана.
    Это обеспечивает fail-fast поведение: приложение не запустится
    без явно заданных переменных окружения.

    Args:
        var_name: Имя переменной окружения
        cast: Тип для преобразования (по умолчанию str)

    Returns:
        Значение переменной окружения

    Raises:
        ImproperlyConfigured: Если переменная не задана
    """
    try:
        return config(var_name, cast=cast)
    except UndefinedValueError:
        raise ImproperlyConfigured(
            f"Переменная окружения {var_name} обязательна! "
            f"Добавьте её в .env файл или Secrets."
        )


# Пути проекта
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Безопасность
# SECRET_KEY обязателен в production, но для тестов test.py переопределяет его
# Используем config() без default — если нет, будет пустая строка (проверка ниже)
SECRET_KEY = config("SECRET_KEY", default="")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",")

# CSRF для Replit — динамическое добавление доменов
# Replit использует два формата доменов: .replit.dev и .repl.co
# Нужно добавить оба варианта в CSRF_TRUSTED_ORIGINS
CSRF_TRUSTED_ORIGINS: list[str] = []


def _add_replit_domain(domain: str) -> None:
    """Добавить домен и его .repl.co версию в CSRF_TRUSTED_ORIGINS."""
    if not domain:
        return
    domain = domain.strip()
    # Добавляем оригинальный домен (.replit.dev)
    origin = f"https://{domain}"
    if origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)
    # Добавляем .repl.co версию (Replit использует оба домена)
    if ".replit.dev" in domain:
        repl_co_domain = domain.replace(".replit.dev", ".repl.co")
        repl_co_origin = f"https://{repl_co_domain}"
        if repl_co_origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(repl_co_origin)


# Добавляем REPLIT_DEV_DOMAIN (основной домен разработки)
_replit_dev_domain = os.getenv("REPLIT_DEV_DOMAIN")
if _replit_dev_domain:
    _add_replit_domain(_replit_dev_domain)

# Добавляем все домены из REPLIT_DOMAINS (через запятую)
_replit_domains = os.getenv("REPLIT_DOMAINS")
if _replit_domains:
    for domain in _replit_domains.split(","):
        _add_replit_domain(domain)

# Cookie-настройки для работы в iframe (Replit webview)
# SameSite=None + Secure=True обязательны для cross-origin iframe
CSRF_COOKIE_SAMESITE = "None"
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "None"
SESSION_COOKIE_SECURE = True

# Приложения Django
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Сторонние приложения
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
    "django_filters",
    "django_redis",
    # Локальные приложения
    "apps.core",
    "apps.users",
    "apps.documents",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],  # Шаблоны приложений находятся в apps/*/templates/ через APP_DIRS
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
# Приоритет: DATABASE_URL > формирование URL из DB_* параметров
# Все параметры ОБЯЗАТЕЛЬНЫ — приложение не запустится без них (fail-fast)
_database_url = os.getenv("DATABASE_URL")

if _database_url:
    # Replit/Docker: используем готовый DATABASE_URL
    DATABASES = {
        "default": dj_database_url.config(
            default=_database_url,
            conn_max_age=config("DB_CONN_MAX_AGE", default=600, cast=int),
            conn_health_checks=True,
        )
    }
else:
    # Локальная разработка: требуем все DB_* параметры явно
    _db_user = require_env("DB_USER")
    _db_password = require_env("DB_PASSWORD")
    _db_host = require_env("DB_HOST")
    _db_port = require_env("DB_PORT")
    _db_name = require_env("DB_NAME")

    _constructed_db_url = (
        f"postgresql://{_db_user}:{_db_password}@{_db_host}:{_db_port}/{_db_name}"
    )

    DATABASES = {
        "default": dj_database_url.config(
            default=_constructed_db_url,
            conn_max_age=config("DB_CONN_MAX_AGE", default=600, cast=int),
            conn_health_checks=True,
        )
    }

# Валидация паролей
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization — полная русская локализация
LANGUAGE_CODE = "ru-ru"
TIME_ZONE = config("TZ", default="Europe/Moscow")
USE_I18N = True
USE_L10N = True
USE_THOUSAND_SEPARATOR = True
USE_TZ = True

# Статические файлы (CSS, JavaScript, изображения)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Медиа-файлы — централизованная структура var
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "var" / "media"

# Тип первичного ключа по умолчанию
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Кастомная модель пользователя
AUTH_USER_MODEL = "users.User"

# Настройки Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.RussianPageNumberPagination",
    "PAGE_SIZE": config("DRF_PAGE_SIZE", default=10, cast=int),
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "apps.core.ordering.RussianSearchFilter",
        "apps.core.ordering.RussianOrderingFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": config("THROTTLE_ANON", default="100/day"),
        "user": config("THROTTLE_USER", default="1000/day"),
        "upload": config("THROTTLE_UPLOAD", default="10/hour"),
    },
}

# drf-spectacular
SPECTACULAR_SETTINGS = {
    "TITLE": "OB3 Document Processing Service API",
    "DESCRIPTION": "REST API для автоматической обработки, классификации и валидации документов",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# SimpleJWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# CORS
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://localhost:5000",
    cast=lambda v: [s.strip() for s in v.split(",")],
)
CORS_ALLOW_CREDENTIALS = True

# Celery Configuration
# CELERY_TASK_ALWAYS_EAGER=True — задачи выполняются синхронно (без Redis)
# Для Replit и локальной разработки без Redis — установить True
# Для Docker/staging/production с Redis — установить False
CELERY_TASK_ALWAYS_EAGER = config("CELERY_TASK_ALWAYS_EAGER", default=False, cast=bool)

if CELERY_TASK_ALWAYS_EAGER:
    # Eager mode: задачи выполняются синхронно, Redis не нужен
    CELERY_BROKER_URL = "memory://"
    CELERY_RESULT_BACKEND = "cache+memory://"
    CELERY_CACHE_BACKEND = "memory"
    CELERY_TASK_EAGER_PROPAGATES = True
else:
    # Async mode: требуется Redis
    CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = config(
        "CELERY_RESULT_BACKEND", default="redis://localhost:6379/0"
    )

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes

# Cache Configuration
REDIS_URL = config("REDIS_URL", default="redis://localhost:6379/1")
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "ob3",
        "TIMEOUT": config("CACHE_TIMEOUT", default=300, cast=int),
    }
}

# Logging — structlog
# Уровень логирования из .env
LOG_LEVEL = config("LOG_LEVEL", default="INFO")

# Базовая конфигурация Django logging (structlog настраивается отдельно)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
}

# Инициализация structlog
# debug=True — цветной консольный вывод (development)
# debug=False — JSON-формат (production)
from config.logging import configure_structlog  # noqa: E402

configure_structlog(debug=DEBUG, log_level=LOG_LEVEL)

# File Upload Settings
MAX_UPLOAD_SIZE = config("MAX_UPLOAD_SIZE", default=10485760, cast=int)  # 10MB
ALLOWED_DOCUMENT_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "image/jpeg",
    "image/png",
]
