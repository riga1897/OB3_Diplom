# Скрипт для запуска всех проверок качества кода
# Использование: .\scripts\windows\check.ps1

Write-Host "🔍 Запуск проверок качества кода..." -ForegroundColor Cyan
Write-Host ""

Write-Host "1️⃣  Ruff (быстрая проверка багов и стиля)..." -ForegroundColor Yellow
poetry run ruff check apps/ config/ tests/
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "✅ Ruff: OK" -ForegroundColor Green
Write-Host ""

Write-Host "2️⃣  Mypy (проверка типов - 100% coverage)..." -ForegroundColor Yellow
poetry run mypy apps/ config/ tests/
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "✅ Mypy: OK" -ForegroundColor Green
Write-Host ""

Write-Host "3️⃣  Black (проверка форматирования)..." -ForegroundColor Yellow
poetry run black --check apps/ config/ tests/
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "✅ Black: OK" -ForegroundColor Green
Write-Host ""

Write-Host "4️⃣  Django system check..." -ForegroundColor Yellow
poetry run python manage.py check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "✅ Django check: OK" -ForegroundColor Green
Write-Host ""

Write-Host "🎉 Все проверки пройдены успешно!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Ruff заменяет: Flake8 + Isort + PyUpgrade + Bandit" -ForegroundColor Cyan
