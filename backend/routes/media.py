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
    return {"drive": {"connected": DRIVE_AVAILABLE, "shared_drive": Config.SHARED_DRIVE_NAME, "status": f"Connected to {Config.SHARED_DRIVE_NAME} ✅" if DRIVE_AVAILABLE else "Not connected"}, "pexels": {"connected": bool(Config.PEXELS_API_KEY), "status": "API key configured ✅" if Config.PEXELS_API_KEY else "Missing"}}

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

@router.get("/media/pexels/photos")
def search_pexels_photos(query: str = Query(...), per_page: int = Query(20)):
    """
    Search for free stock photos on Pexels.

    Pexels offers millions of free, high-quality stock photos.
    All photos are free to use for personal and commercial projects.
    """
    if not Config.PEXELS_API_KEY:
        logger.warning("Pexels API key not configured")
        return {"images": []}
    try:
        url = "https://api.pexels.com/v1/search"
        headers = {"Authorization": Config.PEXELS_API_KEY}
        params = {"query": query, "per_page": per_page}
        with httpx.Client() as client:
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
        images = []
        for photo in data.get('photos', []):
            images.append({
                "id": photo['id'],
                "name": photo.get('alt', 'Pexels Photo'),
                "type": "image",
                "source": "pexels",
                "url": photo['src']['large'],
                "thumbnail": photo['src']['medium'],
                "photographer": photo['photographer'],
                "photographer_url": photo['photographer_url']
            })
        logger.info(f"Found {len(images)} Pexels photos for: {query}")
        return {"images": images}
    except Exception as e:
        logger.error(f"Error searching Pexels photos: {e}")
        return {"images": []}

@router.get("/media/pexels/videos")
def search_pexels_videos(query: str = Query(...), per_page: int = Query(20)):
    """
    Search for free stock videos on Pexels.

    Pexels offers thousands of free, high-quality stock videos.
    All videos are free to use for personal and commercial projects.
    """
    if not Config.PEXELS_API_KEY:
        logger.warning("Pexels API key not configured")
        return {"videos": []}
    try:
        url = "https://api.pexels.com/videos/search"
        headers = {"Authorization": Config.PEXELS_API_KEY}
        params = {"query": query, "per_page": per_page}
        with httpx.Client() as client:
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
        videos = []
        for video in data.get('videos', []):
            # Get the best quality video file (HD preferred)
            video_file = None
            for file in video.get('video_files', []):
                if file.get('quality') == 'hd':
                    video_file = file
                    break
            if not video_file and video.get('video_files'):
                video_file = video['video_files'][0]

            if video_file:
                videos.append({
                    "id": video['id'],
                    "name": f"Video by {video['user']['name']}",
                    "type": "video",
                    "source": "pexels",
                    "url": video_file['link'],
                    "thumbnail": video.get('image'),
                    "duration": video.get('duration'),
                    "width": video.get('width'),
                    "height": video.get('height'),
                    "user": video['user']['name'],
                    "user_url": video['user']['url']
                })
        logger.info(f"Found {len(videos)} Pexels videos for: {query}")
        return {"videos": videos}
    except Exception as e:
        logger.error(f"Error searching Pexels videos: {e}")
        return {"videos": []}
