import os
from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import imageio_ffmpeg
from urllib.parse import quote

# Configuração do caminho do FFmpeg
FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

app = Flask(__name__)
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), 'downloads')
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Caminho absoluto para o ficheiro de cookies
COOKIE_PATH = os.path.abspath('cookies.txt')

def limpar_pasta_downloads():
    try:
        for f in os.listdir(DOWNLOAD_FOLDER):
            file_path = os.path.join(DOWNLOAD_FOLDER, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
    except Exception as e:
        print(f"Erro na limpeza automática: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get-info', methods=['POST'])
def get_info():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL inválida'}), 400

    if '&' in url:
        url = url.split('&')[0]
    if '?' in url and 'watch?v=' not in url and 'youtu.be' in url:
        url = url.split('?')[0]

    ydl_opts = {
        'quiet': True,
        'extract_flat': False,
        'no_warnings': True,
        'ffmpeg_location': FFMPEG_PATH,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        }
    }

    # Só aplica os cookies se o ficheiro existir na raiz
    if os.path.exists(COOKIE_PATH):
        ydl_opts['cookiefile'] = COOKIE_PATH

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                'title': info.get('title'),
                'thumbnail': info.get('thumbnail'),
                'duration': info.get('duration_string', 'Desconhecida')
            })
    except Exception as e:
        print(f"Erro no backend (get_info): {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['POST'])
def download():
    limpar_pasta_downloads()

    data = request.json
    url = data.get('url')
    download_type = data.get('type', 'video')  # 'video' ou 'audio'

    if not url:
        return jsonify({'error': 'URL inválida'}), 400

    if '&' in url:
        url = url.split('&')[0]
    if '?' in url and 'watch?v=' not in url and 'youtu.be' in url:
        url = url.split('?')[0]

    output_template = os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s')
    
    if download_type == 'audio':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'ffmpeg_location': FFMPEG_PATH,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
                }
            },
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
    else:
        ydl_opts = {
            'format': 'bv*+ba/b',
            'outtmpl': output_template,
            'ffmpeg_location': FFMPEG_PATH,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
                }
            },
            'merge_output_format': 'mp4'
        }

    if os.path.exists(COOKIE_PATH):
        ydl_opts['cookiefile'] = COOKIE_PATH

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if download_type == 'audio':
                filename = os.path.splitext(filename)[0] + '.mp3'
            elif not filename.endswith('.mp4'):
                filename = os.path.splitext(filename)[0] + '.mp4'

            base_filename = os.path.basename(filename)
            safe_filename = base_filename.encode('ascii', 'ignore').decode('ascii')
            if not safe_filename.strip():
                safe_filename = "download_media.mp3" if download_type == 'audio' else "download_media.mp4"

            response = send_file(filename, as_attachment=True)
            response.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{quote(safe_filename)}"
            return response

    except Exception as e:
        print(f"Erro no download: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

hugs_app = app
