import pickle
from googleapiclient.discovery import build

with open('credentials/token.pickle', 'rb') as token:
    creds = pickle.load(token)

service = build('drive', 'v3', credentials=creds)

results = service.drives().list(pageSize=10).execute()
drives = results.get('drives', [])

print("\n🔗 Your Shared Drives:\n")
for drive in drives:
    print(f"Name: {drive['name']}")
    print(f"ID: {drive['id']}")
    print("---")
