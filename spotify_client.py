import spotipy
from spotipy.oauth2 import SpotifyOAuth


class SpotifyClient:
    def __init__(self, config):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=config['spotify']['client_id'],
            client_secret=config['spotify']['client_secret'],
            redirect_uri=config['spotify']['redirect_uri'],
            scope="playlist-read-private playlist-modify-private"
        ))

    def get_playlists(self):
        results = self.sp.current_user_playlists()
        playlists = []
        for item in results['items']:
            playlists.append({
                'id': item['id'],
                'name': item['name'],
                'tracks': item['tracks']['total']
            })
        return playlists

    def get_playlist_tracks(self, playlist_id):
        results = self.sp.playlist_tracks(playlist_id)
        tracks = []
        for item in results['items']:
            track = item['track']
            tracks.append({
                'id': track['id'],
                'name': track['name'],
                'artists': [artist['name'] for artist in track['artists']],
                'album': track['album']['name'],
                'uri': track['uri']
            })
        return tracks

    def create_playlist(self, name):
        user_id = self.sp.me()['id']
        playlist = self.sp.user_playlist_create(user_id, name, public=False)
        return playlist['id']

    def add_tracks_to_playlist(self, playlist_id, track_uris):
        self.sp.playlist_add_items(playlist_id, track_uris)

    def remove_tracks_from_playlist(self, playlist_id, track_uris):
        self.sp.playlist_remove_all_occurrences_of_items(playlist_id, track_uris)
