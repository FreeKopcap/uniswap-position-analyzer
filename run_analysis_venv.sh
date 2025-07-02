#!/bin/bash

# Скрипт для анализа позиций Uniswap с виртуальным окружением
echo "=== Анализ позиций Uniswap (с виртуальным окружением) ==="

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "Ошибка: Python3 не установлен"
    exit 1
fi

# Создаем виртуальное окружение, если его нет
if [ ! -d "venv" ]; then
    echo "Создаем виртуальное окружение..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
echo "Активируем виртуальное окружение..."
source venv/bin/activate

# Обновляем pip в виртуальном окружении
echo "Обновляем pip..."
pip install --upgrade pip --quiet

# Устанавливаем зависимости
echo "Устанавливаем зависимости..."
pip install -r requirements.txt --quiet

# Запускаем анализ
echo "Запускаем анализ позиции..."
python uniswap_analyzer.py

# Деактивируем виртуальное окружение
deactivate

echo "Анализ завершен." 