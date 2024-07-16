import logging

import utils
from database import Database
from spotify_client import SpotifyClient
from tidal_client import TidalClient, AuthenticationError, PlaylistModificationError

logger = logging.getLogger(__name__)


class SyncError(Exception):
    pass



class SyncManager:
    def __init__(self, config):
        logger.info("Initializing Database")
        self.db = Database(config)
        logger.info("Database initialized")

        logger.info("Initializing SpotifyClient")
        self.spotify = SpotifyClient(config, self.db)
        logger.info("SpotifyClient initialized")
        
        logger.info("Initializing TidalClient")
        self.tidal = TidalClient(config, self.db)
        logger.info("TidalClient initialized")

    def sync_all_playlists(self):
        spotify_playlists = self.spotify.get_playlists()
        tidal_playlists = self.tidal.get_playlists()

        self.db.cache_playlists('spotify', spotify_playlists)
        self.db.cache_playlists('tidal', tidal_playlists)

        for playlist in spotify_playlists + tidal_playlists:
            self.sync_playlist(playlist)

    def get_cached_playlists(self, platform):
        return self.db.get_cached_playlists(platform)

    def refresh_playlists(self, platform):
        if platform == 'spotify':
            playlists = self.spotify.get_playlists()
        elif platform == 'tidal':
            playlists = self.tidal.get_playlists()
        else:
            raise ValueError(f"Invalid platform: {platform}")

        self.db.cache_playlists(platform, playlists)
        return playlists

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

    def get_common_playlists(self):
        spotify_playlists = self.spotify.get_playlists()
        tidal_playlists = self.tidal.get_playlists()
        
        spotify_names = set(playlist['name'] for playlist in spotify_playlists)
        tidal_names = set(playlist['name'] for playlist in tidal_playlists)
        
        common_names = spotify_names.intersection(tidal_names)
        
        return list(common_names)

    def sync_single_playlist(self, source_platform, target_platform, playlist_id):
        source_client = self.spotify if source_platform == 'spotify' else self.tidal
        target_client = self.tidal if target_platform == 'tidal' else self.spotify

        playlist = next((p for p in source_client.get_playlists() if p['id'] == playlist_id), None)
        if not playlist:
            return {"error": "Playlist not found"}

        try:
            self.sync_playlist(playlist, source_platform)
            return {"message": f"Playlist '{playlist['name']}' synced successfully"}
        except SyncError as e:
            return {"error": str(e)}

    def sync_playlist(self, playlist, source_platform='spotify'):
        try:
            source_platform = 'spotify' if isinstance(playlist, dict) else 'tidal'
            target_platform = 'tidal' if source_platform == 'spotify' else 'spotify'

            source_client = self.spotify if source_platform == 'spotify' else self.tidal
            target_client = self.tidal if target_platform == 'tidal' else self.spotify

            # Get source playlist tracks
            try:
                source_tracks = source_client.get_playlist_tracks(playlist['id'])
            except Exception as e:
                logger.error(f"Error fetching tracks for playlist {playlist['name']} from {source_platform}: {str(e)}")
                return

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
                else:
                    logger.warning(f"No matching track found for {track['name']} by {', '.join(track['artists'])} on the target platform")

            # Remove tracks
            for track_id in tracks_to_remove:
                track = next(track for track in target_tracks if track['id'] == track_id)
                target_client.remove_tracks_from_playlist(target_playlist_id, [track['id']])

            # Update cache
            self.db.cache_playlist(source_platform, playlist['id'], utils.get_current_timestamp())
            self.db.cache_playlist(target_platform, target_playlist_id, utils.get_current_timestamp())

        except (AuthenticationError, PlaylistModificationError) as e:
            logger.error(f"Error syncing playlist {playlist['name']}: {str(e)}")
            raise SyncError(f"Error syncing playlist {playlist['name']}: {str(e)}")
        except (ValueError, KeyError) as e:
            logger.error(f"Data error syncing playlist {playlist['name']}: {str(e)}")
            raise SyncError(f"Data error syncing playlist {playlist['name']}: {str(e)}")
        except IOError as e:
            logger.error(f"I/O error syncing playlist {playlist['name']}: {str(e)}")
            raise SyncError(f"I/O error syncing playlist {playlist['name']}: {str(e)}")
        except Exception as e:
            logger.exception(f"Unexpected error syncing playlist {playlist['name']}: {str(e)}")
            raise SyncError(f"Unexpected error syncing playlist {playlist['name']}: {str(e)}")
