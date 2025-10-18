
# Создаем структуру базы данных SQLite и заполняем ее данными из файла

import sqlite3
import json
from datetime import datetime

# Создаем подключение к БД
conn = sqlite3.connect('organizations.db')
cursor = conn.cursor()

# Создаем таблицу пользователей
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Создаем админа (пароль: admin)
cursor.execute('''
INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)
''', ('admin', 'admin'))

# Создаем таблицу организаций
cursor.execute('''
CREATE TABLE IF NOT EXISTS organizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inn TEXT UNIQUE NOT NULL,
    short_name TEXT,
    full_name TEXT,
    status TEXT,
    legal_address TEXT,
    production_address TEXT,
    additional_address TEXT,
    main_industry TEXT,
    sub_industry TEXT,
    main_okved TEXT,
    okved_activity TEXT,
    production_okved TEXT,
    registration_date TEXT,
    director TEXT,
    parent_company TEXT,
    parent_inn TEXT,
    contact_management TEXT,
    contact_employee TEXT,
    contact_emergency TEXT,
    website TEXT,
    email TEXT,
    support_measures TEXT,
    special_status TEXT,
    sme_status TEXT,
    export_available TEXT,
    export_countries TEXT,
    coordinates_legal TEXT,
    coordinates_production TEXT,
    coordinates_additional TEXT,
    latitude REAL,
    longitude REAL,
    okrug TEXT,
    raion TEXT,
    data_source TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Создаем таблицу финансовых показателей
cursor.execute('''
CREATE TABLE IF NOT EXISTS financial_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id INTEGER,
    year INTEGER,
    revenue REAL,
    net_profit REAL,
    taxes_total REAL,
    profit_tax REAL,
    property_tax REAL,
    land_tax REAL,
    ndfl REAL,
    transport_tax REAL,
    other_taxes REAL,
    excise REAL,
    investments REAL,
    export_volume REAL,
    FOREIGN KEY (org_id) REFERENCES organizations(id)
)
''')

# Создаем таблицу данных о персонале
cursor.execute('''
CREATE TABLE IF NOT EXISTS personnel_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id INTEGER,
    year INTEGER,
    total_employees INTEGER,
    moscow_employees INTEGER,
    total_payroll REAL,
    moscow_payroll REAL,
    avg_salary_total REAL,
    avg_salary_moscow REAL,
    FOREIGN KEY (org_id) REFERENCES organizations(id)
)
''')

# Создаем таблицу недвижимости
cursor.execute('''
CREATE TABLE IF NOT EXISTS real_estate (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id INTEGER,
    cadastral_number_land TEXT,
    land_area REAL,
    land_permitted_use TEXT,
    land_ownership_type TEXT,
    land_owner TEXT,
    cadastral_number_building TEXT,
    building_area REAL,
    building_permitted_use TEXT,
    building_type TEXT,
    building_ownership_type TEXT,
    building_owner TEXT,
    production_area REAL,
    FOREIGN KEY (org_id) REFERENCES organizations(id)
)
''')

# Создаем таблицу продукции
cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id INTEGER,
    standardized_product TEXT,
    product_names TEXT,
    okpd2_codes TEXT,
    product_types TEXT,
    product_catalog TEXT,
    state_order TEXT,
    capacity_load TEXT,
    FOREIGN KEY (org_id) REFERENCES organizations(id)
)
''')

conn.commit()
print("Структура базы данных создана!")

# Заполняем данные из Excel
df_filled = df[df['ИНН'].notna() & (df['ИНН'] != 'ИНН')]

