# backend.py
import sqlite3
from flask import Flask, request, jsonify
import requests
import json
import threading
from datetime import datetime

app = Flask(__name__)

# Конфигурация API
FNS_API_URL = "https://api-fns.ru/api/search"
FNS_API_KEY = "c35fe9f432d553652e59bb7edfdcb4137f64cfe0"
LLM_API_URL = "http://10.250.12.109:8080/api/chat/completions"
LLM_API_KEY = "sk-8c3828c838c94a6ab0c04d0deee2f799"

# подключение к базе
def get_db():
    conn = sqlite3.connect('organizations.db')
    conn.row_factory = sqlite3.Row
    return conn

# Инициализация базы (при старте)
def init_db():
    conn = get_db()
    cursor = conn.cursor()
    # Создания таблиц (если не существует)
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
        raion TEXT
    );
    ''')
    # Админ по умолчанию
    cursor.execute('INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)', ('admin', 'admin'))
    conn.commit()
    conn.close()

init_db()

# API для входа
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
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'fail'}), 401

# API для получения данных организации
@app.route('/api/organization/<int:org_id>', methods=['GET'])
def get_organization(org_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM organizations WHERE id=?', (org_id,))
    org = cursor.fetchone()
    conn.close()
    if org:
        return jsonify(dict(org))
    return jsonify({'error': 'Not found'}), 404

# API для парсинга данных через нейросеть
def parse_data(text):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY}"
    }
    prompt = """""" + """
    {prompt_template}
    """ + """"""
    )
    payload = {
        "model": "gemma3:27b",
        "messages": [{"role": "user", "content": prompt.format(input_data=text)}],
        "temperature": 0.3
    }
    response = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=60)
    if response.status_code == 200:
        result = response.json()
        try:
            json_text = result['choices'][0]['message']['content']
            # extract JSON part
            json_part = json_text.strip()
            return json.loads(json_part)
        except:
            return None
    return None

@app.route('/api/parse', methods=['POST'])
def api_parse():
    data = request.json
    raw_text = data.get('raw_text')
    parsed = parse_data(raw_text)
    if parsed:
        return jsonify(parsed)
    else:
        return jsonify({'error': 'Parsing failed'}), 400

# API для поиска по ФНС
@app.route('/api/fns/search/<inn>', methods=['GET'])
def search_fns(inn):
    params = {'q': inn, 'key': FNS_API_KEY}
    resp = requests.get(FNS_API_URL, params=params)
    return jsonify(resp.json())

# Запуск сервера
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
