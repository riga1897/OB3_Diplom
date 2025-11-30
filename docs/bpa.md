<!--
НАЗНАЧЕНИЕ ФАЙЛА: Лучшие практики и архитектурное руководство для OB3
АУДИТОРИЯ: Разработчики OB3 (только этот проект)
ЖИЗНЕННЫЙ ЦИКЛ: Постоянный (сохраняется после завершения разработки)
ОБСЛУЖИВАНИЕ: Обновляется при изменении архитектуры/паттернов

Лучшие практики для OB3 Document Processing Service.
Включает настройку Docker, стратегию тестирования, руководства по развёртыванию.
Без ссылок на временные файлы разработки или Replit.
-->

# Анализ лучших практик (BPA)
## Дипломный проект: Сервис обработки загружаемых документов (OB3)

**Студент:** Python Developer Course  
**Дата:** 20 ноября 2025  
**Направление:** Backend Development  

---

## 1. Обзор проекта

### 1.1 Цель проекта
Разработать бэкенд-сервис для автоматической обработки, классификации и валидации загружаемых документов различных форматов (PDF, DOCX, TXT, изображения).

### 1.2 Бизнес-ценность
- Обработка документов в **10 раз быстрее** ручного метода
- **99% точности** классификации
- Снижение операционных затрат на обработку документов

### 1.3 Технический стек
- **Backend Framework:** Django REST Framework (DRF)
- **База данных:** PostgreSQL
- **Контейнеризация:** Docker, Docker-Compose
- **API Documentation:** OpenAPI (Swagger)
- **Аутентификация:** JWT (JSON Web Tokens)
- **CORS:** Настройка кросс-доменных запросов
- **Testing:** pytest, coverage ≥ 75%

---

## 2. Архитектура и Best Practices

### 2.1 Django REST Framework Best Practices

#### 2.1.1 Структура проекта
```
document_service/
├── apps/
│   ├── documents/          # Основное приложение
│   │   ├── models.py       # Модели данных
│   │   ├── serializers.py  # Сериализаторы DRF
│   │   ├── views.py        # ViewSets и APIViews
│   │   ├── permissions.py  # Кастомные permissions
│   │   └── tests/          # Тесты приложения
│   └── users/              # Управление пользователями
├── config/                 # Конфигурация проекта
│   ├── settings/
│   │   ├── base.py        # Базовые настройки
│   │   ├── development.py # Development
│   │   └── production.py  # Production
│   ├── urls.py
│   └── wsgi.py
├── utils/                  # Утилиты
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── docker-compose.yml
├── Dockerfile
└── README.md
```

#### 2.1.2 Модели и ORM
**Best Practices:**
- Использовать `django.db.models` для определения моделей
- Добавлять `created_at` и `updated_at` поля через `auto_now_add` и `auto_now`
- Использовать `choices` для статусов и категорий
- Индексировать часто запрашиваемые поля

```python
from django.db import models
from django.contrib.auth.models import User

class Document(models.Model):
    """Модель загруженного документа"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает обработки'
        PROCESSING = 'processing', 'Обрабатывается'
        COMPLETED = 'completed', 'Обработан'
        FAILED = 'failed', 'Ошибка обработки'
    
    class FileType(models.TextChoices):
        PDF = 'pdf', 'PDF'
        DOCX = 'docx', 'Word Document'
        TXT = 'txt', 'Text File'
        IMAGE = 'image', 'Image'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='documents/%Y/%m/%d/')
    file_type = models.CharField(max_length=10, choices=FileType.choices)
    file_size = models.PositiveIntegerField(help_text="Size in bytes")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    
    # Метаданные
    original_filename = models.CharField(max_length=255)
    extracted_text = models.TextField(blank=True)
    classification = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['file_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.original_filename} ({self.status})"
```

#### 2.1.3 Serializers
**Best Practices:**
- Использовать `ModelSerializer` для базовой функциональности
- Валидировать данные на уровне сериализатора
- Использовать `read_only_fields` для полей, которые не должны изменяться
- Создавать отдельные сериализаторы для чтения и записи

