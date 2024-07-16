import unittest
from unittest.mock import patch, MagicMock
from spotify_client import SpotifyClient

class TestSpotifyClient(unittest.TestCase):
    def setUp(self):
        self.config = {
            'spotify': {
                'client_id': 'test_client_id',
                'client_secret': 'test_client_secret',
                'redirect_uri': 'http://localhost:8888/callback'
            }
        }
        self.spotify_client = SpotifyClient(self.config)

    @patch('spotify_client.SpotifyOAuth')
    @patch('spotify_client.spotipy.Spotify')
    def test_authenticate(self, mock_spotify, mock_spotify_oauth):
        mock_auth_manager = MagicMock()
        mock_auth_manager.get_authorize_url.return_value = "http://example.com/auth"
        mock_auth_manager.get_access_token.return_value = {"access_token": "test_token"}
        mock_spotify_oauth.return_value = mock_auth_manager

        with patch('builtins.print'), patch('spotify_client.HTTPServer'), patch('threading.Thread'):
            self.spotify_client.authenticate()

        mock_spotify.assert_called_once_with(auth="test_token")

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

    @patch('spotipy.Spotify')
    def test_create_playlist(self, mock_spotify):
        mock_spotify.return_value.me.return_value = {'id': 'user_id'}
        mock_spotify.return_value.user_playlist_create.return_value = {'id': 'new_playlist_id'}
        playlist_id = self.spotify_client.create_playlist('New Playlist')
        self.assertEqual(playlist_id, 'new_playlist_id')

    @patch('spotipy.Spotify')
    def test_add_tracks_to_playlist(self, mock_spotify):
        self.spotify_client.add_tracks_to_playlist('playlist_id', ['track_uri_1', 'track_uri_2'])
        mock_spotify.return_value.playlist_add_items.assert_called_once_with('playlist_id', ['track_uri_1', 'track_uri_2'])

    @patch('spotipy.Spotify')
    def test_remove_tracks_from_playlist(self, mock_spotify):
        self.spotify_client.remove_tracks_from_playlist('playlist_id', ['track_uri_1', 'track_uri_2'])
        mock_spotify.return_value.playlist_remove_all_occurrences_of_items.assert_called_once_with('playlist_id', ['track_uri_1', 'track_uri_2'])

if __name__ == '__main__':
    unittest.main()
