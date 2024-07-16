import argparse
import logging
import signal
import sys
import unittest

from config import load_config
from sync_manager import SyncManager, SyncError
from tidal_client import AuthenticationError, PlaylistModificationError
from web_app import app

logger = logging.getLogger(__name__)


def signal_handler(_, __):
    print('\nExiting gracefully...')
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def run_tests():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    return result.wasSuccessful()


def main():
    parser = argparse.ArgumentParser(description="Spotify-Tidal Playlist Sync")
    parser.add_argument("--all", action="store_true", help="Sync all playlists")
    parser.add_argument("--playlists", nargs="+", help="List of playlist names to sync")
    parser.add_argument("--gui", action="store_true", help="Launch web GUI")
    parser.add_argument("--run-tests", action="store_true", help="Run all tests")
    args = parser.parse_args()

    try:
        if args.run_tests:
            success = run_tests()
            sys.exit(0 if success else 1)

        if args.gui:
            print("Launching web GUI...")
            logger.info("Starting Flask application from main.py")
            try:
                app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)
            except Exception as e:
                logger.error(f"Failed to start Flask application: {str(e)}")
                sys.exit(1)
            return

        if not args.all and not args.playlists:
            print("Please specify --all or --playlists")
            parser.print_help()
            sys.exit(1)

        try:
            config = load_config()
        except FileNotFoundError:
            print("Configuration file not found. Using default configuration.")
            config = load_config()  # This will now load the default config
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
