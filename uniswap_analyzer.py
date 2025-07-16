#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для анализа позиций Uniswap
Извлекает данные с веб-страницы и выполняет вычисления
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import sys
import requests
import json
import argparse

# === КОНСТАНТЫ ===
ETH_RATE_MIN = 2000  # Минимально допустимый курс ETH для поиска
ETH_RATE_MAX = 4000  # Максимально допустимый курс ETH для поиска
POSITION_ID = "59044"  # Номер позиции Uniswap
ETH_INITIAL = 38.1  # Начальное количество ETH

def parse_arguments():
    """
    Парсит аргументы командной строки
    """
    parser = argparse.ArgumentParser(
        description='Анализатор позиций Uniswap V3',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python3 uniswap_analyzer.py
  python3 uniswap_analyzer.py -p 12345 -i 50.0
  python3 uniswap_analyzer.py --eth_min 1500 --eth_max 3500 --position 67890 --eth_initial 25.5
        """
    )
    
    parser.add_argument('-n', '--eth_min', 
                       type=float, 
                       default=ETH_RATE_MIN,
                       help=f'Минимальный курс ETH для поиска (по умолчанию: {ETH_RATE_MIN})')
    
    parser.add_argument('-x', '--eth_max', 
                       type=float, 
                       default=ETH_RATE_MAX,
                       help=f'Максимальный курс ETH для поиска (по умолчанию: {ETH_RATE_MAX})')
    
    parser.add_argument('-p', '--position', 
                       type=str, 
                       default=POSITION_ID,
                       help=f'Номер позиции Uniswap (по умолчанию: {POSITION_ID})')
    
    parser.add_argument('-i', '--eth_initial', 
                       type=float, 
                       default=ETH_INITIAL,
                       help=f'Начальное количество ETH (по умолчанию: {ETH_INITIAL})')
    
    return parser.parse_args()

def get_eth_price_from_api():
    """
    Получает текущий курс ETH через API CoinGecko
    """
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            eth_price = data['ethereum']['usd']
            print(f"Получен курс ETH через API: ${eth_price:,.2f}")
            return eth_price
        else:
            print(f"Ошибка API: {response.status_code}")
            return None
    except Exception as e:
        print(f"Ошибка при получении курса ETH через API: {e}")
        return None

def extract_position_data_selenium(url, eth_min, eth_max):
    """
    Извлекает данные о позиции с помощью Selenium (эмуляция браузера)
    """
    options = Options()
    # Используем headless режим с дополнительными настройками
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Дополнительные опции для обхода блокировки
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    
    # Выполняем JavaScript для скрытия автоматизации
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    try:
        print("Открываем страницу...")
        driver.get(url)
        
        # Ждем загрузки страницы
        print("Ждем загрузки данных...")
        time.sleep(15)  # Увеличиваем время ожидания
        
        # Сохраняем HTML для отладки
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("HTML страницы сохранен в debug_page.html")
        
        # Проверяем, не попали ли мы на страницу ошибки
        if "ERR_" in driver.page_source or "error" in driver.title.lower():
            print("Обнаружена страница ошибки. Пробуем альтернативный подход...")
            # Попробуем перейти на главную страницу Uniswap
            driver.get("https://app.uniswap.org/")
            time.sleep(10)
            # Теперь попробуем перейти к позиции
            driver.get(url)
            time.sleep(15)
            
            # Сохраняем обновленный HTML
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("Обновленный HTML страницы сохранен в debug_page.html")
        
        # Ищем все элементы с текстом
        all_elements = driver.find_elements(By.XPATH, "//*[text()]")
        all_texts = [el.text for el in all_elements if el.text.strip()]
        
        print(f"Найдено {len(all_texts)} текстовых элементов")
        
        # Ищем элементы с символом $
        dollar_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '$')]")
        dollar_texts = [el.text for el in dollar_elements if '$' in el.text]
        
        print(f"Найдено {len(dollar_texts)} элементов с символом $")
        print("Примеры элементов с $:")
        for i, text in enumerate(dollar_texts[:5]):
            print(f"  {i+1}: {text}")
        
        # Если не нашли элементы с $, попробуем найти любые числа
        if not dollar_texts:
            print("Не найдены элементы с $. Ищем любые числовые значения...")
            # Используем более простой подход - ищем все элементы с текстом и фильтруем по наличию цифр
            all_text_elements = driver.find_elements(By.XPATH, "//*[text()]")
            number_texts = [el.text for el in all_text_elements if any(c.isdigit() for c in el.text) and el.text.strip()]
            print(f"Найдено {len(number_texts)} элементов с числами")
            print("Примеры элементов с числами:")
            for i, text in enumerate(number_texts[:10]):
                print(f"  {i+1}: {text}")
        
        position_usd = None
        eth_rate = None
        
        # Поиск значения позиции (ищем крупные суммы)
        position_patterns = [
            r'(\d{1,3}(?:[,\s]\d{3})*(?:[.,]\d+)?)\s*\$',  # 1,234.56 $ или 1 234,56 $
            r'\$(\d{1,3}(?:[,\s]\d{3})*(?:[.,]\d+)?)',     # $1,234.56
        ]
        
        for text in dollar_texts:
            for pattern in position_patterns:
                matches = re.findall(pattern, text.replace('\u202f', '').replace('\xa0', ''))
                for match in matches:
                    try:
                        value = match.replace(' ', '').replace(',', '.')
                        val = float(value)
                        if val > 1000:  # Ищем крупные суммы (позиция обычно больше 1000$)
                            if not position_usd or val > position_usd:
                                position_usd = val
                                print(f"Найдено значение позиции: ${position_usd:,.2f} в тексте: {text}")
                    except:
                        continue
        
        # Если не нашли позицию через регулярные выражения, возьмем самое большое значение из найденных
        if not position_usd:
            largest_value = 0
            for text in dollar_texts:
                # Ищем все числа в тексте
                numbers = re.findall(r'\$(\d{1,3}(?:[,\s]\d{3})*(?:[.,]\d+)?)', text)
                for num_str in numbers:
                    try:
                        value = num_str.replace(' ', '').replace(',', '.')
                        val = float(value)
                        if val > largest_value and val > 1000:
                            largest_value = val
                    except:
                        continue
            
            if largest_value > 0:
                position_usd = largest_value
                print(f"Используем самое большое найденное значение позиции: ${position_usd:,.2f}")
        
        # Если все еще не нашли позицию, используем правильный парсинг
        if not position_usd and dollar_texts:
            # Берем первое значение (оно самое большое)
            first_text = dollar_texts[0]
            # Убираем символ $ и пробелы
            clean_text = first_text.replace('$', '').replace(' ', '')
            # Ищем все цифры и запятые
            number_match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)', clean_text)
            if number_match:
                try:
                    # Заменяем запятые на пустую строку (разделители тысяч)
                    value_str = number_match.group(1).replace(',', '')
                    position_usd = float(value_str)
                    print(f"Извлечено значение позиции из первого элемента: ${position_usd:,.2f}")
                except:
                    pass
        
        # Если все еще не нашли позицию, используем самый простой способ
        if not position_usd and dollar_texts:
            # Берем первое значение (оно самое большое)
            first_text = dollar_texts[0]
            # Убираем символ $ и пробелы
            clean_text = first_text.replace('$', '').replace(' ', '')
            # Убираем все запятые (они разделяют тысячи)
            clean_text = clean_text.replace(',', '')
            # Ищем число
            number_match = re.search(r'(\d+\.?\d*)', clean_text)
            if number_match:
                try:
                    position_usd = float(number_match.group(1))
                    print(f"Извлечено значение позиции из первого элемента: ${position_usd:,.2f}")
                except:
                    pass
        
        # Поиск курса ETH (значение в скобках)
        eth_patterns = [
            r'\((\d{1,3}(?:[,\s]\d{3})*(?:[.,]\d+)?)\s*\$\)',  # (1,234.56 $) или (1 234,56 $)
            r'\((\d{1,3}(?:[,\s]\d{3})*(?:[.,]\d+)?)\)',       # (1,234.56) или (1 234,56)
        ]
        
        # Ищем курс ETH в тексте страницы
        page_text = driver.page_source
        for pattern in eth_patterns:
            matches = re.findall(pattern, page_text.replace('\u202f', '').replace('\xa0', ''))
            for match in matches:
                try:
                    # Заменяем запятые на точки для правильного парсинга
                    value = match.replace(' ', '').replace(',', '.')
                    val = float(value)
                    if eth_min <= val <= eth_max:  # Курс ETH в заданном диапазоне
                        eth_rate = val
                        print(f"Найдено значение курса ETH: ${eth_rate:,.2f}")
                        break
                except:
                    continue
            if eth_rate:
                break
        
        # Если не нашли через регулярные выражения, попробуем найти в тексте элементов
        if not eth_rate:
            for text in all_texts:
                if '(' in text and ')' in text and '$' in text:
                    # Ищем значение в скобках
                    bracket_match = re.search(r'\(([^)]+)\)', text)
                    if bracket_match:
                        bracket_content = bracket_match.group(1)
                        # Ищем число в скобках
                        number_match = re.search(r'(\d{1,3}(?:[,\s]\d{3})*(?:[.,]\d+)?)', bracket_content)
                        if number_match:
                            try:
                                # Заменяем запятые на точки для правильного парсинга
                                value = number_match.group(1).replace(' ', '').replace(',', '.')
                                val = float(value)
                                if eth_min <= val <= eth_max:
                                    eth_rate = val
                                    print(f"Найдено значение курса ETH: ${eth_rate:,.2f} в тексте: {text}")
                                    break
                            except:
                                continue
        
        # Если все еще не нашли курс ETH, ищем в HTML напрямую
        if not eth_rate:
            # Ищем конкретно значение в скобках с долларом
            eth_match = re.search(r'\(\$(\d{1,3}(?:[,\s]\d{3})*(?:[.,]\d+)?)\)', page_text)
            if eth_match:
                try:
                    value = eth_match.group(1).replace(' ', '').replace(',', '.')
                    eth_rate = float(value)
                    print(f"Найдено значение курса ETH из HTML: ${eth_rate:,.2f}")
                except:
                    pass
        
        # Если все еще не нашли курс ETH, ищем более точно
        if not eth_rate:
            # Ищем значение в скобках с долларом в любом формате
            eth_patterns = [
                r'\(\$(\d{1,3}(?:[,\s]\d{3})*(?:[.,]\d+)?)\)',  # ($2,314.00)
                r'\((\d{1,3}(?:[,\s]\d{3})*(?:[.,]\d+)?)\s*\$\)',  # (2,314.00 $)
                r'\((\d{1,3}(?:[,\s]\d{3})*(?:[.,]\d+)?)\)',  # (2,314.00)
            ]
            
            print("Ищем курс ETH в HTML...")
            for pattern in eth_patterns:
                matches = re.findall(pattern, page_text)
                print(f"Паттерн {pattern}: найдено {len(matches)} совпадений")
                for match in matches:
                    print(f"  Найдено: {match}")
                    try:
                        # Заменяем только запятые между цифрами (разделители тысяч)
                        # Оставляем точку как десятичный разделитель
                        value = match.replace(' ', '')
                        # Заменяем запятые на пустую строку только если они между цифрами
                        value = re.sub(r'(\d),(\d)', r'\1\2', value)
                        val = float(value)
                        print(f"  Преобразовано в число: {val}")
                        if eth_min <= val <= eth_max:
                            eth_rate = val
                            print(f"Найдено значение курса ETH: ${eth_rate:,.2f}")
                            break
                    except Exception as e:
                        print(f"  Ошибка преобразования: {e}")
                        continue
                if eth_rate:
                    break
        
        # Если все еще не нашли курс ETH, попробуем найти в тексте элементов
        if not eth_rate and number_texts:
            print("Ищем курс ETH в тексте элементов...")
            for text in number_texts:
                # Ищем числа в заданном диапазоне
                numbers = re.findall(r'(\d{1,3}(?:[,\s]\d{3})*(?:[.,]\d+)?)', text)
                for num_str in numbers:
                    try:
                        value = num_str.replace(' ', '').replace(',', '.')
                        val = float(value)
                        if eth_min <= val <= eth_max:
                            eth_rate = val
                            print(f"Найдено значение курса ETH: ${eth_rate:,.2f} в тексте: {text}")
                            break
                    except:
                        continue
                if eth_rate:
                    break
        
        return position_usd, eth_rate
        
    except Exception as e:
        print(f"Ошибка при извлечении данных через Selenium: {e}")
        import traceback
        traceback.print_exc()
        return None, None
    finally:
        driver.quit()

def main():
    """
    Основная функция скрипта
    """
    # Парсим аргументы командной строки
    args = parse_arguments()
    
    # URL позиции Uniswap
    url = f"https://app.uniswap.org/positions/v3/unichain/{args.position}"
    
    print("Анализ позиции Uniswap...")
    print(f"URL: {url}")
    print(f"Начальное количество ETH: {args.eth_initial}")
    print(f"Диапазон поиска курса ETH: ${args.eth_min:,.0f} - ${args.eth_max:,.0f}")
    print("-" * 50)
    
    # Извлекаем данные с помощью Selenium
    position_usd, eth_rate = extract_position_data_selenium(url, args.eth_min, args.eth_max)
    
    # Если не удалось найти курс ETH на странице, используем API
    if eth_rate is None:
        print("Не удалось найти курс ETH на странице. Используем API...")
        eth_rate = get_eth_price_from_api()
    
    if position_usd is None:
        print("Не удалось извлечь данные о позиции с веб-страницы.")
        print("Возможные причины:")
        print("1. Страница требует JavaScript для загрузки данных")
        print("2. Изменилась структура страницы")
        print("3. Проблемы с сетевым подключением")
        print("4. Проверьте файл debug_page.html для анализа структуры страницы")
        return
    
    if eth_rate is None:
        print("Не удалось получить курс ETH ни с веб-страницы, ни через API.")
        return
    
    print(f"Размер позиции: ${position_usd:,.2f}")
    print(f"Курс ETH: ${eth_rate:,.2f}")
    print("-" * 50)
    
    # Вычисления
    current_eth_value = args.eth_initial * eth_rate
    current_position_in_eth = position_usd / eth_rate
    
    # Вывод результатов сравнения
    print("СРАВНЕНИЕ 1:")
    print(f"Текущая стоимость начального эфира: ${current_eth_value:,.2f}")
    print(f"Текущее значение позиции: ${position_usd:,.2f}")
    print("-" * 50)
    
    print("СРАВНЕНИЕ 2:")
    print(f"Начальное вложение эфира: {args.eth_initial} ETH")
    print(f"Текущее значение позиции в эфирах: {current_position_in_eth:.4f} ETH")
    print("-" * 50)
    
    # Дополнительный анализ
    if current_eth_value > position_usd:
        print(f"Позиция показывает убыток: ${current_eth_value - position_usd:,.2f}")
    else:
        print(f"Позиция показывает прибыль: ${position_usd - current_eth_value:,.2f}")
    
    if current_position_in_eth > args.eth_initial:
        print(f"Позиция в ETH показывает рост: +{current_position_in_eth - args.eth_initial:.4f} ETH")
    else:
        print(f"Позиция в ETH показывает падение: {current_position_in_eth - args.eth_initial:.4f} ETH")

if __name__ == "__main__":
    main() 