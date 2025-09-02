import logging
import schedule
import time
import os

# Import the modular components of our application
import podcast_fetcher
import transcriber
import llm_processor
import epub_generator
import google_drive_uploader

# --- Configuration ---
# Set up a logger to see the application's progress and any errors.
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# The ID of the Google Drive folder where you want to save the ePubs.
GOOGLE_DRIVE_FOLDER_ID = "1w6tUaUAoIQPOhxbrwm7kCR6NKP_3oIby"
RSS_FEEDS_FILE = 'rss_feeds.txt'
OUTPUT_DIR = 'output_epubs'

def process_podcasts():
    """
    The main function that orchestrates the entire process of fetching,
    processing, and uploading podcast episodes.
    """
    logging.info("Starting the daily podcast check...")

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        logging.info(f"Created output directory: {OUTPUT_DIR}")

    logging.info("Fetching new podcast episodes...")
    new_episodes = podcast_fetcher.get_new_episodes(RSS_FEEDS_FILE)

    if not new_episodes:
        logging.info("Podcast check finished.")
        return

    logging.info(f"Found {len(new_episodes)} new episode(s).")

    for episode in new_episodes:
        logging.info(f"Processing episode: '{episode['title']}' from '{episode['podcast_title']}'")

        try:
            # 2. Transcribe the episode
            # This returns the raw, unformatted block of text from Whisper.
            raw_transcript = transcriber.transcribe_episode(episode)
            if not raw_transcript:
                logging.warning(f"Transcription failed for '{episode['title']}'. Skipping.")
                continue
            logging.info("Transcription successful.")

            # 3. Process with LLM for Summarization
            # We send the raw transcript to get the summary, points, quotes, etc.
            logging.info("Generating content summary with LLM...")
            processed_content = llm_processor.process_transcript_with_llm(raw_transcript, episode['title'])

            if not processed_content:
                logging.warning(f"LLM content generation failed for '{episode['title']}'. Skipping.")
                continue
            logging.info("LLM content generation successful.")
            logging.info(f"LLM generated content: {processed_content}")

            # 4. Format Transcript with LLM for Diarization (NEW STEP)
            # We send the raw transcript again, but this time with a prompt asking for script formatting.
            logging.info("Formatting transcript for speaker diarization with LLM...")
            formatted_transcript = llm_processor.diarize_transcript_with_llm(raw_transcript)
            if not formatted_transcript:
                logging.warning(f"LLM diarization failed for '{episode['title']}'. Using raw transcript.")
                formatted_transcript = raw_transcript # Fallback to the raw transcript if formatting fails

            # 5. Generate ePub
            sanitized_episode_title = "".join(c for c in episode['title'] if c.isalnum() or c in (' ', '.', '_')).rstrip()
            current_date = time.strftime("%Y-%m-%d")
            file_name = f"{current_date}_{episode['podcast_title']}_{sanitized_episode_title}.epub"
            file_path = os.path.join(OUTPUT_DIR, file_name)
            
            logging.info("Generating ePub file...")
            epub_generator.create_epub(
                title=episode['title'],
                podcast_name=episode['podcast_title'],
                summary=processed_content['summary'],
                major_points=processed_content['major_points'],
                quotes=processed_content['quotes'],
                sources=processed_content['sources'],
                # We now pass the nicely formatted transcript to the ePub generator.
                transcript=formatted_transcript,
                file_path=file_path
            )
            logging.info(f"ePub file created at: {file_path}")

            # 6. Upload to Google Drive
            if GOOGLE_DRIVE_FOLDER_ID != "YOUR_GOOGLE_DRIVE_FOLDER_ID":
                logging.info(f"Uploading to Google Drive...")
                upload_successful = google_drive_uploader.upload_file_to_drive(file_path, GOOGLE_DRIVE_FOLDER_ID)
                if upload_successful:
                    logging.info(f"Successfully uploaded '{file_name}' to Google Drive.")
                else:
                    logging.error(f"Failed to upload '{file_name}' to Google Drive. Please check the logs above for details.")
            else:
                logging.warning("Google Drive Folder ID is not set. Skipping upload.")

        except Exception as e:
            logging.error(f"An error occurred while processing episode '{episode['title']}': {e}", exc_info=True)

    logging.info("Podcast check finished.")


def main():
    """
    Main entry point of the application. Schedules the job and runs it.
    """
    logging.info("Application started. Scheduling job.")
    schedule.every().day.at("08:00").do(process_podcasts)
    process_podcasts() 
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()

