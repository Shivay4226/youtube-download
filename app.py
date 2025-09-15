from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import yt_dlp
import os
import tempfile
import json
import logging
import time
from urllib.parse import urlparse
import urllib.parse
from config import config
from functools import wraps
from collections import defaultdict, deque
from utils import get_ydl_options, retry_with_backoff

# Initialize Flask app
app = Flask(__name__)

# Load configuration
config_name = os.environ.get('FLASK_ENV', 'production')
app.config.from_object(config[config_name])

# Configure CORS
CORS(app, origins=app.config['CORS_ORIGINS'])

# Configure logging
logging.basicConfig(
    level=getattr(logging, app.config['LOG_LEVEL']),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Simple rate limiting
rate_limit_storage = defaultdict(lambda: deque())

def rate_limit(max_requests=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if max_requests is None:
                limit = app.config['RATE_LIMIT']
            else:
                limit = max_requests
                
            client_ip = request.remote_addr
            now = time.time()
            minute_ago = now - 60
            
            # Clean old requests
            while rate_limit_storage[client_ip] and rate_limit_storage[client_ip][0] < minute_ago:
                rate_limit_storage[client_ip].popleft()
            
            # Check rate limit
            if len(rate_limit_storage[client_ip]) >= limit:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
            
            # Add current request
            rate_limit_storage[client_ip].append(now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Create downloads directory if it doesn't exist
DOWNLOADS_DIR = os.path.join(os.getcwd(), 'downloads')
if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

# Security headers middleware
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    return response

# Error handlers
@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 error: {request.url}")
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(429)
def rate_limit_error(error):
    return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'version': '1.0.0'
    })

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'message': 'YouTube Downloader API',
        'version': '1.0.0',
        'endpoints': {
            'health': '/health',
            'video_info': '/api/video-info',
            'download': '/api/download',
            'downloads': '/api/downloads'
        }
    })

