import datetime
import logging
import random
import time
from functools import wraps

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
                        logger.exception(f"Function {func.__name__} failed after {retries} retries")
                        raise
                    sleep = (backoff_in_seconds * 2 ** x +
                             random.uniform(0, 1))
                    logger.warning(f"Retrying {func.__name__} in {sleep:.2f} seconds after error: {str(e)}")
                    time.sleep(sleep)
                    x += 1

        return wrapper

    return decorator


def find_matching_track(track, platform_client):
    try:
        # This is a simplified implementation. You may need to improve it based on the available data
        search_query = f"{track['name']} {' '.join(track['artists'])}"
        search_results = platform_client.search_tracks(search_query)

        if search_results:
            return search_results[0]
        logger.info(f"No matching track found for: {search_query}")
        return None
    except KeyError as e:
        logger.error(f"KeyError in find_matching_track: {str(e)}")
        return None
    except Exception as e:
        logger.exception(f"Error finding matching track: {str(e)}")
        return None


def get_current_timestamp():
    try:
        return datetime.datetime.now().isoformat()
    except Exception as e:
        logger.exception(f"Error getting current timestamp: {str(e)}")
        return None
