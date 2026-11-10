import os
from flask import Flask, render_template, request, jsonify, send_file
import requests
import yt_dlp
import imageio_ffmpeg
from urllib.parse import quote

# Configuração do caminho do FFmpeg
FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

app = Flask(__name__)
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), 'downloads')
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Função para limpar arquivos antigos
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

    try:
        # Extração leve apenas para pegar o título real e a miniatura
        ydl_opts = {'quiet': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Vídeo do YouTube')

        formats = [
            {'format_id': 'mp4', 'type': 'video', 'ext': 'mp4', 'resolution': 'Alta Qualidade (MP4)', 'note': 'Vídeo + Áudio'},
            {'format_id': 'mp3', 'type': 'audio', 'ext': 'mp3', 'resolution': 'Apenas Áudio (MP3)', 'note': 'Conversão direta'}
        ]

        return jsonify({
            'title': title,
            'thumbnail': info.get('thumbnail', ''),
            'duration': info.get('duration_string', 'Desconhecida'),
            'formats': formats,
            'source_url': url
        })
    except Exception as e:
        # Fallback caso o yt-dlp dê bloqueio pontual na extração de título
        return jsonify({
            'title': 'Vídeo do YouTube',
            'thumbnail': '',
            'duration': 'Disponível',
            'formats': [
                {'format_id': 'mp4', 'type': 'video', 'ext': 'mp4', 'resolution': 'Alta Qualidade (MP4)', 'note': 'Vídeo + Áudio'},
                {'format_id': 'mp3', 'type': 'audio', 'ext': 'mp3', 'resolution': 'Apenas Áudio (MP3)', 'note': 'Conversão direta'}
            ],
            'source_url': url
        })

@app.route('/download', methods=['POST'])
def download():
    limpar_pasta_downloads()

    data = request.json
    url = data.get('url')
    download_type = data.get('type') # 'video' ou 'audio'

    if not url:
        return jsonify({'error': 'URL ausente'}), 400

    try:
        output_template = os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s')
        
        # Opção otimizada de download pontual
        if download_type == 'audio':
            ydl_opts = {
                'format': 'bestaudio',
                'outtmpl': output_template,
                'ffmpeg_location': FFMPEG_PATH,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
        else:
            ydl_opts = {
                'format': 'bestvideo+bestaudio/best',
                'outtmpl': output_template,
                'ffmpeg_location': FFMPEG_PATH,
                'merge_output_format': 'mp4'
            }

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
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', debug=True, port=port)
