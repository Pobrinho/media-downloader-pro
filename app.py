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
        'cookiefile': COOKIES_PATH if os.path.exists(COOKIES_PATH) else None
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = yt_dlp.YoutubeDL({'quiet': True, 'cookiefile': COOKIES_PATH if os.path.exists(COOKIES_PATH) else None}).extract_info(url, download=False)
            
            formats = []
            seen_res = set()
            
            for f in info.get('formats', []):
                vcodec = f.get('vcodec', 'none')
                acodec = f.get('acodec', 'none')
                ext = f.get('ext')
                format_note = f.get('format_note', '')
                
                # Filtrar apenas áudios úteis
                if vcodec == 'none' and acodec != 'none':
                    abr = f.get('abr', 'N/A')
                    formats.append({
                        'format_id': f.get('format_id'),
                        'type': 'audio',
                        'ext': ext,
                        'resolution': f'Áudio ({abr} kbps)',
                        'note': f'Áudio puro ({ext})'
                    })
                # Filtrar vídeos válidos com resolução
                elif vcodec != 'none' and f.get('height'):
                    height = f.get('height')
                    res = f"{height}p"
                    if res not in seen_res and ext in ['mp4', 'webm']:
                        seen_res.add(res)
                        formats.append({
                            'format_id': f.get('format_id'),
                            'type': 'video',
                            'ext': ext,
                            'resolution': res,
                            'note': f"{format_note or 'Vídeo'} ({ext})"
                        })

            # Se por acaso a lista ficar vazia, adiciona um fallback seguro
            if not formats:
                formats.append({
                    'format_id': 'best',
                    'type': 'video',
                    'ext': 'mp4',
                    'resolution': 'Melhor Qualidade',
                    'note': 'Automático (mp4)'
                })

            return jsonify({
                'title': info.get('title'),
                'thumbnail': info.get('thumbnail'),
                'duration': info.get('duration_string', 'Desconhecida'),
                'formats': formats
            })
    except Exception as e:
        print(f"Erro no backend (get_info): {str(e)}")
        return jsonify({'error': str(e)}), 500
