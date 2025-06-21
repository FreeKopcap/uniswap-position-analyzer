#!/bin/bash

# Скрипт для анализа позиций Uniswap
echo "=== Анализ позиций Uniswap ==="

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "Ошибка: Python3 не установлен"
    exit 1
fi

# Устанавливаем зависимости
echo "Устанавливаем зависимости..."
pip3 install -r requirements.txt

# Запускаем анализ
echo "Запускаем анализ позиции..."
python3 uniswap_analyzer.py

echo "Анализ завершен." 