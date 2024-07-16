from flask import Flask, render_template, request, jsonify
from sync_manager import SyncManager
from config import load_config

app = Flask(__name__)
config = load_config()
sync_manager = SyncManager(config)

@app.route('/')
def index():
    return render_template('index.html')

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

@app.route('/playlists', methods=['GET'])
def get_playlists():
    playlists = sync_manager.get_common_playlists()
    return jsonify(playlists), 200

if __name__ == '__main__':
    app.run(debug=True)
