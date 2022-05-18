import io, os 
from googleapiclient.http import MediaIoBaseDownload,MediaFileUpload
from Google import Create_Service

CLIENT_SECRET_FILE = 'client_secret_test.json'
API_NAME = 'drive'
API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/drive']

service = Create_Service(CLIENT_SECRET_FILE,API_NAME,API_VERSION,SCOPES)

# driveQuery = "(mimeType = 'application/'"

folder_id = '1oN1oPK91McwGKmLltI2667x7tq6HWg78'
mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'







# file_id = '11fb3mtzptYOmGOC-YnUtcK3YX-0BIiWD'
# # file_name = 'test_book.xlsx'

# request = service.files().get_media(fileId=file_id)
# fh = io.BytesIO()
# downloader = MediaIoBaseDownload(fd=fh, request=request)
# done = False

# # path = r"/home/ubuntu/Downloads"
# # os.chdir(path)

# while done is False:
#     status, done = downloader.next_chunk()
#     # print "Download %d%%." % int(status.progress() * 100)


# file_name = 'template.xlsx'
# with open(file_name,'wb') as f:
# 	f.write(fh.read())
# 	f.close()    