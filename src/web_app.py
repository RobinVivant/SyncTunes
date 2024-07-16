import logging
from flask import Flask, render_template, request, jsonify, send_from_directory
from sync_manager import SyncManager
from config import load_config

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("Initializing Flask app")
app = Flask(__name__, static_folder='static')

logger.info("Loading configuration")
config = load_config()

logger.info("Initializing SyncManager")
sync_manager = SyncManager(config)

@app.route('/')
def index():
    logger.info("Rendering index page")
    return render_template('index.html')

@app.route('/static/<path:path>')
def send_static(path):
    logger.info(f"Serving static file: {path}")
    return send_from_directory('static', path)

@app.route('/spotify_playlists', methods=['GET'])
def get_spotify_playlists():
    logger.info("Fetching Spotify playlists")
    try:
        playlists = sync_manager.spotify.get_playlists()
        logger.info(f"Successfully fetched {len(playlists)} Spotify playlists")
        return jsonify(playlists), 200
    except Exception as e:
        logger.error(f"Error fetching Spotify playlists: {str(e)}")
        return jsonify({"error": "Failed to fetch Spotify playlists"}), 500

@app.route('/tidal_playlists', methods=['GET'])
def get_tidal_playlists():
    logger.info("Fetching Tidal playlists")
    try:
        playlists = sync_manager.tidal.get_playlists()
        logger.info(f"Successfully fetched {len(playlists)} Tidal playlists")
        return jsonify(playlists), 200
    except Exception as e:
        logger.error(f"Error fetching Tidal playlists: {str(e)}")
        return jsonify({"error": "Failed to fetch Tidal playlists"}), 500

@app.route('/sync', methods=['POST'])
def sync():
    logger.info("Received sync request")
    data = request.json
    if data.get('all'):
        logger.info("Syncing all playlists")
        sync_manager.sync_all_playlists()
        return jsonify({"message": "All playlists synced successfully"}), 200
    elif data.get('playlists'):
        logger.info(f"Syncing specific playlists: {data['playlists']}")
        sync_manager.sync_specific_playlists(data['playlists'])
        return jsonify({"message": "Specified playlists synced successfully"}), 200
    else:
        logger.warning("Invalid sync request")
        return jsonify({"error": "Invalid request"}), 400

@app.route('/sync_playlist', methods=['POST'])
def sync_playlist():
    logger.info("Received single playlist sync request")
    data = request.json
    source_platform = data.get('source_platform')
    target_platform = data.get('target_platform')
    playlist_id = data.get('playlist_id')
    
    if source_platform and target_platform and playlist_id:
        logger.info(f"Syncing playlist from {source_platform} to {target_platform}")
        result = sync_manager.sync_single_playlist(source_platform, target_platform, playlist_id)
        return jsonify(result), 200
    else:
        logger.warning("Invalid single playlist sync request")
        return jsonify({"error": "Invalid request"}), 400

@app.route('/spotify_auth', methods=['GET'])
def spotify_auth():
    logger.info("Initiating Spotify authentication")
    try:
        sync_manager.spotify.authenticate()
        logger.info("Spotify authentication successful")
        return jsonify({"message": "Spotify authentication successful"}), 200
    except Exception as e:
        logger.error(f"Spotify authentication failed: {str(e)}")
        return jsonify({"error": "Spotify authentication failed"}), 500

if __name__ == '__main__':
    logger.info("Starting Flask application")
    try:
        logger.info("About to start Flask app...")
        app.run(debug=True, use_reloader=False, host='localhost', port=5000)
        logger.info("Flask app has finished running.")
    except Exception as e:
        logger.error(f"Failed to start Flask application: {str(e)}")
