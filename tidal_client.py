import logging
import tidalapi
from tidalapi.exceptions import AuthenticationError, TooManyRequests, ObjectNotFound

logger = logging.getLogger(__name__)


class PlaylistModificationError(Exception):
    pass


class TidalClient:
    def __init__(self, config):
        self.session = tidalapi.Session()
        self.config = config
        self.login()

    def login(self):
        try:
            login_success = self.session.login(self.config['tidal']['username'], self.config['tidal']['password'])
            if not login_success:
                raise AuthenticationError("Failed to login to Tidal. Please check your credentials.")
        except AuthenticationError as e:
            raise AuthenticationError(f"Tidal authentication failed: {str(e)}")

    def check_session(self):
        if not self.session.check_login():
            self.login()

    def get_playlists(self):
        playlists = self.session.user.playlists()
        return [{
            'id': playlist.id,
            'name': playlist.name,
            'tracks': playlist.num_tracks
        } for playlist in playlists]

    def get_playlist_tracks(self, playlist_id):
        playlist = self.session.playlist(playlist_id)
        tracks = playlist.tracks()
        return [{
            'id': track.id,
            'name': track.name,
            'artists': [artist.name for artist in track.artists],
            'album': track.album.name,
            'uri': f'tidal:track:{track.id}'
        } for track in tracks]

    def create_playlist(self, name):
        playlist = self.session.user.create_playlist(name, description="Created by Spotify-Tidal Sync")
        return playlist.id

    def add_tracks_to_playlist(self, playlist_id, track_ids):
        try:
            playlist = self.session.playlist(playlist_id)
            playlist.add(track_ids)
        except ObjectNotFound as e:
            raise PlaylistModificationError(f"Playlist or track not found: {str(e)}")
        except TooManyRequests as e:
            raise PlaylistModificationError(f"Too many requests to Tidal API: {str(e)}")
        except (ValueError, KeyError) as e:
            raise PlaylistModificationError(f"Invalid data when adding tracks to Tidal playlist: {str(e)}")
        except IOError as e:
            raise PlaylistModificationError(f"I/O error when adding tracks to Tidal playlist: {str(e)}")
        except Exception as e:
            logger.exception("Unexpected error when adding tracks to Tidal playlist")
            raise PlaylistModificationError(f"Unexpected error when adding tracks to Tidal playlist: {str(e)}")

    def remove_tracks_from_playlist(self, playlist_id, track_ids):
        try:
            playlist = self.session.playlist(playlist_id)
            for track_id in track_ids:
                playlist.remove_by_id(track_id)
        except ObjectNotFound as e:
            raise PlaylistModificationError(f"Playlist or track not found: {str(e)}")
        except TooManyRequests as e:
            raise PlaylistModificationError(f"Too many requests to Tidal API: {str(e)}")
        except (ValueError, KeyError) as e:
            raise PlaylistModificationError(f"Invalid data when removing tracks from Tidal playlist: {str(e)}")
        except IOError as e:
            raise PlaylistModificationError(f"I/O error when removing tracks from Tidal playlist: {str(e)}")
        except Exception as e:
            logger.exception("Unexpected error when removing tracks from Tidal playlist")
            raise PlaylistModificationError(f"Unexpected error when removing tracks from Tidal playlist: {str(e)}")

    def get_playlist_by_name(self, name):
        playlists = self.get_playlists()
        return next((p for p in playlists if p['name'] == name), None)

    def search_tracks(self, query):
        results = self.session.search('track', query)
        if results and results.tracks:
            track = results.tracks[0]
            return [{
                'id': track.id,
                'name': track.name,
                'artists': [artist.name for artist in track.artists],
                'album': track.album.name,
                'uri': f'tidal:track:{track.id}'
            }]
        return []
