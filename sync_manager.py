from spotify_client import SpotifyClient
from tidal_client import TidalClient
from database import Database
import utils

class SyncManager:
    def __init__(self, config):
        self.spotify = SpotifyClient(config)
        self.tidal = TidalClient(config)
        self.db = Database(config)

    def sync_all_playlists(self):
        spotify_playlists = self.spotify.get_playlists()
        tidal_playlists = self.tidal.get_playlists()
        
        for playlist in spotify_playlists + tidal_playlists:
            self.sync_playlist(playlist)

    def sync_specific_playlists(self, playlist_names):
        for name in playlist_names:
            spotify_playlist = self.spotify.get_playlist_by_name(name)
            tidal_playlist = self.tidal.get_playlist_by_name(name)
            
            if spotify_playlist:
                self.sync_playlist(spotify_playlist)
            elif tidal_playlist:
                self.sync_playlist(tidal_playlist)
            else:
                utils.log_warning(f"Playlist '{name}' not found on either platform")

    def sync_playlist(self, playlist):
        # Implement the sync logic here
        # This should handle bidirectional sync, last-edit-wins conflict resolution,
        # and creation of playlists if they don't exist on the other platform
        pass
