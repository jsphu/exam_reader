import re
import io
import os.path
import logging

# Google API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from .config import CONFIG as cfg
CONFIG = cfg()
credentials_json = CONFIG.credentials_json
prefix = CONFIG.file_name_prefix
main_directory = CONFIG.path

logger = logging.getLogger("exam_reader")

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_target_file_id(service, folder_id, prefix=prefix):
    """Finds the first file in a folder that starts with the prefix."""
    logger.log(10, f"Searching Drive folder {folder_id} for prefix: {prefix}")
    # Search for files inside the folder
    query = f"'{folder_id}' in parents and trashed = false and name contains '{prefix}'"

    results = service.files().list(
        q=query,
        fields="files(id, name)"
    ).execute()

    files = results.get('files', [])
    # Filter strictly for 'startswith'
    for file in files:
        if file['name'].startswith(prefix):
            logger.log(30, f"Match found in Drive: {file['name']} (ID: {file['id']})")
            return file['id'], file['name']
    logger.log(40, f"No file found starting with prefix: {prefix}")
    return None, None

def get_file_id_from_url(url):
    """Extracts the Google Drive file ID from a URL string."""
    logger.log(1, f"Extracting ID from URL: {url}")
    # Regex to catch standard drive URLs
    # Matches patterns like /d/12345abcde/ or id=12345abcde
    pattern = r'[-\w]{25,}'
    match = re.search(pattern, url)
    return match.group(0) if match else None

def authenticate_google_drive():
    """Authenticates using existing OAuth client credentials."""
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    token_dir = os.path.join(main_directory, 'token.json')
    if os.path.exists(token_dir):
        logger.log(10, f"Loading credentials from {token_dir}")
        creds = Credentials.from_authorized_user_file(token_dir, SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        try:
            if creds and creds.expired and creds.refresh_token:
                logger.log(30, "Refreshing expired credentials...")
                creds.refresh(Request())
        except Exception as e:
            logger.log(50, f"Credential refresh failed: {e}\nAuthorization needed.")
            logger.log(10, f"Using client secrets from: {credentials_json}")
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_json, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        logger.log(10, f"Saving new token to {token_dir}")
        with open(token_dir, 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)

def download_pdf_to_memory(service, file_id):
    """Downloads a file from Drive into an in-memory buffer."""
    logger.log(10, f"Initiating download for file ID: {file_id}")
    request = service.files().get_media(fileId=file_id)
    file_buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(file_buffer, request)

    done = False
    while done is False:
        status, done = downloader.next_chunk()
        logger.log(1, f"Download progress: {int(status.progress() * 100)}%")

    # Reset buffer position to the beginning so readers can read it
    file_buffer.seek(0)
    logger.log(30, "Download complete.")
    return file_buffer
