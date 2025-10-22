from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import pickle
import os

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

@router.get("/drive/videos")
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

@router.get("/drive/folders")
async def list_folders():
    """List folders in Google Drive"""
    service = get_drive_service()
    
    if not service:
        return {
            "status": "not_configured",
            "message": "Google Drive not connected",
            "folders": []
        }
    
    try:
        results = service.files().list(
            q="mimeType='application/vnd.google-apps.folder'",
            pageSize=50,
            fields="files(id, name)",
            orderBy="name"
        ).execute()
        
        folders = results.get('files', [])
        
        return {
            "status": "success",
            "folders": folders
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Drive API error: {str(e)}")

@router.get("/drive/status")
async def drive_status():
    """Check Google Drive connection status"""
    service = get_drive_service()
    
    return {
        "connected": service is not None,
        "message": "Google Drive connected ✅" if service else "Run auth_drive.py to connect"
    }
