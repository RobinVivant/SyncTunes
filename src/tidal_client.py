import logging
import time
import datetime
import requests

import tidalapi
from tidalapi.exceptions import AuthenticationError, TooManyRequests, ObjectNotFound

logger = logging.getLogger(__name__)


class PlaylistModificationError(Exception):
    pass


class TidalClient:
    def __init__(self, config, database):
        logger.info("Initializing TidalClient")
        self.config = config
        self.db = database
        self.session = None
        logger.info("Config loaded")
        self.login()
        logger.info("TidalClient initialization completed")

    def login(self, auth_code=None):
        try:
            logger.info("Starting Tidal login process")
            self.session = tidalapi.Session()
            
            if auth_code:
                login_result = self.session.login_oauth(auth_code)
                
                if not login_result or not self.session.check_login():
                    logger.error("Failed to login to Tidal. Please check your credentials.")
                    raise AuthenticationError("Failed to login to Tidal. Please check your credentials.")
                
                self.db.store_token('tidal', self.session.access_token, self.session.expiry_time.isoformat())
                logger.info("Tidal login successful")
            else:
                logger.info("No auth code provided, attempting to use stored token")
                if not self.load_token():
                    logger.warning("No valid stored token found")
                    return False
            
            return True
        except tidalapi.exceptions.AuthenticationError as e:
            logger.error(f"Tidal authentication failed: {str(e)}")
            raise AuthenticationError(f"Tidal authentication failed: {str(e)}")
        except Exception as e:
            logger.exception(f"Unexpected error during Tidal authentication: {str(e)}")
            raise AuthenticationError(f"Unexpected error during Tidal authentication: {str(e)}")

    def get_auth_url(self):
        self.session = tidalapi.Session()
        login, _ = self.session.login_oauth()
        return login.verification_uri_complete.replace('localhost', '127.0.0.1')

    def load_token(self):
        token, expires_at = self.db.get_token('tidal')
        if token and expires_at:
            expires_at = datetime.datetime.fromisoformat(expires_at)
            if expires_at > datetime.datetime.now():
                self.session = tidalapi.Session()
                try:
                    self.session.load_oauth_session(token, expires_at.isoformat())
                    if self.session.check_login():
                        logger.info("Tidal token loaded from database")
                        return True
                except requests.exceptions.HTTPError as e:
                    logger.warning(f"Stored token failed: {e}.")
        return False

    def check_session(self):
        if not self.session.check_login():
            self.login()

    def get_playlists(self):
        self.check_session()
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
        playlist = self.session.user.create_playlist(name, "Created by Spotify-Tidal Sync")
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
        try:
            results = self.session.search('track', query)
            if results and hasattr(results, 'tracks') and results.tracks:
                track = results.tracks[0]
                return [{
                    'id': track.id,
                    'name': track.name,
                    'artists': [artist.name for artist in track.artists],
                    'album': track.album.name,
                    'uri': f'tidal:track:{track.id}'
                }]
            return []
        except Exception as e:
            logger.error(f"Error searching for tracks: {str(e)}")
            return []
