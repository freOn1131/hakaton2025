from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import requests
import json
from datetime import datetime

app = Flask(__name__)

# Параметры API и БД
FNS_API_URL = "https://api-fns.ru/api/search"
FNS_API_KEY = "c35fe9f432d553652e59bb7edfdcb4137f64cfe0"
LLM_API_URL = "http://10.250.12.109:8080/api/chat/completions"
LLM_API_KEY = "sk-8c3828c838c94a6ab0c04d0deee2f799"
LLM_MODEL = "gemma3:27b"
DB_PATH = "organizations.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def chat_completion(content, model=LLM_MODEL, temperature=0.7):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LLM_API_KEY}"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "temperature": temperature,
        "stream": False
    }
    resp = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()

@app.route('/api/parse_data', methods=['POST'])
def parse_data():
    data = request.json
    raw_data = data.get('raw_data', '')
    if not raw_data:
        return jsonify({"error": "Raw data is missing"}), 400

    with open('llm_prompt_template.txt', 'r', encoding='utf-8') as f:
        prompt_template = f.read()

    prompt = prompt_template.replace("{input_data}", raw_data)
    try:
        llm_response = chat_completion(prompt, temperature=0.3)
        content = llm_response['choices'][0]['message']['content']

        # Очистка ответа от markdown кода JSON
        if '```
            start = content.find('```json') + 7
            end = content.find('```
            content = content[start:end]
        elif '```' in content:
            start = content.find('```
            end = content.find('```', start)
            content = content[start:end]

        parsed_json = json.loads(content.strip())
        return jsonify(parsed_json)
    except Exception as e:
        return jsonify({"error": f"Failed to parse data: {str(e)}"}), 500

@app.route('/api/fns/search/inn/<inn>', methods=['GET'])
def fns_search_inn(inn):
    params = {"q": inn, "key": FNS_API_KEY}
    try:
        resp = requests.get(FNS_API_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data and 'items' in data and len(data['items']) > 0:
            return jsonify(data['items'][0])
        return jsonify({})
    except Exception as e:
        return jsonify({"error": f"FNS API error: {str(e)}"}), 500

@app.route('/api/fns/search/name', methods=['GET'])
def fns_search_name():
    name = request.args.get('name', '')
    if not name:
        return jsonify({"error": "Name parameter required"}), 400
    params = {"q": name, "key": FNS_API_KEY}
    try:
        resp = requests.get(FNS_API_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return jsonify(data.get('items', []))
    except Exception as e:
        return jsonify({"error": f"FNS API error: {str(e)}"}), 500

# Serving frontend files
@app.route('/')
def serve_index():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('frontend', path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
