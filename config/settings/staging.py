"""
Настройки staging окружения для OB3 Document Processing Service.

Staging окружение - промежуточное между development и production:
- DEBUG=False (как в production)
- Подробное логирование для отладки (управляется через LOG_LEVEL)
- Смягчённые настройки безопасности для тестирования
- Console email backend (письма в консоль)
- Короткие таймауты кэша
- Локальный кэш (не Redis)

Используется для тестирования перед выкаткой в production.
"""

from django.core.exceptions import ImproperlyConfigured

from decouple import config

from .base import *

# ============================================
# Fail-fast: проверка обязательных переменных
# ============================================
if not SECRET_KEY:
    raise ImproperlyConfigured(
        "SECRET_KEY обязателен для staging/production! "
        "Добавьте его в .env файл или Secrets."
    )

# ============================================
# Режим отладки
# ============================================
DEBUG = config("DEBUG", default=False, cast=bool)

# ============================================
# Разрешённые хосты
# ============================================
ALLOWED_HOSTS: list[str] = config(  # type: ignore[no-redef]
    "ALLOWED_HOSTS",
    default="*",  # type: ignore[arg-type]
    cast=lambda v: [s.strip() for s in v.split(",")] if v != "*" else ["*"],
)

# ============================================
# Безопасность (смягчённая для тестирования)
# ============================================
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=False, cast=bool)
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=False, cast=bool)
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=False, cast=bool)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# ============================================
# Email (консольный бэкенд по умолчанию)
# ============================================
# Для тестирования SMTP установите в .env:
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_BACKEND = config(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)

# ============================================
# База данных
# ============================================
DATABASES["default"]["CONN_MAX_AGE"] = config(  # type: ignore[index, assignment]
    "DB_CONN_MAX_AGE", default=60, cast=int
)

# ============================================
# Кэширование (выбор через CACHE_BACKEND)
# ============================================
# Варианты: redis, locmem (по умолчанию locmem)
_cache_backend = config("CACHE_BACKEND", default="locmem")
_cache_timeout = config("CACHE_TIMEOUT", default=60, cast=int)

if _cache_backend == "redis":
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": config("REDIS_URL", default="redis://localhost:6379/1"),
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
            "KEY_PREFIX": "ob3_staging",
            "TIMEOUT": _cache_timeout,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "staging-cache",
            "TIMEOUT": _cache_timeout,
        }
    }

# ============================================
# Логирование (управляется через LOG_LEVEL в .env)
# ============================================
# structlog настроен в base.py через configure_structlog()
# Уровень логирования берётся из LOG_LEVEL (по умолчанию INFO)

# ============================================
# CORS (разрешительный)
# ============================================
CORS_ALLOW_ALL_ORIGINS = config("CORS_ALLOW_ALL_ORIGINS", default=True, cast=bool)

# ============================================
# Валидация паролей (упрощённая)
# ============================================
AUTH_PASSWORD_VALIDATORS = [  # type: ignore[no-redef, dict-item]
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 6},  # type: ignore[dict-item]
    },
]
