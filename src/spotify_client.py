import datetime
import logging

import spotipy
from spotipy.oauth2 import SpotifyOAuth

import utils

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    pass


class SpotifyClient:
    def __init__(self, config, database):
        self.config = config
        self.db = database
        self.sp = None
        self.auth_manager = None
        self.token_info = None

    def authenticate(self, auth_code=None):
        redirect_uri = "http://localhost:8888/callback/spotify"

        self.auth_manager = SpotifyOAuth(
            client_id=self.config['spotify']['client_id'],
            client_secret=self.config['spotify']['client_secret'],
            redirect_uri=redirect_uri,
            scope="playlist-read-private playlist-modify-private",
            cache_handler=None,
            show_dialog=True
        )

        try:
            if auth_code:
                self.token_info = self.auth_manager.get_access_token(auth_code)
                if not self.token_info:
                    raise AuthenticationError("Failed to get access token")
                self.sp = spotipy.Spotify(auth=self.token_info['access_token'])
                self.save_token()
                logger.info("Spotify authentication successful")
            else:
                logger.info("No auth code provided, attempting to use stored token")
                if not self.load_token():
                    logger.warning("No valid stored token found")
                    return False
            return True
        except Exception as e:
            logger.error(f"Failed to get access token: {str(e)}")
            raise AuthenticationError(f"Failed to get access token: {str(e)}")

    def save_token(self):
        expires_at = datetime.datetime.fromtimestamp(self.token_info['expires_at'])
        self.db.store_token('spotify', self.token_info['access_token'], expires_at.isoformat())
        logger.info("Spotify token saved to database")

    def load_token(self):
        token, expires_at = self.db.get_token('spotify')
        if token and expires_at:
            expires_at = datetime.datetime.fromisoformat(expires_at)
            if expires_at > datetime.datetime.now():
                self.token_info = {'access_token': token, 'expires_at': expires_at.timestamp()}
                self.sp = spotipy.Spotify(auth=token)
                logger.info("Spotify token loaded from database")
                return True
        return False

    def get_auth_url(self):
        redirect_uri = "http://localhost:8888/callback/spotify"
        self.auth_manager = SpotifyOAuth(
            client_id=self.config['spotify']['client_id'],
            client_secret=self.config['spotify']['client_secret'],
            redirect_uri=redirect_uri,
            scope="playlist-read-private playlist-modify-private",
            cache_handler=None,
            show_dialog=True
        )
        return self.auth_manager.get_authorize_url()

    def disconnect(self, platform):
        if platform == 'spotify':
            self.sp = None
            self.auth_manager = None
            self.token_info = None
            self.db.clear_cached_playlists('spotify')
            self.db.clear_cached_tracks('spotify')
            self.db.clear_token('spotify')
            logger.info("Spotify client disconnected and database records purged")
        else:
            logger.warning(f"Attempted to disconnect {platform} from SpotifyClient")

    @utils.retry_with_backoff()
    def get_playlists(self):
        if not self.sp:
            self.authenticate()
        playlists = []
        try:
            results = self.sp.current_user_playlists()
            while results:
                for item in results['items']:
                    playlists.append({
                        'id': item['id'],
                        'name': item['name'],
                        'tracks': item['tracks']['total']
                    })
                if results['next']:
                    results = self.sp.next(results)
                else:
                    results = None
        except Exception as e:
            logger.error(f"Error fetching Spotify playlists: {str(e)}")
            raise
        return playlists

    def get_playlist_tracks(self, playlist_id):
        tracks = []
        results = self.sp.playlist_items(playlist_id, additional_types=('track',))
        while results:
            for item in results['items']:
                if item['track']:
                    track = item['track']
                    tracks.append({
                        'id': track['id'],
                        'name': track['name'],
                        'artists': [artist['name'] for artist in track['artists']],
                        'album': track['album']['name'],
                        'uri': track['uri']
                    })
            if results['next']:
                results = self.sp.next(results)
            else:
                results = None
        return tracks

    def get_playlist_by_name(self, name):
        playlists = self.get_playlists()
        return next((p for p in playlists if p['name'] == name), None)

    def search_tracks(self, query):
        try:
            results = self.sp.search(q=query, type='track', limit=1)
            if results and 'tracks' in results and 'items' in results['tracks'] and results['tracks']['items']:
                track = results['tracks']['items'][0]
                if track:
                    return [{
                        'id': track['id'],
                        'name': track['name'],
                        'artists': [artist['name'] for artist in track['artists']],
                        'album': track['album']['name'],
                        'uri': track['uri']
                    }]
            logger.info(f"No tracks found for query: {query}")
            return []
        except Exception as e:
            logger.error(f"Error searching for tracks: {str(e)}")
            return []

    def create_playlist(self, name):
        user_id = self.sp.me()['id']
        playlist = self.sp.user_playlist_create(user_id, name, public=False)
        return playlist['id']

    def add_tracks_to_playlist(self, playlist_id, track_uris):
        self.sp.playlist_add_items(playlist_id, track_uris)

    def remove_tracks_from_playlist(self, playlist_id, track_uris):
        self.sp.playlist_remove_all_occurrences_of_items(playlist_id, track_uris)
