import argparse
import logging
import signal
import sys

from config import load_config

logger = logging.getLogger(__name__)
from sync_manager import SyncManager, SyncError
from tidal_client import AuthenticationError, PlaylistModificationError


def signal_handler(sig, frame):
    print('\nExiting gracefully...')
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def main():
    parser = argparse.ArgumentParser(description="Spotify-Tidal Playlist Sync")
    parser.add_argument("--all", action="store_true", help="Sync all playlists")
    parser.add_argument("--playlists", nargs="+", help="List of playlist names to sync")
    parser.add_argument("--gui", action="store_true", help="Launch GUI (not implemented yet)")
    args = parser.parse_args()

    try:
        if args.gui:
            print("GUI not implemented yet. Falling back to CLI.")

        if not args.all and not args.playlists:
            print("Please specify --all or --playlists")
            parser.print_help()
            sys.exit(1)

        config = load_config()
        sync_manager = SyncManager(config)

        if args.all:
            sync_manager.sync_all_playlists()
        elif args.playlists:
            sync_manager.sync_specific_playlists(args.playlists)

        print("Sync completed successfully.")
    except AuthenticationError as e:
        print(f"Authentication error: {str(e)}")
        sys.exit(1)
    except PlaylistModificationError as e:
        print(f"Playlist modification error: {str(e)}")
        sys.exit(1)
    except SyncError as e:
        print(f"Sync error: {str(e)}")
        sys.exit(1)
    except (ValueError, IOError, KeyError) as e:
        print(f"Configuration or I/O error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        logger.exception("Unexpected error in main")
        sys.exit(1)


if __name__ == "__main__":
    main()
