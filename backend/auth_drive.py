import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import pickle

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def authorize_drive():
    """Authorize and save credentials for Google Drive access"""
    creds = None
    token_path = 'credentials/token.pickle'
    
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    print("✅ Google Drive authorized successfully!")
    print(f"Token saved to: {token_path}")
    return creds

if __name__ == '__main__':
    authorize_drive()
