import logging
import requests
import os
import google.generativeai as genai
import time
from dotenv import load_dotenv

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
    Downloads an episode's audio and transcribes it natively using the Gemini API.

    Args:
        episode (dict): The episode dictionary containing the audio URL.

    Returns:
        str: The transcribed and diarized text of the episode, or None if transcription fails.
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

    # --- 3. Transcribe and Diarize with Gemini API ---
    audio_file = None
    transcript_text = None
    try:
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logging.error("GEMINI_API_KEY environment variable not found.")
            return None

        genai.configure(api_key=api_key)

        logging.info("Uploading audio file to Gemini File API...")
        audio_file = genai.upload_file(path=temp_audio_path)
        logging.info(f"File uploaded successfully. Name: {audio_file.name}. State: {audio_file.state.name}")

        # Poll the upload status until the file is active.
        # Audio is usually quick, but polling guarantees safety.
        while audio_file.state.name == "PROCESSING":
            logging.info("Waiting for audio file to be processed by Gemini...")
            time.sleep(5)
            audio_file = genai.get_file(audio_file.name)

        if audio_file.state.name != "ACTIVE":
            raise ValueError(f"Gemini file processing failed (state is {audio_file.state.name})")

        logging.info("Audio file is active. Requesting Gemini transcription and diarization...")
        
        # Use gemini-2.5-flash as default, since it supports audio and is fast.
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = """
        Transcribe the following audio recording. Identify and label the speakers (e.g., Nilay, Host, Guest 1, etc.) from context, formatting the output as a script with each speaker's dialogue on a new line. Do not summarize or omit any conversation.
        """
        
        start_time = time.time()
        response = model.generate_content([audio_file, prompt])
        transcript_text = response.text
        
        end_time = time.time()
        duration = end_time - start_time
        logging.info(f"Transcription and diarization completed successfully in {duration:.2f} seconds.")

    except Exception as e:
        logging.error(f"An unexpected error occurred during Gemini transcription: {e}", exc_info=True)
        return None
        
    # --- 4. Clean Up ---
    finally:
        # 1. Remove local temporary file
        if os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
                logging.info(f"Cleaned up local temporary audio file: {temp_audio_path}")
            except Exception as e:
                logging.error(f"Failed to delete local temp audio file: {e}")
                
        # 2. Delete the file from Google Gemini storage
        if audio_file is not None:
            try:
                genai.delete_file(audio_file.name)
                logging.info(f"Cleaned up remote Gemini File API upload: {audio_file.name}")
            except Exception as e:
                logging.error(f"Failed to delete remote Gemini file: {e}")
            
    return transcript_text

