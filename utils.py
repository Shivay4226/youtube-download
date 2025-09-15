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
        'extractor_args': {
            'youtube': {
                'skip': ['dash', 'hls'],
                'player_skip': ['configs', 'webpage'],
                'player_client': ['android', 'web', 'tv_embedded'],
                'skip_manifests': True
            }
        },
        'http_headers': {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'Pragma': 'no-cache'
        },
        # Use mobile client to avoid bot detection
        'format_selector': None,
        'age_limit': None,
        'geo_bypass': True,
        'geo_bypass_country': 'US'
    }
    
    if output_path:
        options['outtmpl'] = output_path
    
    return options

def get_alternative_ydl_options(output_path=None):
    """Alternative yt-dlp options using different extraction method"""
    options = {
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios'],
                'skip': ['dash', 'hls', 'webpage'],
                'player_skip': ['configs', 'webpage', 'js']
            }
        },
        'http_headers': {
            'User-Agent': 'com.google.android.youtube/17.36.4 (Linux; U; Android 12; GB) gzip',
            'X-YouTube-Client-Name': '3',
            'X-YouTube-Client-Version': '17.36.4'
        },
        'format_selector': None,
        'age_limit': None
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
