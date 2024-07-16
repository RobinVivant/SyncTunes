import unittest
from unittest.mock import patch, MagicMock
from sync_manager import SyncManager

class TestSyncManager(unittest.TestCase):
    def setUp(self):
        self.config = {
            'spotify': {},
            'tidal': {},
            'database': {'path': ':memory:'}
        }
        self.sync_manager = SyncManager(self.config)

    @patch('sync_manager.SpotifyClient')
    @patch('sync_manager.TidalClient')
    def test_sync_all_playlists(self, mock_tidal, mock_spotify):
        mock_spotify.return_value.get_playlists.return_value = [{'id': '1', 'name': 'Playlist 1'}]
        mock_tidal.return_value.get_playlists.return_value = [{'id': '2', 'name': 'Playlist 2'}]
        
        with patch.object(self.sync_manager, 'sync_playlist') as mock_sync_playlist:
            self.sync_manager.sync_all_playlists()
            self.assertEqual(mock_sync_playlist.call_count, 2)

    @patch('sync_manager.SpotifyClient')
    @patch('sync_manager.TidalClient')
    def test_sync_specific_playlists(self, mock_tidal, mock_spotify):
        mock_spotify.return_value.get_playlist_by_name.return_value = {'id': '1', 'name': 'Playlist 1'}
        mock_tidal.return_value.get_playlist_by_name.return_value = None
        
        with patch.object(self.sync_manager, 'sync_playlist') as mock_sync_playlist:
            self.sync_manager.sync_specific_playlists(['Playlist 1'])
            mock_sync_playlist.assert_called_once()

    @patch('sync_manager.SpotifyClient')
    @patch('sync_manager.TidalClient')
    def test_sync_playlist(self, mock_tidal, mock_spotify):
        playlist = {'id': '1', 'name': 'Playlist 1'}
        mock_spotify.return_value.get_playlist_tracks.return_value = [
            {'id': '1', 'name': 'Track 1', 'artists': ['Artist 1'], 'album': 'Album 1'}
        ]
        mock_tidal.return_value.get_playlist_tracks.return_value = []
        mock_tidal.return_value.create_playlist.return_value = '2'
        
        self.sync_manager.sync_playlist(playlist)
        
        mock_tidal.return_value.create_playlist.assert_called_once_with('Playlist 1')
        mock_tidal.return_value.add_tracks_to_playlist.assert_called_once()

if __name__ == '__main__':
    unittest.main()
