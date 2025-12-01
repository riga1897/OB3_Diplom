# Настройка и запуск Celery

**Последнее обновление:** 27 ноября 2025

Это руководство описывает настройку и запуск Celery для асинхронных задач в OB3 Document Processing Service.

## Обзор Celery интеграции

Проект использует Celery для асинхронной обработки документов:

1. **Уведомления**: Отправка email администраторам и пользователям
2. **Очистка**: Удаление старых мягко-удалённых документов
3. **Статистика**: Генерация отчётов по документам

### Архитектура

- **config/celery.py**: Конфигурация Celery приложения
- **apps/documents/tasks.py**: Celery-задачи для документов

---

## Два режима работы

### Development (без Redis)

В локальной разработке Celery работает **синхронно**:

```env
# .env.develop
CELERY_TASK_ALWAYS_EAGER=True
CACHE_BACKEND=locmem
```

Задачи выполняются сразу в том же процессе, Redis не требуется.

### Staging/Docker (с Redis)

В Docker окружении Celery работает **асинхронно**:

```env
# .env.stage
CELERY_TASK_ALWAYS_EAGER=False
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
CACHE_BACKEND=redis
```

---

## Зависимости

Celery требует:
- **Redis**: Message broker для Celery
- **celery[redis]**: Python библиотека

Все зависимости установлены через Poetry.

---

## Запуск Celery

### Docker (рекомендуется)

Celery запускается автоматически через Docker Compose:

```bash
# Запустить все сервисы
docker compose up -d

# Проверить статус
docker compose ps

# Логи worker
docker compose logs -f celery_worker

# Логи beat
docker compose logs -f celery_beat
```

### Локальная разработка (с Redis)

Требуется **4 отдельных терминала**:

#### Терминал 1: Redis

```bash
# Вариант 1: Локальный redis-server
redis-server

# Вариант 2: Docker
docker run -p 6379:6379 redis:alpine
```

#### Терминал 2: Celery Worker

```bash
# Windows (обязательно --pool=solo)
poetry run celery -A config worker --pool=solo -l info

# Linux/macOS
poetry run celery -A config worker -l info
```

#### Терминал 3: Celery Beat

```bash
poetry run celery -A config beat -l info
```

#### Терминал 4: Django Server

```bash
poetry run python manage.py runserver 0.0.0.0:8000
```

### Локальная разработка (без Redis)

Если Redis недоступен, используйте eager mode:

```env
# .env
CELERY_TASK_ALWAYS_EAGER=True
```

Задачи будут выполняться синхронно без Celery worker.

---

## Конфигурация

### Основные настройки (config/celery.py)

```python
from celery import Celery

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

### Настройки в settings

```python
# Celery Configuration
CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Europe/Moscow"
CELERY_TASK_ALWAYS_EAGER = config("CELERY_TASK_ALWAYS_EAGER", default=False, cast=bool)

# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    "cleanup_old_documents_daily": {
        "task": "apps.documents.tasks.cleanup_old_documents",
        "schedule": crontab(hour=3, minute=0),  # Каждый день в 3:00
    },
    "generate_statistics_weekly": {
        "task": "apps.documents.tasks.generate_statistics_report",
        "schedule": crontab(hour=0, minute=0, day_of_week=1),  # Понедельник в 00:00
    },
}
```

---

## Асинхронные задачи

### 1. Уведомление администратору

**Задача**: `apps.documents.tasks.send_admin_notification_task`

**Триггер**: При загрузке нового документа

**Логика**:
- Получает документ по ID
- Находит всех активных администраторов
- Отправляет email с информацией о документе

**Использование**:
```python
from apps.documents.tasks import send_admin_notification_task

# Асинхронный вызов
send_admin_notification_task.delay(document_id=str(document.id))
```

### 2. Уведомление пользователю

**Задача**: `apps.documents.tasks.send_user_notification_task`

**Триггер**: При изменении статуса документа (approved/rejected)

**Логика**:
- Получает документ по ID
- Формирует сообщение в зависимости от действия
- Отправляет email владельцу документа

**Использование**:
```python
from apps.documents.tasks import send_user_notification_task

# При подтверждении документа
send_user_notification_task.delay(document_id=str(document.id), action="approved")

