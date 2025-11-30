@echo off
REM Скрипт для автоматического исправления проблем в коде
REM Использование: scripts\windows\fix.bat или poetry run fix

echo 🔧 Автоматическое исправление кода (Ruff + Black)...
echo.

echo 1️⃣  Ruff (автоисправление + isort)...
poetry run ruff check --fix backend/
if %errorlevel% neq 0 exit /b %errorlevel%
echo ✅ Ruff: исправлено
echo.

echo 2️⃣  Black (форматирование)...
poetry run black backend/
if %errorlevel% neq 0 exit /b %errorlevel%
echo ✅ Black: отформатировано
echo.

echo 🎉 Код автоматически исправлен!
echo.
echo 💡 Теперь запустите: poetry run check
echo 💡 Ruff заменяет: Flake8 + Isort