for idx, row in df_filled.iterrows():
    try:
        inn = str(int(row['ИНН']))
        
        # Вставляем организацию
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
            inn,
            str(row['Наименование организации']) if pd.notna(row['Наименование организации']) else None,
            str(row['Полное наименование организации']) if pd.notna(row['Полное наименование организации']) else None,
            str(row['Статус ']) if pd.notna(row['Статус ']) else None,
            str(row['Юридический адрес']) if pd.notna(row['Юридический адрес']) else None,
            str(row['Адрес производства']) if pd.notna(row['Адрес производства']) else None,
            str(row['Адрес дополнительной площадки']) if pd.notna(row['Адрес дополнительной площадки']) else None,
            str(row['Основная отрасль']) if pd.notna(row['Основная отрасль']) else None,
            str(row['Подотрасль (Основная)']) if pd.notna(row['Подотрасль (Основная)']) else None,
            str(row['Основной ОКВЭД ']) if pd.notna(row['Основной ОКВЭД ']) else None,
            str(row['Вид деятельности по основному ОКВЭД ']) if pd.notna(row['Вид деятельности по основному ОКВЭД ']) else None,
            str(row['Производственный ОКВЭД']) if pd.notna(row['Производственный ОКВЭД']) else None,
            str(row['Дата регистрации']) if pd.notna(row['Дата регистрации']) else None,
            str(row['Руководитель']) if pd.notna(row['Руководитель']) else None,
            str(row['Головная организация']) if pd.notna(row['Головная организация']) else None,
            str(row['ИНН головной организации']) if pd.notna(row['ИНН головной организации']) else None,
            str(row['Контактные данные руководства']) if pd.notna(row['Контактные данные руководства']) else None,
            str(row['Контакт сотрудника организации']) if pd.notna(row['Контакт сотрудника организации']) else None,
            str(row['Контактные данные ответственного по ЧС']) if pd.notna(row['Контактные данные ответственного по ЧС']) else None,
            str(row['Сайт']) if pd.notna(row['Сайт']) else None,
            str(row['Электронная почта']) if pd.notna(row['Электронная почта']) else None,
            str(row['Данные об оказанных мерах поддержки']) if pd.notna(row['Данные об оказанных мерах поддержки']) else None,
            str(row['Наличие особого статуса']) if pd.notna(row['Наличие особого статуса']) else None,
            str(row['Статус МСП']) if pd.notna(row['Статус МСП']) else None,
            str(row['Наличие поставок продукции на экспорт ']) if pd.notna(row['Наличие поставок продукции на экспорт ']) else None,
            str(row['Перечень государств-импортеров ']) if pd.notna(row['Перечень государств-импортеров ']) else None,
            str(row['Координаты юридического адреса']) if pd.notna(row['Координаты юридического адреса']) else None,
            str(row['Координаты адреса производства']) if pd.notna(row['Координаты адреса производства']) else None,
            str(row['Координаты адреса дополнительной площадки']) if pd.notna(row['Координаты адреса дополнительной площадки']) else None,
            float(row['Координаты (широта)']) if pd.notna(row['Координаты (широта)']) else None,
            float(row['Координаты (долгота)']) if pd.notna(row['Координаты (долгота)']) else None,
            str(row['Округ']) if pd.notna(row['Округ']) else None,
            str(row['Район']) if pd.notna(row['Район']) else None,
            'excel_import'
        ))
        
        org_id = cursor.lastrowid
        
        # Вставляем финансовые данные за годы 2022-2024
        for year in [2022, 2023, 2024]:
            cursor.execute('''
            INSERT INTO financial_data (
                org_id, year, revenue, net_profit, taxes_total,
                profit_tax, property_tax, land_tax, ndfl,
                transport_tax, other_taxes, excise, investments, export_volume
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                org_id, year,
                float(row[f'Выручка предприятия, тыс. руб. {year}']) if pd.notna(row[f'Выручка предприятия, тыс. руб. {year}']) else None,
                float(row[f'Чистая прибыль (убыток),тыс. руб. {year}']) if pd.notna(row[f'Чистая прибыль (убыток),тыс. руб. {year}']) else None,
                float(row[f'Налоги, уплаченные в бюджет Москвы (без акцизов), тыс.руб. {year}']) if pd.notna(row[f'Налоги, уплаченные в бюджет Москвы (без акцизов), тыс.руб. {year}']) else None,
                float(row[f'Налог на прибыль, тыс.руб. {year}']) if pd.notna(row[f'Налог на прибыль, тыс.руб. {year}']) else None,
                float(row[f'Налог на имущество, тыс.руб. {year}']) if pd.notna(row[f'Налог на имущество, тыс.руб. {year}']) else None,
                float(row[f'Налог на землю, тыс.руб. {year}']) if pd.notna(row[f'Налог на землю, тыс.руб. {year}']) else None,
                float(row[f'НДФЛ, тыс.руб. {year}']) if pd.notna(row[f'НДФЛ, тыс.руб. {year}']) else None,
                float(row[f'Транспортный налог, тыс.руб. {year}']) if pd.notna(row[f'Транспортный налог, тыс.руб. {year}']) else None,
                float(row[f'Прочие налоги {year}']) if pd.notna(row[f'Прочие налоги {year}']) else None,
                float(row[f'Акцизы, тыс. руб. {year}']) if pd.notna(row[f'Акцизы, тыс. руб. {year}']) else None,
                float(row[f'Инвестиции в Мск {year} тыс. руб.']) if pd.notna(row[f'Инвестиции в Мск {year} тыс. руб.']) else None,
                float(row[f'Объем экспорта, тыс. руб. {year}']) if pd.notna(row[f'Объем экспорта, тыс. руб. {year}']) else None
            ))
        
        # Вставляем данные о персонале за годы 2022-2024
        for year in [2022, 2023, 2024]:
            cursor.execute('''
            INSERT INTO personnel_data (
                org_id, year, total_employees, moscow_employees,
                total_payroll, moscow_payroll, avg_salary_total, avg_salary_moscow
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                org_id, year,
                int(row[f'Среднесписочная численность персонала (всего по компании), чел {year}']) if pd.notna(row[f'Среднесписочная численность персонала (всего по компании), чел {year}']) else None,
                int(row[f'Среднесписочная численность персонала, работающего в Москве, чел {year}']) if pd.notna(row[f'Среднесписочная численность персонала, работающего в Москве, чел {year}']) else None,
                float(row[f'Фонд оплаты труда всех сотрудников организации, тыс. руб {year}']) if pd.notna(row[f'Фонд оплаты труда всех сотрудников организации, тыс. руб {year}']) else None,
                float(row[f'Фонд оплаты труда  сотрудников, работающих в Москве, тыс. руб. {year}']) if pd.notna(row[f'Фонд оплаты труда  сотрудников, работающих в Москве, тыс. руб. {year}']) else None,
                float(row[f'Средняя з.п. всех сотрудников организации,  тыс.руб. {year}']) if pd.notna(row[f'Средняя з.п. всех сотрудников организации,  тыс.руб. {year}']) else None,
                float(row[f'Средняя з.п. сотрудников, работающих в Москве,  тыс.руб. {year}']) if pd.notna(row[f'Средняя з.п. сотрудников, работающих в Москве,  тыс.руб. {year}']) else None
            ))
        
        # Вставляем данные о недвижимости
        cursor.execute('''
        INSERT INTO real_estate (
            org_id, cadastral_number_land, land_area, land_permitted_use,
            land_ownership_type, land_owner, cadastral_number_building,
            building_area, building_permitted_use, building_type,
            building_ownership_type, building_owner, production_area
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            org_id,
            str(row['Кадастровый номер ЗУ']) if pd.notna(row['Кадастровый номер ЗУ']) else None,
            float(row['Площадь ЗУ']) if pd.notna(row['Площадь ЗУ']) else None,
            str(row['Вид разрешенного использования ЗУ']) if pd.notna(row['Вид разрешенного использования ЗУ']) else None,
            str(row['Вид собственности ЗУ']) if pd.notna(row['Вид собственности ЗУ']) else None,
            str(row['Собственник ЗУ']) if pd.notna(row['Собственник ЗУ']) else None,
            str(row['Кадастровый номер ОКСа']) if pd.notna(row['Кадастровый номер ОКСа']) else None,
            float(row['Площадь ОКСов']) if pd.notna(row['Площадь ОКСов']) else None,
            str(row['Вид разрешенного использования ОКСов']) if pd.notna(row['Вид разрешенного использования ОКСов']) else None,
            str(row['Тип строения и цель использования']) if pd.notna(row['Тип строения и цель использования']) else None,
            str(row['Вид собственности ОКСов']) if pd.notna(row['Вид собственности ОКСов']) else None,
            str(row['Собственник ОКСов']) if pd.notna(row['Собственник ОКСов']) else None,
            float(row['Площадь производственных помещений, кв.м.']) if pd.notna(row['Площадь производственных помещений, кв.м.']) else None
        ))
        
        # Вставляем данные о продукции
        cursor.execute('''
        INSERT INTO products (
            org_id, standardized_product, product_names, okpd2_codes,
            product_types, product_catalog, state_order, capacity_load
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            org_id,
            str(row['Стандартизированная продукция']) if pd.notna(row['Стандартизированная продукция']) else None,
            str(row['Название (виды производимой продукции)']) if pd.notna(row['Название (виды производимой продукции)']) else None,
            str(row['Перечень производимой продукции по кодам ОКПД 2']) if pd.notna(row['Перечень производимой продукции по кодам ОКПД 2']) else None,
            str(row['Перечень производимой продукции по типам и сегментам']) if pd.notna(row['Перечень производимой продукции по типам и сегментам']) else None,
            str(row['Каталог продукции']) if pd.notna(row['Каталог продукции']) else None,
            str(row['Наличие госзаказа']) if pd.notna(row['Наличие госзаказа']) else None,
            str(row['Уровень загрузки производственных мощностей']) if pd.notna(row['Уровень загрузки производственных мощностей']) else None
        ))
        
        print(f"Добавлена организация: {inn} - {row['Наименование организации']}")
        
    except Exception as e:
        print(f"Ошибка при добавлении записи: {e}")
        continue

conn.commit()

# Проверяем что данные добавлены
cursor.execute('SELECT COUNT(*) FROM organizations')
print(f"\nВсего организаций в БД: {cursor.fetchone()[0]}")

cursor.execute('SELECT COUNT(*) FROM financial_data')
print(f"Всего финансовых записей: {cursor.fetchone()[0]}")

cursor.execute('SELECT COUNT(*) FROM personnel_data')
print(f"Всего записей о персонале: {cursor.fetchone()[0]}")

conn.close()
print("\nБаза данных успешно создана и заполнена!")