@app.route('/api/video-info', methods=['POST', 'OPTIONS'])
@rate_limit(5)  # 5 requests per minute for video info
def get_video_info():
    """Get video information including available qualities and languages"""
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        logger.info(f"Video info request for URL: {url[:50]}...")  # Log first 50 chars
        
        # Get anti-bot yt-dlp options
        ydl_opts = get_ydl_options()
        
        @retry_with_backoff(max_retries=3, base_delay=2)
        def extract_info_with_retry():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        
        # Extract video info with retry mechanism
        info = extract_info_with_retry()
        
        # Get available video formats
        video_streams = []
        audio_streams = []
        
        for fmt in info.get('formats', []):
            # Video formats (including adaptive streams)
            if fmt.get('vcodec') != 'none' and fmt.get('height'):
                video_streams.append({
                    'format_id': fmt.get('format_id'),
                    'resolution': f"{fmt.get('height')}p" if fmt.get('height') else 'N/A',
                    'fps': fmt.get('fps'),
                    'file_size': fmt.get('filesize') or fmt.get('filesize_approx', 0),
                    'ext': fmt.get('ext'),
                    'quality': fmt.get('format_note', ''),
                    'vcodec': fmt.get('vcodec', ''),
                    'acodec': fmt.get('acodec', ''),
                    'tbr': fmt.get('tbr')
                })
            
            # Audio formats
            if fmt.get('acodec') != 'none' and fmt.get('vcodec') == 'none':
                audio_streams.append({
                    'format_id': fmt.get('format_id'),
                    'quality': fmt.get('format_note', ''),
                    'file_size': fmt.get('filesize') or fmt.get('filesize_approx', 0),
                    'ext': fmt.get('ext'),
                    'acodec': fmt.get('acodec', ''),
                    'abr': fmt.get('abr')
                })
        
        # Get available captions
        captions = []
        if info.get('subtitles'):
            for lang_code, subs in info.get('subtitles', {}).items():
                captions.append({
                    'code': lang_code,
                    'name': lang_code.upper(),
                    'language': lang_code
                })
        
        video_info = {
            'title': info.get('title', 'Unknown'),
            'uploader': info.get('uploader', 'Unknown'),
            'duration': info.get('duration', 0),
            'view_count': info.get('view_count', 0),
            'like_count': info.get('like_count', 0),
            'description': (info.get('description', '')[:500] + '...') if len(info.get('description', '')) > 500 else info.get('description', ''),
            'thumbnail_url': info.get('thumbnail', ''),
            'video_streams': video_streams[:15],
            'audio_streams': audio_streams[:8],
            'captions': captions
        }
        
        return jsonify(video_info)
    
    except Exception as e:
        logger.error(f"Error in get_video_info: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download', methods=['POST', 'OPTIONS'])
@rate_limit(3)  # 3 downloads per minute per IP
def download_video():
    """Download video with specified quality and options"""
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        url = data.get('url')
        download_type = data.get('type', 'video')  # 'video' or 'audio'
        quality = data.get('quality')  # format_id for specific stream
        include_captions = data.get('include_captions', False)
        caption_language = data.get('caption_language', 'en')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        logger.info(f"Download request for URL: {url[:50]}...")  # Log first 50 chars
        
        # Get anti-bot yt-dlp options
        ydl_opts = get_ydl_options(os.path.join(DOWNLOADS_DIR, '%(title)s.%(ext)s'))
        
        if download_type == 'audio':
            # Audio download options
            if quality:
                ydl_opts['format'] = quality
            else:
                ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['outtmpl'] = os.path.join(DOWNLOADS_DIR, '%(title)s_audio.%(ext)s')
        else:
            # Video download options
            if quality:
                # For adaptive streams, combine video and audio
                ydl_opts['format'] = f'{quality}+bestaudio/best'
            else:
                # Get best quality available (up to 4K)
                ydl_opts['format'] = 'best[height<=2160]/bestvideo[height<=2160]+bestaudio/best'
            
            # Download subtitles if requested
            if include_captions:
                ydl_opts['writesubtitles'] = True
                ydl_opts['writeautomaticsub'] = True
                ydl_opts['subtitleslangs'] = [caption_language]
                ydl_opts['subtitlesformat'] = 'srt'
        
        # Use temporary directory for download
        import tempfile
        temp_dir = tempfile.mkdtemp()
        temp_ydl_opts = ydl_opts.copy()
        temp_ydl_opts['outtmpl'] = os.path.join(temp_dir, '%(title)s.%(ext)s')
        
        with yt_dlp.YoutubeDL(temp_ydl_opts) as ydl:
            # Get info first to determine filename
            info = ydl.extract_info(url, download=False)
            safe_title = "".join(c for c in info['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            
            # Download to temporary directory
            ydl.download([url])
            
            # Find the downloaded file in temp directory
            downloaded_files = []
            for file in os.listdir(temp_dir):
                if safe_title.lower() in file.lower():
                    downloaded_files.append(file)
            
            if not downloaded_files:
                # Fallback: find the most recent file
                files = [(f, os.path.getctime(os.path.join(temp_dir, f))) 
                        for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))]
                if files:
                    downloaded_files = [max(files, key=lambda x: x[1])[0]]
            
            if not downloaded_files:
                return jsonify({'error': 'Download completed but file not found'}), 500
            
            main_file = downloaded_files[0]
            temp_filepath = os.path.join(temp_dir, main_file)
            
            # Stream file directly without storing on server
            def generate():
                try:
                    with open(temp_filepath, 'rb') as f:
                        while True:
                            data = f.read(4096)
                            if not data:
                                break
                            yield data
                finally:
                    # Clean up temp files after streaming
                    import shutil
                    try:
                        shutil.rmtree(temp_dir)
                    except:
                        pass
            
            # Get file size for Content-Length header
            file_size = os.path.getsize(temp_filepath)
            
            # Determine MIME type based on file extension
            ext = os.path.splitext(main_file)[1].lower()
            mime_types = {
                '.mp4': 'video/mp4',
                '.webm': 'video/webm',
                '.mkv': 'video/x-matroska',
                '.mp3': 'audio/mpeg',
                '.m4a': 'audio/mp4',
                '.opus': 'audio/opus',
                '.srt': 'text/plain'
            }
            mime_type = mime_types.get(ext, 'application/octet-stream')
            
            # Safely encode filename for Content-Disposition header
            try:
                # Try to encode as ASCII first
                safe_filename = main_file.encode('ascii').decode('ascii')
                content_disposition = f'attachment; filename="{safe_filename}"'
            except UnicodeEncodeError:
                # Use RFC 5987 encoding for non-ASCII characters
                encoded_filename = urllib.parse.quote(main_file.encode('utf-8'))
                content_disposition = f"attachment; filename*=UTF-8''{encoded_filename}"
            
            response = Response(
                generate(),
                mimetype=mime_type,
                headers={
                    'Content-Disposition': content_disposition,
                    'Content-Length': str(file_size),
                    'Cache-Control': 'no-cache'
                }
            )
            return response
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-file/<filename>', methods=['GET'])
def download_file(filename):
    """Stream downloaded files to user's browser"""
    try:
        # URL decode the filename
        decoded_filename = urllib.parse.unquote(filename)
        filepath = os.path.join(DOWNLOADS_DIR, decoded_filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        def generate():
            with open(filepath, 'rb') as f:
                while True:
                    data = f.read(4096)  # Read in chunks
                    if not data:
                        break
                    yield data
        
        # Get file size for Content-Length header
        file_size = os.path.getsize(filepath)
        
        # Determine MIME type based on file extension
        ext = os.path.splitext(decoded_filename)[1].lower()
        mime_types = {
            '.mp4': 'video/mp4',
            '.webm': 'video/webm',
            '.mkv': 'video/x-matroska',
            '.mp3': 'audio/mpeg',
            '.m4a': 'audio/mp4',
            '.opus': 'audio/opus',
            '.srt': 'text/plain'
        }
        mime_type = mime_types.get(ext, 'application/octet-stream')
        
        # Safely encode filename for Content-Disposition header
        try:
            # Try to encode as ASCII first
            safe_filename = decoded_filename.encode('ascii').decode('ascii')
            content_disposition = f'attachment; filename="{safe_filename}"'
        except UnicodeEncodeError:
            # Use RFC 5987 encoding for non-ASCII characters
            encoded_filename = urllib.parse.quote(decoded_filename.encode('utf-8'))
            content_disposition = f"attachment; filename*=UTF-8''{encoded_filename}"
        
        response = Response(
            generate(),
            mimetype=mime_type,
            headers={
                'Content-Disposition': content_disposition,
                'Content-Length': str(file_size),
                'Cache-Control': 'no-cache'
            }
        )
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/downloads', methods=['GET'])
def list_downloads():
    """List all downloaded files"""
    try:
        files = []
        if os.path.exists(DOWNLOADS_DIR):
            for filename in os.listdir(DOWNLOADS_DIR):
                filepath = os.path.join(DOWNLOADS_DIR, filename)
                if os.path.isfile(filepath):
                    files.append({
                        'filename': filename,
                        'size': os.path.getsize(filepath),
                        'modified': os.path.getmtime(filepath)
                    })
        # Sort by modification time (newest first) and limit to recent 20 files
        files.sort(key=lambda x: x['modified'], reverse=True)
        return jsonify({'files': files[:20], 'total_count': len(files)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear-downloads', methods=['POST', 'OPTIONS'])
def clear_downloads():
    """Clear all downloaded files"""
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        if os.path.exists(DOWNLOADS_DIR):
            for filename in os.listdir(DOWNLOADS_DIR):
                filepath = os.path.join(DOWNLOADS_DIR, filename)
                if os.path.isfile(filepath):
                    os.remove(filepath)
        return jsonify({'success': True, 'message': 'All downloads cleared'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete-file/<filename>', methods=['DELETE', 'OPTIONS'])
def delete_file(filename):
    """Delete a specific downloaded file"""
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        filepath = os.path.join(DOWNLOADS_DIR, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({'success': True, 'message': f'File {filename} deleted'})
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )
