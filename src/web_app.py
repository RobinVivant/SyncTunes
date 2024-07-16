from flask import Flask, render_template, request, jsonify
from sync_manager import SyncManager
from config import load_config

app = Flask(__name__)
config = load_config()
sync_manager = SyncManager(config)

@app.route('/')
def index():
    logger.info("Rendering index page")
    return render_template('index.html')

@app.route('/spotify_playlists', methods=['GET'])
def get_spotify_playlists():
    logger.info("Fetching Spotify playlists")
    playlists = sync_manager.spotify.get_playlists()
    return jsonify(playlists), 200

@app.route('/tidal_playlists', methods=['GET'])
def get_tidal_playlists():
    logger.info("Fetching Tidal playlists")
    playlists = sync_manager.tidal.get_playlists()
    return jsonify(playlists), 200

@app.route('/sync', methods=['POST'])
def sync():
    data = request.json
    if data.get('all'):
        sync_manager.sync_all_playlists()
        return jsonify({"message": "All playlists synced successfully"}), 200
    elif data.get('playlists'):
        sync_manager.sync_specific_playlists(data['playlists'])
        return jsonify({"message": "Specified playlists synced successfully"}), 200
    else:
        return jsonify({"error": "Invalid request"}), 400

@app.route('/spotify_playlists', methods=['GET'])
def get_spotify_playlists():
    playlists = sync_manager.spotify.get_playlists()
    return jsonify(playlists), 200

@app.route('/tidal_playlists', methods=['GET'])
def get_tidal_playlists():
    playlists = sync_manager.tidal.get_playlists()
    return jsonify(playlists), 200

@app.route('/sync_playlist', methods=['POST'])
def sync_playlist():
    data = request.json
    source_platform = data.get('source_platform')
    target_platform = data.get('target_platform')
    playlist_id = data.get('playlist_id')
    
    if source_platform and target_platform and playlist_id:
        result = sync_manager.sync_single_playlist(source_platform, target_platform, playlist_id)
        return jsonify(result), 200
    else:
        return jsonify({"error": "Invalid request"}), 400

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
