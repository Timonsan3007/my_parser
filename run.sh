#!/bin/bash

# Проверяем существование виртуального окружения
if [ ! -d "venv" ]; then
    echo "Ошибка: виртуальное окружение 'venv' не найдено."
    echo "Запустите сначала: python -m venv venv && pip install -r requirements.txt"
    exit 1
fi

# Активируем виртуальное окружение
source venv/bin/activate || { echo "Не удалось активировать venv"; exit 1; }

# Запуск скриптов
echo "Запускаем parser.py..."
python parser.py || { echo "Ошибка при выполнении parser.py"; exit 1; }

echo "Запускаем vk_parser.py..."
python vk_parser.py || { echo "Ошибка при выполнении vk_parser.py"; exit 1; }

echo "Все скрипты успешно выполнены."

chmod +x run.sh