# Скрипт для запуска всех тестов проекта (Django APITestCase + pytest-django)
# Генерирует комбинированный coverage отчёт
#
# Использование:
#   .\scripts\windows\test_all.ps1                     # В PowerShell
#   docker-compose exec web pwsh scripts/windows/test_all.ps1  # В Docker (если установлен pwsh)

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "🧪 Starting test suite..." -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📋 Step 1/3: Running Django APITestCase tests (78 tests)" -ForegroundColor Yellow
Write-Host "Location: lms/tests.py, users/tests.py"
Write-Host "---"
poetry run coverage run --source=users,lms,config manage.py test
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "📋 Step 2/3: Running pytest-django tests (187 tests)" -ForegroundColor Yellow
Write-Host "Location: tests/ directory"
Write-Host "---"
poetry run coverage run --append --source=users,lms,config -m pytest --no-cov
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "📋 Step 3/3: Generating coverage report" -ForegroundColor Yellow
Write-Host "---"
poetry run coverage report
poetry run coverage html

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "✅ All 265 tests completed!" -ForegroundColor Green
Write-Host "📊 HTML coverage report: htmlcov\index.html"
Write-Host "================================" -ForegroundColor Green
