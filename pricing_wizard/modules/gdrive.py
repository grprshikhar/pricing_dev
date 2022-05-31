from modules.gsheet import gsheet_api_check
from apiclient.http import MediaFileUpload
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive']

# Expect this to be the only function needed to be called from outside this module
# Need to check if this creates a link to gdrive and a path we can write to
def upload(fileout_name):
    # Credentials
    creds     = gsheet_api_check(SCOPES)
    service   = build('drive', 'v3', credentials=creds)
    folder_id = '1oN1oPK91McwGKmLltI2667x7tq6HWg78'
    mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    body  = {'name': fileout_name, 'parents':[folder_id],'mimeType': mime_type}
    media = MediaFileUpload(fileout_name, mimetype = mime_type)
    file  = service.files().create(body=body, media_body=media).execute()

def list_folder():
    creds = gsheet_api_check(SCOPES)
    service = build('drive', 'v3', credentials=creds)
    folder_id = '1oN1oPK91McwGKmLltI2667x7tq6HWg78'

    results = service.files().list(spaces="drive").execute()
    items   = results.get('files', [])
    print (items)

