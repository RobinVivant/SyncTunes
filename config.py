import os
from dotenv import load_dotenv

def load_config():
    load_dotenv()
    
    return {
        'spotify': {
            'client_id': os.getenv('SPOTIFY_CLIENT_ID'),
            'client_secret': os.getenv('SPOTIFY_CLIENT_SECRET'),
        },
        'tidal': {
            'client_id': os.getenv('TIDAL_CLIENT_ID'),
            'client_secret': os.getenv('TIDAL_CLIENT_SECRET'),
        },
        'database': {
            'path': os.getenv('DATABASE_PATH', 'spotify_tidal_sync.db'),
        }
    }
