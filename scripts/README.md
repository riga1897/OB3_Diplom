# Скрипты проекта

Эта директория содержит скрипты для автоматизации разработки, упорядоченные по платформам.

**Последнее обновление:** 27 ноября 2025

## Структура

```
scripts/
├── unix/              # Скрипты для Linux/Mac/WSL (bash)
│   ├── test_all.sh   # Запуск всех тестов + coverage
│   ├── check.sh      # Проверка качества кода
│   ├── fix.sh        # Автоисправление кода
│   └── watch.sh      # Watch-режим (автопроверка при изменении)
│
├── windows/           # Скрипты для Windows
│   ├── test_all.bat  # CMD версия
│   ├── test_all.ps1  # PowerShell версия
│   ├── check.bat     # CMD версия
│   ├── check.ps1     # PowerShell версия
│   ├── fix.bat       # CMD версия
│   └── fix.ps1       # PowerShell версия
│
├── entrypoint.sh      # Docker entrypoint скрипт
│
└── Python модули (используются Poetry)
    ├── check.py      # Модуль для poetry run check
    └── fix.py        # Модуль для poetry run fix
```

---

## Использование

### Linux / macOS / WSL

```bash
# Все тесты + coverage
./scripts/unix/test_all.sh

# Проверка качества кода
./scripts/unix/check.sh

# Автоисправление кода
./scripts/unix/fix.sh

# Watch-режим (автопроверка при изменении файлов)
./scripts/unix/watch.sh
```

### Windows CMD

```cmd
REM Все тесты
scripts\windows\test_all.bat

REM Проверка качества кода
scripts\windows\check.bat

REM Автоисправление кода
scripts\windows\fix.bat
```

### Windows PowerShell

```powershell
# Все тесты
.\scripts\windows\test_all.ps1

# Проверка качества кода
.\scripts\windows\check.ps1

# Автоисправление кода
.\scripts\windows\fix.ps1
```

### Через Poetry (кросс-платформенно)

```bash
poetry run check  # Проверка качества
poetry run fix    # Автоисправление
```

### Через Makefile (только Linux/Mac/WSL)

```bash
make test           # Все тесты локально
make test-docker    # Тесты в Docker
make check          # Проверка качества кода
make fix            # Автоисправление
```

---

## Описание скриптов

### test_all

**Что делает:**
1. Запускает pytest тесты
2. Генерирует coverage отчёт
3. Создаёт HTML отчёт в `var/coverage/htmlcov/`

### check

**Что делает:**
1. Ruff — быстрая проверка багов и стиля
2. Mypy — проверка типов (100% type coverage)
3. Black — проверка форматирования
4. Django system check

### fix

**Что делает:**
1. Ruff — автоисправление проблем
2. Black — автоформатирование кода

### watch (только Unix)

**Что делает:**
- Отслеживает изменения в `apps/`, `config/`, `tests/`
- Автоматически запускает ruff и mypy при сохранении файлов
- Требует `inotify-tools` (устанавливается автоматически)

---

## Работа в Docker

```bash
# Запуск тестов
docker compose exec web pytest

# Проверка качества кода
docker compose exec web ruff check apps/
docker compose exec web mypy apps config tests
docker compose exec web black --check apps/

# Через скрипты
docker compose exec web ./scripts/unix/check.sh
```

---

## Docker Entrypoint

`entrypoint.sh` используется как точка входа для Docker контейнеров:

```bash
# Режимы запуска
./entrypoint.sh web     # Django + Gunicorn (миграции + collectstatic)
./entrypoint.sh worker  # Celery Worker
./entrypoint.sh beat    # Celery Beat
```

---

## Рекомендации

| Ваша ОС | Рекомендуемый способ |
|---------|---------------------|
| **Windows** | `.\scripts\windows\*.ps1` (PowerShell) |
| **Linux/Mac** | `./scripts/unix/*.sh` (bash) или `make` |
| **WSL** | `./scripts/unix/*.sh` (bash) |
| **Docker** | `docker compose exec web pytest` |
| **Любая** | `poetry run check` / `poetry run fix` |

---

## Важно

1. **Unix скрипты** (`*.sh`) требуют прав на выполнение:
   ```bash
   chmod +x scripts/unix/*.sh
   chmod +x scripts/entrypoint.sh
   ```

2. **PowerShell скрипты** могут требовать разрешения:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. **Watch режим** (`watch.sh`) доступен **только на Unix** системах.
