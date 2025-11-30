# Скрипт для автоматического исправления проблем в коде
# Использование: .\scripts\windows\fix.ps1 или poetry run fix

Write-Host "🔧 Автоматическое исправление кода..." -ForegroundColor Cyan
Write-Host ""

Write-Host "1️⃣  Ruff (автоисправление)..." -ForegroundColor Yellow
poetry run ruff check --fix users/ lms/ config/
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "✅ Ruff: исправлено" -ForegroundColor Green
Write-Host ""

Write-Host "2️⃣  Black (форматирование)..." -ForegroundColor Yellow
poetry run black users/ lms/ config/
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "✅ Black: отформатировано" -ForegroundColor Green
Write-Host ""

Write-Host "3️⃣  Isort (сортировка импортов)..." -ForegroundColor Yellow
poetry run isort users/ lms/ config/
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "✅ Isort: отсортировано" -ForegroundColor Green
Write-Host ""

Write-Host "🎉 Код автоматически исправлен!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Теперь запустите: poetry run check" -ForegroundColor Cyan
