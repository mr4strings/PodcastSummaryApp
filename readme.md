Automated Podcast Summarizer
This Python application automates the process of keeping up with your favorite podcasts. It monitors RSS feeds for new episodes, downloads and transcribes them for free using a local AI model, generates a detailed summary with an LLM, and uploads a neatly formatted e-book to your Google Drive.

Features
Monitors Multiple Podcasts: Easily track any number of podcasts by adding their RSS feeds to a simple text file.

Automated Daily Checks: Runs automatically every day to find and process episodes published within the last 36 hours.

Duplicate Prevention: Keeps a log of processed episodes to ensure the same episode is never processed more than once.

Free Local Transcription: Utilizes the powerful, open-source Whisper model to perform high-quality audio transcription directly on your machine at no cost.

AI-Powered Summarization: Leverages the Google Gemini API to generate:

A concise summary of the episode.

A bulleted list of major points and takeaways.

Noteworthy quotes.

A list of any sources referenced.

Speaker Identification (Diarization): Uses the LLM to intelligently format the raw transcript into a readable script, identifying and labeling the different speakers.

ePub Creation: Packages all generated content into a clean, easy-to-read ePub file.

Automatic Cloud Upload: Securely uploads the final ePub file to a specific folder in your Google Drive.

How It Works
The application follows a simple, automated pipeline:

Check History: Reads processed_episodes.log to get a list of episodes that have already been processed.

Fetch: Parses rss_feeds.txt and checks each feed for new episodes that are not in the history log.

Transcribe: Downloads the audio for each new episode and uses the local Whisper model to generate a raw text transcript.

Summarize & Diarize: Sends the transcript to the Gemini API for both summarization and speaker identification.

Generate: Assembles all the generated content into a well-formatted ePub file.

Upload: Uploads the ePub to your designated Google Drive folder.

Log Success: After a successful upload, writes the episode's unique ID to processed_episodes.log to prevent future reprocessing.

Setup and Installation Guide
Follow these steps to get the application running on your local machine.

Step 1: Prerequisites (Mandatory)
Before you begin, you must have the following software installed on your system:

Python 3.7+: Download Python

Git: Download Git

ffmpeg: The Whisper transcription model requires ffmpeg to process audio.

Windows: Download a static build from ffmpeg.org (the "gyan.dev" link is recommended). Unzip the file to a permanent location (e.g., C:\ffmpeg) and add the bin subfolder (e.g., C:\ffmpeg\bin) to your Windows System Path.

macOS (using Homebrew): Run brew install ffmpeg in your terminal.

Linux (using apt): Run sudo apt update && sudo apt install ffmpeg in your terminal.

To verify, open a new terminal window and run ffmpeg -version. You should see version details, not a "command not found" error.

Step 2: Clone the Repository
Open your terminal, navigate to the directory where you want to store the project, and run the following command:

git clone [https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git)
cd YOUR_REPOSITORY_NAME

Step 3: Install Python Dependencies
Install all the required Python libraries by running:

pip install -r requirements.txt

Step 4: Configure APIs and Credentials
4.1. Google Drive API
Create a Google Cloud Project: Go to the Google Cloud Console and create a new project.

Enable the Google Drive API: In your project, go to APIs & Services > Library, search for "Google Drive API", and Enable it.

Create OAuth 2.0 Credentials:

Go to APIs & Services > Credentials.

Click Create Credentials > OAuth client ID.

Select Desktop app as the application type and give it a name.

Click Create, then DOWNLOAD JSON.

Save this file in the root of your project folder and rename it to credentials.json.

4.2. Google Gemini API
Go to the Google AI Studio.

Click "Create API key in new project" and copy the generated key.

Step 5: Configure the Application
Create your .env file:

In the project folder, you will find a template file named _env.

Rename this file to .env.

Open the .env file and paste your Gemini API key.

Set Your Google Drive Folder ID:

Go to Google Drive and navigate to the folder where you want to save the ePubs.

The Folder ID is the last part of the URL: https://drive.google.com/drive/folders/THIS_IS_THE_FOLDER_ID

Copy this ID.

Open main.py and replace the placeholder value in the GOOGLE_DRIVE_FOLDER_ID variable with your actual ID.

Add Your Podcasts:

Open rss_feeds.txt and replace the placeholder URLs with the RSS feeds of the podcasts you want to follow, one URL per line.

Running the Application
You are now ready to run the application!

Navigate to the project directory in your terminal.

Run the main script:

python main.py

First-Time Google Authentication
The very first time you run the script, you will need to authorize its access to your Google Drive:

A link will appear in your terminal. Copy and paste it into your web browser.

Log in to the Google account associated with your Google Drive.

Grant the application permission to create files in your drive.

After you approve, you will be redirected to a page that may show an error. This is normal.

The script will automatically create a token.json file in your project folder. This file securely stores your authorization so you will not have to log in again.

The script will now run its full process. Be patient during the transcription step, as it can take several minutes depending on the length of the podcast and the speed of your computer.

Running Unit Tests
To verify that the transcriber module is working correctly without processing a full podcast, you can run the included unit tests:

python test_transcriber.py


## GitHub Preparation

To keep your credentials secure when sharing this code on GitHub, ensure you follow these practices:
1. **Never commit sensitive files:** The `.gitignore` is pre-configured to ignore `.env`, `credentials.json`, `token.json`, and generated outputs.
2. **Share the configuration template:** Use `.env.example` as a starting template for other contributors to set up their environment variables.

## Deploying to Railway

Railway is an excellent platform to host the Podcast Summarizer as a background worker process that runs daily.

### 1. Google Drive Headless Authentication
Because a cloud container cannot launch a local browser to complete the Google OAuth process:
1. Run the application locally first and complete the authorization. This creates `token.json` in your local directory.
2. Copy the contents of your local `credentials.json` and `token.json` files.
3. You will paste these JSON contents into the environment variables on Railway (see below). The application will automatically recreate the files at startup when deployed.

### 2. Railway Configuration
1. Create a new service on [Railway](https://railway.app) and link it to your GitHub repository.
2. In the service settings, set the **Start Command** to:
   ```bash
   python main.py
   ```
3. Add the following **Environment Variables** in the Railway dashboard:
   - `GEMINI_API_KEY`: Your Google Gemini API Key.
   - `GOOGLE_DRIVE_FOLDER_ID`: The ID of your target Google Drive folder.
   - `GOOGLE_DRIVE_CREDENTIALS`: The raw JSON contents of your `credentials.json`.
   - `GOOGLE_DRIVE_TOKEN`: The raw JSON contents of your `token.json`.
   - `RSS_FEEDS`: (Optional) A comma-separated list of RSS feed URLs. If set, this overrides the local `rss_feeds.txt` file, allowing you to edit subscription feeds directly from the Railway dashboard without redeploying.

