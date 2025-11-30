# Руководство разработчика

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-green?logo=django&logoColor=white)
![Poetry](https://img.shields.io/badge/Poetry-1.8+-purple?logo=poetry&logoColor=white)

**Требования к разработке для проекта OB3 Document Processing Service**

</div>

---

## 📋 Содержание

- [Режимы работы](#-режимы-работы)
- [Настройка окружения](#-настройка-окружения)
- [База данных](#-база-данных)
- [Docker](#-docker)
- [Тестирование](#-тестирование)
- [Качество кода](#-качество-кода)
- [Типизация](#-типизация)
- [Запуск проекта](#-запуск-проекта)
- [API документация](#-api-документация)
- [Архитектура](#-архитектура)

---

## 🔄 Режимы работы

Проект поддерживает два режима работы:

| Режим | Файл конфигурации | Назначение |
|-------|-------------------|------------|
| **Development** | `.env.develop` → `.env` | Локальная разработка (Replit, Windows, Linux, macOS) |
| **Staging/Docker** | `.env.stage` → `.env` | Docker Compose с полным стеком |

### Development (без Redis/Celery)

```env
CELERY_TASK_ALWAYS_EAGER=True   # Задачи выполняются синхронно
CACHE_BACKEND=locmem            # Локальный кэш в памяти
DEBUG=True
ALLOWED_HOSTS=*
```

### Staging/Docker (полный стек)

```env
CELERY_TASK_ALWAYS_EAGER=False  # Асинхронные задачи через Redis
CACHE_BACKEND=redis             # Redis для кэширования
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
```

---

## ⚙️ Настройка окружения

### Требования к системе

| Компонент | Версия | Обязательность |
|-----------|--------|----------------|
| Python | 3.12+ | ✅ Обязательно |
| PostgreSQL | 16+ | ✅ Обязательно |
| Poetry | 1.8+ | ✅ Обязательно |
| Git | Latest | ✅ Обязательно |
| Redis | 7+ | ⚪ Опционально |
| Docker | 20+ | ⚪ Опционально |

### Установка зависимостей

```bash
# 1. Клонировать репозиторий
git clone <repository-url>
cd ob3-document-processing-service

# 2. Установить зависимости через Poetry
poetry install

# 3. Активировать виртуальное окружение
poetry shell
```

### Переменные окружения

```bash
# Для локальной разработки
cp .env.develop.example .env

# Для Docker/Staging
cp .env.stage.example .env
```

<details>
<summary>📝 Обязательные переменные</summary>

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,*

# Database
DB_NAME=ob3_documents
DB_USER=ob3_user
DB_PASSWORD=ob3_password
DB_HOST=localhost
DB_PORT=5432

# Или DATABASE_URL для Replit
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Временная зона
TZ=Europe/Moscow
```

</details>

<details>
<summary>📝 Переменные для Staging/Docker</summary>

```env
# Redis & Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
REDIS_URL=redis://redis:6379/1
CELERY_TASK_ALWAYS_EAGER=False
CACHE_BACKEND=redis

# API Throttling
THROTTLE_ANON=100/day
THROTTLE_USER=1000/day
THROTTLE_UPLOAD=10/hour

# File Upload
MAX_UPLOAD_SIZE=10485760  # 10MB
```

</details>

> ⚠️ **Важно:** Никогда не коммитить `.env` в Git!

---

## 🗄️ База данных

### Создание базы данных PostgreSQL

**Windows (PowerShell):**
```powershell
psql -U postgres -c "CREATE DATABASE ob3_documents;"
psql -U postgres -c "CREATE USER ob3_user WITH PASSWORD 'ob3_password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE ob3_documents TO ob3_user;"
```

**Linux/macOS:**
```bash
sudo -u postgres psql -c "CREATE DATABASE ob3_documents;"
sudo -u postgres psql -c "CREATE USER ob3_user WITH PASSWORD 'ob3_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ob3_documents TO ob3_user;"
```

### Миграции

```bash
# Создать миграции
poetry run python manage.py makemigrations

# Применить миграции
poetry run python manage.py migrate

# Проверить статус
poetry run python manage.py showmigrations
```

### Management команды

#### `create_superuser` — Создание суперпользователя

```bash
# С дефолтным паролем "admin123"
poetry run python manage.py create_superuser

# С кастомными параметрами
poetry run python manage.py create_superuser \
    --username admin \
    --email admin@example.com \
    --password SecurePass123
```

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `--username` | Имя пользователя | `admin` |
| `--email` | Email | `admin@example.com` |
| `--password` | Пароль | `admin123` |

> ✅ **Идемпотентность:** Если пользователь уже существует, команда пропустит создание.

#### `load_initial_data` — Загрузка начальных данных

```bash
# Полная перезагрузка: очистка БД + загрузка фикстур
poetry run python manage.py load_initial_data

# Dry-run (показать план без выполнения)
poetry run python manage.py load_initial_data --dry-run
```

**Что делает команда:**
1. Очищает все таблицы приложений (TRUNCATE CASCADE)
2. Сбрасывает sequences (счётчики ID)
3. Загружает фикстуры в правильном порядке

**Доступные фикстуры:**

| Файл | Содержимое |
|------|------------|
| `fixtures/users.json` | Пользователи: `admin` (superuser), `user` (обычный) |
| `fixtures/documents.json` | 6 документов: 2 approved, 2 pending, 2 rejected |

---

## 🐳 Docker

### Архитектура контейнеров

```
postgres ──┐
           ├─→ web (миграции + collectstatic) ─┬─→ nginx
redis ─────┘                                   ├─→ celery_worker
                                               └─→ celery_beat
```

### Быстрый старт

```bash
# 1. Скопировать конфигурацию
cp .env.stage.example .env

# 2. Отредактировать SECRET_KEY
nano .env

# 3. Запустить все сервисы
docker compose up -d

# 4. Создать суперпользователя
docker compose exec web python manage.py create_superuser

# 5. Загрузить начальные данные
docker compose exec web python manage.py load_initial_data
```

### Основные команды

| Команда | Описание |
|---------|----------|
| `docker compose up -d` | Запустить сервисы |
| `docker compose down` | Остановить сервисы |
| `docker compose logs -f` | Просмотр логов |
| `docker compose build --no-cache` | Пересобрать образы |
| `docker compose down -v` | Удалить с volumes |

> 📖 Подробнее: [docker.md](docker.md)

---

## 🧪 Тестирование

> **Архитектурное решение:** OB3 использует **pytest-django 100%** для всего тестирования.

### Статистика

| Метрика | Значение |
|---------|----------|
| Тесты | 250 |
| Покрытие | 100% |
| Минимум | 95% |

### Запуск тестов

#### Docker (рекомендуется)

> ⚠️ **Важно:** Используйте флаг `-e DJANGO_SETTINGS_MODULE=config.settings.test`

```bash
# Все тесты
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test web pytest

# С verbose выводом
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test web pytest -v --tb=short

# Только unit-тесты
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test web pytest -m unit

# Только integration-тесты
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test web pytest -m integration

# Параллельное выполнение
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test web pytest -n auto
```

**Почему нужен флаг `-e`?**
- В `docker-compose.yml` установлен `DJANGO_SETTINGS_MODULE=config.settings.staging`
- Флаг переопределяет настройки для тестов:
  - Изолированный `MEDIA_ROOT` (`/app/var/media/tests/`)
  - Celery в eager mode
  - Быстрое хэширование паролей

#### Локально

```bash
# Все тесты
poetry run pytest

# С покрытием
poetry run pytest --cov=apps --cov-report=html:var/coverage/htmlcov

# С переиспользованием БД (быстрее)
poetry run pytest --reuse-db
```

### Coverage отчёты

```bash
# HTML отчёт
open var/coverage/htmlcov/index.html

# XML отчёт (для CI/CD)
cat var/coverage/coverage.xml
```

---

## 🔍 Качество кода

### Линтинг-стек

| Инструмент | Назначение | Порядок |
|------------|------------|---------|
| **Ruff** | Linting + Isort | 1️⃣ Первый |
| **Mypy** | Type checking | 2️⃣ Второй |
| **Black** | Форматирование | 3️⃣ Третий |

### Порядок выполнения

```bash
# 1. RUFF - выполняется ПЕРВЫМ
poetry run ruff check apps/

# 2. MYPY - проверка типов (strict mode)
poetry run mypy apps config tests

# 3. BLACK - форматирование кода
poetry run black apps/
```

### Автоматическое исправление

```bash
# Применить все автофиксы
poetry run ruff check --fix apps/
poetry run black apps/
```

### Pre-commit hooks

```bash
# Установка
poetry run pre-commit install

# Ручной запуск
poetry run pre-commit run --all-files
```

---

## 📝 Типизация

### Конфигурация Mypy

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### Требования

- ✅ **100% type coverage** — обязательно для всех файлов
- ✅ Все функции должны иметь аннотации типов

```python
# ❌ ПЛОХО: Нет типов
def get_documents(user_id):
    return Document.objects.filter(owner_id=user_id)

# ✅ ХОРОШО: Полная типизация
from django.db.models import QuerySet

def get_documents(user_id: int) -> QuerySet["Document"]:
    """Получить документы пользователя."""
    return Document.objects.filter(owner_id=user_id)
```

---

## 🚀 Запуск проекта

### Development (без Celery)

```bash
poetry run python manage.py runserver 0.0.0.0:5000
```

### Development (с Celery)

Требуется **4 терминала**:

```bash
# Терминал 1: Redis
redis-server

# Терминал 2: Celery Worker
poetry run celery -A config worker --pool=solo -l info  # Windows
poetry run celery -A config worker -l info              # Linux/macOS

# Терминал 3: Celery Beat
poetry run celery -A config beat -l info

# Терминал 4: Django Server
poetry run python manage.py runserver 0.0.0.0:5000
```

### Проверка работоспособности

```bash
# Django
poetry run python manage.py check

# Redis
redis-cli ping  # Должен вернуть PONG

# Celery
poetry run celery -A config inspect active
```

---

## 📖 API документация

| Сервис | URL |
|--------|-----|
| Swagger UI | http://127.0.0.1:5000/api/schema/swagger-ui/ |
| ReDoc | http://127.0.0.1:5000/api/schema/redoc/ |
| OpenAPI Schema | http://127.0.0.1:5000/api/schema/ |
| Django Admin | http://127.0.0.1:5000/admin/ |
| API Root | http://127.0.0.1:5000/api/ |
| Health Check | http://127.0.0.1:5000/health/ |

### JWT аутентификация

```bash
# Получение токенов
curl -X POST http://localhost:5000/api/users/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Использование токена
curl -X GET http://localhost:5000/api/documents/ \
  -H "Authorization: Bearer <access_token>"

# Обновление токена
curl -X POST http://localhost:5000/api/users/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<refresh_token>"}'
```

---

## 🏛️ Архитектура

### Структура проекта

```
.
├── apps/                       # Django приложения
│   ├── core/                   # Абстрактные модели, общие компоненты
│   │   ├── cache.py            # CacheManager для кэширования
│   │   └── management/         # Management команды
│   ├── documents/              # Обработка документов
│   │   ├── models.py           # Document, ProcessingTask
│   │   ├── views.py            # DocumentViewSet
│   │   ├── serializers.py      # DocumentSerializer
│   │   ├── permissions.py      # IsOwner, IsModerator
│   │   ├── services.py         # Service Layer (бизнес-логика)
│   │   ├── tasks.py            # Celery tasks
│   │   ├── file_types.py       # Категоризация файлов
│   │   └── validators.py       # Валидаторы
│   └── users/                  # Пользователи и аутентификация
├── config/                     # Настройки Django
│   ├── settings/               # base, development, staging, test
│   ├── celery.py               # Celery конфигурация
│   └── urls.py
├── fixtures/                   # Начальные данные
├── tests/                      # Тесты (pytest-django)
├── docs/                       # Документация
├── var/                        # Артефакты
│   ├── media/                  # Загруженные документы
│   ├── logs/                   # Логи приложения
│   └── coverage/               # Coverage отчёты
├── nginx/                      # Nginx конфигурация
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

### Service Layer Pattern

```
View → Serializer → Service → Model
                       ↓
                  Celery Task
```

- **Views** — HTTP обработка, валидация
- **Services** — бизнес-логика
- **Tasks** — асинхронная обработка
- **Models** — данные

### Async Views vs Celery

| Критерий | Async Views | Sync + Celery (наш выбор) |
|----------|-------------|---------------------------|
| Параллельные внешние API | Нужны | Не используем |
| WebSockets | Нужны | Не используем |
| Тяжёлые фоновые задачи | Не подходят | ✅ Celery |
| CRUD операции | Избыточны | ✅ Sync views |
| Сложность отладки | Выше | Ниже |

---

## 🛡️ Безопасность

### Чек-лист

- [x] `.env` добавлен в `.gitignore`
- [x] `SECRET_KEY` не захардкожен
- [x] `DEBUG=False` на staging/production
- [x] `ALLOWED_HOSTS` настроен
- [x] Пароли не логируются
- [x] SQL инъекции защищены через ORM
- [x] CSRF middleware включен

### Категоризация файлов

**Разрешённые (~120 расширений):**
- 📄 Документы: PDF, DOCX, TXT, RTF, ODT
- 🖼️ Изображения: JPG, PNG, GIF, WEBP
- 🎵 Аудио: MP3, WAV, FLAC
- 🎬 Видео: MP4, AVI, MKV
- 📊 Данные: CSV, JSON, XML

**Заблокированные (~70 расширений):**
- ❌ Исполняемые: `.exe`, `.dll`, `.so`
- ❌ Скрипты: `.bat`, `.cmd`, `.ps1`, `.sh`
- ❌ Макросы: `.docm`, `.xlsm`, `.pptm`

---

<div align="center">

**Последнее обновление:** 28 ноября 2025

**Проект:** OB3 Document Processing Service

</div>
