from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import pickle
import os

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

class DriveFile(BaseModel):
    id: str
    name: str
    mimeType: str
    webViewLink: Optional[str] = None
    thumbnailLink: Optional[str] = None
    size: Optional[str] = None

def get_drive_service():
    """Initialize Google Drive service"""
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

@router.get("/videos")
async def list_videos(folder_id: Optional[str] = None):
    """List video files from Google Drive folder"""
    service = get_drive_service()
    
    if not service:
        return {
            "status": "not_configured",
            "message": "Google Drive not connected. Run auth_drive.py to authorize.",
            "files": []
        }
    
    try:
        query = "mimeType contains 'video/'"
        if folder_id:
            query += f" and '{folder_id}' in parents"
        
        results = service.files().list(
            q=query,
            pageSize=50,
            fields="files(id, name, mimeType, webViewLink, thumbnailLink, size)",
            orderBy="modifiedTime desc"
        ).execute()
        
        files = results.get('files', [])
        
        return {
            "status": "success",
            "files": files,
            "total": len(files)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Drive API error: {str(e)}")

@router.get("/folders")
async def list_folders():
    """List folders in the Marketing folder"""
    service = get_drive_service()
    
    if not service:
        return {"folders": []}
    
    try:
        from config import Config
        marketing_id = find_marketing_folder_id(service)
        if not marketing_id:
            return {"folders": []}
        
        query = f"'{marketing_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(
            q=query,
            corpora='drive',
            driveId=Config.SHARED_DRIVE_ID,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            fields='files(id, name)',
            pageSize=100
        ).execute()
        
        folders = [{"id": marketing_id, "name": "📁 Marketing (Root)"}]
        for file in results.get('files', []):
            if not file['name'].startswith('.'):
                folders.append({"id": file['id'], "name": file['name']})
        
        return {"folders": folders}
    except Exception as e:
        logger.error(f"Error loading folders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def drive_status():
    """Check Google Drive connection status"""
    service = get_drive_service()
    
    return {
        "connected": service is not None,
        "message": "Google Drive connected ✅" if service else "Run auth_drive.py to connect"
    }

@router.get("/file/{file_id}/download")
async def download_file(file_id: str):
    """Download a file from Google Drive"""
    try:
        service = get_drive_service()
        if not service:
            raise HTTPException(status_code=503, detail="Google Drive not connected")
        
        # Get file metadata
        file_metadata = service.files().get(fileId=file_id, fields="name,mimeType").execute()
        
        # Download file content
        request = service.files().get_media(fileId=file_id)
        file_content = request.execute()
        
        return {
            "success": True,
            "filename": file_metadata['name'],
            "mimeType": file_metadata['mimeType'],
            "content": file_content
        }
    except Exception as e:
        logger.error(f"Error downloading file from Drive: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def find_marketing_folder_id(service):
    """Find the Marketing folder in the shared drive"""
    try:
        from config import Config
        query = f"'{Config.SHARED_DRIVE_ID}' in parents and name='{Config.MARKETING_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(
            q=query,
            corpora='drive',
            driveId=Config.SHARED_DRIVE_ID,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            fields='files(id)',
            pageSize=1
        ).execute()
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


@router.get("/folder/{folder_id}/files")
async def list_folder_files(folder_id: str):
    """List files in a specific folder from Marketing shared drive"""
    service = get_drive_service()
    
    if not service:
        return {"files": []}
    
    try:
        from config import Config
        query = f"'{folder_id}' in parents and trashed=false"
        results = service.files().list(
            q=query,
            corpora='drive',
            driveId=Config.SHARED_DRIVE_ID,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            fields='files(id, name, mimeType, shortcutDetails)',
            pageSize=1000
        ).execute()
        
        files = []
        for file in results.get('files', []):
            # Skip hidden files and folders
            if not file['name'].startswith('.'):
                files.append(file)
        
        logger.info(f"Found {len(files)} files in folder {folder_id}")
        return {"files": files}
    except Exception as e:
        logger.error(f"Error loading files: {e}")
        raise HTTPException(status_code=500, detail=str(e))
