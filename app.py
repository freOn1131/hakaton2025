# app.py

from flask import Flask, request, jsonify, render_template, send_from_directory
import sqlite3
import requests
import json
import PyPDF2
import io

app = Flask(__name__)

# Конфигурация API провайдеров
API_PROVIDERS = {
    "fns": {
        "name": "API-ФНС",
        "url": "https://api-fns.ru/api/search",
        "key": "30f98ca92ed94f3774fde7930d237775639fd7b5"
    },
    "dadata": {
        "name": "DaData",
        "url": "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/party",
        "key": "YOUR_DADATA_KEY"  # Заменить на реальный ключ
    },
    "spark": {
        "name": "СПАРК Интерфакс",
        "url": "https://spark-interfax.ru/api",
        "key": "YOUR_SPARK_KEY"  # Заменить на реальный ключ
    }
}

LLM_API_URL = "http://10.250.12.109:8080/api/chat/completions"
LLM_API_KEY = "sk-8c3828c838c94a6ab0c04d0deee2f799"
DATABASE = 'organizations.db'
PROMPT_FILE = 'llm_prompt_template.txt'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Инициализация базы данных"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Создание всех необходимых таблиц
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
        
        CREATE TABLE IF NOT EXISTS organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inn TEXT UNIQUE,
            short_name TEXT,
            full_name TEXT,
            status TEXT,
            legal_address TEXT,
            production_address TEXT,
            main_industry TEXT,
            sub_industry TEXT,
            main_okved TEXT,
            registration_date TEXT,
            director TEXT,
            okrug TEXT,
            raion TEXT,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        
        CREATE TABLE IF NOT EXISTS financial_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization_id INTEGER,
            year INTEGER,
            revenue REAL,
            net_profit REAL,
            taxes_total REAL,
            FOREIGN KEY (organization_id) REFERENCES organizations(id)
        );
        
        CREATE TABLE IF NOT EXISTS personnel_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization_id INTEGER,
            year INTEGER,
            total_employees INTEGER,
            avg_salary_moscow REAL,
            FOREIGN KEY (organization_id) REFERENCES organizations(id)
        );
    ''')
    
    # Добавляем тестовые данные
    cursor.execute('INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)', ('admin', 'admin'))
    cursor.execute('''
        INSERT OR IGNORE INTO organizations 
        (inn, short_name, full_name, status, legal_address, main_industry, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('7714431171', 'АО "СВОБОДА"', 'АКЦИОНЕРНОЕ ОБЩЕСТВО "СВОБОДА"', 
          'Действующая', '127015, г. Москва, ул. Вятская, д. 47 стр. 8', 
          'Химическая промышленность', 1))
    
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return jsonify({'status': 'success', 'user_id': user['id']})
    return jsonify({'status': 'fail'}), 401

@app.route('/api/providers', methods=['GET'])
def get_providers():
    """Получить список доступных провайдеров API"""
    return jsonify([{"id": key, "name": value["name"]} for key, value in API_PROVIDERS.items()])

@app.route('/api/user/organizations/<int:user_id>', methods=['GET'])
def get_user_organizations(user_id):
    """Получить организации пользователя"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM organizations WHERE user_id = ?', (user_id,))
    orgs = cursor.fetchall()
    conn.close()
    return jsonify([dict(org) for org in orgs])

@app.route('/api/organization/<int:org_id>', methods=['GET'])
def get_organization(org_id):
    """Получить полную информацию об организации с финансами и персоналом"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM organizations WHERE id=?', (org_id,))
    org = cursor.fetchone()
    
    if not org:
        conn.close()
        return jsonify({'error': 'Organization not found'}), 404
    
    org_data = dict(org)
    
    # Финансовые данные
    cursor.execute('SELECT * FROM financial_data WHERE organization_id=? ORDER BY year', (org_id,))
    org_data['financial_data'] = [dict(row) for row in cursor.fetchall()]
    
    # Данные о персонале
    cursor.execute('SELECT * FROM personnel_data WHERE organization_id=? ORDER BY year', (org_id,))
    org_data['personnel_data'] = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return jsonify(org_data)

