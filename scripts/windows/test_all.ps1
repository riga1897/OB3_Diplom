# Скрипт для запуска всех тестов проекта (pytest-django)
# Генерирует coverage отчёт
#
# Использование:
#   .\scripts\windows\test_all.ps1                     # В PowerShell
#   docker-compose exec web pwsh scripts/windows/test_all.ps1  # В Docker

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "🧪 Starting test suite..." -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📋 Running pytest-django tests (250 tests)" -ForegroundColor Yellow
Write-Host "Location: tests/ directory"
Write-Host "---"
poetry run pytest tests/ --cov=apps --cov=config --cov-report=html:var/coverage/htmlcov --cov-report=xml:var/coverage/coverage.xml
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "✅ All tests completed!" -ForegroundColor Green
Write-Host "📊 HTML coverage report: var\coverage\htmlcov\index.html"
Write-Host "================================" -ForegroundColor Green
