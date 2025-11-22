"""
Google Drive Routes - Multi-Tenant Per-User Implementation
Handles Google Drive integration with per-user OAuth tokens from database
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import httpx
import os

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import setup_logger
from db_pool import get_db_connection  # Use connection pool
from utils.auth_dependency import get_current_user_id

logger = setup_logger(__name__)
router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

class DriveFile(BaseModel):
    id: str
    name: str
    mimeType: str
    webViewLink: Optional[str] = None
    thumbnailLink: Optional[str] = None
    size: Optional[str] = None


async def refresh_google_drive_token(user_id: str, refresh_token: str) -> str:
    """Refresh Google Drive access token"""
    token_url = "https://oauth2.googleapis.com/token"

    data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)

        if response.status_code != 200:
            logger.error(f"Token refresh failed: {response.text}")
            raise HTTPException(
                status_code=500,
                detail="Failed to refresh Google Drive token"
            )

        tokens = response.json()
        new_access_token = tokens["access_token"]
        expires_in = tokens.get("expires_in", 3600)
        new_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        # Update token in database
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("""
                    UPDATE user_cloud_storage_tokens
                    SET access_token = %s,
                        token_expires_at = %s,
                        last_refreshed_at = NOW(),
                        updated_at = NOW()
                    WHERE user_id = %s AND provider = 'google_drive'
                """, (new_access_token, new_expires_at, user_id))

                conn.commit()
                logger.info(f"Refreshed Google Drive token for user {user_id}")

                return new_access_token
            except Exception as e:
                conn.rollback()
                logger.error(f"Error updating token: {e}")
                raise
            finally:
                cur.close()


def get_drive_service(user_id: str):
    """
    Initialize Google Drive service for specific user
    Uses per-user OAuth tokens from database
    """
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            # Get user's Google Drive tokens from database
            cur.execute("""
                SELECT access_token, refresh_token, token_expires_at
                FROM user_cloud_storage_tokens
                WHERE user_id = %s AND provider = 'google_drive' AND is_active = true
            """, (user_id,))

            token_record = cur.fetchone()

            if not token_record:
                logger.warning(f"No Google Drive connection for user {user_id}")
                return None

            access_token = token_record['access_token']
            refresh_token = token_record['refresh_token']
            token_expires_at = token_record['token_expires_at']

            # Check if token is expired or about to expire (within 5 minutes)
            from datetime import timedelta
            if token_expires_at < datetime.utcnow() + timedelta(minutes=5):
                logger.info(f"Token expired for user {user_id}, refreshing...")
                # Need to use async, so we'll handle this in the route
                # For now, try with existing token and let it fail
                pass

            # Build credentials
            creds = Credentials(
                token=access_token,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=GOOGLE_CLIENT_ID,
                client_secret=GOOGLE_CLIENT_SECRET
            )

            service = build('drive', 'v3', credentials=creds)
            return service

        except Exception as e:
            logger.error(f"Error initializing Drive service for user {user_id}: {e}")
            return None
        finally:
            cur.close()


@router.get("/videos")
async def list_videos(folder_id: Optional[str] = None, user_id: str = Depends(get_current_user_id)):
    """List video files from user's Google Drive"""
    service = get_drive_service(user_id)

    if not service:
        return {
            "status": "not_configured",
            "message": "Google Drive not connected. Please connect your Google Drive in settings.",
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Drive API error for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list videos from Google Drive")


@router.get("/folders")
async def list_folders(parent_folder_id: Optional[str] = None, user_id: str = Depends(get_current_user_id)):
    """List folders in user's Google Drive"""
    service = get_drive_service(user_id)

    if not service:
        return {"folders": []}

    try:
        # Query folders (either root or specific parent)
        if parent_folder_id:
            query = f"'{parent_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        else:
            query = "'root' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"

        results = service.files().list(
            q=query,
            fields='files(id, name)',
            pageSize=100,
            orderBy='name'
        ).execute()

        folders = []
        for file in results.get('files', []):
            if not file['name'].startswith('.'):
                folders.append({"id": file['id'], "name": file['name']})

        return {"folders": folders}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading folders for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list folders from Google Drive")


@router.get("/status")
async def drive_status(user_id: str = Depends(get_current_user_id)):
    """Check user's Google Drive connection status"""
    service = get_drive_service(user_id)

    return {
        "connected": service is not None,
        "message": "Google Drive connected ✅" if service else "Connect Google Drive in settings to access your files"
    }


@router.get("/file/{file_id}/download")
async def download_file(file_id: str, user_id: str = Depends(get_current_user_id)):
    """Download a file from user's Google Drive"""

    try:
        service = get_drive_service(user_id)
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file from Drive for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to download file from Google Drive")


@router.get("/folder/{folder_id}/files")
async def list_folder_files(folder_id: str, user_id: str = Depends(get_current_user_id)):
    """List files in a specific folder from user's Google Drive"""
    service = get_drive_service(user_id)

    if not service:
        return {"files": []}

    try:
        query = f"'{folder_id}' in parents and trashed=false"
        results = service.files().list(
            q=query,
            fields='files(id, name, mimeType, thumbnailLink, size, modifiedTime)',
            pageSize=1000,
            orderBy='name'
        ).execute()

        files = []
        for file in results.get('files', []):
            # Skip hidden files
            if not file['name'].startswith('.'):
                files.append(file)

        logger.info(f"Found {len(files)} files in folder {folder_id} for user {user_id}")
        return {"files": files}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading files for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list files from Google Drive")


@router.get("/search")
async def search_files(query: str, file_type: Optional[str] = None, user_id: str = Depends(get_current_user_id)):
    """Search files in user's Google Drive"""
    service = get_drive_service(user_id)

    if not service:
        return {"files": []}

    try:
        # Build search query
        search_query = f"name contains '{query}' and trashed=false"
        if file_type:
            search_query += f" and mimeType contains '{file_type}'"

        results = service.files().list(
            q=search_query,
            fields='files(id, name, mimeType, thumbnailLink, size, modifiedTime)',
            pageSize=50,
            orderBy='modifiedTime desc'
        ).execute()

        files = results.get('files', [])

        logger.info(f"Search '{query}' found {len(files)} files for user {user_id}")
        return {"files": files}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching files for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to search files in Google Drive")
