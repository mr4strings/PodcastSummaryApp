Podcast Summarizer Application
This Python application automatically checks for new podcast episodes from a list of RSS feeds, transcribes them, generates a summary and key points using an LLM, and uploads the result as an ePub file to your Google Drive.

Features
Automated Daily Checks: Runs every day at 8 AM to find new episodes from the last 24 hours.

Modular Design: Code is split into logical modules for fetching, transcribing, processing, and uploading.

ePub Generation: Creates a well-formatted ePub file with a summary, major points, quotes, sources, and the full transcript.

Google Drive Integration: Automatically uploads the final ePub to a specific folder in your Google Drive.

Project Structure
.
├── main.py                   # Main script to run the application
├── podcast_fetcher.py        # Fetches new episodes from RSS feeds
├── transcriber.py            # Transcribes audio (currently a placeholder)
├── llm_processor.py          # Processes transcript with an LLM (currently a placeholder)
├── epub_generator.py         # Creates the ePub file
├── google_drive_uploader.py  # Handles uploading to Google Drive
├── rss_feeds.txt             # Your list of podcast RSS feeds
├── requirements.txt          # List of required Python packages
└── README.md                 # This file

Setup Instructions
Follow these steps to get the application running on your local machine.

Step 1: Clone or Download the Code
First, get all the files into a single folder on your computer.

Step 2: Install Python Libraries
Make sure you have Python 3 installed. Then, open your terminal or command prompt, navigate to the project folder, and install the required packages using pip:

pip install -r requirements.txt

Step 3: Configure Your Podcast Feeds
Open the rss_feeds.txt file and add the URLs of the podcast RSS feeds you want to follow. Add one URL per line.

Step 4: Set Up Google Drive API Access
This is the most involved step. You need to authorize the application to upload files to your Google Drive.

Create a Google Cloud Project:

Go to the Google Cloud Console.

Create a new project (or select an existing one).

Enable the Google Drive API:

In your project, go to "APIs & Services" > "Library".

Search for "Google Drive API" and click Enable.

Create OAuth 2.0 Credentials:

Go to "APIs & Services" > "Credentials".

Click Create Credentials > OAuth client ID.

If prompted, configure the consent screen first. Choose External and provide a name for the app (e.g., "Podcast Uploader"). Fill in the required user support and developer contact info.

For the Application type, select Desktop app.

Click Create. A window will appear with your Client ID and Client Secret.

Click DOWNLOAD JSON. Rename the downloaded file to credentials.json and place it in the same folder as the Python scripts. Treat this file like a password; do not share it.

Get Your Google Drive Folder ID:

In your Google Drive, create the folder where you want the summaries to be saved (e.g., My Drive/Rakuten Kobo/Podcast Summaries).

Open the folder in your browser. The URL will look something like this: https://drive.google.com/drive/folders/1a2b3c4d5e6f7g8h9i0j_kLmnOpQrStUv.

The long string of characters at the end is the Folder ID. Copy it.

Open main.py and replace "YOUR_GOOGLE_DRIVE_FOLDER_ID" with the ID you just copied.

Step 5: Run the Application for the First Time
The first time you run the script, you will need to authorize it with Google.

Open your terminal or command prompt in the project folder.

Run the main script:

python main.py

A new tab or window will open in your web browser, asking you to log in to your Google account and grant permission for the app to access your Google Drive.

After you approve, the page will show a success message, and you can close it. The script will create a token.json file in your project folder. This file stores your authorization, so you won't have to log in every time.

How to Schedule the Script
The main.py script is already configured to run the podcast check every day at 8:00 AM. To make this work, you need to leave the script running continuously in a terminal window.

For a more robust, long-term solution, you should use your operating system's task scheduler:

On Windows: Use the Task Scheduler to create a new task that runs python.exe with main.py as the argument at your desired time.

On macOS/Linux: Use cron. Open your crontab by running crontab -e in the terminal and add a line like this to run the script at 8 AM every day:

0 8 * * * /usr/bin/python3 /path/to/your/project/main.py

(Make sure to use the correct paths for your Python executable and script).

Next Steps: Integrating Real Services
The transcriber.py and llm_processor.py files are currently placeholders. To make the application fully functional, you will need to:

Choose a Transcription Service:

Sign up for a service like AssemblyAI, Deepgram, or use OpenAI's Whisper.

Get an API key from the service.

Modify the transcriber.py file to download the audio and send it to the service's API, then return the text.

Choose an LLM Provider:

Sign up for an LLM API like OpenAI (GPT models), Google (Gemini models), or Anthropic (Claude models).

Get an API key.

Modify the llm_processor.py file to send the transcript to the model with a carefully crafted prompt asking for the summary, points, quotes, and sources. You should ask it to respond in a structured format like JSON for easy parsing.