```python
from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения документов"""
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'owner', 'owner_username', 'file', 'file_url',
            'file_type', 'file_size', 'status', 'original_filename',
            'extracted_text', 'classification', 'created_at', 
            'updated_at', 'processed_at'
        ]
        read_only_fields = ['id', 'owner', 'status', 'created_at', 'updated_at', 'processed_at']
    
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None

class DocumentCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания документов"""
    
    class Meta:
        model = Document
        fields = ['file', 'file_type']
    
    def validate_file(self, value):
        """Валидация размера файла"""
        max_size = 10 * 1024 * 1024  # 10 MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"Размер файла не должен превышать {max_size / 1024 / 1024} MB"
            )
        return value
    
    def validate(self, attrs):
        """Валидация соответствия типа файла"""
        file = attrs.get('file')
        file_type = attrs.get('file_type')
        
        type_extensions = {
            'pdf': ['.pdf'],
            'docx': ['.docx', '.doc'],
            'txt': ['.txt'],
            'image': ['.jpg', '.jpeg', '.png', '.gif']
        }
        
        if file:
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in type_extensions.get(file_type, []):
                raise serializers.ValidationError({
                    'file': f"Неверное расширение файла для типа {file_type}"
                })
        
        return attrs
```

#### 2.1.4 Views и ViewSets
**Best Practices:**
- Использовать `ViewSets` для стандартных CRUD операций
- Использовать `APIView` для кастомной логики
- Применять `permissions` и `authentication`
- Использовать `pagination` для списков

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Document
from .serializers import DocumentSerializer, DocumentCreateSerializer
from .tasks import process_document  # Celery task

class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления документами
    
    list: Получить список документов пользователя
    create: Загрузить новый документ
    retrieve: Получить информацию о документе
    update: Обновить документ (частично)
    destroy: Удалить документ
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Пользователи видят только свои документы"""
        return Document.objects.filter(owner=self.request.user)
    
    def get_serializer_class(self):
        """Разные сериализаторы для разных действий"""
        if self.action == 'create':
            return DocumentCreateSerializer
        return DocumentSerializer
    
    def perform_create(self, serializer):
        """Автоматически привязываем документ к пользователю"""
        document = serializer.save(
            owner=self.request.user,
            original_filename=self.request.FILES['file'].name
        )
        # Асинхронная обработка документа
        process_document.delay(document.id)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Получить статистику по документам пользователя"""
        queryset = self.get_queryset()
        stats = {
            'total': queryset.count(),
            'by_status': {
                status[0]: queryset.filter(status=status[0]).count()
                for status in Document.Status.choices
            },
            'by_type': {
                file_type[0]: queryset.filter(file_type=file_type[0]).count()
                for file_type in Document.FileType.choices
            }
        }
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def reprocess(self, request, pk=None):
        """Повторная обработка документа"""
        document = self.get_object()
        if document.status in [Document.Status.COMPLETED, Document.Status.FAILED]:
            document.status = Document.Status.PENDING
            document.save()
            process_document.delay(document.id)
            return Response({'status': 'Document queued for reprocessing'})
        return Response(
            {'error': 'Document is already being processed'},
            status=status.HTTP_400_BAD_REQUEST
        )
```

---

### 2.2 Аутентификация и безопасность

#### 2.2.1 JWT Authentication
**Best Practices:**
- Использовать `djangorestframework-simplejwt` для JWT
- Настроить время жизни токенов
- Использовать refresh tokens

```python
# settings.py
from datetime import timedelta

