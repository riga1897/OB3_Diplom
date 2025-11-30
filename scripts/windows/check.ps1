# Скрипт для запуска всех проверок качества кода
# Использование: .\scripts\windows\check.ps1 или poetry run check

Write-Host "🔍 Запуск проверок качества кода..." -ForegroundColor Cyan
Write-Host ""

Write-Host "1️⃣  Ruff (быстрая проверка багов и стиля)..." -ForegroundColor Yellow
poetry run ruff check users/ lms/ config/
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "✅ Ruff: OK" -ForegroundColor Green
Write-Host ""

Write-Host "2️⃣  Mypy (проверка типов)..." -ForegroundColor Yellow
poetry run mypy users/ lms/ config/
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "✅ Mypy: OK" -ForegroundColor Green
Write-Host ""

Write-Host "3️⃣  Black (проверка форматирования)..." -ForegroundColor Yellow
poetry run black --check users/ lms/ config/
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "✅ Black: OK" -ForegroundColor Green
Write-Host ""

Write-Host "4️⃣  Isort (проверка сортировки импортов)..." -ForegroundColor Yellow
poetry run isort --check-only users/ lms/ config/
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "✅ Isort: OK" -ForegroundColor Green
Write-Host ""

Write-Host "5️⃣  Flake8 (дополнительные проверки)..." -ForegroundColor Yellow
poetry run flake8 users/ lms/ config/
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "✅ Flake8: OK" -ForegroundColor Green
Write-Host ""

Write-Host "6️⃣  Django system check..." -ForegroundColor Yellow
poetry run python manage.py check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "✅ Django check: OK" -ForegroundColor Green
Write-Host ""

Write-Host "🎉 Все проверки пройдены успешно!" -ForegroundColor Green
