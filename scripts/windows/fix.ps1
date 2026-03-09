# Скрипт для автоматического исправления проблем в коде
# Использование: .\scripts\windows\fix.ps1

Write-Host "🔧 Автоматическое исправление кода..." -ForegroundColor Cyan
Write-Host ""

Write-Host "1️⃣  Ruff (автоисправление + isort)..." -ForegroundColor Yellow
poetry run ruff check --fix apps/ config/ tests/
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "✅ Ruff: исправлено" -ForegroundColor Green
Write-Host ""

Write-Host "2️⃣  Black (форматирование)..." -ForegroundColor Yellow
poetry run black apps/ config/ tests/
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "✅ Black: отформатировано" -ForegroundColor Green
Write-Host ""

Write-Host "🎉 Код автоматически исправлен!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Теперь запустите: .\scripts\windows\check.ps1" -ForegroundColor Cyan
Write-Host "💡 Ruff заменяет: Flake8 + Isort" -ForegroundColor Cyan
