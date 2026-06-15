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

    # We use the @patch decorator to replace functions with mock objects.
    @patch('transcriber.genai.GenerativeModel')
    @patch('transcriber.genai.delete_file')
    @patch('transcriber.genai.upload_file')
    @patch('transcriber.requests.get')
    @patch('transcriber.os.getenv', return_value="fake_api_key")
    def test_successful_transcription(self, mock_getenv, mock_requests_get, mock_upload_file, mock_delete_file, mock_generative_model):
        """
        Tests the entire transcription process by mocking the download and Gemini API steps.
        This is our new, reliable "happy path" test.
        """
        print("\n--- Running Test: Successful Transcription (with Mocks) ---")

        # --- 1. Setup the Mocks ---
        # Mock requests.get for audio download
        mock_response = MagicMock()
        mock_response.__enter__.return_value.iter_content.return_value = [b"fake_audio_chunk"]
        mock_requests_get.return_value = mock_response

        # Mock the Gemini File Upload object
        mock_file = MagicMock()
        mock_file.name = "files/test-file-123"
        mock_file.state.name = "ACTIVE"
        mock_upload_file.return_value = mock_file

        # Mock the Gemini GenerativeModel response
        mock_model_instance = MagicMock()
        mock_response_content = MagicMock()
        mock_response_content.text = "Hello world"
        mock_model_instance.generate_content.return_value = mock_response_content
        mock_generative_model.return_value = mock_model_instance
        
        # Create a mock episode dictionary
        mock_episode = {
            'title': 'Test Success Episode',
            'links': [{'rel': 'enclosure', 'href': 'http://fake-audio-url.com/episode.mp3'}]
        }

        # --- 2. Action ---
        transcript = transcribe_episode(mock_episode)

        # --- 3. Assertions ---
        self.assertIsNotNone(transcript, "FAIL: Transcript should not be None.")
        self.assertEqual(transcript, "Hello world", "FAIL: Transcript did not match the mocked output.")
        
        # Verify that our mocks were actually called
        mock_requests_get.assert_called_once_with('http://fake-audio-url.com/episode.mp3', stream=True, headers=unittest.mock.ANY)
        mock_upload_file.assert_called_once_with(path="temp_episode.mp3")
        mock_model_instance.generate_content.assert_called_once()
        mock_delete_file.assert_called_once_with("files/test-file-123")
        
        print("--- SUCCESS: Function correctly handled mocked download and Gemini API calls. ---")

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

