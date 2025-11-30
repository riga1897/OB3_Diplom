@echo off
REM Скрипт для запуска всех проверок качества кода
REM Использование: scripts\windows\check.bat или poetry run check

echo 🔍 Запуск проверок качества кода (Ruff + Mypy + Black)...
echo.

echo 1️⃣  Ruff (проверка кода + isort)...
poetry run ruff check backend/
if %errorlevel% neq 0 exit /b %errorlevel%
echo ✅ Ruff: OK
echo.

echo 2️⃣  Mypy (проверка типов - 100%% coverage)...
cd backend && poetry run mypy apps config tests && cd ..
if %errorlevel% neq 0 exit /b %errorlevel%
echo ✅ Mypy: OK
echo.

echo 3️⃣  Black (проверка форматирования)...
poetry run black --check backend/
if %errorlevel% neq 0 exit /b %errorlevel%
echo ✅ Black: OK
echo.

echo 4️⃣  Django system check...
cd backend && poetry run python manage.py check && cd ..
if %errorlevel% neq 0 exit /b %errorlevel%
echo ✅ Django check: OK
echo.

echo 🎉 Все проверки пройдены успешно!
echo.
echo 💡 Ruff заменяет: Flake8 + Isort + PyUpgrade + Bandit
