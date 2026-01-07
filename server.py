# ARQUIVO: server.py
# Este arquivo roda escondido em segundo plano, controlado pelo painel.
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import re
import threading
import uuid

app = Flask(__name__)
CORS(app)

# Caminho absoluto para garantir que funcione
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, 'downloads')

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

tasks = {}

def process_download_task(task_id, url, type_dl):
    tasks[task_id]['message'] = "Vídeo sendo baixado no servidor..."
    
    def progress_hook(d):
        if d['status'] == 'downloading':
            tasks[task_id]['message'] = "Baixando..."
        elif d['status'] == 'finished':
            tasks[task_id]['message'] = "Convertendo..."

    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
        'restrictfilenames': True,
        'noplaylist': True,
        'progress_hooks': [progress_hook],
    }

    if type_dl == 'audio':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        ydl_opts.update({'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'})

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if type_dl == 'audio':
                base, _ = os.path.splitext(filename)
                filename = base + '.mp3'
            
            clean_name = os.path.basename(filename)
            tasks[task_id]['status'] = 'completed'
            tasks[task_id]['filename'] = clean_name
            tasks[task_id]['download_url'] = f"/get-file/{clean_name}"
            
    except Exception as e:
        tasks[task_id]['status'] = 'error'
        tasks[task_id]['error'] = str(e)

@app.route('/queue', methods=['POST'])
def queue_download():
    data = request.json
    url = data.get('url')
    type_dl = data.get('type')
    if not url: return jsonify({"error": "No URL"}), 400
    task_id = str(uuid.uuid4())
    tasks[task_id] = {'status': 'processing', 'message': 'Iniciando...', 'filename': None}
    threading.Thread(target=process_download_task, args=(task_id, url, type_dl)).start()
    return jsonify({"task_id": task_id})

@app.route('/status/<task_id>', methods=['GET'])
def get_status(task_id):
    task = tasks.get(task_id)
    if not task: return jsonify({"error": "Task not found"}), 404
    return jsonify(task)

@app.route('/get-file/<filename>', methods=['GET'])
def get_file(filename):
    return send_file(os.path.join(DOWNLOAD_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    # Roda na porta 5000
    app.run(host='0.0.0.0', port=5000)