INSTALLED_APPS = [
    ...
    'rest_framework',
    'rest_framework_simplejwt',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

```python
# urls.py
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
```

#### 2.2.2 Permissions
**Best Practices:**
- Создавать кастомные permissions для сложной логики
- Использовать `IsAuthenticated`, `IsAdminUser` для базовой защиты

```python
from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Кастомный permission: владелец может редактировать,
    остальные - только читать
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions для всех
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions только для владельца
        return obj.owner == request.user
```

---

### 2.3 CORS Configuration

**Best Practices:**
- Использовать `django-cors-headers` для настройки CORS
- Настраивать CORS в зависимости от окружения (development/production)
- Разрешать только необходимые origins

```python
# settings.py
INSTALLED_APPS = [
    'corsheaders',
    ...
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Должен быть первым
    'django.middleware.common.CommonMiddleware',
    ...
]

# Development
if DEBUG:
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:5173",  # Vite dev server
    ]
else:
    # Production
    CORS_ALLOWED_ORIGINS = [
        "https://yourdomain.com",
        "https://www.yourdomain.com",
    ]

# Разрешить credentials (cookies, JWT в headers)
CORS_ALLOW_CREDENTIALS = True

# Разрешенные заголовки
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
```

**Важно:** CORS и JWT работают вместе:
- CORS разрешает браузеру делать запросы с фронтенда к API
- JWT токен передается в заголовке `Authorization: Bearer <token>`
- CORS проверяет origin запроса, JWT проверяет личность пользователя

---

### 2.4 API Documentation (OpenAPI/Swagger)

**Best Practices:**
- Использовать `drf-spectacular` для генерации OpenAPI схемы
- Документировать все endpoints
- Добавлять примеры запросов/ответов

```python
# settings.py
INSTALLED_APPS = [
    ...
    'drf_spectacular',
]

REST_FRAMEWORK = {
    ...
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Document Processing Service API',
    'DESCRIPTION': 'API для обработки и управления документами',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}

# urls.py
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
```

---

### 2.5 Database Best Practices

#### 2.5.1 PostgreSQL Configuration
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'document_service'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,  # Connection pooling
    }
}
```

#### 2.5.2 Миграции
**Best Practices:**
- Создавать миграции после каждого изменения моделей
- Проверять сгенерированные миграции перед применением
- Использовать `squashmigrations` для оптимизации

```bash
# Создать миграции
python manage.py makemigrations

# Проверить SQL миграций
python manage.py sqlmigrate documents 0001

# Применить миграции
python manage.py migrate

# Откатить миграцию
python manage.py migrate documents 0001
```

---

### 2.6 Testing Best Practices

> **ВАЖНО (28.11.2025):** OB3 использует **pytest-django 100%** для всего тестирования. Примеры ниже показывают старый подход (Django TestCase/APITestCase) из других проектов. Для актуальных примеров см. `tests/` и `docs/testing.md`.

#### 2.6.1 Структура тестов (старый подход - для справки)
```python
# documents/tests/test_models.py
from django.test import TestCase
from django.contrib.auth.models import User
from ..models import Document

class DocumentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_document_creation(self):
        """Тест создания документа"""
        document = Document.objects.create(
            owner=self.user,
            original_filename='test.pdf',
            file_type=Document.FileType.PDF,
            file_size=1024
        )
        self.assertEqual(document.status, Document.Status.PENDING)
        self.assertEqual(str(document), 'test.pdf (pending)')

# documents/tests/test_api.py
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from ..models import Document

class DocumentAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_list_documents(self):
        """Тест получения списка документов"""
        Document.objects.create(
            owner=self.user,
            original_filename='test.pdf',
            file_type=Document.FileType.PDF,
            file_size=1024
        )
        
        response = self.client.get('/api/documents/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_document_unauthenticated(self):
        """Тест создания документа без аутентификации"""
        self.client.force_authenticate(user=None)
        response = self.client.post('/api/documents/', {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
```

#### 2.6.2 Покрытие тестами
```bash
# Установить coverage
pip install coverage

# Запустить тесты с coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Генерация HTML отчета

# Цель: покрытие >= 75%
```

---

### 2.7 Docker и Development Environment

#### 2.7.1 Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Установка Python зависимостей
COPY requirements/base.txt requirements/prod.txt ./requirements/
RUN pip install --no-cache-dir -r requirements/prod.txt

# Копирование кода приложения
COPY . .

# Создание пользователя для запуска приложения
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Команда запуска
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

#### 2.7.2 docker-compose.yml
```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: document_service
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
      - media_volume:/app/media
    ports:
      - "8000:8000"
    environment:
      - DEBUG=1
      - DB_HOST=db
      - DB_NAME=document_service
      - DB_USER=postgres
      - DB_PASSWORD=postgres
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
  
  celery:
    build: .
    command: celery -A config worker --loglevel=info
    volumes:
      - .:/app
    environment:
      - DB_HOST=db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
  media_volume:
```

---

### 2.8 Code Quality и PEP8

**Best Practices:**
- Использовать `black` для форматирования
- Использовать `flake8` для линтинга
- Использовать `isort` для сортировки импортов
- Использовать `mypy` для type checking

```bash
# .flake8
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = migrations, __pycache__, venv

# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.venv
  | migrations
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88

# Запуск проверок
black .
isort .
flake8
mypy .
```

---

### 2.9 Docker Infrastructure & Testing Strategy

#### 2.9.1 Production Parity: PostgreSQL для тестов

**Архитектурное решение:** Использование PostgreSQL вместо SQLite для тестов.

**Обоснование:**
- ✅ **Production parity**: Избегаем SQL dialect проблем (SQLite vs PostgreSQL)
- ✅ **Реальные constraints**: ArrayField, JSONB, CHECK constraints работают идентично
- ✅ **Full-text search**: Поддержка PostgreSQL специфичных возможностей
- ✅ **Concurrent tests**: PostgreSQL лучше обрабатывает параллельные тесты

**Конфигурация:**
```python
# backend/config/settings/test.py
import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'ob3_test'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
        'HOST': os.getenv('DB_HOST', 'postgres'),  # Docker service name
        'PORT': os.getenv('DB_PORT', '5432'),
        'TEST': {
            'NAME': 'test_ob3_db',  # Отдельная БД для тестов
        },
    }
}

# Оптимизация для тестов
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
CELERY_TASK_ALWAYS_EAGER = True  # Sync execution
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

**Почему НЕ SQLite для тестов:**
- ❌ Отсутствие ArrayField → ложные положительные тесты
- ❌ Нет JSONB → не тестируются JSON операции  
- ❌ Ограниченная поддержка CHECK constraints
- ❌ Разные SQL команды (CREATE INDEX, ALTER TABLE)

---

#### 2.9.2 Docker Volume Strategy: /app/var структура

**Проблема:** Артефакты сборки (media, logs, coverage) должны быть доступны на хост-машине для инспекции.

**Решение:** Централизованная структура `/app/var/` с volume mounts.

**Структура:**
```
/app/var/
├── media/          # Загруженные файлы (MEDIA_ROOT)
├── logs/           # Application logs
└── coverage/       # Coverage reports (HTML/XML)
    └── htmlcov/    # HTML coverage report
```

**Первоначальная настройка:**
```bash
# После git clone создайте структуру (если .gitkeep файлы отсутствуют):
mkdir -p var/media var/logs var/coverage

# Структура уже присутствует в репозитории через .gitkeep файлы
# для совместимости с Docker bind mounts
```

**Docker Compose конфигурация:**
```yaml
services:
  web:
    volumes:
      - ./var/media:/app/var/media
      - ./var/logs:/app/var/logs
      - ./var/coverage:/app/var/coverage
  
  celery_worker:
    volumes:
      - ./var/media:/app/var/media
      - ./var/logs:/app/var/logs
      - ./var/coverage:/app/var/coverage
  
  celery_beat:
    volumes:
      - ./var/media:/app/var/media
      - ./var/logs:/app/var/logs
      - ./var/coverage:/app/var/coverage
  
  test:
    volumes:
      - ./var/media:/app/var/media
      - ./var/logs:/app/var/logs
      - ./var/coverage:/app/var/coverage
    env_file:
      - .env  # DB credentials для PostgreSQL тестов
```

**Важно:** Все сервисы (web, celery_worker, celery_beat, test) монтируют все три директории для консистентности.

**Преимущества:**
- ✅ Артефакты доступны на хосте без `docker cp`
- ✅ Coverage reports открываются в браузере (`var/coverage/htmlcov/index.html`)
- ✅ Логи персистентны между перезапусками контейнера
- ✅ Media файлы сохраняются при пересборке образа
- ✅ `.gitkeep` файлы сохраняют структуру в Git (игнорируется содержимое)

---

#### 2.9.3 Cross-Platform Compatibility: Non-Root User

**Проблема:** Файлы, созданные Docker (root), недоступны для редактирования на Windows/macOS.

**Решение:** Non-root пользователь с UID 1000 (стандартный UID пользователя на Linux/macOS/Windows).

**Dockerfile:**
```dockerfile
FROM python:3.12-slim

# Создаём пользователя ob3 с фиксированным UID 1000
RUN groupadd -g 1000 ob3 && \
    useradd -u 1000 -g ob3 -m -s /bin/bash ob3

WORKDIR /app

# Копируем зависимости (как root для установки)
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-interaction --no-ansi

# Создаём структуру /app/var с правами ob3
RUN mkdir -p /app/var/media /app/var/logs /app/var/coverage && \
    chown -R ob3:ob3 /app/var

# Копируем код и переключаемся на ob3
COPY --chown=ob3:ob3 . .

# Все команды выполняются от имени ob3
USER ob3

CMD ["poetry", "run", "python", "backend/manage.py", "runserver", "0.0.0.0:8000"]
```

**Почему UID 1000:**
- ✅ **Linux**: Первый пользователь обычно имеет UID 1000
- ✅ **macOS**: Стандартный UID для пользователей
- ✅ **Windows (WSL)**: Default user в WSL имеет UID 1000
- ✅ **Docker Desktop**: Автоматический mapping на текущего пользователя

**Последствия:**
```bash
# На хосте (после docker-compose up):
ls -l var/media/
# -rw-r--r-- 1 youruser yourgroup 1234 Nov 20 10:00 document.pdf
# ✅ Файлы принадлежат вам, не root!

# Редактирование логов:
nano var/logs/django.log  # ✅ Работает без sudo
```

---

#### 2.9.4 Windows Compatibility Checklist

**PostgreSQL:**
- ✅ Native Windows installer (не требуется WSL)
- ✅ Работает через `localhost:5432` или Docker service `postgres`

**Redis:**
- ⚠️ Официальная поддержка отсутствует
- ✅ **Решение 1**: WSL2 + Redis в Linux
- ✅ **Решение 2**: Docker Compose (рекомендуется)
- ⚠️ **Решение 3**: Memurai (платная альтернатива)

**Celery:**
```bash
# Windows требует --pool=solo (не поддерживается prefork)
# docker-compose.yml:
celery_worker:
  command: poetry run celery -A backend.config worker --pool=solo --loglevel=info
```

**Docker Desktop:**
- ✅ Volume mounts работают автоматически
- ✅ UID 1000 маппится на Windows user
- ⚠️ Файловая система медленнее (используйте WSL2 backend)

**Тестирование на Windows:**
```bash
# Локально (без Docker):
$env:DB_HOST="localhost"  # PowerShell
poetry run pytest

# Через Docker Compose (рекомендуется):
docker-compose run --rm test
```

---

#### 2.9.5 Testing Strategy: Coverage & Artifacts

**pytest.ini:**
```ini
[pytest]
DJANGO_SETTINGS_MODULE = backend.config.settings.test
pythonpath = .
testpaths = backend/tests
addopts = 
    -v
    --strict-markers
    --cov=backend.apps
    --cov-report=term-missing
    --cov-report=html:/app/var/coverage/htmlcov
    --cov-report=xml:/app/var/coverage/coverage.xml
    --cov-fail-under=75
markers =
    unit: Unit tests
    integration: Integration tests
```

**Запуск тестов:**
```bash
# Через Docker (рекомендуется)
docker-compose run --rm test

# Coverage report доступен в:
# var/coverage/htmlcov/index.html

# CI/CD интеграция (XML для SonarQube/Codecov):
# var/coverage/coverage.xml
```

**Factory Boy для тестовых данных:**
```python
# backend/tests/factories.py
import factory
from apps.users.models import User
from apps.documents.models import Document

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    
    email = factory.Faker('email')
    username = factory.Faker('user_name')

class DocumentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Document
    
    owner = factory.SubFactory(UserFactory)
    file = factory.django.FileField(filename='test.pdf')
    file_type = Document.FileType.PDF
```

**Преимущества PostgreSQL для тестов:**
```python
# Тесты для ArrayField (не работает в SQLite)
def test_document_tags():
    doc = DocumentFactory(tags=['invoice', 'accounting'])
    assert 'invoice' in doc.tags  # ✅ Работает с PostgreSQL

# Тесты для JSONB
def test_document_metadata():
    doc = DocumentFactory(metadata={'author': 'John Doe'})
    assert doc.metadata['author'] == 'John Doe'  # ✅ JSONB в PostgreSQL
```

---

## 3. Этапы реализации проекта

### Этап 1: Настройка окружения и базовая конфигурация
- ✅ Создание Django проекта
- ✅ Настройка PostgreSQL
- ✅ Конфигурация Docker
- ✅ Настройка DRF
- ✅ Настройка JWT аутентификации

### Этап 2: Модели и миграции
- ✅ Создание моделей Document, User
- ✅ Создание и применение миграций
- ✅ Настройка индексов

### Этап 3: API и бизнес-логика
- ✅ Сериализаторы для документов
- ✅ ViewSets для CRUD операций
- ✅ Permissions и валидация
- ✅ Обработка файлов

### Этап 4: Обработка документов
- ✅ Извлечение метаданных
- ✅ Классификация документов
- ✅ Индексация содержимого
- ✅ Асинхронная обработка (Celery)

### Этап 5: Безопасность и CORS
- ✅ Настройка CORS
- ✅ JWT токены
- ✅ Rate limiting
- ✅ Валидация файлов

### Этап 6: Документация
- ✅ OpenAPI схема
- ✅ Swagger UI
- ✅ README.md
- ✅ API примеры

### Этап 7: Тестирование
- ✅ Unit tests
- ✅ Integration tests
- ✅ API tests
- ✅ Coverage >= 75%

### Этап 8: Деплой
- ✅ Production настройки
- ✅ Gunicorn
- ✅ Nginx (опционально)
- ✅ CI/CD (опционально)

---

## 4. Полезные команды

### Django
```bash
# Создать проект
django-admin startproject config .

# Создать приложение
python manage.py startapp documents

# Миграции
python manage.py makemigrations
python manage.py migrate

# Создать суперпользователя
python manage.py createsuperuser

# Запуск сервера
python manage.py runserver

# Запуск тестов
python manage.py test

# Сбор статики
python manage.py collectstatic
```

### Docker
```bash
# Сборка и запуск
docker-compose up --build

# Остановка
docker-compose down

# Просмотр логов
docker-compose logs -f web

# Выполнение команд в контейнере
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py test
```

---

## 5. Контрольный список перед защитой

### Функциональность
- [ ] Все CRUD операции работают
- [ ] Загрузка файлов различных форматов
- [ ] Валидация файлов
- [ ] Классификация документов
- [ ] Поиск по документам
- [ ] Статистика

### Безопасность
- [ ] JWT аутентификация настроена
- [ ] CORS правильно сконфигурирован
- [ ] Permissions работают корректно
- [ ] Валидация данных на всех уровнях
- [ ] Секреты в переменных окружения

### Качество кода
- [ ] PEP8 соблюден
- [ ] Код отформатирован (black)
- [ ] Нет линтер ошибок (flake8)
- [ ] Покрытие тестами >= 75%
- [ ] Все тесты проходят

### Документация
- [ ] README.md заполнен
- [ ] OpenAPI документация доступна
- [ ] Комментарии в коде
- [ ] Примеры запросов к API

### Деплой
- [ ] Docker работает
- [ ] docker-compose.yml настроен
- [ ] Переменные окружения вынесены
- [ ] Миграции применяются автоматически

---

## 6. Источники и дополнительные материалы

### Официальная документация
- Django: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- PostgreSQL: https://www.postgresql.org/docs/
- Docker: https://docs.docker.com/

### Best Practices
- Two Scoops of Django (книга)
- REST API Design Rulebook
- 12 Factor App: https://12factor.net/

### Инструменты
- djangorestframework-simplejwt
- django-cors-headers
- drf-spectacular
- celery
- pytest-django

---

## 7. Заключение

Этот BPA документ содержит все необходимые best practices для успешной реализации дипломного проекта "Сервис обработки загружаемых документов". 

Следуя этим рекомендациям, вы создадите:
- ✅ Профессиональный, масштабируемый backend
- ✅ Безопасное API с JWT и CORS
- ✅ Хорошо протестированное приложение
- ✅ Документированный код
- ✅ Готовый к деплою сервис

**Успехов на защите! 🚀**
