import argparse
import logging
import signal
import sys
import unittest

from config import load_config
from sync_manager import SyncManager, SyncError
from tidal_client import AuthenticationError, PlaylistModificationError
from web_app import app

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def signal_handler(_, __):
    logger.info('Received interrupt signal. Exiting gracefully...')
    print('\nExiting gracefully...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def run_tests():
    logger.info("Starting test suite")
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    logger.info(f"Test suite completed. Success: {result.wasSuccessful()}")
    return result.wasSuccessful()

def main():
    logger.info("Starting main function")
    parser = argparse.ArgumentParser(description="Spotify-Tidal Playlist Sync")
    parser.add_argument("--all", action="store_true", help="Sync all playlists")
    parser.add_argument("--playlists", nargs="+", help="List of playlist names to sync")
    parser.add_argument("--gui", action="store_true", help="Launch web GUI")
    parser.add_argument("--run-tests", action="store_true", help="Run all tests")
    args = parser.parse_args()
    logger.debug(f"Parsed arguments: {args}")

    try:
        if args.run_tests:
            logger.info("Running tests")
            success = run_tests()
            sys.exit(0 if success else 1)

        if args.gui:
            logger.info("Launching web GUI")
            print("Launching web GUI...")
            logger.info("Starting Flask application from main.py")
            try:
                print("GUI is available at: http://localhost:5000")
                logger.info("About to start Flask app...")
                app.run(debug=True, use_reloader=False, host='localhost', port=8888)
                logger.info("Flask app has finished running.")
            except Exception as e:
                logger.error(f"Failed to start Flask application: {str(e)}")
                sys.exit(1)
            logger.info("Exiting GUI mode.")
            return

        if not args.all and not args.playlists:
            logger.warning("No sync option specified")
            print("Please specify --all or --playlists")
            parser.print_help()
            sys.exit(1)

        try:
            logger.info("Loading configuration")
            config = load_config()
        except FileNotFoundError:
            logger.warning("Configuration file not found. Using default configuration.")
            print("Configuration file not found. Using default configuration.")
            config = load_config()  # This will now load the default config
        
        logger.info("Initializing SyncManager")
        sync_manager = SyncManager(config)

        if args.all:
            logger.info("Syncing all playlists")
            sync_manager.sync_all_playlists()
        elif args.playlists:
            logger.info(f"Syncing specific playlists: {args.playlists}")
            sync_manager.sync_specific_playlists(args.playlists)

        logger.info("Sync completed successfully")
        print("Sync completed successfully.")
    except AuthenticationError as e:
        logger.error(f"Authentication error: {str(e)}")
        print(f"Authentication error: {str(e)}")
        sys.exit(1)
    except PlaylistModificationError as e:
        logger.error(f"Playlist modification error: {str(e)}")
        print(f"Playlist modification error: {str(e)}")
        sys.exit(1)
    except SyncError as e:
        logger.error(f"Sync error: {str(e)}")
        print(f"Sync error: {str(e)}")
        sys.exit(1)
    except (ValueError, IOError, KeyError) as e:
        logger.error(f"Configuration or I/O error: {str(e)}")
        print(f"Configuration or I/O error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error in main")
        print(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    logger.info("Script started")
    main()
    logger.info("Script finished")
