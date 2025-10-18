from flask import Flask, request, jsonify, render_template, send_from_directory
import sqlite3
import requests
import json

app = Flask(__name__)

# Исправлена URL-адрес API FNS: убрана лишняя строка и пробелы
FNS_API_URL = "https://api-fns.ru/api/search"
FNS_API_KEY = "30f98ca92ed94f3774fde7930d237775639fd7b5"
LLM_API_URL = "http://10.250.12.109:8080/api/chat/completions"
LLM_API_KEY = "sk-8c3828c838c94a6ab0c04d0deee2f799"

DATABASE = 'organizations.db'
PROMPT_FILE = 'llm_prompt_template.txt'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

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
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'fail'}), 401

@app.route('/api/parse', methods=['POST'])
def api_parse():
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
        
        # Исправлен доступ к полю 'message' внутри 'choices'
        # Предполагается, что структура ответа LLM: {"choices": [{"message": {"content": "..."}}, ...]}
        # или {"choices": [{"delta": {"content": "..."}}, ...]} для stream или {"choices": [{"text": "..."}]}
        # Попробуем наиболее вероятную структуру для /chat/completions
        
        # Проверяем структуру ответа
        choices = result.get('choices', [])
        if not choices:
            raise ValueError("LLM response has no 'choices' field or it's empty")
        
        first_choice = choices[0]
        
        # Попробуем стандартную структуру chat completions
        content = first_choice.get('message', {}).get('content')
        if content is None:
            # Попробуем альтернативную структуру, например, если возвращается 'text'
             content = first_choice.get('text')
        if content is None:
             # Попробуем, если возвращается просто строка в 'content' на верхнем уровне choice
             content = first_choice.get('content')
        
        if content is None:
            raise ValueError(f"Could not extract content from LLM response: {result}")
        
        json_text = content.strip()

        # Убираем Markdown кодовые блоки (```json или ```)
        # Исправлены синтаксические ошибки в условиях и срезах
        if json_text.startswith("```json"):
            json_text = json_text[7:]  # Убираем "```json"
        elif json_text.startswith("```"):
            json_text = json_text[3:]  # Убираем "```"
        
        json_text = json_text.strip()
        
        if json_text.endswith("```"):
            json_text = json_text[:-3].strip() # Убираем завершающий "```"

        parsed = json.loads(json_text)
        return jsonify(parsed)
    except json.JSONDecodeError as e:
        # Добавлена проверка на ошибку парсинга JSON
        return jsonify({'error': f'JSON parsing error: {e}', 'received_text': json_text}), 500
    except Exception as e:
        return jsonify({'error': f'LLM parsing error: {e}'}), 500

@app.route('/api/fns/search/<inn>', methods=['GET'])
def search_fns(inn):
    params = {'q': inn, 'key': FNS_API_KEY}
    try:
        resp = requests.get(FNS_API_URL, params=params)
        resp.raise_for_status()
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({'error': f'FNS API error: {e}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8188, debug=False)
