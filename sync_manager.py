import utils
from database import Database
from spotify_client import SpotifyClient
from tidal_client import TidalClient, AuthenticationError, PlaylistModificationError

class SyncError(Exception):
    pass


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
        try:
            source_platform = 'spotify' if isinstance(playlist, dict) else 'tidal'
            target_platform = 'tidal' if source_platform == 'spotify' else 'spotify'

            source_client = self.spotify if source_platform == 'spotify' else self.tidal
            target_client = self.tidal if target_platform == 'tidal' else self.spotify

            # Get source playlist tracks
            source_tracks = source_client.get_playlist_tracks(playlist['id'])

            # Check if playlist exists on target platform
            target_playlist = next((p for p in target_client.get_playlists() if p['name'] == playlist['name']), None)

            if target_playlist is None:
                # Create playlist on target platform if it doesn't exist
                target_playlist_id = target_client.create_playlist(playlist['name'])
            else:
                target_playlist_id = target_playlist['id']

            # Get target playlist tracks
            target_tracks = target_client.get_playlist_tracks(target_playlist_id)

            # Find tracks to add and remove
            source_track_ids = set(track['id'] for track in source_tracks)
            target_track_ids = set(track['id'] for track in target_tracks)

            tracks_to_add = source_track_ids - target_track_ids
            tracks_to_remove = target_track_ids - source_track_ids

            # Add new tracks
            for track_id in tracks_to_add:
                track = next(track for track in source_tracks if track['id'] == track_id)
                matching_track = utils.find_matching_track(track, target_client)
                if matching_track:
                    target_client.add_tracks_to_playlist(target_playlist_id, [matching_track['id']])

            # Remove tracks
            for track_id in tracks_to_remove:
                track = next(track for track in target_tracks if track['id'] == track_id)
                target_client.remove_tracks_from_playlist(target_playlist_id, [track['id']])

            # Update cache
            self.db.cache_playlist(source_platform, playlist['id'], utils.get_current_timestamp())
            self.db.cache_playlist(target_platform, target_playlist_id, utils.get_current_timestamp())

        except (AuthenticationError, PlaylistModificationError) as e:
            print(f"Error syncing playlist {playlist['name']}: {str(e)}")
        except Exception as e:
            print(f"Unexpected error syncing playlist {playlist['name']}: {str(e)}")
