import logging
import threading
import time
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler

import tidalapi
from tidalapi.exceptions import AuthenticationError, TooManyRequests, ObjectNotFound

logger = logging.getLogger(__name__)


class PlaylistModificationError(Exception):
    pass


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Authentication successful! You can close this window.")
        self.server.path = self.path


class TidalClient:
    def __init__(self, config):
        logger.info("Initializing TidalClient")
        self.session = tidalapi.Session()
        logger.info("TidalAPI Session created")
        self.config = config
        logger.info("Config loaded")
        self.login()
        logger.info("TidalClient initialization completed")

    def login(self):
        try:
            logger.info("Starting Tidal login process")
            login, future = self.session.login_oauth()
            logger.info("OAuth login initiated")

            # Open the authorization URL in a web browser
            auth_url = login.verification_uri_complete
            print(f"\nPlease open this URL in your web browser if it doesn't open automatically:\n{auth_url}\n")
            webbrowser.open(auth_url)
            logger.info("Authorization URL provided to user")

            # Start local server to listen for the callback
            server = HTTPServer(('localhost', 8888), CallbackHandler)
            server_thread = threading.Thread(target=server.handle_request)
            server_thread.start()
            logger.info("Local server started to listen for callback")

            server_thread.join(timeout=60)  # Wait for a maximum of 60 seconds
            logger.info("Waiting for server thread to complete")

            if server_thread.is_alive():
                server.shutdown()
                logger.error("Tidal authentication timed out")
                raise AuthenticationError("Tidal authentication timed out")

            # Parse the callback URL
            parsed_url = urllib.parse.urlparse(server.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            logger.info("Callback URL parsed")

            # Check if the authentication was successful
            if 'code' in query_params:
                logger.info("Authorization code received, waiting for future result")
                future.result(timeout=30)  # Wait for a maximum of 30 seconds
                logger.info("Future result received")
            elif 'error' in query_params:
                logger.error(f"Failed to login to Tidal. Error: {query_params['error'][0]}")
                raise AuthenticationError(f"Failed to login to Tidal. Error: {query_params['error'][0]}")
            else:
                logger.error("Failed to login to Tidal. Authorization code not received.")
                raise AuthenticationError("Failed to login to Tidal. Authorization code not received.")

            if not self.session.check_login():
                logger.error("Failed to login to Tidal. Please check your credentials.")
                raise AuthenticationError("Failed to login to Tidal. Please check your credentials.")
            
            logger.info("Tidal login successful")
        except Exception as e:
            logger.exception(f"Tidal authentication failed: {str(e)}")
            raise AuthenticationError(f"Tidal authentication failed: {str(e)}")

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
