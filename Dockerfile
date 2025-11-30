# ============================================
# OB3 Document Processing Service
# Dockerfile для Django + Gunicorn + Celery
# ============================================
# Multi-stage build для оптимизации размера образа
#
# Стадии:
#   builder  - установка зависимостей
#   runtime  - финальный образ
#
# Режимы запуска (через entrypoint):
#   web     - Django + Gunicorn
#   worker  - Celery Worker
#   beat    - Celery Beat
#
# Сборка: docker compose build

# ============================================
# Стадия 1: Builder - установка зависимостей
# ============================================
FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.8.4 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /app

COPY pyproject.toml poetry.lock* ./

RUN poetry install --no-root --with dev && rm -rf $POETRY_CACHE_DIR

# ============================================
# Стадия 2: Runtime - финальный образ
# ============================================
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    postgresql-client \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1000 ob3 && \
    useradd -u 1000 -g ob3 -m -s /bin/bash ob3

WORKDIR /app

# Создаём директории ДО копирования .venv (chown работает только с пустыми папками = мгновенно)
RUN mkdir -p /app/static /app/staticfiles /app/var/media /app/var/logs /app/var/coverage && \
    chown -R ob3:ob3 /app

# Копируем .venv и код с --chown (владелец устанавливается при копировании)
COPY --from=builder --chown=ob3:ob3 /app/.venv /app/.venv

COPY --chown=ob3:ob3 apps ./apps
COPY --chown=ob3:ob3 config ./config
COPY --chown=ob3:ob3 tests ./tests
COPY --chown=ob3:ob3 static ./static
COPY --chown=ob3:ob3 manage.py pytest.ini ./

COPY --chown=ob3:ob3 scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER ob3

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["web"]
