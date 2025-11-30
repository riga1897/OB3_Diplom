@echo off
REM Скрипт для запуска всех тестов проекта (Django APITestCase + pytest-django)
REM Генерирует комбинированный coverage отчёт
REM
REM Использование:
REM   scripts\windows\test_all.bat              # В Windows CMD
REM   docker-compose exec web scripts/windows/test_all.bat  # В Docker (если нужно)

echo.
echo ================================
echo 🧪 Starting test suite...
echo ================================
echo.

echo 📋 Step 1/3: Running Django APITestCase tests (78 tests)
echo Location: lms/tests.py, users/tests.py
echo ---
poetry run coverage run --source=users,lms,config manage.py test
if %errorlevel% neq 0 exit /b %errorlevel%

echo.
echo 📋 Step 2/3: Running pytest-django tests (187 tests)
echo Location: tests/ directory
echo ---
poetry run coverage run --append --source=users,lms,config -m pytest --no-cov
if %errorlevel% neq 0 exit /b %errorlevel%

echo.
echo 📋 Step 3/3: Generating coverage report
echo ---
poetry run coverage report
poetry run coverage html

echo.
echo ================================
echo ✅ All 265 tests completed!
echo 📊 HTML coverage report: htmlcov\index.html
echo ================================
