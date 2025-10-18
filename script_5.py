
# Создаем данные для примера организации для веб-приложения
import json

# Получаем данные первой организации из БД
conn = sqlite3.connect('organizations.db')
cursor = conn.cursor()

cursor.execute('SELECT * FROM organizations LIMIT 1')
org = cursor.fetchone()

if org:
    org_dict = {
        'id': org[0],
        'inn': org[1],
        'short_name': org[2],
        'full_name': org[3],
        'status': org[4],
        'legal_address': org[5],
        'production_address': org[6],
        'main_industry': org[8],
        'sub_industry': org[9],
        'okrug': org[31],
        'raion': org[32]
    }
    
    # Получаем финансовые данные
    cursor.execute('SELECT * FROM financial_data WHERE org_id = ?', (org[0],))
    financial_rows = cursor.fetchall()
    
    financial_data = []
    for row in financial_rows:
        financial_data.append({
            'year': row[2],
            'revenue': row[3] if row[3] else 0,
            'net_profit': row[4] if row[4] else 0,
            'taxes_total': row[5] if row[5] else 0,
            'investments': row[12] if row[12] else 0,
            'export_volume': row[13] if row[13] else 0
        })
    
    # Получаем данные о персонале
    cursor.execute('SELECT * FROM personnel_data WHERE org_id = ?', (org[0],))
    personnel_rows = cursor.fetchall()
    
    personnel_data = []
    for row in personnel_rows:
        personnel_data.append({
            'year': row[2],
            'total_employees': row[3] if row[3] else 0,
            'moscow_employees': row[4] if row[4] else 0,
            'avg_salary_moscow': row[7] if row[7] else 0
        })
    
    org_dict['financial_data'] = financial_data
    org_dict['personnel_data'] = personnel_data
    
    print("Пример данных организации для веб-приложения:")
    print(json.dumps(org_dict, ensure_ascii=False, indent=2))
    
    # Сохраняем в файл для использования в приложении
    with open('example_org_data.json', 'w', encoding='utf-8') as f:
        json.dump(org_dict, f, ensure_ascii=False, indent=2)

conn.close()

# Создаем список индустрий для фильтрации
industries = [
    "Химическая промышленность",
    "Станкостроение и инструментальная промышленность",
    "Пищевая промышленность",
    "Машиностроение",
    "Металлургия",
    "Электроника и радиотехника",
    "Легкая промышленность",
    "Фармацевтика",
    "Деревообработка",
    "Строительные материалы"
]

industries_json = json.dumps(industries, ensure_ascii=False, indent=2)
print("\n\nСписок отраслей:")
print(industries_json)

with open('industries.json', 'w', encoding='utf-8') as f:
    json.dump(industries, f, ensure_ascii=False, indent=2)
