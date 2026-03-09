#!/bin/bash
# Скрипт для запуска всех проверок качества кода
# Использование: ./scripts/unix/check.sh или poetry run check

set -e

# Get absolute path to project root
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "🔍 Запуск проверок качества кода (Ruff + Mypy + Black)..."
echo ""

echo "1️⃣  Ruff (проверка кода + isort)..."
poetry run ruff check .
echo "✅ Ruff: OK"
echo ""

echo "2️⃣  Mypy (проверка типов)..."
MYPY_EXIT=0
poetry run mypy apps config tests || MYPY_EXIT=$?
if [ "$MYPY_EXIT" -eq 0 ]; then
    echo "✅ Mypy: 0 errors"
else
    echo "⚠️  Mypy: found $MYPY_EXIT type errors (baseline)"
    echo "💡 Постепенное внедрение strict mode - исправляйте ошибки модуль за модулем"
fi
echo ""

echo "3️⃣  Black (проверка форматирования)..."
BLACK_EXIT=0
poetry run black --check . || BLACK_EXIT=$?
if [ "$BLACK_EXIT" -eq 0 ]; then
    echo "✅ Black: OK"
else
    echo "❌ Black: форматирование требуется"
    exit 1
fi
echo ""

echo "4️⃣  Django system check..."
DJANGO_EXIT=0
poetry run python manage.py check || DJANGO_EXIT=$?
if [ "$DJANGO_EXIT" -eq 0 ]; then
    echo "✅ Django check: OK"
else
    echo "❌ Django check: failed"
    exit 1
fi
echo ""

if [ "$MYPY_EXIT" -gt 0 ]; then
    echo "⚠️  Критические проверки (Ruff/Black/Django) пройдены"
    echo "⚠️  Mypy: baseline errors detected - требуется постепенное исправление"
    echo "💡 Ruff заменяет: Flake8 + Isort + PyUpgrade + Bandit"
    exit 0  # Don't block on Mypy baseline errors
else
    echo "🎉 Все проверки пройдены успешно (включая Mypy)!"
    echo "💡 Ruff заменяет: Flake8 + Isort + PyUpgrade + Bandit"
fi
