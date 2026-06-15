# google_drive_uploader.py
# This module handles authenticating with the Google Drive API and
# uploading a file to a specified folder.
# NOTE: This requires setting up a Google Cloud Platform project and
#       OAuth 2.0 credentials. See the README.md for instructions.

import os
import io
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import logging

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_credentials():
    """
    Handles user authentication for the Google Drive API.
    It looks for a 'token.json' file which stores the user's access and refresh tokens.
    If it's not found or invalid, it will launch a browser window for the user to log in.
    Supports bootstrapping these files from environment variables for headless environments.
    """
    # Bootstrap credentials.json from environment variable if it exists and file doesn't
    if not os.path.exists('credentials.json') and os.environ.get('GOOGLE_DRIVE_CREDENTIALS'):
        logging.info("Recreating credentials.json from GOOGLE_DRIVE_CREDENTIALS environment variable.")
        try:
            with open('credentials.json', 'w') as f:
                f.write(os.environ.get('GOOGLE_DRIVE_CREDENTIALS'))
        except Exception as e:
            logging.error(f"Failed to write credentials.json from environment: {e}")

    # Bootstrap token.json from environment variable if it exists and file doesn't
    if not os.path.exists('token.json') and os.environ.get('GOOGLE_DRIVE_TOKEN'):
        logging.info("Recreating token.json from GOOGLE_DRIVE_TOKEN environment variable.")
        try:
            with open('token.json', 'w') as f:
                f.write(os.environ.get('GOOGLE_DRIVE_TOKEN'))
        except Exception as e:
            logging.error(f"Failed to write token.json from environment: {e}")

    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # IMPORTANT: You need a 'credentials.json' file from Google Cloud.
            # See the README for how to get this.
            if not os.path.exists('credentials.json'):
                logging.error("credentials.json not found. Please follow the setup instructions in README.md.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def upload_file_to_drive(file_path, folder_id):
    """
    Uploads a file to a specific folder in Google Drive.

    Args:
        file_path (str): The path to the file to upload.
        folder_id (str): The ID of the Google Drive folder to upload to.
    """
    try:
        creds = get_credentials()
        if not creds:
            logging.error("Could not obtain Google Drive credentials. Skipping upload.")
            return

        service = build('drive', 'v3', credentials=creds)

        file_name = os.path.basename(file_path)
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        media = MediaFileUpload(file_path, mimetype='application/epub+zip', resumable=True)
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        logging.info(f"File '{file_name}' uploaded with ID: {file.get('id')}")
        return True

    except HttpError as error:
        logging.error(f'An HTTP error occurred with Google Drive API: {error}')
        return False
    except Exception as e:
        logging.error(f'An error occurred during Google Drive upload: {e}')
        return False


def download_processed_log_from_drive(local_path, folder_id):
    """
    Downloads the processed_episodes.log from Google Drive to local_path,
    merging with the local log if it already exists.
    """
    try:
        creds = get_credentials()
        if not creds:
            logging.error("Could not obtain Google Drive credentials for downloading log.")
            return False

        service = build('drive', 'v3', credentials=creds)
        
        # Search for processed_episodes.log in the specified folder
        query = f"name = 'processed_episodes.log' and '{folder_id}' in parents and trashed = false"
        results = service.files().list(q=query, fields="files(id)").execute()
        files = results.get('files', [])
        
        if not files:
            logging.info("processed_episodes.log not found on Google Drive. This is normal for a first run.")
            return False

        file_id = files[0]['id']
        logging.info(f"Found processed_episodes.log on Google Drive with ID: {file_id}. Downloading...")
        
        # Download the file content using MediaIoBaseDownload to avoid json parsing error in execute()
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            
        drive_content = fh.getvalue().decode('utf-8')
        drive_ids = {line.strip() for line in drive_content.split('\n') if line.strip()}
        
        # Merge with existing local file if it exists
        local_ids = set()
        if os.path.exists(local_path):
            try:
                with open(local_path, 'r') as f:
                    local_ids = {line.strip() for line in f if line.strip()}
            except Exception as e:
                logging.error(f"Error reading local processed log: {e}")
                
        merged_ids = drive_ids.union(local_ids)
        
        # Ensure directory exists for local_path if it's nested (e.g. /data/processed_episodes.log)
        dir_name = os.path.dirname(local_path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name)
            
        # Write merged IDs back to local path
        with open(local_path, 'w') as f:
            f.write('\n'.join(sorted(merged_ids)) + '\n')
            
        logging.info(f"Successfully downloaded and merged {len(merged_ids)} processed episode IDs from Google Drive.")
        return True
        
    except Exception as e:
        logging.error(f"Error downloading processed episodes log from Google Drive: {e}")
        return False


def upload_processed_log_to_drive(local_path, folder_id):
    """
    Uploads or updates the processed_episodes.log on Google Drive with local contents.
    """
    try:
        if not os.path.exists(local_path):
            logging.warning(f"Local processed log {local_path} does not exist. Skipping upload.")
            return False
            
        creds = get_credentials()
        if not creds:
            logging.error("Could not obtain Google Drive credentials for uploading log.")
            return False

        service = build('drive', 'v3', credentials=creds)
        
        # Search for processed_episodes.log in the specified folder
        query = f"name = 'processed_episodes.log' and '{folder_id}' in parents and trashed = false"
        results = service.files().list(q=query, fields="files(id)").execute()
        files = results.get('files', [])
        
        media = MediaFileUpload(local_path, mimetype='text/plain', resumable=True)
        
        if files:
            file_id = files[0]['id']
            logging.info(f"Updating existing processed_episodes.log on Google Drive (ID: {file_id})...")
            service.files().update(fileId=file_id, media_body=media).execute()
        else:
            logging.info("Creating new processed_episodes.log on Google Drive...")
            file_metadata = {
                'name': 'processed_episodes.log',
                'parents': [folder_id]
            }
            service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            
        logging.info("Successfully uploaded processed episodes log to Google Drive.")
        return True
        
    except Exception as e:
        logging.error(f"Error uploading processed episodes log to Google Drive: {e}")
        return False

    