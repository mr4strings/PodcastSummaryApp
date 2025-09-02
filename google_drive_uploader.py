# google_drive_uploader.py
# This module handles authenticating with the Google Drive API and
# uploading a file to a specified folder.
# NOTE: This requires setting up a Google Cloud Platform project and
#       OAuth 2.0 credentials. See the README.md for instructions.

import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import logging

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_credentials():
    """
    Handles user authentication for the Google Drive API.
    It looks for a 'token.json' file which stores the user's access and refresh tokens.
    If it's not found or invalid, it will launch a browser window for the user to log in.
    """
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
    