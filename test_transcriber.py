import unittest
from unittest.mock import patch, MagicMock
import os
import logging
import string
from transcriber import transcribe_episode
import requests # We need to import this to mock its exceptions

# --- Test Configuration ---
logging.basicConfig(level=logging.ERROR)

class TestTranscriber(unittest.TestCase):
    """
    This class uses mocking to test the transcriber.py module in isolation,
    without relying on network requests or the actual Whisper model.
    This makes the tests fast, reliable, and able to run offline.
    """

    # We use the @patch decorator to replace a function with a mock object.
    # The mocks are passed into the test method from the bottom up (so 'mock_whisper' is first).
    @patch('transcriber.whisper.load_model')
    @patch('transcriber.requests.get')
    def test_successful_transcription(self, mock_requests_get, mock_whisper_load_model):
        """
        Tests the entire transcription process by mocking the download and transcription steps.
        This is our new, reliable "happy path" test.
        """
        print("\n--- Running Test: Successful Transcription (with Mocks) ---")

        # --- 1. Setup the Mocks ---
        # Mock the successful download of an audio file.
        # We configure the context manager that `requests.get` returns.
        mock_response = MagicMock()
        mock_response.__enter__.return_value.iter_content.return_value = [b"fake_audio_chunk"]
        mock_requests_get.return_value = mock_response

        # Mock the Whisper transcription result.
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {'text': 'Hello world'}
        mock_whisper_load_model.return_value = mock_model
        
        # Create a mock episode dictionary. The URL can be anything now.
        mock_episode = {
            'title': 'Test Success Episode',
            'links': [{'rel': 'enclosure', 'href': 'http://fake-audio-url.com/episode.mp3'}]
        }

        # --- 2. Action: Call the function we want to test ---
        transcript = transcribe_episode(mock_episode)

        # --- 3. Assertions: Check if our code handled the mock data correctly ---
        self.assertIsNotNone(transcript, "FAIL: Transcript should not be None.")
        self.assertEqual(transcript, "Hello world", "FAIL: Transcript did not match the mocked output.")
        
        # Verify that our mocks were actually called.
        mock_requests_get.assert_called_once_with('http://fake-audio-url.com/episode.mp3', stream=True, headers=unittest.mock.ANY)
        mock_model.transcribe.assert_called_once()
        
        print("--- SUCCESS: Function correctly handled mocked download and transcription. ---")

    @patch('transcriber.requests.get')
    def test_download_failure(self, mock_requests_get):
        """
        Tests that the function handles a network error during download.
        """
        print("\n--- Running Test: Handles Download Failure ---")
        
        # 1. Setup: Configure the mock to raise a network error.
        mock_requests_get.side_effect = requests.exceptions.RequestException("Test network error")
        
        mock_episode = {
            'title': 'Test Download Failure',
            'links': [{'rel': 'enclosure', 'href': 'http://fake-audio-url.com/episode.mp3'}]
        }
        
        # 2. Action & Assertion
        transcript = transcribe_episode(mock_episode)
        self.assertIsNone(transcript, "FAIL: Function should return None on download failure.")
        
        print("--- SUCCESS: Function correctly handled a download failure. ---")


    def test_failure_with_no_audio_url(self):
        """
        Tests that the function gracefully handles an episode with no audio URL.
        This test needs no mocks as it should fail before any network calls.
        """
        print("\n--- Running Test: Handles Missing Audio URL ---")
        
        mock_episode_failure = {
            'title': 'Test Failure Episode',
            'links': []
        }
        transcript = transcribe_episode(mock_episode_failure)
        self.assertIsNone(transcript, "FAIL: Function should return None when no audio URL is found.")
        
        print("--- SUCCESS: Function correctly handled a missing audio URL. ---")

if __name__ == '__main__':
    unittest.main()

