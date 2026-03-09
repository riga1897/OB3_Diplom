#!/bin/bash
# Watch-режим: автоматическая проверка при изменении файлов
# Требует: inotify-tools (устанавливается автоматически при первом запуске)
# Использование: ./scripts/unix/watch.sh

echo "👀 Watch-режим: отслеживание изменений в apps/, config/ и tests/"
echo "💡 При сохранении файла автоматически запустятся ruff и mypy"
echo "⏸️  Для остановки нажмите Ctrl+C"
echo ""

check_and_install_inotify() {
    if ! command -v inotifywait &> /dev/null; then
        echo "📦 Установка inotify-tools..."
        # В Replit используем nix-env
        nix-env -iA nixpkgs.inotify-tools
    fi
}

run_quick_checks() {
    clear
    echo "📝 Файл изменен: $1"
    echo "🔍 Запуск быстрых проверок..."
    echo ""
    
    echo "1️⃣  Ruff..."
    if poetry run ruff check apps/ config/ tests/; then
        echo "✅ Ruff: OK"
    else
        echo "❌ Ruff: есть ошибки"
    fi
    echo ""
    
    echo "2️⃣  Mypy..."
    if poetry run mypy apps/ config/ tests/; then
        echo "✅ Mypy: OK"
    else
        echo "❌ Mypy: есть ошибки"
    fi
    echo ""
    
    echo "⏳ Ожидание изменений..."
}

# Проверка и установка inotify-tools
check_and_install_inotify

# Запуск отслеживания
while inotifywait -r -e modify,create,delete apps/ config/ tests/; do
    run_quick_checks "$REPLY"
done
