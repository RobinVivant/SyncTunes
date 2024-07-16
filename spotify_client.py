import logging
import spotipy
from spotipy.oauth2 import SpotifyOAuth

import utils

logger = logging.getLogger(__name__)


class SpotifyClient:
    def __init__(self, config):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=config['spotify']['client_id'],
            client_secret=config['spotify']['client_secret'],
            redirect_uri=config['spotify']['redirect_uri'],
            scope="playlist-read-private playlist-modify-private"
        ))

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
                return [{
                    'id': track['id'],
                    'name': track['name'],
                    'artists': [artist['name'] for artist in track['artists']],
                    'album': track['album']['name'],
                    'uri': track['uri']
                }]
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
