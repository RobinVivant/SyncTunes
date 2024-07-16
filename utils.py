import logging
from functools import wraps
import time
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_warning(message):
    logger.warning(message)

def retry_with_backoff(retries=3, backoff_in_seconds=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            x = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if x == retries:
                        raise
                    sleep = (backoff_in_seconds * 2 ** x +
                             random.uniform(0, 1))
                    time.sleep(sleep)
                    x += 1
        return wrapper
    return decorator

import datetime

def find_matching_track(track, platform_client):
    # This is a simplified implementation. You may need to improve it based on the available data
    search_query = f"{track['name']} {' '.join(track['artists'])}"
    search_results = platform_client.search_tracks(search_query)
    
    if search_results:
        return search_results[0]
    return None

def get_current_timestamp():
    return datetime.datetime.now().isoformat()
