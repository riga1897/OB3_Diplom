# OB3 Document Processing Service

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-green?logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/DRF-3.16-red?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-red?logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5.5-green?logo=celery&logoColor=white)
![Coverage](https://img.shields.io/badge/Coverage-100%25-brightgreen)
![Tests](https://img.shields.io/badge/Tests-250-success)

**Django REST API сервис для автоматической обработки, классификации и валидации документов**

[Быстрый старт](#-быстрый-старт) •
[API](#-api-endpoints) •
[Документация](#-документация) •
[Разработка](#-разработка)

</div>

---

## 📋 Содержание

- [О проекте](#-о-проекте)
- [Возможности](#-возможности)
- [Технологии](#-технологии)
- [Быстрый старт](#-быстрый-старт)
- [API Endpoints](#-api-endpoints)
- [Тестирование](#-тестирование)
- [Разработка](#-разработка)
- [Безопасность](#-безопасность)
- [Документация](#-документация)

---

## 🎯 О проекте

**OB3 Document Processing Service** — backend-сервис для автоматизированной обработки документов различных форматов. Разработан как дипломный проект курса Python Developer.

| | |
|---|---|
| **Студент** | Python Developer Course |
| **Направление** | Backend Development (OB3) |
| **Дата** | Ноябрь 2025 |

---

## ✨ Возможности

| Функция | Описание |
|---------|----------|
| 📤 **Загрузка документов** | PDF, DOCX, TXT, JPG, PNG и другие форматы |
| 📝 **Извлечение текста** | Автоматическое извлечение из PDF и DOCX |
| 🏷️ **Классификация** | Определение типа: invoice, contract, report, letter |
| ⚡ **Асинхронная обработка** | Фоновые задачи через Celery + Redis |
| 🔐 **JWT аутентификация** | Безопасный доступ к API |
| 📖 **Swagger/ReDoc** | Интерактивная API документация |
| 🛡️ **Валидация файлов** | Многоуровневая защита от вредоносных файлов |

---

## 🛠️ Технологии

<table>
<tr>
<td width="50%">

### Backend
| Технология | Версия |
|------------|--------|
| Python | 3.12 |
| Django | 5.2.7 |
| Django REST Framework | 3.16.1 |
| PostgreSQL | 16 |
| Redis | 7 |
| Celery | 5.5.3 |

</td>
<td width="50%">

### Инструменты
| Инструмент | Назначение |
|------------|------------|
| Poetry | Зависимости |
| Docker Compose | Контейнеризация |
| pytest | Тестирование |
| Ruff | Линтинг |
| Mypy | Типизация |
| Black | Форматирование |

</td>
</tr>
</table>

---

## 🏗️ Архитектура

### Структура проекта

```
ob3-document-processing-service/
├── apps/                          # Django приложения
│   ├── core/                      # Общие компоненты, абстрактные модели
│   │   ├── cache.py               # Менеджер кэширования
│   │   └── management/commands/   # Management команды
│   ├── users/                     # Пользователи + JWT аутентификация
│   └── documents/                 # Обработка документов
│       ├── file_types.py          # Категоризация файлов (~120 расширений)
│       ├── services.py            # Service Layer (бизнес-логика)
│       ├── tasks.py               # Celery задачи
│       └── validators.py          # Валидаторы безопасности
├── config/                        # Конфигурация Django
│   ├── settings/                  # Settings (base, development, staging, test)
│   └── celery.py                  # Конфигурация Celery
├── fixtures/                      # Фикстуры для начальных данных
├── tests/                         # Тесты (pytest-django, 250 тестов)
├── docs/                          # Документация
├── var/                           # Артефакты (media, logs, coverage)
├── nginx/                         # Конфигурация Nginx
├── docker-compose.yml             # Docker сервисы
├── Dockerfile                     # Multi-stage образ
└── pyproject.toml                 # Poetry конфигурация
```

### Docker контейнеры

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

---

## 🚀 Быстрый старт

### Предварительные требования

- Docker 20+ и Docker Compose
- Git

### 1. Клонировать репозиторий

```bash
git clone <repository-url>
cd ob3-document-processing-service
```

### 2. Настроить окружение

```bash
cp .env.stage.example .env
# Отредактируйте SECRET_KEY в .env файле
```

### 3. Запустить Docker Compose

```bash
docker compose up --build -d
```

> Миграции и collectstatic выполняются автоматически при запуске.

### 4. Создать суперпользователя

```bash
# Быстрый способ (admin / admin123)
docker compose exec web python manage.py create_superuser

# С кастомным паролем
docker compose exec web python manage.py create_superuser --password SecurePass123
```

### 5. Загрузить тестовые данные (опционально)

```bash
docker compose exec web python manage.py load_initial_data
```

<details>
<summary>📦 Содержимое фикстур</summary>

| Файл | Содержимое |
|------|------------|
| `fixtures/users.json` | 2 пользователя: `admin` (superuser), `user` |
| `fixtures/documents.json` | 6 документов: 2 approved, 2 pending, 2 rejected |

</details>

### 6. Открыть приложение

| Сервис | URL |
|--------|-----|
| API Root | http://localhost/api/ |
| Swagger UI | http://localhost/api/schema/swagger-ui/ |
| ReDoc | http://localhost/api/schema/redoc/ |
| Admin | http://localhost/admin/ |
| Health Check | http://localhost/health/ |

---

## 📡 API Endpoints

### Аутентификация

```http
POST /api/users/token/          # Получить JWT токен
POST /api/users/token/refresh/  # Обновить JWT токен
```

### Документы

```http
GET    /api/documents/                    # Список документов
POST   /api/documents/                    # Загрузить документ
GET    /api/documents/{id}/               # Детали документа
PUT    /api/documents/{id}/               # Обновить документ
DELETE /api/documents/{id}/               # Удалить документ
POST   /api/documents/{id}/reprocess/     # Перезапустить обработку
DELETE /api/documents/{id}/soft_delete/   # Мягкое удаление
POST   /api/documents/{id}/restore/       # Восстановить документ
```

### Задачи обработки

```http
GET /api/documents/tasks/        # Список задач
GET /api/documents/tasks/{id}/   # Детали задачи
```

<details>
<summary>📝 Пример запроса</summary>

```bash
# Получить токен
curl -X POST http://localhost/api/users/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123"}'

# Загрузить документ
curl -X POST http://localhost/api/documents/ \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@document.pdf" \
  -F "title=My Document"
```

</details>

---

## 🧪 Тестирование

### Статистика

| Метрика | Значение |
|---------|----------|
| Тесты | 250 |
| Покрытие | 100% |
| Фреймворк | pytest-django |

### Запуск тестов

```bash
# В Docker (рекомендуется)
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test web pytest

# С verbose выводом
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test web pytest -v

# Параллельное выполнение
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test web pytest -n auto

# Локально
poetry run pytest
```

> **Важно:** В Docker используйте флаг `-e DJANGO_SETTINGS_MODULE=config.settings.test`

### Code Quality

```bash
# Ruff (линтинг)
docker compose exec web ruff check apps/

# Mypy (типизация)
docker compose exec web mypy apps config tests

# Black (форматирование)
docker compose exec web black --check apps/
```

---

## 💻 Разработка

### Два режима работы

| Режим | Конфигурация | Назначение |
|-------|--------------|------------|
| **Development** | `.env.develop` | Локальная разработка без Docker |
| **Staging** | `.env.stage` | Docker Compose с полным стеком |

### Локальная разработка

```bash
# Установить зависимости
poetry install

# Скопировать конфигурацию
cp .env.develop.example .env

# Применить миграции
poetry run python manage.py migrate

# Создать суперпользователя
poetry run python manage.py create_superuser

# Запустить сервер
poetry run python manage.py runserver 0.0.0.0:5000
```

### Management команды

| Команда | Описание |
|---------|----------|
| `create_superuser` | Создать суперпользователя (идемпотентная) |
| `load_initial_data` | Загрузить фикстуры с полным сбросом БД |

```bash
# Примеры использования
python manage.py create_superuser --username admin --password SecurePass123
python manage.py load_initial_data --dry-run
```

---

## 🛡️ Безопасность

### Аутентификация и авторизация

- ✅ JWT аутентификация с refresh токенами
- ✅ Permission classes (IsOwner, IsAuthenticated, IsModerator)
- ✅ Изоляция данных пользователей

### Валидация файлов

<details>
<summary>📁 Поддерживаемые форматы (~120 расширений)</summary>

| Категория | Примеры |
|-----------|---------|
| 📄 Документы | PDF, DOCX, TXT, RTF, ODT |
| 🖼️ Изображения | JPG, PNG, GIF, WEBP, SVG |
| 🎵 Аудио | MP3, WAV, FLAC, OGG |
| 🎬 Видео | MP4, AVI, MKV, MOV |
| 🗜️ Архивы | ZIP, RAR, 7Z, TAR.GZ |
| 📊 Данные | CSV, JSON, XML, XLSX |

</details>

<details>
<summary>🚫 Заблокированные типы (~70 расширений)</summary>

| Категория | Примеры |
|-----------|---------|
| Исполняемые | `.exe`, `.dll`, `.so`, `.bin` |
| Скрипты | `.bat`, `.cmd`, `.ps1`, `.sh`, `.vbs` |
| Макросы Office | `.docm`, `.xlsm`, `.pptm` |
| Системные | `.sys`, `.drv`, `.iso` |

</details>

### Многоуровневая валидация

1. **API (Serializer)** — ранняя проверка при загрузке
2. **FileField validators** — валидация Django
3. **Model.save()** — централизованная проверка

---

## 📚 Документация

| Документ | Описание |
|----------|----------|
| [developers.md](docs/developers.md) | Руководство разработчика |
| [docker.md](docs/docker.md) | Настройка Docker |
| [celery.md](docs/celery.md) | Настройка Celery |
| [testing.md](docs/testing.md) | Руководство по тестированию |
| [roadmap.md](docs/roadmap.md) | План развития проекта |
| [Swagger UI](http://localhost/api/schema/swagger-ui/) | Интерактивная документация API |
| [ReDoc](http://localhost/api/schema/redoc/) | Альтернативная документация API |

---

## 📄 Лицензия

MIT License

---

<div align="center">

**Python Developer Course — Дипломный проект OB3**

Made with ❤️ and Django

</div>
