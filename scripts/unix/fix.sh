#!/bin/bash
# Скрипт для автоматического исправления проблем в коде
# Использование: ./scripts/unix/fix.sh или poetry run fix

set -e

# Get absolute path to project root
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "🔧 Автоматическое исправление кода (Ruff + Black)..."
echo ""

echo "1️⃣  Ruff (автоисправление + isort)..."
poetry run ruff check --fix .
echo "✅ Ruff: исправлено"
echo ""

echo "2️⃣  Black (форматирование)..."
poetry run black .
echo "✅ Black: отформатировано"
echo ""

echo "🎉 Код автоматически исправлен!"
echo ""
echo "💡 Теперь запустите: ./scripts/unix/check.sh"
echo "💡 Ruff заменяет: Flake8 + Isort"
