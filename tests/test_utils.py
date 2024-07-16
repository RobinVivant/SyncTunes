import unittest
from unittest.mock import patch, MagicMock
import utils

class TestUtils(unittest.TestCase):
    @patch('logging.warning')
    def test_log_warning(self, mock_warning):
        utils.log_warning("Test warning")
        mock_warning.assert_called_once_with("Test warning")

    def test_retry_with_backoff(self):
        @utils.retry_with_backoff(retries=3, backoff_in_seconds=0)
        def test_function():
            raise Exception("Test exception")

        with self.assertRaises(Exception):
            test_function()

    @patch('utils.platform_client')
    def test_find_matching_track(self, mock_platform_client):
        track = {
            'name': 'Test Track',
            'artists': ['Test Artist']
        }
        mock_platform_client.search_tracks.return_value = [
            {
                'id': '1',
                'name': 'Test Track',
                'artists': ['Test Artist'],
                'album': 'Test Album',
                'uri': 'test:uri'
            }
        ]
        result = utils.find_matching_track(track, mock_platform_client)
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'Test Track')

    def test_get_current_timestamp(self):
        timestamp = utils.get_current_timestamp()
        self.assertIsNotNone(timestamp)
        self.assertIsInstance(timestamp, str)

if __name__ == '__main__':
    unittest.main()
