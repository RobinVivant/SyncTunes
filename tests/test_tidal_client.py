import unittest
from unittest.mock import patch, MagicMock
from tidal_client import TidalClient, AuthenticationError, PlaylistModificationError

class TestTidalClient(unittest.TestCase):
    def setUp(self):
        self.config = {
            'tidal': {
                'username': 'test_username',
                'password': 'test_password'
            }
        }
        self.tidal_client = TidalClient(self.config)

    @patch('tidalapi.Session')
    def test_login_success(self, mock_session):
        mock_session.return_value.login.return_value = True
        self.tidal_client.login()
        mock_session.return_value.login.assert_called_once_with('test_username', 'test_password')

    @patch('tidalapi.Session')
    def test_login_failure(self, mock_session):
        mock_session.return_value.login.return_value = False
        with self.assertRaises(AuthenticationError):
            self.tidal_client.login()

    @patch('tidalapi.Session')
    def test_get_playlists(self, mock_session):
        mock_playlist = MagicMock()
        mock_playlist.id = '1'
        mock_playlist.name = 'Playlist 1'
        mock_playlist.num_tracks = 10
        mock_session.return_value.user.playlists.return_value = [mock_playlist]
        playlists = self.tidal_client.get_playlists()
        self.assertEqual(len(playlists), 1)
        self.assertEqual(playlists[0]['name'], 'Playlist 1')

    @patch('tidalapi.Session')
    def test_get_playlist_tracks(self, mock_session):
        mock_track = MagicMock()
        mock_track.id = '1'
        mock_track.name = 'Track 1'
        mock_track.artists = [MagicMock(name='Artist 1')]
        mock_track.album.name = 'Album 1'
        mock_session.return_value.playlist.return_value.tracks.return_value = [mock_track]
        tracks = self.tidal_client.get_playlist_tracks('playlist_id')
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0]['name'], 'Track 1')

    @patch('tidalapi.Session')
    def test_add_tracks_to_playlist(self, mock_session):
        self.tidal_client.add_tracks_to_playlist('playlist_id', ['track_id'])
        mock_session.return_value.playlist.return_value.add.assert_called_once_with(['track_id'])

    @patch('tidalapi.Session')
    def test_remove_tracks_from_playlist(self, mock_session):
        self.tidal_client.remove_tracks_from_playlist('playlist_id', ['track_id'])
        mock_session.return_value.playlist.return_value.remove_by_id.assert_called_once_with('track_id')

if __name__ == '__main__':
    unittest.main()
