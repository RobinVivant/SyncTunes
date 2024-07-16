import argparse
from sync_manager import SyncManager
from config import load_config
from lint import run_linter

def main():
    parser = argparse.ArgumentParser(description="Spotify-Tidal Playlist Sync")
    parser.add_argument("--all", action="store_true", help="Sync all playlists")
    parser.add_argument("--playlists", nargs="+", help="List of playlist names to sync")
    parser.add_argument("--gui", action="store_true", help="Launch GUI (not implemented yet)")
    parser.add_argument("--lint", action="store_true", help="Run linter")
    args = parser.parse_args()

    if args.lint:
        run_linter()
        return

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

if __name__ == "__main__":
    main()
