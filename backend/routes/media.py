from fastapi import APIRouter, Query
from typing import Optional
import httpx
import os

router = APIRouter()

try:
    from .drive import get_drive_service
    DRIVE_AVAILABLE = True
except ImportError:
    DRIVE_AVAILABLE = False

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
SHARED_DRIVE_ID = "0AM2nUL9uMdpsUk9PVA"

def find_marketing_folder_id(service):
    """Find Marketing folder ID"""
    query = f"'{SHARED_DRIVE_ID}' in parents and name='Marketing' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(
        q=query,
        corpora='drive',
        driveId=SHARED_DRIVE_ID,
        includeItemsFromAllDrives=True,
        supportsAllDrives=True,
        fields='files(id)',
        pageSize=1
    ).execute()
    files = results.get('files', [])
    return files[0]['id'] if files else None

@router.get("/media/status")
def get_status():
    return {
        "drive": {
            "connected": DRIVE_AVAILABLE,
            "shared_drive": "GECS Labs",
            "status": "Connected to GECS Labs ✅" if DRIVE_AVAILABLE else "Not connected"
        },
        "unsplash": {
            "connected": bool(UNSPLASH_ACCESS_KEY),
            "status": "API key configured ✅" if UNSPLASH_ACCESS_KEY else "Missing"
        }
    }

@router.get("/media/folders")
def get_folders():
    """Get ONLY direct children of Marketing folder (not recursive)"""
    if not DRIVE_AVAILABLE:
        return {"folders": []}
    
    try:
        service = get_drive_service()
        marketing_id = find_marketing_folder_id(service)
        
        if not marketing_id:
            return {"folders": []}
        
        # Get ONLY direct subfolders of Marketing (NO recursion)
        query = f"'{marketing_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        
        results = service.files().list(
            q=query,
            corpora='drive',
            driveId=SHARED_DRIVE_ID,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            fields='files(id, name)',
            pageSize=100
        ).execute()
        
        folders = [{
            "id": marketing_id,
            "name": "📁 Marketing (Root)",
            "path": "Marketing",
            "asset_count": 0
        }]
        
        for file in results.get('files', []):
            if not file['name'].startswith('.'):
                folders.append({
                    "id": file['id'],
                    "name": file['name'],
                    "path": file['name'],
                    "asset_count": 0
                })
        
        folders.sort(key=lambda x: x['name'])
        return {"folders": folders}
        
    except Exception as e:
        print(f"Error: {e}")
        return {"folders": []}

@router.get("/media/library")
def get_library(folder_id: Optional[str] = Query(None)):
    """Get files AND subfolders in selected folder"""
    if not folder_id:
        return {"assets": []}
    
    if not DRIVE_AVAILABLE:
        return {"assets": []}
    
    try:
        service = get_drive_service()
        
        query = f"'{folder_id}' in parents and trashed=false"
        
        results = service.files().list(
            q=query,
            corpora='drive',
            driveId=SHARED_DRIVE_ID,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            fields='files(id, name, mimeType, size, thumbnailLink)',
            pageSize=1000
        ).execute()
        
        assets = []
        for file in results.get('files', []):
            if not file['name'].startswith('.'):
                mime = file.get('mimeType', '')
                
                if mime == 'application/vnd.google-apps.folder':
                    asset_type = 'folder'
                elif 'video' in mime:
                    asset_type = 'video'
                elif 'image' in mime:
                    asset_type = 'image'
                else:
                    asset_type = 'document'
                
                assets.append({
                    "id": file['id'],
                    "name": file['name'],
                    "type": asset_type,
                    "source": "drive",
                    "thumbnail": file.get('thumbnailLink'),
                    "size": file.get('size', '0')
                })
        
        return {"assets": assets}
        
    except Exception as e:
        print(f"Error: {e}")
        return {"assets": []}

@router.get("/media/unsplash")
def search_unsplash(query: str = Query(...), per_page: int = Query(20)):
    if not UNSPLASH_ACCESS_KEY:
        return {"images": []}
    
    try:
        url = "https://api.unsplash.com/search/photos"
        headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
        params = {"query": query, "per_page": per_page}
        
        with httpx.Client() as client:
            response = client.get(url, headers=headers, params=params)
            data = response.json()
        
        images = []
        for photo in data.get('results', []):
            images.append({
                "id": photo['id'],
                "name": photo.get('alt_description', 'Untitled'),
                "type": "image",
                "source": "unsplash",
                "url": photo['urls']['regular'],
                "thumbnail": photo['urls']['small']
            })
        
        return {"images": images}
        
    except Exception as e:
        print(f"Error: {e}")
        return {"images": []}
