@echo off
REM Скрипт для запуска всех тестов проекта (pytest-django)
REM Генерирует coverage отчёт
REM
REM Использование:
REM   scripts\windows\test_all.bat              # В Windows CMD
REM   docker-compose exec web scripts/windows/test_all.bat  # В Docker

echo.
echo ================================
echo 🧪 Starting test suite...
echo ================================
echo.

echo 📋 Running pytest-django tests (250 tests)
echo Location: tests/ directory
echo ---
poetry run pytest tests/ --cov=apps --cov=config --cov-report=html:var/coverage/htmlcov --cov-report=xml:var/coverage/coverage.xml
if %errorlevel% neq 0 exit /b %errorlevel%

echo.
echo ================================
echo ✅ All tests completed!
echo 📊 HTML coverage report: var\coverage\htmlcov\index.html
echo ================================