@app.route('/api/organization/<int:org_id>', methods=['PUT'])
def update_organization(org_id):
    """Обновить данные организации"""
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    fields = []
    values = []
    org_fields = ['short_name', 'full_name', 'status', 'legal_address', 'director']
    
    for field in org_fields:
        if field in data:
            fields.append(f"{field}=?")
            values.append(data[field])
    
    if fields:
        values.append(org_id)
        cursor.execute(f"UPDATE organizations SET {', '.join(fields)} WHERE id=?", values)
        conn.commit()
    
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/parse', methods=['POST'])
def api_parse():
    """Парсинг текстовых данных через LLM"""
    raw_text = request.json.get('raw_text')
    if not raw_text:
        return jsonify({'error': 'No raw_text provided'}), 400
    
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        prompt_template = f.read()
    
    prompt = prompt_template.replace("{input_data}", raw_text)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY}"
    }
    
    payload = {
        "model": "gemma3:27b",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "stream": False
    }
    
    try:
        resp = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        result = resp.json()
        
        choices = result.get('choices', [])
        if not choices:
            raise ValueError("LLM response has no 'choices'")
        
        content = choices[0].get('message', {}).get('content', '')
        json_text = content.strip()
        
        # Убираем Markdown
        if json_text.startswith("```json"):
            json_text = json_text[7:]
        elif json_text.startswith("```"):
            json_text = json_text[3:]
        
        if json_text.endswith("```"):
            json_text = json_text[:-3]
        
        json_text = json_text.strip()
        parsed = json.loads(json_text)
        return jsonify(parsed)
        
    except json.JSONDecodeError as e:
        return jsonify({'error': f'JSON error: {e}', 'text': json_text}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/parse/pdf', methods=['POST'])
def api_parse_pdf():
    """Парсинг PDF файлов"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        # Парсим текст через LLM
        return parse_text_with_llm(text)
        
    except Exception as e:
        return jsonify({'error': f'PDF error: {str(e)}'}), 500

def parse_text_with_llm(text):
    """Вспомогательная функция парсинга текста"""
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        prompt_template = f.read()
    
    prompt = prompt_template.replace("{input_data}", text)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY}"
    }
    
    payload = {
        "model": "gemma3:27b",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "stream": False
    }
    
    try:
        resp = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        result = resp.json()
        
        content = result['choices'][0]['message']['content']
        json_text = content.strip()
        
        if json_text.startswith("```json"):
            json_text = json_text[7:]
        elif json_text.startswith("```"):
            json_text = json_text[3:]
        if json_text.endswith("```"):
            json_text = json_text[:-3]
        
        return jsonify(json.loads(json_text.strip()))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fns/search/<inn>', methods=['GET'])
def search_fns(inn):
    """Поиск по ФНС с выбором провайдера"""
    provider = request.args.get('provider', 'fns')
    
    if not inn.isdigit():
        return jsonify({'error': 'ИНН должен содержать только цифры'}), 400
    
    if provider == 'fns':
        params = {'q': inn, 'key': API_PROVIDERS['fns']['key'], 'filter': 'active'}
        headers = {"User-Agent": "Mozilla/5.0 (compatible; FNS API Client)"}
        
        try:
            response = requests.get(API_PROVIDERS['fns']['url'], params=params, 
                                  headers=headers, timeout=10)
            
            if response.status_code == 403:
                return jsonify({'error': '403 Forbidden'}), 403
            
            response.raise_for_status()
            data = response.json()
            
            if not data.get('items'):
                return jsonify({'error': 'Компания не найдена'}), 404
            
            return jsonify(data)
            
        except requests.exceptions.Timeout:
            return jsonify({'error': 'Timeout'}), 504
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Provider not implemented'}), 501

@app.route('/api/save', methods=['POST'])
def save_organization():
    """Сохранение организации в БД"""
    data = request.json
    user_id = data.get('user_id', 1)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO organizations 
            (inn, short_name, full_name, status, legal_address, production_address,
             main_industry, sub_industry, main_okved, registration_date, director,
             okrug, raion, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('inn'), data.get('short_name'), data.get('full_name'),
            data.get('status'), data.get('legal_address'), data.get('production_address'),
            data.get('main_industry'), data.get('sub_industry'), data.get('main_okved'),
            data.get('registration_date'), data.get('director'), data.get('okrug'),
            data.get('raion'), user_id
        ))
        
        org_id = cursor.lastrowid
        
        # Сохраняем финансы
        if 'financial_data' in data:
            for fin in data['financial_data']:
                cursor.execute('''
                    INSERT INTO financial_data 
                    (organization_id, year, revenue, net_profit, taxes_total)
                    VALUES (?, ?, ?, ?, ?)
                ''', (org_id, fin.get('year'), fin.get('revenue'), 
                     fin.get('net_profit'), fin.get('taxes_total')))
        
        # Сохраняем персонал
        if 'personnel_data' in data:
            for pers in data['personnel_data']:
                cursor.execute('''
                    INSERT INTO personnel_data 
                    (organization_id, year, total_employees, avg_salary_moscow)
                    VALUES (?, ?, ?, ?)
                ''', (org_id, pers.get('year'), pers.get('total_employees'),
                     pers.get('avg_salary_moscow')))
        
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'organization_id': org_id})
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8188, debug=False)
