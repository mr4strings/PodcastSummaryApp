import logging
import feedparser
from datetime import datetime, timedelta, timezone
import time
import requests # We need to import requests for this new method

def get_new_episodes(rss_feeds_file):
    """
    Parses a list of RSS feeds and returns episodes published in the last 36 hours.
    This version uses a more robust two-step fetching process to handle tricky feeds.

    Args:
        rss_feeds_file (str): The path to the text file containing RSS feed URLs.

    Returns:
        list: A list of dictionaries, where each dictionary represents a new episode.
    """
    try:
        with open(rss_feeds_file, 'r') as f:
            feeds = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logging.error(f"The RSS feeds file was not found at: {rss_feeds_file}")
        return []

    new_episodes = []
    now_utc = datetime.now(timezone.utc)
    time_cutoff = now_utc - timedelta(hours=36)
    
    logging.debug(f"Current UTC time is: {now_utc.isoformat()}")
    logging.debug(f"Time cutoff for new episodes is: {time_cutoff.isoformat()}")

    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'

    for feed_url in feeds:
        logging.info(f"Parsing feed: {feed_url}")
        try:
            # --- THE FIX: TWO-STEP FETCHING ---
            # Step 1: Use the robust `requests` library to download the raw feed content first.
            # This is more reliable than letting feedparser handle the network request directly.
            headers = {'User-Agent': user_agent}
            response = requests.get(feed_url, headers=headers, timeout=15) # Add a timeout
            response.raise_for_status() # This will raise an error for bad responses (4xx or 5xx)
            feed_content = response.text

            # Step 2: Pass the downloaded text content to feedparser to parse.
            # This avoids many of the common network-related parsing errors.
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

                logging.debug(
                    f"Checking Episode: '{entry.get('title', 'No Title')}' | "
                    f"Published: {episode_pub_time_utc.isoformat()} | "
                    f"Is it new? {episode_pub_time_utc > time_cutoff}"
                )

                if episode_pub_time_utc > time_cutoff:
                    episode_info = {
                        'title': entry.get('title', 'No Title'),
                        'podcast_title': podcast_title,
                        'links': entry.get('links', []),
                        'published': episode_pub_time_utc.isoformat(),
                        'media_content': entry.get('media_content', [])
                    }
                    new_episodes.append(episode_info)
                    logging.info(f"Found new episode: '{episode_info['title']}' from '{podcast_title}'")
        
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to download feed {feed_url}: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred while processing feed {feed_url}: {e}")

    if not new_episodes:
         logging.info("No new episodes found within the time window.")
         
    return new_episodes

