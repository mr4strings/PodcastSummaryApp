import logging
import requests
import os
import whisper
import time

def _find_audio_url(episode):
    """
    Tries to find the audio URL from an episode's data using multiple methods.
    This is a helper function to make the main function cleaner.

    Args:
        episode (dict): The episode data from the RSS feed.

    Returns:
        str: The found audio URL, or None.
    """
    # Method 1: Look for the standard 'enclosure' link, which is the most reliable.
    try:
        url = next(link['href'] for link in episode.get('links', []) if link.get('rel') == 'enclosure')
        if url:
            logging.info("Found audio URL via 'enclosure' link.")
            return url
    except (StopIteration, KeyError):
        pass  # If not found, we'll try the next method.

    # Method 2: If no enclosure is found, look for any link ending in a common audio format.
    # This is an excellent fallback for non-standard RSS feeds.
    try:
        audio_extensions = ['.mp3', '.m4a', '.wav', '.aac', '.ogg']
        for link in episode.get('links', []):
            href = link.get('href', '')
            if any(href.lower().endswith(ext) for ext in audio_extensions):
                logging.info(f"Found audio URL by file extension ({href[-4:]}).")
                return href
    except (StopIteration, KeyError):
        pass  # If still not found, we'll try the next method.
        
    # Method 3: Check for the 'media_content' key. This is a powerful fallback
    # for feeds (like Cal Newport's) that embed media differently.
    try:
        media_contents = episode.get('media_content', [])
        if media_contents and media_contents[0].get('url'):
            url = media_contents[0]['url']
            logging.info("Found audio URL via 'media_content' key.")
            return url
    except (IndexError, KeyError):
        pass # If the structure is unexpected, we'll just move on.

    # If all methods fail, we log the available keys from the feed. This is very
    # useful for debugging any future podcasts that might fail.
    logging.warning(f"Could not find audio URL. Available keys in episode data: {list(episode.keys())}")
    return None

def transcribe_episode(episode):
    """
    Downloads an episode's audio and transcribes it locally using the open-source Whisper model.

    Args:
        episode (dict): The episode dictionary containing the audio URL.

    Returns:
        str: The transcribed text of the episode, or None if transcription fails.
    """
    
    # --- 1. Find the Audio URL using our robust helper function ---
    audio_url = _find_audio_url(episode)
    if not audio_url:
        logging.error("Could not find a usable audio URL in the episode data after trying multiple methods.")
        return None

    logging.info(f"Downloading audio from: {audio_url[:50]}...")

    # --- 2. Download the Audio File ---
    temp_audio_path = "temp_episode.mp3" 
    try:
        # We'll use a user-agent header to appear like a standard browser, which can help prevent getting blocked.
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        with requests.get(audio_url, stream=True, headers=headers) as r:
            r.raise_for_status()
            with open(temp_audio_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        logging.info(f"Audio downloaded successfully to {temp_audio_path}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download audio file: {e}")
        return None

    # --- 3. Transcribe with Local Whisper Model ---
    transcript_text = None
    try:
        logging.info("Loading local Whisper model ('base'). This might take a moment...")
        model = whisper.load_model("base")
        
        logging.info("Model loaded. Starting local transcription...")
        start_time = time.time()
        
        result = model.transcribe(temp_audio_path)
        transcript_text = result["text"]
        
        end_time = time.time()
        duration = end_time - start_time
        logging.info(f"Transcription successful in {duration:.2f} seconds.")
        
    except Exception as e:
        logging.error(f"An unexpected error occurred during local transcription: {e}", exc_info=True)
        return None
        
    # --- 4. Clean Up ---
    finally:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
            logging.info(f"Cleaned up temporary audio file: {temp_audio_path}")
            
    return transcript_text

