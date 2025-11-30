#!/bin/bash
# ============================================
# OB3 Document Processing Service
# Entrypoint скрипт для Docker контейнера
# ============================================
# Режимы запуска (первый аргумент):
#   web     - Django + Gunicorn (миграции + collectstatic)
#   worker  - Celery Worker (без миграций)
#   beat    - Celery Beat (без миграций)
#
# Тесты запускаются через: docker compose exec web pytest
#
# Архитектура:
#   - Только web контейнер выполняет миграции и collectstatic
#   - Celery контейнеры ждут готовности web через depends_on

set -e

MODE="${1:-web}"
shift || true

echo "=== OB3 Entrypoint (режим: $MODE) ==="

# ============================================
# Ожидание PostgreSQL
# ============================================
wait_for_postgres() {
    echo "Ожидание PostgreSQL..."
    local max_attempts=30
    local attempt=1
    
    while ! pg_isready -h "${DB_HOST:-postgres}" -p "${DB_PORT:-5432}" -U "${DB_USER:-ob3_user}" -d "${DB_NAME:-ob3_documents}" -q; do
        if [ $attempt -ge $max_attempts ]; then
            echo "ОШИБКА: PostgreSQL недоступен после $max_attempts попыток"
            exit 1
        fi
        echo "PostgreSQL недоступен, попытка $attempt/$max_attempts..."
        sleep 2
        attempt=$((attempt + 1))
    done
    echo "PostgreSQL готов!"
}

# ============================================
# Запуск в зависимости от режима
# ============================================
case "$MODE" in
    web)
        wait_for_postgres
        
        echo "Применение миграций..."
        python manage.py migrate --noinput
        
        echo "Сбор статических файлов..."
        python manage.py collectstatic --noinput
        
        echo "=== Запуск Gunicorn ==="
        exec gunicorn config.wsgi:application \
            --bind 0.0.0.0:8000 \
            --workers 2 \
            --threads 4 \
            --worker-class gthread \
            --access-logfile - \
            --error-logfile - \
            --capture-output \
            --timeout 120
        ;;
    
    worker)
        echo "=== Запуск Celery Worker ==="
        exec celery -A config.celery worker \
            --loglevel=info \
            --pool=solo \
            --concurrency=2
        ;;
    
    beat)
        echo "=== Запуск Celery Beat ==="
        exec celery -A config.celery beat \
            --loglevel=info
        ;;
    
    *)
        echo "Неизвестный режим: $MODE"
        echo "Доступные режимы: web, worker, beat"
        echo "Для тестов: docker compose exec web pytest"
        exit 1
        ;;
esac