# При отклонении документа
send_user_notification_task.delay(document_id=str(document.id), action="rejected")
```

### 3. Очистка старых документов

**Задача**: `apps.documents.tasks.cleanup_old_documents`

**Триггер**: Автоматически каждый день в 3:00 через Celery Beat

**Логика**:
- Находит документы с `is_deleted=True` и `deleted_at` старше 30 дней
- Удаляет файлы и записи из БД
- Логирует статистику очистки

**Ручной запуск**:
```python
from apps.documents.tasks import cleanup_old_documents

result = cleanup_old_documents.delay()
# Или синхронно
result = cleanup_old_documents()
```

### 4. Генерация статистики

**Задача**: `apps.documents.tasks.generate_statistics_report`

**Триггер**: Автоматически каждый понедельник в 00:00 через Celery Beat

**Логика**:
- Собирает агрегированную статистику по документам
- Подсчитывает количество по статусам
- Вычисляет общий размер файлов

**Ручной запуск**:
```python
from apps.documents.tasks import generate_statistics_report

stats = generate_statistics_report()
print(stats)
# {'total_documents': 100, 'pending': 10, 'approved': 80, 'rejected': 10, 'total_size': 1024000}
```

---

## Мониторинг

### Celery Worker логи

```bash
# Docker
docker compose logs -f celery_worker

# Локально (вывод в терминале worker)
```

Пример вывода:
```
[INFO/MainProcess] Task apps.documents.tasks.send_admin_notification_task[abc-123] received
[INFO/MainProcess] Task apps.documents.tasks.send_admin_notification_task[abc-123] succeeded in 1.5s
```

### Celery Beat логи

```bash
# Docker
docker compose logs -f celery_beat
```

Пример вывода:
```
[INFO/Beat] Scheduler: Sending due task cleanup_old_documents_daily
```

### Проверка статуса worker

```bash
# Docker
docker compose exec celery_worker celery -A config inspect active

# Локально
poetry run celery -A config inspect active
```

### Список зарегистрированных задач

```bash
# Docker
docker compose exec celery_worker celery -A config inspect registered

# Локально
poetry run celery -A config inspect registered
```

---

## Troubleshooting

### Windows: DatabaseWrapper error

**Ошибка**: `DatabaseWrapper objects created in a thread can only be used in that same thread`

**Решение**: Используйте `--pool=solo`:
```bash
celery -A config worker --pool=solo -l info
```

### Redis connection refused

**Проблема**: Redis недоступен

**Решение**:
- Запустите Redis: `redis-server` или `docker run -p 6379:6379 redis:alpine`
- Проверьте порт: `redis-cli ping` должен вернуть `PONG`
- Или используйте eager mode: `CELERY_TASK_ALWAYS_EAGER=True`

### Задачи не выполняются

**Проблема**: Celery worker не запущен

**Решение**:
```bash
# Проверьте что worker запущен
docker compose ps celery_worker

# Проверьте логи
docker compose logs celery_worker

# Перезапустите worker
docker compose restart celery_worker
```

### Email не отправляются

**Проблема**: Проверьте EMAIL_BACKEND

**Решение**:
```python
# Development (вывод в консоль)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Production (SMTP)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
```

---

## Docker архитектура

### celery_worker сервис

```yaml
celery_worker:
  build:
    context: .
    dockerfile: Dockerfile
  command: worker
  depends_on:
    web:
      condition: service_healthy
  environment:
    - CELERY_BROKER_URL=redis://redis:6379/0
    - CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### celery_beat сервис

```yaml
celery_beat:
  build:
    context: .
    dockerfile: Dockerfile
  command: beat
  depends_on:
    web:
      condition: service_healthy
```

### Entrypoint

```bash
# Worker mode
celery -A config worker --loglevel=info --pool=solo --concurrency=2

# Beat mode
celery -A config beat --loglevel=info
```

---

## Дополнительные ресурсы

- [Celery Documentation](https://docs.celeryq.dev/)
- [Redis Documentation](https://redis.io/docs/)

---

**Создано:** 27 ноября 2025  
**Версия проекта:** Django 5.2.7, Celery 5.5.3, Python 3.12
