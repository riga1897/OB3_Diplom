"""
Настройки test окружения для OB3 Document Processing Service.

Test окружение - для запуска тестов:
- PostgreSQL для production parity
- Быстрое хэширование паролей (MD5)
- Локальный кэш (не Redis)
- Celery в eager mode (синхронное выполнение)
- Минимальное логирование
"""

import os

from .base import *

# ============================================
# Режим отладки
# ============================================
DEBUG = True
SECRET_KEY = "test-secret-key-for-testing-only-do-not-use-in-production"

# ============================================
# База данных (PostgreSQL для production parity)
# ============================================
# Избегаем проблем с SQL диалектом: ArrayField, JSONB, constraints
DATABASES = {  # type: ignore[assignment]
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "ob3_test"),
        "USER": os.getenv("DB_USER", "ob3_user"),
        "PASSWORD": os.getenv("DB_PASSWORD", "ob3_password"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "TEST": {  # type: ignore[dict-item]
            "NAME": "test_ob3_db",
        },
    }
}

# ============================================
# Хэширование паролей (ускоренное для тестов)
# ============================================
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# ============================================
# Кэширование (локальное, без Redis)
# ============================================
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    }
}

# ============================================
# Celery (eager mode — синхронное выполнение)
# ============================================
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"  # In-memory брокер для тестов
CELERY_RESULT_BACKEND = "cache+memory://"  # In-memory backend результатов
CELERY_CACHE_BACKEND = "memory"  # Предотвращает попытки подключения к Redis

# ============================================
# Медиа-файлы (изоляция тестов)
# ============================================
MEDIA_ROOT = BASE_DIR / "var" / "media" / "tests"

# ============================================
# Логирование (минимальный вывод)
# ============================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
        "level": "CRITICAL",
    },
}

# ============================================
# Email (консольный backend)
# ============================================
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ============================================
# Throttling (отключён для тестов)
# ============================================
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []  # type: ignore[index]
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # type: ignore[index]
    "anon": None,
    "user": None,
    "upload": None,  # Требуется DocumentViewSet.get_throttles()
}
