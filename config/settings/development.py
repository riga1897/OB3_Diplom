"""
Настройки development окружения для OB3 Document Processing Service.

Development окружение - для локальной разработки:
- DEBUG=True по умолчанию
- Подробное логирование (управляется через LOG_LEVEL)
- Console email backend
- Упрощённая валидация паролей
- Локальный кэш (не Redis)
"""

from decouple import config

from .base import *

# ============================================
# Режим отладки
# ============================================
DEBUG = config("DEBUG", default=True, cast=bool)

# ============================================
# Разрешённые хосты
# ============================================
ALLOWED_HOSTS: list[str] = config(  # type: ignore[no-redef]
    "ALLOWED_HOSTS",
    default="*",  # type: ignore[arg-type]
    cast=lambda v: [s.strip() for s in v.split(",")] if v != "*" else ["*"],
)

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
# Шаблоны (отладка включена)
# ============================================
TEMPLATES[0]["OPTIONS"]["debug"] = True  # type: ignore[index]

# ============================================
# Логирование (управляется через LOG_LEVEL в .env)
# ============================================
# structlog настроен в base.py через configure_structlog()
# Уровень логирования берётся из LOG_LEVEL (по умолчанию DEBUG)

# ============================================
# CORS (разрешительный для разработки)
# ============================================
CORS_ALLOW_ALL_ORIGINS = config("CORS_ALLOW_ALL_ORIGINS", default=True, cast=bool)

# ============================================
# Валидация паролей (отключена)
# ============================================
AUTH_PASSWORD_VALIDATORS = []

# ============================================
# Кэширование (выбор через CACHE_BACKEND)
# ============================================
# Варианты: redis, locmem (по умолчанию locmem)
_cache_backend = config("CACHE_BACKEND", default="locmem")
_cache_timeout = config("CACHE_TIMEOUT", default=300, cast=int)

if _cache_backend == "redis":
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": config("REDIS_URL", default="redis://localhost:6379/1"),
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
            "KEY_PREFIX": "ob3_dev",
            "TIMEOUT": _cache_timeout,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "development-cache",
            "TIMEOUT": _cache_timeout,
        }
    }
