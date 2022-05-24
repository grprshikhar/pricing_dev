# Path
import os.path
# Google API
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import sys

# Scope variable
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# This function authorises against the Google API
def gsheet_api_check(SCOPES):
    # Best to use relative paths or provide the path
    # we need through an environment variable

    # path = r"/home/ubuntu/pricing_wizard/APIs"
    # path = r"/Users/shikharsrivastava/Documents/APIs"
    # os.chdir(path)

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token_sheet.json'):
        creds = Credentials.from_authorized_user_file('token_sheet.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token_sheet.json', 'w') as token:
            token.write(creds.to_json())
    
    return creds

# This function will return the data from the spreadsheet range
def pull_sheet_data(SCOPES,SPREADSHEET_ID,DATA_TO_PULL):
    # Check API functioning
    creds = gsheet_api_check(SCOPES)
    # Create google service
    service = build('sheets', 'v4', credentials=creds)
    # Create sheet service
    sheet = service.spreadsheets()
    # Access and pull spreadsheet data result object
    try:
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,range=DATA_TO_PULL).execute()
    except HttpError as e:
        print ("")
        print (f"{e}")
        print ("")
        print (f"This error was returned while trying to access data in spreadsheet [{SPREADSHEET_ID}]")
        print (f"Please ensure that this spreadsheet is shared with 'Grover' in the share options.")
        sys.exit(1)

    # Get data
    values = result.get('values', [])
    
    # Check output
    if not values:
        print(f"No data found [{SPREADSHEET_ID}].")
        return None
    else:
        print (f"Data pulled from spreadsheet [{SPREADSHEET_ID}].")
        return values