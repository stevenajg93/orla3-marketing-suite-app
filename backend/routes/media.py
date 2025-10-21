from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import pickle
import os
import httpx

router = APIRouter()

SHARED_DRIVE_ID = "0AM2nUL9uMdpsUk9PVA"  # GECS Labs

class MediaAsset(BaseModel):
    id: str
    name: str
    type: str
    source: str
    url: Optional[str] = None
    thumbnail: Optional[str] = None
    size: Optional[str] = None
    folder: Optional[str] = None
    created_at: Optional[str] = None

class MediaFolder(BaseModel):
    id: str
    name: str
    path: str
    asset_count: int

def get_drive_service():
    token_path = 'credentials/token.pickle'
    if not os.path.exists(token_path):
        return None
    try:
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"Drive auth error: {e}")
        return None

@router.get("/media/library")
async def get_media_library(folder_id: Optional[str] = None, media_type: Optional[str] = None):
    """Get all media assets from GECS Labs shared drive"""
    service = get_drive_service()
    
    drive_assets = []
    
    if service:
        try:
            # If no folder selected, show root level
            parent_id = folder_id if folder_id else SHARED_DRIVE_ID
            
            # Build query
            query_parts = [f"'{parent_id}' in parents", "trashed=false"]
            
            # Filter by type if specified
            if media_type and media_type != 'all':
                if media_type == 'video':
                    query_parts.append("mimeType contains 'video/'")
                elif media_type == 'image':
                    query_parts.append("(mimeType contains 'image/' or mimeType contains 'jpeg' or mimeType contains 'png')")
                elif media_type == 'document':
                    query_parts.append("(mimeType contains 'document' or mimeType contains 'pdf')")
            
            query = " and ".join(query_parts)
            
            results = service.files().list(
                q=query,
                pageSize=1000,
                fields="files(id, name, mimeType, webViewLink, thumbnailLink, size, createdTime, iconLink)",
                orderBy="folder,name",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                corpora='drive',
                driveId=SHARED_DRIVE_ID
            ).execute()
            
            files = results.get('files', [])
            
            for file in files:
                # Determine asset type
                mime = file['mimeType']
                
                if 'folder' in mime:
                    asset_type = 'folder'
                elif 'video' in mime:
                    asset_type = 'video'
                elif 'image' in mime or 'jpeg' in mime or 'png' in mime:
                    asset_type = 'image'
                else:
                    asset_type = 'document'
                
                drive_assets.append({
                    'id': file['id'],
                    'name': file['name'],
                    'type': asset_type,
                    'source': 'drive',
                    'url': file.get('webViewLink'),
                    'thumbnail': file.get('thumbnailLink') or file.get('iconLink'),
                    'size': file.get('size', '0'),
                    'created_at': file.get('createdTime')
                })
        except Exception as e:
            print(f"Drive error: {e}")
            return {
                'drive_connected': True,
                'shared_drive': 'GECS Labs',
                'error': str(e),
                'assets': [],
                'total': 0
            }
    
    return {
        'drive_connected': service is not None,
        'shared_drive': 'GECS Labs',
        'assets': drive_assets,
        'total': len(drive_assets)
    }

@router.get("/media/folders")
async def get_media_folders():
    """Get ALL folders recursively from GECS Labs shared drive"""
    service = get_drive_service()
    
    if not service:
        return {'connected': False, 'folders': []}
    
    try:
        # Get ALL folders from shared drive (not just root)
        results = service.files().list(
            q=f"mimeType='application/vnd.google-apps.folder' and trashed=false",
            pageSize=1000,
            fields="files(id, name, parents)",
            orderBy="name",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            corpora='drive',
            driveId=SHARED_DRIVE_ID
        ).execute()
        
        folders = results.get('files', [])
        
        # Build folder hierarchy
        folder_map = {}
        for folder in folders:
            folder_map[folder['id']] = {
                'id': folder['id'],
                'name': folder['name'],
                'parents': folder.get('parents', [])
            }
        
        # Build paths
        def get_path(folder_id, visited=None):
            if visited is None:
                visited = set()
            if folder_id in visited or folder_id == SHARED_DRIVE_ID:
                return ""
            visited.add(folder_id)
            
            folder = folder_map.get(folder_id)
            if not folder:
                return ""
            
            parents = folder.get('parents', [])
            if not parents or parents[0] == SHARED_DRIVE_ID:
                return folder['name']
            
            parent_path = get_path(parents[0], visited)
            if parent_path:
                return f"{parent_path}/{folder['name']}"
            return folder['name']
        
        # Count files in each folder
        all_folders = []
        for folder in folders:
            path = get_path(folder['id'])
            
            # Count files
            count_result = service.files().list(
                q=f"'{folder['id']}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed=false",
                pageSize=1,
                fields="files(id)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            
            all_folders.append({
                'id': folder['id'],
                'name': folder['name'],
                'path': path,
                'asset_count': len(count_result.get('files', []))
            })
        
        # Sort by path
        all_folders.sort(key=lambda x: x['path'])
        
        return {
            'connected': True,
            'shared_drive': 'GECS Labs',
            'folders': all_folders
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Drive API error: {str(e)}")

@router.get("/media/unsplash")
async def search_unsplash(query: str, per_page: int = 20):
    access_key = os.getenv("UNSPLASH_ACCESS_KEY")
    if not access_key:
        return {'images': []}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.unsplash.com/search/photos",
                params={"query": query, "per_page": per_page},
                headers={"Authorization": f"Client-ID {access_key}"}
            )
            data = response.json()
            
            images = []
            for result in data.get('results', []):
                images.append({
                    'id': result['id'],
                    'name': result.get('description') or result.get('alt_description') or 'Unsplash Image',
                    'type': 'image',
                    'source': 'unsplash',
                    'url': result['urls']['regular'],
                    'thumbnail': result['urls']['thumb'],
                    'created_at': result['created_at']
                })
            
            return {'images': images, 'total': data.get('total', 0)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unsplash error: {str(e)}")

@router.get("/media/status")
async def media_status():
    service = get_drive_service()
    unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY")
    
    return {
        'drive': {
            'connected': service is not None,
            'shared_drive': 'GECS Labs',
            'status': 'Connected to GECS Labs ✅' if service else 'Not connected'
        },
        'unsplash': {
            'connected': bool(unsplash_key),
            'status': 'API key configured ✅' if unsplash_key else 'No API key'
        }
    }
