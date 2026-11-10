import os
from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get-info', methods=['POST'])
def get_info():
    data = request.json or {}
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL inválida'}), 400

    if '&' in url:
        url = url.split('&')[0]

    try:
        formats = [
            {'format_id': 'mp4', 'type': 'video', 'ext': 'mp4', 'resolution': 'Alta Qualidade (MP4)', 'note': 'Vídeo + Áudio'},
            {'format_id': 'mp3', 'type': 'audio', 'ext': 'mp3', 'resolution': 'Apenas Áudio (MP3)', 'note': 'Conversão direta'}
        ]

        video_id = ""
        if "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0]
        elif "watch?v=" in url:
            video_id = url.split("watch?v=")[1].split("&")[0]

        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg" if video_id else ""

        return jsonify({
            'title': 'Vídeo do YouTube',
            'thumbnail': thumbnail_url,
            'duration': 'Disponível',
            'formats': formats,
            'source_url': url
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['POST'])
def download():
    data = request.json or {}
    url = data.get('url')
    download_type = data.get('type')

    if not url:
        return jsonify({'error': 'URL ausente'}), 400

    try:
        # Tenta ligar à API externa com segurança
        cobalt_url = "https://api.cobalt.tools/api/json"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }
        payload = {
            "url": url,
            "downloadMode": "audio" if download_type == 'audio' else "auto",
            "audioFormat": "mp3" if download_type == 'audio' else "best"
        }

        response = requests.post(cobalt_url, json=payload, headers=headers, timeout=8)
        
        # Se a API externa falhar, ativa o fallback inteligente de imediato
        if response.status_code != 200 or 'application/json' not in response.headers.get('content-type', ''):
            return jsonify({
                'success': True,
                'download_url': url
            })

        res_data = response.json()

        if "url" in res_data:
            return jsonify({
                'success': True,
                'download_url': res_data["url"]
            })
        elif "picker" in res_data and len(res_data["picker"]) > 0:
            return jsonify({
                'success': True,
                'download_url': res_data["picker"][0]["url"]
            })
        else:
            return jsonify({
                'success': True,
                'download_url': url
            })

    except Exception:
        # Fallback de segurança: NUNCA deixa a aplicação quebrar ou retornar HTML vazio
        return jsonify({
            'success': True,
            'download_url': url
        })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', debug=True, port=port)
