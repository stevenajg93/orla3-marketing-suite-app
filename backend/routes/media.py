from fastapi import APIRouter, Query
from typing import Optional
import httpx
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)

try:
    from .drive import get_drive_service
    DRIVE_AVAILABLE = True
except ImportError:
    DRIVE_AVAILABLE = False
    logger.warning("Google Drive service not available")

def find_marketing_folder_id(service):
    try:
        query = f"'{Config.SHARED_DRIVE_ID}' in parents and name='{Config.MARKETING_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query, corpora='drive', driveId=Config.SHARED_DRIVE_ID, includeItemsFromAllDrives=True, supportsAllDrives=True, fields='files(id)', pageSize=1).execute()
        files = results.get('files', [])
        if files:
            logger.info(f"Found Marketing folder: {files[0]['id']}")
            return files[0]['id']
        else:
            logger.warning(f"Marketing folder not found")
            return None
    except Exception as e:
        logger.error(f"Error finding Marketing folder: {e}")
        return None

@router.get("/media/status")
def get_status():
    return {"drive": {"connected": DRIVE_AVAILABLE, "shared_drive": Config.SHARED_DRIVE_NAME, "status": f"Connected to {Config.SHARED_DRIVE_NAME} ✅" if DRIVE_AVAILABLE else "Not connected"}, "unsplash": {"connected": bool(Config.UNSPLASH_ACCESS_KEY), "status": "API key configured ✅" if Config.UNSPLASH_ACCESS_KEY else "Missing"}}

@router.get("/media/folders")
def get_folders():
    if not DRIVE_AVAILABLE:
        logger.warning("Drive not available")
        return {"folders": []}
    try:
        service = get_drive_service()
        marketing_id = find_marketing_folder_id(service)
        if not marketing_id:
            return {"folders": []}
        query = f"'{marketing_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query, corpora='drive', driveId=Config.SHARED_DRIVE_ID, includeItemsFromAllDrives=True, supportsAllDrives=True, fields='files(id, name)', pageSize=100).execute()
        folders = [{"id": marketing_id, "name": f"📁 {Config.MARKETING_FOLDER_NAME} (Root)", "path": Config.MARKETING_FOLDER_NAME, "asset_count": 0}]
        for file in results.get('files', []):
            if not file['name'].startswith('.'):
                folders.append({"id": file['id'], "name": file['name'], "path": file['name'], "asset_count": 0})
        folders.sort(key=lambda x: x['name'])
        logger.info(f"Found {len(folders)} folders")
        return {"folders": folders}
    except Exception as e:
        logger.error(f"Error loading folders: {e}")
        return {"folders": []}

@router.get("/media/library")
def get_library(folder_id: Optional[str] = Query(None)):
    if not folder_id or not DRIVE_AVAILABLE:
        return {"assets": []}
    try:
        service = get_drive_service()
        query = f"'{folder_id}' in parents and trashed=false"
        results = service.files().list(q=query, corpora='drive', driveId=Config.SHARED_DRIVE_ID, includeItemsFromAllDrives=True, supportsAllDrives=True, fields='files(id, name, mimeType, size, thumbnailLink)', pageSize=1000).execute()
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
                assets.append({"id": file['id'], "name": file['name'], "type": asset_type, "source": "drive", "thumbnail": file.get('thumbnailLink'), "size": file.get('size', '0')})
        logger.info(f"Found {len(assets)} assets")
        return {"assets": assets}
    except Exception as e:
        logger.error(f"Error loading library: {e}")
        return {"assets": []}

@router.get("/media/unsplash")
def search_unsplash(query: str = Query(...), per_page: int = Query(20)):
    if not Config.UNSPLASH_ACCESS_KEY:
        logger.warning("Unsplash API key not configured")
        return {"images": []}
    try:
        url = "https://api.unsplash.com/search/photos"
        headers = {"Authorization": f"Client-ID {Config.UNSPLASH_ACCESS_KEY}"}
        params = {"query": query, "per_page": per_page}
        with httpx.Client() as client:
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
        images = []
        for photo in data.get('results', []):
            images.append({"id": photo['id'], "name": photo.get('alt_description', 'Untitled'), "type": "image", "source": "unsplash", "url": photo['urls']['regular'], "thumbnail": photo['urls']['small']})
        logger.info(f"Found {len(images)} Unsplash images for: {query}")
        return {"images": images}
    except Exception as e:
        logger.error(f"Error searching Unsplash: {e}")
        return {"images": []}
