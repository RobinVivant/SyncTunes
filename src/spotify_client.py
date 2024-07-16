import logging
import threading
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler

import spotipy
from spotipy.oauth2 import SpotifyOAuth

import utils

logger = logging.getLogger(__name__)


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Authentication successful! You can close this window.")
        self.server.path = self.path


class SpotifyClient:
    def __init__(self, config):
        self.config = config
        self.sp = None
        self.authenticate()

    def authenticate(self):
        redirect_uri = "http://localhost:8888/callback"

        auth_manager = SpotifyOAuth(
            client_id=self.config['spotify']['client_id'],
            client_secret=self.config['spotify']['client_secret'],
            redirect_uri=redirect_uri,
            scope="playlist-read-private playlist-modify-private",
            open_browser=False
        )

        auth_url = auth_manager.get_authorize_url()
        webbrowser.open(auth_url)

        # Start local server to listen for the callback
        server = HTTPServer(('localhost', 8888), CallbackHandler)
        server_thread = threading.Thread(target=server.handle_request)
        server_thread.start()

        server_thread.join(timeout=60)  # Wait for a maximum of 60 seconds

        if server_thread.is_alive():
            server.shutdown()
            raise Exception("Spotify authentication timed out")

        # Parse the callback URL
        parsed_url = urllib.parse.urlparse(server.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        code = query_params.get('code', [None])[0]

        if code:
            try:
                token_info = auth_manager.get_access_token(code)
                self.sp = spotipy.Spotify(auth=token_info['access_token'])
                logger.info("Spotify authentication successful")
            except Exception as e:
                logger.error(f"Failed to get access token: {str(e)}")
                raise Exception(f"Failed to get access token: {str(e)}")
        else:
            logger.error("Failed to get authorization code")
            raise Exception("Failed to get authorization code")

    @utils.retry_with_backoff()
    def get_playlists(self):
        playlists = []
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
