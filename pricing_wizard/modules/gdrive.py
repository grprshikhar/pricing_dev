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

def list_folder(folder_id = '1oN1oPK91McwGKmLltI2667x7tq6HWg78'):
    creds = gdrive_api_check(SCOPES)
    service = build('drive', 'v3', credentials=creds)
    # List files in the parent folder (weird syntax...)
    results = service.files().list(q=f"'{folder_id}' in parents", spaces="drive", ).execute()
    items   = results.get('files', [])
    return items

def download_from_list(folder_id = '1X9hOcO4vCjBJDoxjpVSRdH2m5DgOdyNZ'):
    from modules.options_handler import options_handler
    run_opts        = options_handler()
    folder_files    = list_folder(folder_id)
    select_template = run_opts.choice_question("Select template file :", [x["name"] for x in folder_files])
    matching_file   = next(filter(lambda x : x['name'] == select_template, folder_files), None)
    if matching_file:
        file_id = matching_file["id"]
        return file_id
    else:
        return None

def download_store_template():
    # Fixed - Pricing/Templates
    folder_id = '1X9hOcO4vCjBJDoxjpVSRdH2m5DgOdyNZ'
    # Fixed - File name
    file_name = '1template_stores.xlsx'
    # Fixed - File ID
    file_id   = '11fb3mtzptYOmGOC-YnUtcK3YX-0BIiWD'
    # Check the information
    files = list_folder(folder_id)
    matching_file   = next(filter(lambda x : x['name'] == file_name and x['id'] == file_id, files), None)
    if not matching_file:
        raise ValueError(f"The template file [{file_name}] does not match the expected id [{file_id}].\nCheck the details in modules/gdrive.py")

























