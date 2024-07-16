import datetime
import logging

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
        self.login_future = None
        logger.info("Config loaded")
        self.login()
        logger.info("TidalClient initialization completed")

    def login(self, auth_code=None):
        try:
            logger.info("Starting Tidal login process")
            self.session = tidalapi.Session()

            if auth_code:
                logger.info("Auth code provided, completing OAuth flow")
                self.login_future = self.session.login_oauth(auth_code)
                login, future = self.login_future
                logger.info(f"OAuth login result: {login}")
                logger.info(f"OAuth future result: {future}")

                if not self.session.check_login():
                    logger.error("Failed to login to Tidal. Please check your credentials.")
                    return False

                self.store_session_data()
                logger.info("Tidal login successful")
            else:
                logger.info("No auth code provided, attempting to use stored token")
                if not self.load_token():
                    logger.warning("No valid stored token found")
                    self.login_future = self.get_auth_url()
                    return False

            return True
        except tidalapi.exceptions.AuthenticationError as e:
            logger.error(f"Tidal authentication failed: {str(e)}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error during Tidal authentication: {str(e)}")
            return False

    def get_auth_url(self):
        self.session = tidalapi.Session()
        self.login_future = self.session.login_oauth()
        logger.info(f"Tidal auth URL: {self.login_future[0].verification_uri_complete}")
        return self.login_future[0].verification_uri_complete

    def check_auth_status(self):
        if not hasattr(self, 'login_future') or self.login_future is None:
            logger.error("login_future is not initialized")
            self.login_future = self.get_auth_url()
            return 'pending'

        try:
            # Check if the login_future is a tuple (as returned by login_oauth)
            if isinstance(self.login_future, tuple) and len(self.login_future) == 2:
                login, future = self.login_future
                # Check if the future is done without blocking
                if future.done():
                    login_result = future.result()
                    if login_result:
                        self.session = login_result
                        expiry_time_str = self.session.expiry_time.isoformat() if self.session.expiry_time else None
                        self.db.store_token('tidal', self.session.access_token, expiry_time_str)
                        logger.info("Tidal login successful")
                        return 'success'
                    else:
                        logger.error("Tidal login failed")
                        return 'failed'
                else:
                    return 'pending'
            else:
                # If login_future is not a tuple, it's likely the auth URL
                return 'pending'
        except Exception as e:
            logger.error(f"Error checking Tidal auth status: {str(e)}")
            return 'failed'

    def store_session_data(self):
        if self.session and self.session.check_login():
            session_data = {
                'token_type': self.session.token_type,
                'access_token': self.session.access_token,
                'refresh_token': self.session.refresh_token,
                'expiry_time': self.session.expiry_time.isoformat() if self.session.expiry_time else None
            }
            self.db.store_token('tidal', str(session_data), session_data['expiry_time'])
            logger.info("Tidal session data stored successfully")
        else:
            logger.error("No valid Tidal session to store")

    def load_token(self):
        token, expires_at = self.db.get_token('tidal')
        if token and expires_at:
            try:
                session_data = eval(token)
                expires_at = datetime.datetime.fromisoformat(expires_at)
                if expires_at > datetime.datetime.now():
                    self.session = tidalapi.Session()
                    self.session.load_oauth_session(
                        session_data['token_type'],
                        session_data['access_token'],
                        session_data['refresh_token'],
                        expires_at
                    )
                    if self.session.check_login():
                        logger.info("Tidal token loaded from database")
                        return True
            except Exception as e:
                logger.warning(f"Failed to load stored token: {e}")
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

    def disconnect(self, platform):
        if platform == 'tidal':
            self.session = None
            self.login_future = None
            self.db.clear_cached_playlists('tidal')
            self.db.clear_cached_tracks('tidal')
            self.db.clear_token('tidal')
            logger.info("Tidal client disconnected and database records purged")
        else:
            logger.warning(f"Attempted to disconnect {platform} from TidalClient")
