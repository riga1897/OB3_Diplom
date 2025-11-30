#!/bin/bash
# Скрипт для запуска всех тестов проекта (Django APITestCase + pytest-django)
# Генерирует комбинированный coverage отчёт
#
# Использование:
#   ./scripts/test_all.sh              # Локально
#   docker-compose exec web ./scripts/test_all.sh  # В Docker контейнере

set -e

echo "🧪 Starting test suite..."
echo "================================"
echo ""

echo "📋 Step 1/3: Running Django APITestCase tests (78 tests)"
echo "Location: lms/tests.py, users/tests.py"
echo "---"
coverage run --source='users,lms,config' manage.py test

echo ""
echo "📋 Step 2/3: Running pytest-django tests (187 tests)"
echo "Location: tests/ directory"
echo "---"
coverage run --append --source='users,lms,config' -m pytest --no-cov

echo ""
echo "📋 Step 3/3: Generating coverage report"
echo "---"
coverage report
coverage html

echo ""
echo "================================"
echo "✅ All 265 tests completed!"
echo "📊 HTML coverage report: htmlcov/index.html"
echo "================================"
