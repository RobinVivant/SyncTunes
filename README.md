# Spotify-Tidal Playlist Sync

This project is a command-line tool that allows bidirectional synchronization of playlists between Spotify and Tidal music streaming platforms.

## Features

- Bidirectional sync between Spotify and Tidal playlists
- On-demand synchronization
- Option to sync all playlists or specific playlists
- Playlist creation on the target platform if it doesn't exist
- Caching of playlist data to improve performance
- Error handling with retries and throttling
- Logging of warnings for tracks not found on the target platform

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/spotify-tidal-sync.git
   cd spotify-tidal-sync
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your configuration file `config.yaml` with your Spotify and Tidal credentials.

## Usage

To sync all playlists:
```
python main.py --all
```

To sync specific playlists:
```
python main.py --playlists "Playlist1" "Playlist2"
```

## Configuration

Create a `config.yaml` file in the project root with the following structure:

```yaml
spotify:
  client_id: your_spotify_client_id
  client_secret: your_spotify_client_secret
  redirect_uri: your_spotify_redirect_uri

tidal:
  username: your_tidal_username
  password: your_tidal_password

database:
  path: path_to_your_sqlite_database
```

## Development

This project is structured with the following main components:

- `main.py`: Entry point of the application
- `spotify_client.py`: Handles Spotify API interactions
- `tidal_client.py`: Handles Tidal API interactions
- `sync_manager.py`: Manages the synchronization process
- `database.py`: Handles local caching of playlist data
- `utils.py`: Contains utility functions

## Future Improvements

- Implement a graphical user interface (GUI)
- Add support for real-time synchronization
- Improve track matching between platforms
- Implement more sophisticated conflict resolution strategies

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
