import argparse
import sys

from config import load_config
from sync_manager import SyncManager


def main():
    parser = argparse.ArgumentParser(description="Spotify-Tidal Playlist Sync")
    parser.add_argument("--all", action="store_true", help="Sync all playlists")
    parser.add_argument("--playlists", nargs="+", help="List of playlist names to sync")
    parser.add_argument("--gui", action="store_true", help="Launch GUI (not implemented yet)")
    args = parser.parse_args()

    try:
        config = load_config()
        sync_manager = SyncManager(config)

        if args.gui:
            print("GUI not implemented yet. Falling back to CLI.")

        if args.all:
            sync_manager.sync_all_playlists()
        elif args.playlists:
            sync_manager.sync_specific_playlists(args.playlists)
        else:
            print("Please specify --all or --playlists")
            parser.print_help()
            sys.exit(1)

        print("Sync completed successfully.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
