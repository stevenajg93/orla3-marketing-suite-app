import os
from googleapiclient.discovery import build

def get_marketing_assets(service, folder_id):
    # Query for files only in "marketing" folder or subfolders (recursive search)
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(q=query,
                                   fields="files(id, name, mimeType, parents)").execute()
    files = results.get('files', [])
    assets = []
    for file in files:
        if file['mimeType'] == 'application/vnd.google-apps.folder':
            # Recursive - fetch assets in subfolder
            assets.extend(get_marketing_assets(service, file['id']))
        else:
            assets.append(file)
    return assets

# Usage example (replace 'MARKETING_FOLDER_ID' with actual folder ID)
# service = build('drive', 'v3', credentials=creds)
# marketing_assets = get_marketing_assets(service, MARKETING_FOLDER_ID)
