import logging
import feedparser
from datetime import datetime, timedelta, timezone
import time
import requests
import os

# --- Configuration ---
# The name of the file where we'll store the IDs of processed episodes.
PROCESSED_LOG_FILE = 'processed_episodes.log'

def _load_processed_ids():
    """
    Loads the set of already processed episode IDs from the log file.
    Using a set provides very fast lookups.
    """
    # This is a good practice to ensure the log file exists on the first run.
    if not os.path.exists(PROCESSED_LOG_FILE):
        return set()
    try:
        with open(PROCESSED_LOG_FILE, 'r') as f:
            # We read each line and strip any whitespace to get a clean set of IDs.
            return {line.strip() for line in f}
    except Exception as e:
        logging.error(f"Could not read processed episodes log: {e}")
        return set()

def get_new_episodes(rss_feeds_file):
    """
    Parses RSS feeds and returns episodes that are new (within 36 hours) and
    have not been processed before.
    """
    # ... (code to read rss_feeds_file remains the same) ...
    try:
        with open(rss_feeds_file, 'r') as f:
            feeds = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logging.error(f"The RSS feeds file was not found at: {rss_feeds_file}")
        return []

    # Load the IDs of episodes we've already handled.
    processed_ids = _load_processed_ids()
    logging.info(f"Loaded {len(processed_ids)} previously processed episode IDs.")

    new_episodes = []
    now_utc = datetime.now(timezone.utc)
    time_cutoff = now_utc - timedelta(hours=36)
    
    logging.debug(f"Current UTC time is: {now_utc.isoformat()}")
    logging.debug(f"Time cutoff for new episodes is: {time_cutoff.isoformat()}")

    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'

    for feed_url in feeds:
        # ... (code for fetching and parsing the feed remains the same) ...
        logging.info(f"Parsing feed: {feed_url}")
        try:
            headers = {'User-Agent': user_agent}
            response = requests.get(feed_url, headers=headers, timeout=15)
            response.raise_for_status()
            feed_content = response.text
            parsed_feed = feedparser.parse(feed_content)

            if parsed_feed.bozo:
                logging.warning(f"Feed may be ill-formed: {feed_url}. Bozo flag was set, but attempting to process anyway.")

            logging.debug(f"Feed parsed. Found {len(parsed_feed.entries)} total entries.")
            podcast_title = parsed_feed.feed.get('title', 'Unknown Podcast')

            for entry in parsed_feed.entries:
                published_time_struct = entry.get('published_parsed')
                if not published_time_struct:
                    continue 

                episode_pub_time_utc = datetime.fromtimestamp(time.mktime(published_time_struct), tz=timezone.utc)
                
                # --- DUPLICATE CHECK LOGIC ---
                # A unique ID for the episode, usually a URL or a generated string.
                episode_id = entry.get('id')
                if not episode_id:
                    logging.warning(f"Episode '{entry.get('title')}' is missing a unique ID. Skipping.")
                    continue

                logging.debug(
                    f"Checking Episode: '{entry.get('title', 'No Title')}' | "
                    f"Published: {episode_pub_time_utc.isoformat()} | "
                    f"Is it new? {episode_pub_time_utc > time_cutoff} | "
                    f"Already processed? {episode_id in processed_ids}"
                )

                # An episode is only added if it's both recent AND its ID is not in our log.
                if episode_pub_time_utc > time_cutoff and episode_id not in processed_ids:
                    episode_info = {
                        'id': episode_id, # We must include the ID now.
                        'title': entry.get('title', 'No Title'),
                        'podcast_title': podcast_title,
                        'links': entry.get('links', []),
                        'published': episode_pub_time_utc.isoformat(),
                        'media_content': entry.get('media_content', [])
                    }
                    new_episodes.append(episode_info)
                    logging.info(f"Found new episode to process: '{episode_info['title']}' from '{podcast_title}'")
        
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to download feed {feed_url}: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred while processing feed {feed_url}: {e}")

    if not new_episodes:
         logging.info("No new episodes found within the time window that haven't already been processed.")
         
    return new_episodes

