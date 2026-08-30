import os
from pathlib import Path
from loguru import logger
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive.readonly']
TARGET_FOLDER_ID = "1aBxLl0aeiFks6Me-32CeXuGIp5s0BBlG"

def get_drive_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def find_existing_doc(service, doc_title, folder_id):
    query = f"name = '{doc_title}' and '{folder_id}' in parents and mimeType = 'application/vnd.google-apps.document' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])
    return files[0]['id'] if files else None

def upload_or_update_md(service, file_path):
    path_obj = Path(file_path)
    doc_title = path_obj.stem
    existing_file_id = find_existing_doc(service, doc_title, TARGET_FOLDER_ID)

    media = MediaFileUpload(file_path, mimetype='text/markdown', resumable=True)

    if existing_file_id:
        logger.info(f"Updating existing Doc: '{doc_title}' (Path: {file_path})")
        service.files().update(
            fileId=existing_file_id,
            media_body=media
        ).execute()
    else:
        logger.info(f"Creating new Doc in folder: '{doc_title}' (Path: {file_path})")
        file_metadata = {
            'name': doc_title,
            'mimeType': 'application/vnd.google-apps.document',
            'parents': [TARGET_FOLDER_ID]
        }
        service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

def process_markdown_files():
    service = get_drive_service()
    current_dir = Path.cwd()
    
    ignore_dirs = {'.git', '.venv', 'spanish-tutor-env', '__pycache__', 'node_modules'}
    
    md_files = [
        f for f in current_dir.rglob("*.md")
        if not any(part in ignore_dirs for part in f.parts)
    ]

    logger.info(f"Found {len(md_files)} Markdown file(s) across project and subfolders.")

    for md_file in md_files:
        try:
            upload_or_update_md(service, str(md_file))
        except Exception as e:
            logger.error(f"Error processing {md_file}: {e}")

if __name__ == '__main__':
    process_markdown_files()