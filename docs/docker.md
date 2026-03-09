# Docker Development Setup

<div align="center">

![Docker](https://img.shields.io/badge/Docker-20+-blue?logo=docker&logoColor=white)
![Docker Compose](https://img.shields.io/badge/Docker%20Compose-2.0+-blue?logo=docker&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-red?logo=redis&logoColor=white)

**Руководство по настройке Docker для OB3 Document Processing Service**

</div>

---

## 📋 Содержание

- [Обзор](#-обзор)
- [Архитектура](#-архитектура)
- [Предварительные требования](#-предварительные-требования)
- [Быстрый старт](#-быстрый-старт)
- [Переменные окружения](#-переменные-окружения)
- [Volumes и персистентность](#-volumes-и-персистентность)
- [Тестирование в Docker](#-тестирование-в-docker)
- [Управление сервисами](#-управление-сервисами)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Обзор

### Ключевые особенности

| Особенность | Описание |
|-------------|----------|
| 🐳 **6 сервисов** | PostgreSQL, Redis, Django Web, Celery Worker, Celery Beat, Nginx |
| 📦 **Multi-stage Dockerfile** | Оптимизация размера образа (builder + runtime) |
| 🔄 **Автоматические миграции** | Применяются через entrypoint script |
| ❤️ **Health checks** | Мониторинг состояния всех сервисов |
| 💾 **Named volumes** | Персистентность данных PostgreSQL и media |
| 🔒 **Non-root пользователь** | Безопасность: пользователь `ob3` (UID 1000) |

### Когда использовать Docker

| ✅ Используйте Docker | ❌ Используйте локальную разработку |
|----------------------|-------------------------------------|
| Работа в команде | Быстрая итерация и debugging |
| Тестирование Celery | Работа только с Django |
| Полная изоляция | Ограниченные ресурсы |
| Подготовка к production | — |

---

## 🏗️ Архитектура

### Диаграмма сервисов

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose Network                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │    Nginx     │    │  PostgreSQL  │    │    Redis     │   │
│  │   Port: 80   │───▶│   Database   │    │Message Broker│   │
│  └──────┬───────┘    └──────────────┘    └──────┬───────┘   │
│         │                    │                   │           │
│         ▼                    ▼                   ▼           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │  Web Django  │───▶│Celery Worker │◀───│ Celery Beat  │   │
│  │  + Gunicorn  │    │ (async tasks)│    │  (scheduler) │   │
│  │  Port: 8000  │    └──────────────┘    └──────────────┘   │
│  └──────────────┘                                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Описание сервисов

<table>
<tr>
<td width="50%">

#### 1. postgres — Database
| Параметр | Значение |
|----------|----------|
| Образ | `postgres:16-alpine` |
| Container | `ob3_postgres` |
| Volume | `postgres_data` |
| Healthcheck | `pg_isready` |

#### 2. redis — Message Broker
| Параметр | Значение |
|----------|----------|
| Образ | `redis:7-alpine` |
| Container | `ob3_redis` |
| DB №0 | Celery broker |
| DB №1 | Django cache |

#### 3. web — Django Application
| Параметр | Значение |
|----------|----------|
| Образ | Custom multi-stage |
| Container | `ob3_web` |
| Port | 8000 (internal) |
| User | `ob3` (UID 1000) |

</td>
<td width="50%">

#### 4. celery_worker — Async Tasks
| Параметр | Значение |
|----------|----------|
| Образ | Custom (тот же что web) |
| Container | `ob3_celery_worker` |
| Команда | `celery -A config worker` |
| Задачи | Обработка документов |

#### 5. celery_beat — Scheduler
| Параметр | Значение |
|----------|----------|
| Образ | Custom (тот же что web) |
| Container | `ob3_celery_beat` |
| Команда | `celery -A config beat` |
| Задачи | Периодические задачи |

#### 6. nginx — Reverse Proxy
| Параметр | Значение |
|----------|----------|
| Образ | `nginx:1.25-alpine` |
| Container | `ob3_nginx` |
| Port | 80 (external) |
| Зависимости | web (healthy) |

</td>
</tr>
</table>

---

## 📋 Предварительные требования

### Установка Docker

<details>
<summary>🪟 Windows</summary>

1. Скачайте [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
2. Запустите установщик
3. Проверьте:
```powershell
docker --version
docker compose version
```

</details>

<details>
<summary>🍎 macOS</summary>

1. Скачайте [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
2. Проверьте:
```bash
docker --version
docker compose version
```

</details>

<details>
<summary>🐧 Linux (Ubuntu/Debian)</summary>

```bash
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER
docker --version
docker compose version
```

</details>

### Минимальные требования

| Ресурс | Минимум | Рекомендуется |
|--------|---------|---------------|
| RAM | 4 GB | 8 GB |
| Disk | 10 GB | 20 GB |
| CPU | 2 cores | 4 cores |

---

## 🚀 Быстрый старт

> ⚠️ **ВАЖНО:** При первом запуске необходимо **собрать образы** локально!
> Образы `web`, `celery_worker`, `celery_beat` собираются из Dockerfile проекта и не существуют в Docker Hub.

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd ob3-project
```

### 2. Настройка переменных окружения

```bash
cp .env.stage.example .env
# Отредактируйте SECRET_KEY!
nano .env
```

### 3. Сборка и запуск

#### Первый запуск (обязательно с `--build`)

```bash
# Собрать образы И запустить контейнеры
docker compose up --build -d

# Просмотр логов
docker compose logs -f
```

#### Последующие запуски

```bash
# Если код не менялся — без пересборки
docker compose up -d

# Если код изменился — с пересборкой
docker compose up --build -d
```

<details>
<summary>❓ Ошибка "pull access denied for web"</summary>

**Причина:** Docker пытается скачать образ `web` из Docker Hub, но его там нет — он должен быть собран локально из `Dockerfile`.

**Решение:**
```bash
# Сначала соберите образы
docker compose build

# Затем запустите
docker compose up -d

# Или одной командой
docker compose up --build -d
```

</details>

### 4. Создание суперпользователя

```bash
# Быстрый способ (admin / admin123)
docker compose exec web python manage.py create_superuser

# С кастомным паролем
docker compose exec web python manage.py create_superuser --password SecurePass123
```

### 5. Загрузка начальных данных

```bash
# Полная перезагрузка БД + фикстуры
docker compose exec web python manage.py load_initial_data

# Dry-run (показать план)
docker compose exec web python manage.py load_initial_data --dry-run
```

<details>
<summary>📦 Содержимое фикстур</summary>

| Файл | Содержимое |
|------|------------|
| `fixtures/users.json` | `admin` (superuser), `user` (обычный) |
| `fixtures/documents.json` | 6 документов (2 approved, 2 pending, 2 rejected) |

</details>

### 6. Проверка работы

| Сервис | URL |
|--------|-----|
| API Root | http://localhost/api/ |
| Swagger UI | http://localhost/api/schema/swagger-ui/ |
| Django Admin | http://localhost/admin/ |
| Health Check | http://localhost/health/ |

---

## ⚙️ Переменные окружения

### Основные переменные

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL
DB_NAME=ob3_documents
DB_USER=ob3_user
DB_PASSWORD=ob3_password
DB_HOST=postgres
DB_PORT=5432

# Redis & Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
REDIS_URL=redis://redis:6379/1
CACHE_BACKEND=redis
CELERY_TASK_ALWAYS_EAGER=False
```

> ⚠️ **Важно:** `SECRET_KEY` должен содержать `$$` вместо `$` для экранирования в Docker Compose.

---

## 💾 Volumes и персистентность

### Named Volumes

| Volume | Путь в контейнере | Содержимое |
|--------|-------------------|------------|
| `postgres_data` | `/var/lib/postgresql/data` | База данных PostgreSQL |
| `redis_data` | `/data` | Redis persistence |
| `static_files` | `/app/staticfiles` | Статические файлы |
| `media_files` | `/app/var/media` | Загруженные документы |

### Bind Mounts

| Host путь | Путь в контейнере | Назначение |
|-----------|-------------------|------------|
| `./var/logs` | `/app/var/logs` | Логи приложения |
| `./var/coverage` | `/app/var/coverage` | Coverage отчёты |
| `./tests` | `/app/tests` | Тесты (hot reload) |
| `./fixtures` | `/app/fixtures` | Фикстуры |

### Управление Volumes

```bash
# Список всех volumes
docker volume ls

# Backup базы данных
docker compose exec postgres pg_dump -U ob3_user ob3_documents > backup.sql

# Restore базы данных
docker compose exec -T postgres psql -U ob3_user ob3_documents < backup.sql

# Удаление volumes (ОСТОРОЖНО!)
docker compose down -v
```

---

## 🧪 Тестирование в Docker

### Запуск тестов

> ⚠️ **Важно:** Используйте флаг `-e DJANGO_SETTINGS_MODULE=config.settings.test`

```bash
# Все тесты
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test web pytest

# С verbose выводом
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test web pytest -v --tb=short

# Только unit тесты
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test web pytest -m unit

# Только integration тесты
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test web pytest -m integration

# Параллельное выполнение
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test web pytest -n auto
```

<details>
<summary>❓ Почему нужен флаг -e?</summary>

- В `docker-compose.yml` установлен `DJANGO_SETTINGS_MODULE=config.settings.staging`
- Флаг `-e` переопределяет настройки для тестов:
  - Изолированный `MEDIA_ROOT` (`/app/var/media/tests/`)
  - Тестовая база данных
  - Celery в eager mode
  - Быстрое хэширование паролей (MD5)

</details>

### Coverage отчёты

```bash
# HTML отчёт
open var/coverage/htmlcov/index.html

# XML отчёт (для CI/CD)
cat var/coverage/coverage.xml
```

### Code Quality

```bash
# Ruff (linting)
docker compose exec web ruff check apps/

# Mypy (type checking)
docker compose exec web mypy apps config tests

# Black (formatting check)
docker compose exec web black --check apps/
```

---

## 🎛️ Управление сервисами

### Основные команды

| Команда | Описание |
|---------|----------|
| `docker compose up -d` | Запуск всех сервисов |
| `docker compose down` | Остановка всех сервисов |
| `docker compose restart` | Перезапуск всех сервисов |
| `docker compose restart web` | Перезапуск одного сервиса |
| `docker compose ps` | Статус сервисов |
| `docker compose logs -f` | Логи всех сервисов |
| `docker compose logs -f web` | Логи конкретного сервиса |

### Rebuild образов

```bash
# После изменения Dockerfile или зависимостей
docker compose up --build -d

# Принудительная пересборка без cache
docker compose build --no-cache

# Пересборка одного сервиса
docker compose build web
```

### Выполнение команд

```bash
# Django shell
docker compose exec web python manage.py shell

# Создание миграций
docker compose exec web python manage.py makemigrations

# Применение миграций
docker compose exec web python manage.py migrate

# Bash в контейнере
docker compose exec web bash
```

---

## 🔧 Troubleshooting

### Контейнер web не стартует

<details>
<summary>🔍 Решение</summary>

```bash
# Проверьте логи
docker compose logs web

# Частые причины:
# 1. PostgreSQL не готов - подождите healthcheck
# 2. Ошибка в миграциях - исправьте и пересоберите
# 3. SECRET_KEY не установлен - проверьте .env
```

</details>

### Celery worker не подключается к Redis

<details>
<summary>🔍 Решение</summary>

```bash
# Проверьте что Redis запущен
docker compose ps redis

# Проверьте healthcheck
docker compose exec redis redis-cli ping
```

</details>

### Тесты не находят pytest

<details>
<summary>🔍 Решение</summary>

```bash
# Пересоберите образ с dev зависимостями
docker compose build --no-cache web
```

</details>

### База данных не создаётся

<details>
<summary>🔍 Решение</summary>

```bash
# Проверьте postgres
docker compose ps postgres

# Проверьте переменные окружения
docker compose exec web env | grep DB_

# Пересоздайте volume (удалит данные!)
docker compose down -v
docker compose up -d
```

</details>

### Coverage не сохраняется

<details>
<summary>🔍 Решение</summary>

```bash
# Проверьте права на директорию
ls -la var/

# Создайте директорию
mkdir -p var/coverage

# Проверьте что volume смонтирован
docker compose exec web ls -la /app/var/coverage/
```

</details>

### Nginx возвращает 502 Bad Gateway

<details>
<summary>🔍 Решение</summary>

```bash
# Проверьте что web healthy
docker compose ps web

# Проверьте healthcheck endpoint
docker compose exec web curl -f http://localhost:8000/health/

# Перезапустите nginx после web
docker compose restart nginx
```

</details>

---

## 📦 Multi-stage Dockerfile

```dockerfile
# Stage 1: Builder
FROM python:3.12-slim AS builder
# Устанавливает Poetry и зависимости в .venv

# Stage 2: Runtime
FROM python:3.12-slim AS runtime
# Создаёт директории ДО копирования .venv
RUN mkdir -p /app/var/{media,logs,coverage} && chown -R ob3:ob3 /app

# Копирует готовый .venv без Poetry
COPY --from=builder --chown=ob3:ob3 /app/.venv /app/.venv
```

### Преимущества

| Преимущество | Описание |
|--------------|----------|
| 📦 Меньший размер | Нет Poetry в runtime |
| 🔒 Безопасность | Non-root пользователь |
| ⚡ Оптимизация | mkdir + chown до COPY .venv |
| 🔧 PATH | Настроен на .venv напрямую |

---

<div align="center">

**Создано:** 27 ноября 2025 • **Обновлено:** 28 ноября 2025

**Django 5.2.7 • DRF 3.16.1 • Python 3.12**

</div>
