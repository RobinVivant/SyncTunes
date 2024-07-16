import unittest
from unittest.mock import patch, MagicMock
from spotify_client import SpotifyClient

class TestSpotifyClient(unittest.TestCase):
    def setUp(self):
        self.config = {
            'spotify': {
                'client_id': 'test_client_id',
                'client_secret': 'test_client_secret',
                'redirect_uri': 'test_redirect_uri'
            }
        }
        self.spotify_client = SpotifyClient(self.config)

    @patch('spotipy.Spotify')
    def test_get_playlists(self, mock_spotify):
        mock_spotify.return_value.current_user_playlists.return_value = {
            'items': [{'id': '1', 'name': 'Playlist 1', 'tracks': {'total': 10}}],
            'next': None
        }
        playlists = self.spotify_client.get_playlists()
        self.assertEqual(len(playlists), 1)
        self.assertEqual(playlists[0]['name'], 'Playlist 1')

    @patch('spotipy.Spotify')
    def test_get_playlist_tracks(self, mock_spotify):
        mock_spotify.return_value.playlist_items.return_value = {
            'items': [{'track': {'id': '1', 'name': 'Track 1', 'artists': [{'name': 'Artist 1'}], 'album': {'name': 'Album 1'}, 'uri': 'spotify:track:1'}}],
            'next': None
        }
        tracks = self.spotify_client.get_playlist_tracks('playlist_id')
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0]['name'], 'Track 1')

    @patch('spotipy.Spotify')
    def test_search_tracks(self, mock_spotify):
        mock_spotify.return_value.search.return_value = {
            'tracks': {'items': [{'id': '1', 'name': 'Track 1', 'artists': [{'name': 'Artist 1'}], 'album': {'name': 'Album 1'}, 'uri': 'spotify:track:1'}]}
        }
        tracks = self.spotify_client.search_tracks('query')
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0]['name'], 'Track 1')

if __name__ == '__main__':
    unittest.main()
