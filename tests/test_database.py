import unittest
import os
from src.database import Database

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.config = {'database': {'path': ':memory:'}}
        self.db = Database(self.config)

    @classmethod
    def setUpClass(cls):
        # Create a test configuration file
        with open('test_config.yaml', 'w') as f:
            f.write("""
            spotify:
              client_id: test_spotify_client_id
              client_secret: test_spotify_client_secret
            tidal:
              client_id: test_tidal_client_id
              client_secret: test_tidal_client_secret
            database:
              path: :memory:
            """)

    @classmethod
    def tearDownClass(cls):
        # Remove the test configuration file
        os.remove('test_config.yaml')

    def test_create_tables(self):
        cursor = self.db.conn.cursor()
        
        # Check if playlists table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='playlists'")
        self.assertIsNotNone(cursor.fetchone())
        
        # Check if tracks table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tracks'")
        self.assertIsNotNone(cursor.fetchone())

    def test_cache_playlist(self):
        self.db.cache_playlist('spotify', 'playlist_id', '2023-01-01T00:00:00')
        
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM playlists WHERE platform='spotify' AND playlist_id='playlist_id'")
        result = cursor.fetchone()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[2], '2023-01-01T00:00:00')

    def test_get_cached_playlist(self):
        self.db.cache_playlist('spotify', 'playlist_id', '2023-01-01T00:00:00')
        
        result = self.db.get_cached_playlist('spotify', 'playlist_id')
        self.assertEqual(result, '2023-01-01T00:00:00')
        
        result = self.db.get_cached_playlist('spotify', 'non_existent_id')
        self.assertIsNone(result)

    def test_cache_track(self):
        metadata = {'name': 'Track 1', 'artist': 'Artist 1'}
        self.db.cache_track('spotify', 'track_id', metadata)
        
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM tracks WHERE platform='spotify' AND track_id='track_id'")
        result = cursor.fetchone()
        
        self.assertIsNotNone(result)
        self.assertEqual(eval(result[2]), metadata)

    def test_get_cached_track(self):
        metadata = {'name': 'Track 1', 'artist': 'Artist 1'}
        self.db.cache_track('spotify', 'track_id', metadata)
        
        result = self.db.get_cached_track('spotify', 'track_id')
        self.assertEqual(result, metadata)
        
        result = self.db.get_cached_track('spotify', 'non_existent_id')
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
