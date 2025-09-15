import random
import time
from functools import wraps

# User agent rotation to avoid bot detection
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0'
]

def get_random_user_agent():
    """Get a random user agent to avoid bot detection"""
    return random.choice(USER_AGENTS)

def get_ydl_options(output_path=None):
    """Get yt-dlp options with aggressive anti-bot measures"""
    options = {
        'quiet': True,
        'no_warnings': True,
        'no_check_certificate': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'android'],
                'skip': ['hls', 'dash'],
                'innertube_host': 'youtubei.googleapis.com',
                'innertube_key': None,
                'check_formats': None
            }
        },
        'http_headers': {
            'User-Agent': 'com.google.ios.youtube/19.09.3 (iPhone14,3; U; CPU iOS 15_6 like Mac OS X)',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Origin': 'https://www.youtube.com',
            'X-YouTube-Client-Name': '5',
            'X-YouTube-Client-Version': '19.09.3'
        },
        'cookiefile': None,
        'extract_flat': False,
        'writethumbnail': False,
        'writeinfojson': False
    }
    
    if output_path:
        options['outtmpl'] = output_path
    
    return options

def get_alternative_ydl_options(output_path=None):
    """Alternative yt-dlp options using web client with minimal requests"""
    options = {
        'quiet': True,
        'no_warnings': True,
        'no_check_certificate': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['web'],
                'skip': ['hls', 'dash', 'live_chat'],
                'innertube_host': 'www.youtube.com',
                'innertube_key': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Referer': 'https://www.youtube.com/',
            'Origin': 'https://www.youtube.com'
        },
        'format': 'best[height<=720]/best',
        'extract_flat': False
    }
    
    if output_path:
        options['outtmpl'] = output_path
    
    return options

def get_fallback_ydl_options(output_path=None):
    """Fallback options with minimal configuration"""
    options = {
        'quiet': True,
        'no_warnings': True,
        'format': 'worst/best',
        'extractor_args': {
            'youtube': {
                'player_client': ['web'],
                'skip': ['hls', 'dash']
            }
        }
    }
    
    if output_path:
        options['outtmpl'] = output_path
    
    return options

def retry_with_backoff(max_retries=3, base_delay=1):
    """Decorator to retry function with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(delay)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
