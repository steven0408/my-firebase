from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = '/tmp/key.json'

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('drive', 'v3', credentials=creds)

FILE_ID = '1AxZwDpqcSWz5prwJ5WRZM4fh76kLDb_Y'
FILE_PATH = 'my-firebase/trigger_file.txt'

media = MediaFileUpload(FILE_PATH, resumable=True)
request = service.files().update(fileId=FILE_ID, media_body=media)
response = request.execute()

print('Trigger file updated:', response)
