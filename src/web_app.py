import logging

from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for

from config import load_config
from sync_manager import SyncManager

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("Initializing Flask app")
app = Flask(__name__, static_folder='static')

logger.info("Loading configuration")
config = load_config()
logger.info("Configuration loaded successfully")

logger.info("Flask app initialization complete")


def get_sync_manager():
    return SyncManager(config)


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
        sync_manager = get_sync_manager()
        if not sync_manager.spotify.sp:
            logger.info("Spotify client not authenticated, returning cached playlists")
            playlists = sync_manager.get_cached_playlists('spotify')
        else:
            playlists = sync_manager.refresh_playlists('spotify')
        logger.info(f"Successfully fetched {len(playlists)} Spotify playlists")
        return jsonify(playlists), 200
    except Exception as e:
        logger.error(f"Error fetching Spotify playlists: {str(e)}")
        return jsonify({"error": "Failed to fetch Spotify playlists"}), 500


@app.route('/tidal_playlists', methods=['GET'])
def get_tidal_playlists():
    logger.info("Fetching Tidal playlists")
    try:
        sync_manager = get_sync_manager()
        if not sync_manager.tidal.session:
            logger.info("Tidal client not authenticated, returning cached playlists")
            playlists = sync_manager.get_cached_playlists('tidal')
        else:
            playlists = sync_manager.refresh_playlists('tidal')
        logger.info(f"Successfully fetched {len(playlists)} Tidal playlists")
        return jsonify(playlists), 200
    except Exception as e:
        logger.error(f"Error fetching Tidal playlists: {str(e)}")
        return jsonify({"error": "Failed to fetch Tidal playlists"}), 500


@app.route('/refresh_playlists', methods=['POST'])
def refresh_playlists():
    logger.info("Refreshing playlists")
    data = request.json
    platform = data.get('platform')
    if platform not in ['spotify', 'tidal']:
        return jsonify({"error": "Invalid platform"}), 400
    try:
        sync_manager = get_sync_manager()
        playlists = sync_manager.refresh_playlists(platform)
        logger.info(f"Successfully refreshed {len(playlists)} {platform} playlists")
        return jsonify(playlists), 200
    except Exception as e:
        logger.error(f"Error refreshing {platform} playlists: {str(e)}")
        return jsonify({"error": f"Failed to refresh {platform} playlists"}), 500


@app.route('/sync', methods=['POST'])
def sync():
    logger.info("Received sync request")
    data = request.json
    sync_manager = get_sync_manager()
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
        sync_manager = get_sync_manager()
        result = sync_manager.sync_single_playlist(source_platform, target_platform, playlist_id)
        return jsonify(result), 200
    else:
        logger.warning("Invalid single playlist sync request")
        return jsonify({"error": "Invalid request"}), 400


@app.route('/spotify_auth', methods=['GET'])
def spotify_auth():
    logger.info("Initiating Spotify authentication")
    sync_manager = get_sync_manager()
    auth_url = sync_manager.spotify.get_auth_url()
    return redirect(auth_url)


@app.route('/tidal_auth', methods=['GET'])
def tidal_auth():
    logger.info("Initiating Tidal authentication")
    sync_manager = get_sync_manager()
    auth_url = "https://" + sync_manager.tidal.get_auth_url()
    logger.info(f"Tidal auth URL: {auth_url}")
    return jsonify({"auth_url": auth_url})


@app.route('/check_tidal_auth', methods=['GET'])
def check_tidal_auth():
    sync_manager = get_sync_manager()
    auth_status = sync_manager.tidal.check_auth_status()
    if auth_status == 'success':
        return jsonify({"status": "success"})
    elif auth_status == 'pending':
        return jsonify({"status": "pending"})
    else:
        return jsonify({"status": "failed"})


@app.route('/callback/spotify')
def spotify_callback():
    logger.info("Spotify callback received")
    code = request.args.get('code')
    sync_manager = get_sync_manager()
    try:
        sync_manager.spotify.authenticate(code)
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Spotify authentication failed: {str(e)}")
        return jsonify({"error": "Spotify authentication failed"}), 500




if __name__ == '__main__':
    logger.info("Starting Flask application")
    try:
        logger.info("About to start Flask app...")
        app.run(debug=True, use_reloader=False, host='localhost', port=5000, threaded=True)
        logger.info("Flask app has finished running.")
    except Exception as e:
        logger.error(f"Failed to start Flask application: {str(e)}")
