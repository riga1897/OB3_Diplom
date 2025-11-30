# Тестирование

<div align="center">

![pytest](https://img.shields.io/badge/pytest-8.0+-blue?logo=pytest&logoColor=white)
![Coverage](https://img.shields.io/badge/Coverage-100%25-brightgreen)
![Tests](https://img.shields.io/badge/Tests-250-success)

**Руководство по тестированию OB3 Document Processing Service**

</div>

---

## 📋 Содержание

- [Структура тестов](#-структура-тестов)
- [Запуск тестов](#-запуск-тестов)
- [Coverage отчёты](#-coverage-отчёты)
- [Тестирование API](#-тестирование-api)
- [Фикстуры и фабрики](#-фикстуры-и-фабрики)
- [Примеры тестов](#-примеры-тестов)
- [TDD подход](#-tdd-подход)
- [Troubleshooting](#-troubleshooting)

---

## 📁 Структура тестов

```
tests/                           # Все тесты проекта (pytest-django)
├── conftest.py                 # Общие фикстуры
├── factories.py                # Factory Boy фабрики
├── test_models.py              # Unit-тесты моделей
├── test_serializers.py         # Unit-тесты сериализаторов
├── test_api_documents.py       # Integration-тесты API
├── test_api_users.py           # Integration-тесты пользователей
├── test_permissions.py         # Тесты permissions
├── test_tasks.py               # Тесты Celery tasks
├── test_services.py            # Тесты сервисного слоя
└── test_cache.py               # Тесты кэширования
```

### Маркеры pytest

| Маркер | Назначение |
|--------|------------|
| `@pytest.mark.unit` | Unit-тесты (модели, сериализаторы, сервисы) |
| `@pytest.mark.integration` | Integration-тесты (API, views) |
| `@pytest.mark.slow` | Медленные тесты (можно пропускать) |

---

## 🚀 Запуск тестов

### Docker (рекомендуется)

```bash
# Основная команда
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test web pytest

# С verbose выводом
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test web pytest -v

# Только unit-тесты
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test web pytest -m unit

# Только integration-тесты
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test web pytest -m integration

# Исключить медленные тесты
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test web pytest -m "not slow"

# Конкретный файл
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test web pytest tests/test_models.py

# Конкретный класс
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test web pytest tests/test_models.py::TestDocumentModel

# По паттерну в названии
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test web pytest -k "document"

# Параллельное выполнение
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test web pytest -n auto
```

### Локально (development)

```bash
# Все тесты
poetry run pytest

# С verbose
poetry run pytest -v

# Только unit-тесты
poetry run pytest -m unit

# Параллельное выполнение
poetry run pytest -n auto

# Переиспользование БД (быстрее)
poetry run pytest --reuse-db

# Пересоздать БД
poetry run pytest --create-db
```

---

## 📊 Coverage отчёты

### Автоматическое покрытие

Coverage настроен в `pytest.ini` и запускается автоматически:

```ini
addopts =
    --cov=apps
    --cov-report=term-missing
    --cov-report=html:var/coverage/htmlcov
    --cov-report=xml:var/coverage/coverage.xml
    --cov-fail-under=95
```

### Пути отчётов

| Тип | Путь | Назначение |
|-----|------|------------|
| HTML | `var/coverage/htmlcov/index.html` | Визуальный отчёт |
| XML | `var/coverage/coverage.xml` | CI/CD интеграция |
| Terminal | stdout | Быстрый просмотр |

### Просмотр HTML-отчёта

```bash
# macOS
open var/coverage/htmlcov/index.html

# Linux
xdg-open var/coverage/htmlcov/index.html

# Windows
start var/coverage/htmlcov/index.html
```

### Требования к покрытию

| Модуль | Цель |
|--------|------|
| `apps/documents/models.py` | ≥90% |
| `apps/documents/serializers.py` | ≥90% |
| `apps/documents/views.py` | ≥85% |
| `apps/documents/services.py` | ≥95% |
| `apps/documents/tasks.py` | ≥90% |
| `apps/users/permissions.py` | 100% |

---

## 🔌 Тестирование API

### Получение JWT токена

```bash
curl -X POST http://0.0.0.0:5000/api/users/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'
```

**Ответ:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Загрузка документа

```bash
curl -X POST http://0.0.0.0:5000/api/documents/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/path/to/document.pdf"
```

**Ответ (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "file": "http://0.0.0.0:5000/media/documents/2025/11/26/document.pdf",
  "original_filename": "document.pdf",
  "file_type": "pdf",
  "status": "pending",
  "created_at": "2025-11-26T10:30:00Z"
}
```

### Список документов

```bash
curl -X GET http://0.0.0.0:5000/api/documents/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Фильтрация и поиск

```bash
# По статусу
curl "http://0.0.0.0:5000/api/documents/?status=pending" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# По типу файла
curl "http://0.0.0.0:5000/api/documents/?file_type=pdf" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Поиск по имени
curl "http://0.0.0.0:5000/api/documents/?search=contract" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Сортировка
curl "http://0.0.0.0:5000/api/documents/?ordering=-created_at" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### HTTPie (альтернатива curl)

```bash
# Установка
pip install httpie

# Получение токена
http POST http://0.0.0.0:5000/api/users/token/ \
  username=testuser \
  password=testpass123

# Загрузка документа
http -f POST http://0.0.0.0:5000/api/documents/ \
  Authorization:"Bearer YOUR_ACCESS_TOKEN" \
  file@/path/to/document.pdf
```

### Swagger UI

| URL | Описание |
|-----|----------|
| `/api/schema/swagger-ui/` | Swagger UI |
| `/api/schema/redoc/` | ReDoc |
| `/api/schema/` | OpenAPI Schema |

**Авторизация в Swagger:**
1. Нажмите **Authorize**
2. Введите: `Bearer YOUR_ACCESS_TOKEN`
3. Нажмите **Authorize**

---

## 🏭 Фикстуры и фабрики

### Основные фикстуры (conftest.py)

```python
import pytest
from rest_framework.test import APIClient

@pytest.fixture
def api_client():
    """DRF API Client."""
    return APIClient()

@pytest.fixture
def user(db, django_user_model):
    """Создание тестового пользователя."""
    return django_user_model.objects.create_user(
        email="test@example.com",
        password="testpass123"
    )

@pytest.fixture
def authenticated_client(api_client, user):
    """Авторизованный API клиент."""
    api_client.force_authenticate(user=user)
    return api_client
```

### Factory Boy фабрики

```python
import factory
from apps.documents.models import Document
from apps.users.models import User

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    
    email = factory.Faker("email")
    username = factory.Faker("user_name")

class DocumentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Document
    
    owner = factory.SubFactory(UserFactory)
    original_filename = factory.Faker("file_name", extension="pdf")
    file_type = Document.FileType.PDF
```

---

## 📝 Примеры тестов

### Unit-тест модели

```python
import pytest
from apps.documents.models import Document
from tests.factories import DocumentFactory

@pytest.mark.unit
class TestDocumentModel:
    def test_create_document(self, db, user):
        """Тест создания документа."""
        doc = DocumentFactory(
            owner=user,
            original_filename="test.pdf",
            file_type=Document.FileType.PDF
        )
        assert doc.owner == user
        assert doc.original_filename == "test.pdf"
        assert doc.status == Document.Status.PENDING
```

### Integration-тест API

```python
import pytest
from django.urls import reverse
from rest_framework import status

@pytest.mark.integration
class TestDocumentAPI:
    def test_list_documents(self, authenticated_client, document):
        """Тест получения списка документов."""
        url = reverse("document-list")
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

    def test_create_document_unauthorized(self, api_client):
        """Тест создания без авторизации."""
        url = reverse("document-list")
        response = api_client.post(url, {})
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
```

### Тест валидации файлов

```python
import pytest
from django.core.exceptions import ValidationError
from apps.documents.models import Document

@pytest.mark.unit
class TestFileValidation:
    def test_block_dangerous_extension(self, db, user):
        """Блокировка опасного расширения."""
        doc = Document(
            owner=user,
            original_filename="malware.exe",
            file_type=Document.FileType.OTHER,
        )
        with pytest.raises(ValidationError) as exc_info:
            doc.save()
        
        assert "exe" in str(exc_info.value).lower()
```

### Тест Celery task

```python
import pytest
from apps.documents.tasks import send_admin_notification_task

@pytest.mark.unit
class TestCeleryTasks:
    def test_send_admin_notification(self, db, document):
        """Тест отправки уведомления администратору."""
        result = send_admin_notification_task.apply(
            args=[str(document.id)]
        ).get()
        
        assert result["status"] == "sent"
        assert result["document_id"] == str(document.id)
```

---

## 🔄 TDD подход

### Red-Green-Refactor

1. **Red** — напишите провальный тест
2. **Green** — напишите минимальный код для прохождения
3. **Refactor** — улучшите код, тесты остаются зелёными

### Автоперезапуск тестов

```bash
# pytest-watch
poetry run ptw -- --reuse-db -m unit

# entr (Linux/macOS)
find tests apps -name '*.py' | entr poetry run pytest --reuse-db -m unit
```

---

## 🔍 Troubleshooting

<details>
<summary><b>Тесты медленные</b></summary>

```bash
# Используйте --reuse-db
poetry run pytest --reuse-db

# Параллельное выполнение
poetry run pytest -n auto --reuse-db

# Пропустите медленные тесты
poetry run pytest -m "not slow"
```

</details>

<details>
<summary><b>Тесты падают из-за БД</b></summary>

```bash
# Пересоздайте БД
poetry run pytest --create-db

# Очистите кэш pytest
poetry run pytest --cache-clear
```

</details>

<details>
<summary><b>Coverage не сохраняется в Docker</b></summary>

```bash
# Проверьте что директория существует
mkdir -p var/coverage

# Проверьте права
ls -la var/coverage/

# Запустите тесты
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test web pytest
```

</details>

<details>
<summary><b>Тесты файлов не удаляются</b></summary>

Тестовые файлы изолированы в `var/media/tests/` и автоматически удаляются через pytest fixture `clean_test_media_files`.

```python
@pytest.fixture(autouse=True)
def clean_test_media_files():
    """Автоочистка тестовых файлов."""
    yield
    test_media = Path(settings.MEDIA_ROOT) / "tests"
    if test_media.exists():
        shutil.rmtree(test_media)
```

</details>

---

## 📋 Коды ответов API

| Код | Описание |
|-----|----------|
| 200 | Успешный запрос |
| 201 | Документ создан |
| 204 | Документ удалён |
| 400 | Ошибка валидации |
| 401 | Требуется авторизация |
| 403 | Доступ запрещён |
| 404 | Документ не найден |
| 429 | Превышен лимит запросов |

---

## ✅ Полная проверка перед коммитом

### Docker

```bash
# 1. Тесты с coverage
docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test web pytest

# 2. Code quality
docker compose exec web ruff check apps/
docker compose exec web mypy apps config tests
docker compose exec web black --check apps/
```

### Локально

```bash
# 1. Форматирование
poetry run ruff check --fix apps/
poetry run black apps/

# 2. Проверка типов
poetry run mypy apps config tests
poetry run ruff check apps/

# 3. Тесты
poetry run pytest
```

---

<div align="center">

**Последнее обновление:** 28 ноября 2025

</div>
