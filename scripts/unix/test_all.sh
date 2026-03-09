#!/bin/bash
# Скрипт для запуска всех тестов проекта (pytest-django)
# Генерирует coverage отчёт
#
# Использование:
#   ./scripts/unix/test_all.sh              # Локально
#   docker-compose exec web ./scripts/unix/test_all.sh  # В Docker контейнере

set -e

echo "🧪 Starting test suite..."
echo "================================"
echo ""

echo "📋 Running pytest-django tests (250 tests)"
echo "Location: tests/ directory"
echo "---"
poetry run pytest tests/ --cov=apps --cov=config --cov-report=html:var/coverage/htmlcov --cov-report=xml:var/coverage/coverage.xml

echo ""
echo "================================"
echo "✅ All tests completed!"
echo "📊 HTML coverage report: var/coverage/htmlcov/index.html"
echo "================================"
