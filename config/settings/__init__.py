"""
Модуль выбора настроек Django.

Автоматически выбирает настройки на основе переменной ENVIRONMENT.
Приоритет: DJANGO_SETTINGS_MODULE > ENVIRONMENT > автоопределение

Использование в .env:
    ENVIRONMENT=development  # или staging, production, test

Модуль выполняет:
1. Проверяет DJANGO_SETTINGS_MODULE (если задан явно - использует его)
2. Проверяет переменную ENVIRONMENT из .env
3. Автоопределение на основе REPLIT_DEPLOYMENT для Replit

Допустимые значения ENVIRONMENT:
- development (по умолчанию) - разработка, DEBUG=True
- staging - тестирование перед production
- production - боевое окружение
- test - для pytest
"""
