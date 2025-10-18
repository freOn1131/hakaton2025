
# Создаем пример Python кода для интеграции с API и работы с БД
backend_code = """
# backend.py - Бэкенд для работы с организациями

import sqlite3
import json
import requests
from typing import Optional, Dict, List, Any
from datetime import datetime

# ==========================
# КОНФИГУРАЦИЯ API
# ==========================

# API ФНС
FNS_API_URL = "https://api-fns.ru/api/search"
FNS_API_KEY = "c35fe9f432d553652e59bb7edfdcb4137f64cfe0"

# API DaData для очистки адресов
DADATA_API_URL = "https://cleaner.dadata.ru/api/v1/clean/address"
DADATA_API_KEY = "5343b1ebeb87e21afe2eee6156907b86dc5eee09"

# API LLM для разбора данных
LLM_API_URL = "http://10.250.12.109:8080/api/chat/completions"
LLM_API_KEY = "sk-8c3828c838c94a6ab0c04d0deee2f799"
LLM_MODEL = "gemma3:27b"

# База данных
DB_PATH = "organizations.db"

# ==========================
# ФУНКЦИИ ДЛЯ РАБОТЫ С LLM
# ==========================

def chat_completion(content: str, model: str = LLM_MODEL, temperature: float = 0.7) -> Dict:
    \"\"\"Отправка запроса к LLM API\"\"\"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY}"
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "temperature": temperature,
        "stream": False
    }
    
    try:
        resp = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Ошибка при обращении к LLM: {e}")
        return None

def parse_data_with_llm(raw_data: str) -> Optional[Dict]:
    \"\"\"Разбор сырых данных с помощью LLM\"\"\"
    
    # Загружаем промпт-шаблон
    with open('llm_prompt_template.txt', 'r', encoding='utf-8') as f:
        prompt_template = f.read()
    
    # Формируем промпт с данными
    prompt = prompt_template.replace("{input_data}", raw_data)
    
    # Отправляем запрос
    result = chat_completion(prompt, temperature=0.3)
    
    if result and 'choices' in result:
        response_text = result['choices'][0]['message']['content']
        
        # Пытаемся извлечь JSON из ответа
        try:
            # Ищем JSON в ответе (может быть обернут в ```json ... ```)
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end]
            elif '```' in response_text:
                json_start = response_text.find('```') + 3
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end]
            
            parsed_data = json.loads(response_text.strip())
            return parsed_data
        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга JSON: {e}")
            print(f"Ответ LLM: {response_text}")
            return None
    
    return None

# ==========================
# ФУНКЦИИ ДЛЯ РАБОТЫ С API ФНС
# ==========================

def search_fns_by_inn(inn: str) -> Optional[Dict]:
    \"\"\"Поиск организации в ФНС по ИНН\"\"\"
    headers = {
        "Content-Type": "application/json"
    }
    
    params = {
        "q": inn,
        "key": FNS_API_KEY
    }
    
    try:
        resp = requests.get(FNS_API_URL, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        if data and 'items' in data and len(data['items']) > 0:
            return data['items'][0]
        return None
    except Exception as e:
        print(f"Ошибка при обращении к API ФНС: {e}")
        return None

def search_fns_by_name(name: str) -> List[Dict]:
    \"\"\"Поиск организаций в ФНС по названию\"\"\"
    headers = {
        "Content-Type": "application/json"
    }
    
    params = {
        "q": name,
        "key": FNS_API_KEY
    }
    
    try:
        resp = requests.get(FNS_API_URL, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        if data and 'items' in data:
            return data['items']
        return []
    except Exception as e:
        print(f"Ошибка при обращении к API ФНС: {e}")
        return []

# ==========================
# ФУНКЦИИ ДЛЯ РАБОТЫ С DADATA
# ==========================

def clean_address_dadata(address: str) -> Optional[Dict]:
    \"\"\"Очистка и стандартизация адреса через DaData\"\"\"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Token {DADATA_API_KEY}"
    }
    
    payload = [address]
    
    try:
        resp = requests.post(DADATA_API_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        if data and len(data) > 0:
            return data[0]
        return None
    except Exception as e:
        print(f"Ошибка при обращении к DaData: {e}")
        return None

# ==========================
# ФУНКЦИИ ДЛЯ РАБОТЫ С БД
# ==========================

def get_db_connection():
    \"\"\"Создание подключения к БД\"\"\"
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def search_org_in_db_by_inn(inn: str) -> Optional[Dict]:
    \"\"\"Поиск организации в БД по ИНН\"\"\"
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM organizations WHERE inn = ?
    ''', (inn,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def search_org_in_db_by_name(name: str) -> List[Dict]:
    \"\"\"Поиск организаций в БД по названию\"\"\"
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM organizations 
        WHERE short_name LIKE ? OR full_name LIKE ?
    ''', (f'%{name}%', f'%{name}%'))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_org_financial_data(org_id: int) -> List[Dict]:
    \"\"\"Получение финансовых данных организации\"\"\"
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM financial_data WHERE org_id = ? ORDER BY year
    ''', (org_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_org_personnel_data(org_id: int) -> List[Dict]:
    \"\"\"Получение данных о персонале организации\"\"\"
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM personnel_data WHERE org_id = ? ORDER BY year
    ''', (org_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def insert_organization_to_db(org_data: Dict) -> int:
    \"\"\"Добавление организации в БД\"\"\"
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Вставка основных данных организации
    cursor.execute('''
        INSERT OR REPLACE INTO organizations (
            inn, short_name, full_name, status, legal_address, 
            production_address, additional_address, main_industry, sub_industry,
            main_okved, okved_activity, production_okved, registration_date,
            director, parent_company, parent_inn, contact_management,
            contact_employee, contact_emergency, website, email,
            support_measures, special_status, sme_status, export_available,
            export_countries, coordinates_legal, coordinates_production,
            coordinates_additional, latitude, longitude, okrug, raion, data_source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        org_data.get('inn'),
        org_data.get('short_name'),
        org_data.get('full_name'),
        org_data.get('status'),
        org_data.get('legal_address'),
        org_data.get('production_address'),
        org_data.get('additional_address'),
        org_data.get('main_industry'),
        org_data.get('sub_industry'),
        org_data.get('main_okved'),
        org_data.get('okved_activity'),
        org_data.get('production_okved'),
        org_data.get('registration_date'),
        org_data.get('director'),
        org_data.get('parent_company'),
        org_data.get('parent_inn'),
        org_data.get('contact_management'),
        org_data.get('contact_employee'),
        org_data.get('contact_emergency'),
        org_data.get('website'),
        org_data.get('email'),
        org_data.get('support_measures'),
        org_data.get('special_status'),
        org_data.get('sme_status'),
        org_data.get('export_available'),
        org_data.get('export_countries'),
        org_data.get('coordinates_legal'),
        org_data.get('coordinates_production'),
        org_data.get('coordinates_additional'),
        org_data.get('latitude'),
        org_data.get('longitude'),
        org_data.get('okrug'),
        org_data.get('raion'),
        org_data.get('data_source', 'user_input')
    ))
    
    org_id = cursor.lastrowid
    
    # Вставка финансовых данных
    if 'financial_data' in org_data and org_data['financial_data']:
        for fin_data in org_data['financial_data']:
            cursor.execute('''
                INSERT INTO financial_data (
                    org_id, year, revenue, net_profit, taxes_total,
                    profit_tax, property_tax, land_tax, ndfl,
                    transport_tax, other_taxes, excise, investments, export_volume
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                org_id,
                fin_data.get('year'),
                fin_data.get('revenue'),
                fin_data.get('net_profit'),
                fin_data.get('taxes_total'),
                fin_data.get('profit_tax'),
                fin_data.get('property_tax'),
                fin_data.get('land_tax'),
                fin_data.get('ndfl'),
                fin_data.get('transport_tax'),
                fin_data.get('other_taxes'),
                fin_data.get('excise'),
                fin_data.get('investments'),
                fin_data.get('export_volume')
            ))
    
    # Вставка данных о персонале
    if 'personnel_data' in org_data and org_data['personnel_data']:
        for pers_data in org_data['personnel_data']:
            cursor.execute('''
                INSERT INTO personnel_data (
                    org_id, year, total_employees, moscow_employees,
                    total_payroll, moscow_payroll, avg_salary_total, avg_salary_moscow
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                org_id,
                pers_data.get('year'),
                pers_data.get('total_employees'),
                pers_data.get('moscow_employees'),
                pers_data.get('total_payroll'),
                pers_data.get('moscow_payroll'),
                pers_data.get('avg_salary_total'),
                pers_data.get('avg_salary_moscow')
            ))
    
    # Вставка данных о недвижимости
    if 'real_estate' in org_data and org_data['real_estate']:
        re_data = org_data['real_estate']
        cursor.execute('''
            INSERT INTO real_estate (
                org_id, cadastral_number_land, land_area, land_permitted_use,
                land_ownership_type, land_owner, cadastral_number_building,
                building_area, building_permitted_use, building_type,
                building_ownership_type, building_owner, production_area
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            org_id,
            re_data.get('cadastral_number_land'),
            re_data.get('land_area'),
            re_data.get('land_permitted_use'),
            re_data.get('land_ownership_type'),
            re_data.get('land_owner'),
            re_data.get('cadastral_number_building'),
            re_data.get('building_area'),
            re_data.get('building_permitted_use'),
            re_data.get('building_type'),
            re_data.get('building_ownership_type'),
            re_data.get('building_owner'),
            re_data.get('production_area')
        ))
    
    # Вставка данных о продукции
    if 'products' in org_data and org_data['products']:
        prod_data = org_data['products']
        cursor.execute('''
            INSERT INTO products (
                org_id, standardized_product, product_names, okpd2_codes,
                product_types, product_catalog, state_order, capacity_load
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            org_id,
            prod_data.get('standardized_product'),
            prod_data.get('product_names'),
            prod_data.get('okpd2_codes'),
            prod_data.get('product_types'),
            prod_data.get('product_catalog'),
            prod_data.get('state_order'),
            prod_data.get('capacity_load')
        ))
    
    conn.commit()
    conn.close()
    
    return org_id

def compare_data(user_data: Dict, fns_data: Dict) -> Dict:
    \"\"\"Сравнение данных пользователя с данными ФНС\"\"\"
    differences = {}
    
    fields_to_compare = [
        ('inn', 'ИНН'),
        ('short_name', 'Краткое наименование'),
        ('full_name', 'Полное наименование'),
        ('status', 'Статус'),
        ('legal_address', 'Юридический адрес'),
        ('director', 'Руководитель'),
        ('main_okved', 'Основной ОКВЭД'),
        ('registration_date', 'Дата регистрации')
    ]
    
    for field, label in fields_to_compare:
        user_value = user_data.get(field)
        fns_value = fns_data.get(field)
        
        if user_value != fns_value:
            differences[field] = {
                'label': label,
                'user': user_value,
                'fns': fns_value,
                'match': False
            }
        else:
            differences[field] = {
                'label': label,
                'user': user_value,
                'fns': fns_value,
                'match': True
            }
    
    return differences

def get_organizations_by_industry(industry: str) -> List[Dict]:
    \"\"\"Получение списка организаций по отрасли\"\"\"
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM organizations 
        WHERE main_industry LIKE ? OR sub_industry LIKE ?
        ORDER BY short_name
    ''', (f'%{industry}%', f'%{industry}%'))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    \"\"\"Аутентификация пользователя\"\"\"
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM users WHERE username = ? AND password = ?
    ''', (username, password))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def register_user(username: str, password: str) -> bool:
    \"\"\"Регистрация нового пользователя\"\"\"
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO users (username, password) VALUES (?, ?)
        ''', (username, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

# ==========================
# ПРИМЕР ИСПОЛЬЗОВАНИЯ
# ==========================

if __name__ == "__main__":
    # Пример поиска в БД
    print("=== Поиск в БД ===")
    org = search_org_in_db_by_inn("7714431171")
    if org:
        print(f"Найдена организация: {org['short_name']}")
        
        # Получаем финансовые данные
        fin_data = get_org_financial_data(org['id'])
        print(f"Финансовых записей: {len(fin_data)}")
        
        # Получаем данные о персонале
        pers_data = get_org_personnel_data(org['id'])
        print(f"Записей о персонале: {len(pers_data)}")
    
    # Пример разбора данных с помощью LLM
    print("\\n=== Разбор данных с помощью LLM ===")
    raw_data = \"\"\"
    Организация: ООО "Пример"
    ИНН: 1234567890
    Адрес: Москва, ул. Примерная, д. 1
    Выручка 2023: 5000000 тыс. руб.
    Численность: 150 человек
    \"\"\"
    
    # parsed = parse_data_with_llm(raw_data)
    # if parsed:
    #     print(f"Разобранные данные: {json.dumps(parsed, ensure_ascii=False, indent=2)}")
    
    print("\\nБэкенд готов к работе!")
"""

# Сохраняем код бэкенда
with open('backend.py', 'w', encoding='utf-8') as f:
    f.write(backend_code)

print("Файл backend.py создан!")
print("\nОсновные функции бэкенда:")
print("- chat_completion() - отправка запроса к LLM API")
print("- parse_data_with_llm() - разбор сырых данных с помощью LLM")
print("- search_fns_by_inn() - поиск организации в ФНС по ИНН")
print("- search_fns_by_name() - поиск организаций в ФНС по названию")
print("- clean_address_dadata() - очистка и стандартизация адреса")
print("- search_org_in_db_by_inn() - поиск организации в БД по ИНН")
print("- search_org_in_db_by_name() - поиск организаций в БД по названию")
print("- insert_organization_to_db() - добавление организации в БД")
print("- compare_data() - сравнение данных пользователя с данными ФНС")
print("- get_organizations_by_industry() - получение списка организаций по отрасли")
print("- authenticate_user() - аутентификация пользователя")
print("- register_user() - регистрация нового пользователя")
