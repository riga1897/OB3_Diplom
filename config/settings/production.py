"""
Настройки production окружения для OB3 Document Processing Service.

Production окружение - боевой сервер:
- DEBUG=False (обязательно)
- Максимальная безопасность (SSL, HSTS, secure cookies)
- SMTP email backend
- Redis кэш (из base.py)
- Строгая валидация паролей (из base.py)

Политики безопасности жёстко заданы - это сделано намеренно.
"""

from decouple import config

from .base import *

# ============================================
# Режим отладки (ВСЕГДА False в production)
# ============================================
DEBUG = False

# ============================================
# Разрешённые хосты (обязательно указать!)
# ============================================
ALLOWED_HOSTS: list[str] = config(  # type: ignore[no-redef]
    "ALLOWED_HOSTS",
    default="",  # type: ignore[arg-type]
    cast=lambda v: [s.strip() for s in v.split(",") if s.strip()],
)

# ============================================
# Безопасность (ПОЛИТИКИ - жёсткие значения)
# ============================================
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=31536000, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ============================================
# Email (SMTP)
# ============================================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@ob3.example.com")

# ============================================
# База данных (connection pooling)
# ============================================
DATABASES["default"]["CONN_MAX_AGE"] = config(  # type: ignore[index, assignment]
    "DB_CONN_MAX_AGE", default=600, cast=int
)

# ============================================
# Статические файлы (с хэшированием)
# ============================================
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

# ============================================
# Логирование (управляется через LOG_LEVEL в .env)
# ============================================
# structlog настроен в base.py через configure_structlog()
# В production: JSON-формат (debug=False)
# Уровень логирования берётся из LOG_LEVEL (по умолчанию ERROR)

# ============================================
# Администраторы (уведомления об ошибках)
# ============================================
ADMINS = [
    ("Admin", config("ADMIN_EMAIL", default="admin@ob3.example.com")),
]

# ============================================
# Облачное хранилище (опционально)
# ============================================
# Раскомментировать для использования S3:
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default='')
# AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default='')
# AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME', default='')
# AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')
