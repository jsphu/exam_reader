import re
import io
import os.path

# Google API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from config import CONFIG as cfg
CONFIG = cfg()
credentials_json = CONFIG.credentials_json
prefix = CONFIG.file_name_prefix

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_target_file_id(service, folder_id, prefix=prefix):
    """Finds the first file in a folder that starts with the prefix."""
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
            print(file['name'])
            return file['id']
    return None

def get_file_id_from_url(url):
    """Extracts the Google Drive file ID from a URL string."""
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
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # POINT THIS TO YOUR DOWNLOADED OAUTH CLIENT FILE
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_json, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)

def download_pdf_to_memory(service, file_id):
    """Downloads a file from Drive into an in-memory buffer."""
    request = service.files().get_media(fileId=file_id)
    file_buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(file_buffer, request)
    
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        # Optional: Print download progress
        # print(f"Download {int(status.progress() * 100)}%.")
    
    # Reset buffer position to the beginning so readers can read it
    file_buffer.seek(0)
    return file_buffer

