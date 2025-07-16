#!/bin/bash

# Скрипт для анализа позиций Uniswap с виртуальным окружением
echo "=== Анализ позиций Uniswap (с виртуальным окружением) ==="

# Функция для вывода справки
show_help() {
    echo "Использование: $0 [опции]"
    echo ""
    echo "Опции:"
    echo "  -n, --eth_min VALUE    Минимальный курс ETH для поиска (значение по умолчанию задается в uniswap_analyzer.py)"
    echo "  -x, --eth_max VALUE    Максимальный курс ETH для поиска (значение по умолчанию задается в uniswap_analyzer.py)"
    echo "  -p, --position VALUE   Номер позиции Uniswap (значение по умолчанию задается в uniswap_analyzer.py)"
    echo "  -i, --eth_initial VALUE Начальное количество ETH (значение по умолчанию задается в uniswap_analyzer.py)"
    echo "  -h, --help            Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0"
    echo "  $0 -p 12345 -i 50.0"
    echo "  $0 --eth_min 1500 --eth_max 3500 --position 67890 --eth_initial 25.5"
    echo ""
}

# Парсим аргументы
PYTHON_ARGS=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--eth_min)
            PYTHON_ARGS="$PYTHON_ARGS -n $2"
            shift 2
            ;;
        -x|--eth_max)
            PYTHON_ARGS="$PYTHON_ARGS -x $2"
            shift 2
            ;;
        -p|--position)
            PYTHON_ARGS="$PYTHON_ARGS -p $2"
            shift 2
            ;;
        -i|--eth_initial)
            PYTHON_ARGS="$PYTHON_ARGS -i $2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Неизвестная опция: $1"
            show_help
            exit 1
            ;;
    esac
done

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

# Запускаем анализ с переданными аргументами
echo "Запускаем анализ позиции..."
python uniswap_analyzer.py $PYTHON_ARGS

# Деактивируем виртуальное окружение
deactivate

echo "Анализ завершен." 