import sqlite3
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, config):
        try:
            self.conn = sqlite3.connect(config['database']['path'])
            self.create_tables()
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlists (
                platform TEXT,
                playlist_id TEXT,
                last_modified TEXT,
                PRIMARY KEY (platform, playlist_id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracks (
                platform TEXT,
                track_id TEXT,
                metadata TEXT,
                PRIMARY KEY (platform, track_id)
            )
        ''')
        self.conn.commit()

    def cache_playlist(self, platform, playlist_id, last_modified):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO playlists (platform, playlist_id, last_modified)
            VALUES (?, ?, ?)
        ''', (platform, playlist_id, last_modified))
        self.conn.commit()

    def get_cached_playlist(self, platform, playlist_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT last_modified FROM playlists
            WHERE platform = ? AND playlist_id = ?
        ''', (platform, playlist_id))
        result = cursor.fetchone()
        return result[0] if result else None

    def cache_track(self, platform, track_id, metadata):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO tracks (platform, track_id, metadata)
            VALUES (?, ?, ?)
        ''', (platform, track_id, str(metadata)))
        self.conn.commit()

    def get_cached_track(self, platform, track_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT metadata FROM tracks
            WHERE platform = ? AND track_id = ?
        ''', (platform, track_id))
        result = cursor.fetchone()
        return eval(result[0]) if result else None
