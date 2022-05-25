import pickle
import io, os
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

def _create_service(client_secret_file, api_name, api_version, *scopes):
    #print(client_secret_file, api_name, api_version, scopes, sep='-')
    CLIENT_SECRET_FILE = client_secret_file
    API_SERVICE_NAME = api_name
    API_VERSION = api_version
    SCOPES = scopes[0]
    # print(SCOPES)
    # path = r"/Users/shikharsrivastava/Documents/APIs"
    # path = r"/home/ubuntu/pricing_wizard/APIs"
    # os.chdir(path)
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token1.json'):
        creds = Credentials.from_authorized_user_file('token1.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token1.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build(API_SERVICE_NAME, API_VERSION, credentials=creds)
        # print(API_SERVICE_NAME, 'service created successfully')
        return service
    except Exception as e:
        print('Unable to connect.')
        print(e)
        return None
# Not used?
def convert_to_RFC_datetime(year=1900, month=1, day=1, hour=0, minute=0):
    import datetime
    dt = datetime.datetime(year, month, day, hour, minute, 0).isoformat() + 'Z'
    return dt

# Expect this to be the only function needed to be called from outside this module
# Need to check if this creates a link to gdrive and a path we can write to
def create_connection():

    CLIENT_SECRET_FILE = 'client_secret_test.json'
    API_NAME = 'drive'
    API_VERSION = 'v3'
    SCOPES = ['https://www.googleapis.com/auth/drive']
    
    service = _create_service(CLIENT_SECRET_FILE,API_NAME,API_VERSION,SCOPES)
    
    # driveQuery = "(mimeType = 'application/'"
    
    folder_id = '1oN1oPK91McwGKmLltI2667x7tq6HWg78'
    mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
