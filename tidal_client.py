import tidalapi

class TidalClient:
    def __init__(self, config):
        self.session = tidalapi.Session()
        # Note: Tidal doesn't support OIDC, so we'll need to use login credentials
        self.session.login(config['tidal']['username'], config['tidal']['password'])

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
        playlist = self.session.user.create_playlist(name)
        return playlist.id

    def add_tracks_to_playlist(self, playlist_id, track_ids):
        playlist = self.session.playlist(playlist_id)
        tracks = [self.session.track(track_id) for track_id in track_ids]
        playlist.add(tracks)
