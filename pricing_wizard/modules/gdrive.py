import os
# Google API
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from apiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from modules.print_utils import print_check

# Scope variable
SCOPES = ['https://www.googleapis.com/auth/drive']

# This function authorises against the Google API
def gdrive_api_check(SCOPES):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token_drive.json'):
        creds = Credentials.from_authorized_user_file('token_drive.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token_drive.json', 'w') as token:
            token.write(creds.to_json())
    
    return creds

# Expect this to be the only function needed to be called from outside this module
# Need to check if this creates a link to gdrive and a path we can write to
def upload(fileout_name):
    # Credentials
    creds     = gdrive_api_check(SCOPES)
    service   = build('drive', 'v3', credentials=creds)
    # We may want to adjust this to a pricing wizard folder
    folder_id = '1oN1oPK91McwGKmLltI2667x7tq6HWg78'
    mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    body  = {'name': fileout_name, 'parents':[folder_id],'mimeType': mime_type}
    media = MediaFileUpload(fileout_name, mimetype = mime_type)
    file  = service.files().create(body=body, media_body=media).execute()

def list_folder():
    creds = gdrive_api_check(SCOPES)
    service = build('drive', 'v3', credentials=creds)
    # We may want to adjust this to a pricing wizard folder
    folder_id = '1oN1oPK91McwGKmLltI2667x7tq6HWg78'
    # List files in the parent folder (weird syntax...)
    results = service.files().list(q=f"'{folder_id}' in parents", spaces="drive", ).execute()
    items   = results.get('files', [])
    for i in items:
        print (i)


