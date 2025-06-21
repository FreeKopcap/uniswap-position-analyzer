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

def extract_position_data_selenium(url):
    """
    Извлекает данные о позиции с помощью Selenium (эмуляция браузера)
    """
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(options=options)
    try:
        print("Открываем страницу...")
        driver.get(url)
        
        # Ждем загрузки страницы
        print("Ждем загрузки данных...")
        time.sleep(10)
        
        # Сохраняем HTML для отладки
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("HTML страницы сохранен в debug_page.html")
        
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
                    if 2000 <= val <= 2500:  # Курс ETH в диапазоне 2000-2500
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
                                if 2000 <= val <= 2500:
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
                        if 2000 <= val <= 2500:
                            eth_rate = val
                            print(f"Найдено значение курса ETH: ${eth_rate:,.2f}")
                            break
                    except Exception as e:
                        print(f"  Ошибка преобразования: {e}")
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
    # URL позиции Uniswap
    url = "https://app.uniswap.org/positions/v3/unichain/59044"
    
    # Константа начального количества ETH
    eth_initial = 38.1
    
    print("Анализ позиции Uniswap...")
    print(f"URL: {url}")
    print(f"Начальное количество ETH: {eth_initial}")
    print("-" * 50)
    
    # Извлекаем данные с помощью Selenium
    position_usd, eth_rate = extract_position_data_selenium(url)
    
    if position_usd is None or eth_rate is None:
        print("Не удалось извлечь данные с веб-страницы.")
        print("Возможные причины:")
        print("1. Страница требует JavaScript для загрузки данных")
        print("2. Изменилась структура страницы")
        print("3. Проблемы с сетевым подключением")
        print("4. Проверьте файл debug_page.html для анализа структуры страницы")
        return
    
    print(f"Размер позиции: ${position_usd:,.2f}")
    print(f"Курс ETH: ${eth_rate:,.2f}")
    print("-" * 50)
    
    # Вычисления
    current_eth_value = eth_initial * eth_rate
    current_position_in_eth = position_usd / eth_rate
    
    # Вывод результатов сравнения
    print("СРАВНЕНИЕ 1:")
    print(f"Текущая стоимость начального эфира: ${current_eth_value:,.2f}")
    print(f"Текущее значение позиции: ${position_usd:,.2f}")
    print("-" * 50)
    
    print("СРАВНЕНИЕ 2:")
    print(f"Начальное вложение эфира: {eth_initial} ETH")
    print(f"Текущее значение позиции в эфирах: {current_position_in_eth:.4f} ETH")
    print("-" * 50)
    
    # Дополнительный анализ
    if current_eth_value > position_usd:
        print(f"Позиция показывает убыток: ${current_eth_value - position_usd:,.2f}")
    else:
        print(f"Позиция показывает прибыль: ${position_usd - current_eth_value:,.2f}")
    
    if current_position_in_eth > eth_initial:
        print(f"Позиция в ETH показывает рост: +{current_position_in_eth - eth_initial:.4f} ETH")
    else:
        print(f"Позиция в ETH показывает падение: {current_position_in_eth - eth_initial:.4f} ETH")

if __name__ == "__main__":
    main() 