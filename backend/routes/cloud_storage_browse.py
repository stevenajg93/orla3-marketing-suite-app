"""
Cloud Storage File Browsing Routes
Browse files from Google Drive, OneDrive, and Dropbox
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import httpx
import os
import json
from typing import Optional, List, Dict
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import setup_logger
from db_pool import get_db_connection  # Use connection pool
from middleware import get_user_id
from utils.auth_dependency import get_user_context

router = APIRouter()
logger = setup_logger(__name__)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")



def update_access_token_in_db(user_id: str, organization_id: str, provider: str, new_access_token: str, expires_in: int):
    """Update access token in database after refresh"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            from datetime import datetime, timedelta, timezone
            new_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

            # Try updating organization-level token first
            if organization_id:
                cursor.execute("""
                    UPDATE user_cloud_storage_tokens
                    SET access_token = %s, token_expires_at = %s
                    WHERE organization_id = %s AND provider = %s AND is_active = true
                """, (new_access_token, new_expires_at, str(organization_id), provider))

                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"Updated org-level token for org {organization_id}")
                    return

            # Fallback to user-level token
            cursor.execute("""
                UPDATE user_cloud_storage_tokens
                SET access_token = %s, token_expires_at = %s
                WHERE user_id = %s AND provider = %s AND is_active = true
            """, (new_access_token, new_expires_at, str(user_id), provider))

            conn.commit()
            logger.info(f"Updated user-level token for user {user_id}")

        finally:
            cursor.close()


def get_organization_cloud_connection(organization_id: str, provider: str, user_id: str = None):
    """
    Get organization's cloud storage connection from database

    Organization-level cloud storage ensures all team members access the same shared drive.
    Fallback to user_id for legacy connections created before multi-tenant migration.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Convert to string to avoid UUID adapter errors
        org_id_str = str(organization_id)

        try:
            # Try organization-level connection first
            cursor.execute("""
                SELECT
                    access_token,
                    refresh_token,
                    token_expires_at,
                    provider_email,
                    storage_type,
                    drive_id,
                    metadata
                FROM user_cloud_storage_tokens
                WHERE organization_id = %s
                  AND provider = %s
                  AND is_active = true
                ORDER BY connected_at DESC
                LIMIT 1
            """, (org_id_str, provider))

            connection = cursor.fetchone()

            # Fallback to user-level connection if no org connection found
            if not connection and user_id:
                logger.warning(f"No org-level {provider} found for org {org_id_str}, trying user-level for user {user_id}")
                cursor.execute("""
                    SELECT
                        access_token,
                        refresh_token,
                        token_expires_at,
                        provider_email,
                        storage_type,
                        drive_id,
                        metadata
                    FROM user_cloud_storage_tokens
                    WHERE user_id = %s
                      AND provider = %s
                      AND is_active = true
                    ORDER BY connected_at DESC
                    LIMIT 1
                """, (str(user_id), provider))
                connection = cursor.fetchone()

            if not connection:
                raise HTTPException(
                    status_code=404,
                    detail=f"No active {provider} connection found. Please connect {provider} first."
                )

            # Convert to dict
            connection = dict(connection)

            # Extract selected_folders from metadata if available
            metadata = connection.get('metadata', {}) or {}
            connection['selected_folders'] = metadata.get('selected_folders', [])

            logger.info(f"Cloud connection loaded for organization {org_id_str}: provider={provider}, storage_type={connection.get('storage_type', 'personal')}")
            return connection

        finally:
            cursor.close()


# ============================================================================
# DROPBOX FILE BROWSING
# ============================================================================

@router.get("/cloud-storage/browse/dropbox")
async def browse_dropbox_files(
    request: Request,
    path: Optional[str] = "",
    context: Dict = Depends(get_user_context)
):
    """
    Browse Dropbox files and folders

    Query params:
    - path: Folder path to browse (default: root)

    ORGANIZATION-LEVEL: Shows files from organization's connected Dropbox
    """
    organization_id = context['organization_id']
    user_id = context['user_id']
    connection = get_organization_cloud_connection(organization_id, 'dropbox', user_id)

    access_token = connection['access_token']
    selected_folders = connection.get('selected_folders', [])

    # If user has folder restrictions, check if current path is allowed
    if selected_folders and len(selected_folders) > 0:
        # Check if browsing an allowed folder or subfolder
        is_allowed = any(
            path.startswith(folder['path']) if 'path' in folder else path.startswith(folder.get('id', ''))
            for folder in selected_folders
        )
        if not is_allowed and path != "":
            raise HTTPException(
                status_code=403,
                detail="Access to this folder is restricted. Please select this folder in Cloud Storage settings."
            )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # List folder contents
            response = await client.post(
                "https://api.dropboxapi.com/2/files/list_folder",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "path": f"/{path}" if path and not path.startswith("/") else (path or ""),
                    "recursive": False,
                    "include_media_info": True,
                    "include_deleted": False,
                    "include_has_explicit_shared_members": False
                }
            )

            if response.status_code == 401:
                raise HTTPException(status_code=401, detail="Dropbox access token expired. Please reconnect.")

            if response.status_code != 200:
                logger.error(f"Dropbox API error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail=f"Dropbox API error: {response.text}")

            data = response.json()
            entries = data.get('entries', [])

            # Transform to standard format
            files = []
            folders = []

            for entry in entries:
                if entry['.tag'] == 'folder':
                    folders.append({
                        'id': entry['id'],
                        'name': entry['name'],
                        'type': 'folder',
                        'path': entry['path_display'],
                        'source': 'dropbox'
                    })
                else:
                    # File entry
                    file_info = {
                        'id': entry['id'],
                        'name': entry['name'],
                        'type': get_file_type(entry['name']),
                        'path': entry['path_display'],
                        'size': entry.get('size', 0),
                        'modified': entry.get('client_modified', ''),
                        'source': 'dropbox'
                    }

                    # Add thumbnail if available
                    if 'media_info' in entry and 'metadata' in entry['media_info']:
                        media = entry['media_info']['metadata']
                        if '.tag' in media and media['.tag'] == 'photo':
                            file_info['has_thumbnail'] = True

                    files.append(file_info)

            return {
                "success": True,
                "provider": "dropbox",
                "current_path": path or "/",
                "folders": folders,
                "files": files,
                "has_more": data.get('has_more', False)
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error browsing Dropbox files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to browse Dropbox files: {str(e)}")


@router.get("/cloud-storage/file/dropbox/{file_id}")
async def get_dropbox_file_link(request: Request, file_id: str, context: Dict = Depends(get_user_context)):
    """Get temporary download link for Dropbox file"""
    organization_id = context['organization_id']
    user_id = context['user_id']
    connection = get_organization_cloud_connection(organization_id, 'dropbox', user_id)

    access_token = connection['access_token']

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.dropboxapi.com/2/files/get_temporary_link",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json={"path": file_id}
            )

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to get file link")

            data = response.json()
            return {
                "success": True,
                "link": data.get('link'),
                "metadata": data.get('metadata')
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Dropbox file link: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Dropbox file link")


# ============================================================================
# ONEDRIVE FILE BROWSING
# ============================================================================

@router.get("/cloud-storage/browse/onedrive")
async def browse_onedrive_files(
    request: Request,
    path: Optional[str] = "",
    context: Dict = Depends(get_user_context)
):
    """
    Browse OneDrive files and folders

    Query params:
    - path: Folder path or item ID to browse (default: root)

    ORGANIZATION-LEVEL: Shows files from organization's connected OneDrive
    """
    organization_id = context['organization_id']
    user_id = context['user_id']
    connection = get_organization_cloud_connection(organization_id, 'onedrive', user_id)

    access_token = connection['access_token']
    selected_folders = connection.get('selected_folders', [])

    # If user has folder restrictions, check if current path is allowed
    if selected_folders and len(selected_folders) > 0:
        # Check if browsing an allowed folder (by ID or path)
        is_allowed = any(
            path.startswith(folder.get('id', '')) or path.startswith(folder.get('path', ''))
            for folder in selected_folders
        )
        if not is_allowed and path != "":
            raise HTTPException(
                status_code=403,
                detail="Access to this folder is restricted. Please select this folder in Cloud Storage settings."
            )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Determine endpoint based on path
            if path and path.startswith("items/"):
                # Browse specific folder by ID
                endpoint = f"https://graph.microsoft.com/v1.0/me/drive/{path}/children"
            elif path:
                # Browse by path
                endpoint = f"https://graph.microsoft.com/v1.0/me/drive/root:/{path}:/children"
            else:
                # Browse root
                endpoint = "https://graph.microsoft.com/v1.0/me/drive/root/children"

            response = await client.get(
                endpoint,
                headers={"Authorization": f"Bearer {access_token}"}
            )

            if response.status_code == 401:
                raise HTTPException(status_code=401, detail="OneDrive access token expired. Please reconnect.")

            if response.status_code != 200:
                logger.error(f"OneDrive API error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail=f"OneDrive API error: {response.text}")

            data = response.json()
            items = data.get('value', [])

            # Transform to standard format
            files = []
            folders = []

            for item in items:
                if 'folder' in item:
                    # Folder
                    folders.append({
                        'id': item['id'],
                        'name': item['name'],
                        'type': 'folder',
                        'path': item.get('parentReference', {}).get('path', '') + '/' + item['name'],
                        'item_count': item['folder'].get('childCount', 0),
                        'source': 'onedrive'
                    })
                else:
                    # File
                    file_info = {
                        'id': item['id'],
                        'name': item['name'],
                        'type': get_file_type(item['name']),
                        'size': item.get('size', 0),
                        'modified': item.get('lastModifiedDateTime', ''),
                        'web_url': item.get('webUrl', ''),
                        'source': 'onedrive'
                    }

                    # Add thumbnail URL if available
                    if '@microsoft.graph.downloadUrl' in item:
                        file_info['download_url'] = item['@microsoft.graph.downloadUrl']

                    # Check for thumbnail
                    if 'image' in item or 'video' in item or 'photo' in item:
                        file_info['has_thumbnail'] = True

                    files.append(file_info)

            return {
                "success": True,
                "provider": "onedrive",
                "current_path": path or "/",
                "folders": folders,
                "files": files,
                "next_link": data.get('@odata.nextLink')
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error browsing OneDrive files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to browse OneDrive files: {str(e)}")


@router.get("/cloud-storage/file/onedrive/{item_id}")
async def get_onedrive_file_link(request: Request, item_id: str, context: Dict = Depends(get_user_context)):
    """Get download link for OneDrive file"""
    organization_id = context['organization_id']
    user_id = context['user_id']
    connection = get_organization_cloud_connection(organization_id, 'onedrive', user_id)

    access_token = connection['access_token']

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"https://graph.microsoft.com/v1.0/me/drive/items/{item_id}",
                headers={"Authorization": f"Bearer {access_token}"}
            )

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to get file metadata")

            item = response.json()

            return {
                "success": True,
                "name": item.get('name'),
                "size": item.get('size'),
                "download_url": item.get('@microsoft.graph.downloadUrl'),
                "web_url": item.get('webUrl'),
                "thumbnail_url": item.get('thumbnails', [{}])[0].get('large', {}).get('url') if 'thumbnails' in item else None
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting OneDrive file link: {e}")
        raise HTTPException(status_code=500, detail="Failed to get OneDrive file link")


# ============================================================================
# GOOGLE DRIVE FILE BROWSING
# ============================================================================

@router.get("/cloud-storage/browse/google_drive")
async def browse_google_drive_files(
    request: Request,
    folder_id: Optional[str] = None,
    context: Dict = Depends(get_user_context)
):
    """
    Browse Google Drive files and folders

    Query params:
    - folder_id: Folder ID to browse (default: root)

    ORGANIZATION-LEVEL: Shows files from organization's connected shared drive
    All team members see the same files
    """
    try:
        organization_id = context['organization_id']
        user_id = context['user_id']
        connection = get_organization_cloud_connection(organization_id, 'google_drive', user_id)

        access_token = connection['access_token']
        refresh_token = connection.get('refresh_token')
        token_expires_at = connection.get('token_expires_at')
        selected_folders = connection.get('selected_folders', [])

        # Check if token is expired or about to expire (within 5 minutes)
        from datetime import datetime, timedelta, timezone
        if token_expires_at:
            expiry_time = token_expires_at if isinstance(token_expires_at, datetime) else datetime.fromisoformat(str(token_expires_at))

            # Ensure both datetimes are timezone-aware for comparison
            if expiry_time.tzinfo is None:
                expiry_time = expiry_time.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            time_until_expiry = expiry_time - now

            if time_until_expiry < timedelta(minutes=5):
                logger.info(f"Access token expired or expiring soon, refreshing...")
                if refresh_token:
                    try:
                        new_token_data = await refresh_google_drive_token(refresh_token)
                        access_token = new_token_data['access_token']
                        update_access_token_in_db(user_id, organization_id, 'google_drive', access_token, new_token_data['expires_in'])
                        logger.info("Successfully refreshed and updated Google Drive access token")
                    except Exception as refresh_error:
                        logger.error(f"Failed to refresh token: {str(refresh_error)}")
                        raise HTTPException(
                            status_code=401,
                            detail="Access token expired and refresh failed. Please reconnect Google Drive."
                        )
                else:
                    logger.warning("Token expired but no refresh token available")
                    raise HTTPException(
                        status_code=401,
                        detail="Access token expired. Please reconnect Google Drive."
                    )

        logger.info(f"User {user_id} ({context['role']}) browsing org {organization_id} Google Drive")
    except HTTPException as e:
        logger.error(f"Failed to get organization connection: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting connection: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to access Google Drive: {str(e)}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            files_list = []
            folders_list = []

            # If browsing root, show shared drives as folders
            if not folder_id:
                # List shared drives
                shared_drives_response = await client.get(
                    "https://www.googleapis.com/drive/v3/drives",
                    headers={"Authorization": f"Bearer {access_token}"},
                    params={"pageSize": 100}
                )

                logger.info(f"Shared drives API response: status={shared_drives_response.status_code}")

                # Handle 401 - token expired, try to refresh
                if shared_drives_response.status_code == 401:
                    logger.warning("Received 401 from Google Drive API, attempting token refresh...")
                    if refresh_token:
                        try:
                            new_token_data = await refresh_google_drive_token(refresh_token)
                            access_token = new_token_data['access_token']
                            update_access_token_in_db(user_id, organization_id, 'google_drive', access_token, new_token_data['expires_in'])
                            logger.info("Token refreshed after 401, retrying request...")

                            # Retry the request with new token
                            shared_drives_response = await client.get(
                                "https://www.googleapis.com/drive/v3/drives",
                                headers={"Authorization": f"Bearer {access_token}"},
                                params={"pageSize": 100}
                            )
                        except Exception as e:
                            logger.error(f"Token refresh failed: {str(e)}")
                            raise HTTPException(status_code=401, detail="Authentication failed. Please reconnect Google Drive.")
                    else:
                        raise HTTPException(status_code=401, detail="Access token expired. Please reconnect Google Drive.")

                if shared_drives_response.status_code == 200:
                    shared_drives_data = shared_drives_response.json()
                    drives_count = len(shared_drives_data.get('drives', []))
                    logger.info(f"Found {drives_count} shared drives for org {organization_id}")

                    for drive in shared_drives_data.get('drives', []):
                        folders_list.append({
                            "id": drive['id'],
                            "name": f"📁 {drive['name']} (Shared Drive)",
                            "type": "folder",
                            "mime_type": "application/vnd.google-apps.folder",
                            "size": 0,
                            "source": "google_drive"
                        })
                else:
                    logger.error(f"Shared drives API error: {shared_drives_response.status_code} - {shared_drives_response.text}")

            # Build query for regular files/folders
            if folder_id:
                query = f"'{folder_id}' in parents and trashed=false"
            else:
                query = "'root' in parents and trashed=false"

            # List files and folders
            response = await client.get(
                "https://www.googleapis.com/drive/v3/files",
                headers={"Authorization": f"Bearer {access_token}"},
                params={
                    "q": query,
                    "fields": "files(id, name, mimeType, size, thumbnailLink, webViewLink, modifiedTime)",
                    "pageSize": 1000,
                    "orderBy": "folder,name",
                    "supportsAllDrives": "true",
                    "includeItemsFromAllDrives": "true"
                }
            )

            # Handle 401 - token expired, try to refresh
            if response.status_code == 401:
                logger.warning("Received 401 from Google Drive files API, attempting token refresh...")
                if refresh_token:
                    try:
                        new_token_data = await refresh_google_drive_token(refresh_token)
                        access_token = new_token_data['access_token']
                        update_access_token_in_db(user_id, organization_id, 'google_drive', access_token, new_token_data['expires_in'])
                        logger.info("Token refreshed after 401, retrying files request...")

                        # Retry the request with new token
                        response = await client.get(
                            "https://www.googleapis.com/drive/v3/files",
                            headers={"Authorization": f"Bearer {access_token}"},
                            params={
                                "q": query,
                                "fields": "files(id, name, mimeType, size, thumbnailLink, webViewLink, modifiedTime)",
                                "pageSize": 1000,
                                "orderBy": "folder,name",
                                "supportsAllDrives": "true",
                                "includeItemsFromAllDrives": "true"
                            }
                        )
                    except Exception as e:
                        logger.error(f"Token refresh failed: {str(e)}")
                        raise HTTPException(status_code=401, detail="Authentication failed. Please reconnect Google Drive.")
                else:
                    raise HTTPException(status_code=401, detail="Access token expired. Please reconnect Google Drive.")

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=f"Google Drive API error: {response.text}")

            data = response.json()

            for item in data.get('files', []):
                # Check if it's a folder
                is_folder = item['mimeType'] == 'application/vnd.google-apps.folder'

                # Privacy filtering: if user has selected folders, only show those
                if selected_folders and len(selected_folders) > 0:
                    is_allowed = any(
                        item['id'] == folder.get('id') or
                        folder_id == folder.get('id')  # Allow browsing inside selected folders
                        for folder in selected_folders
                    )
                    if not is_allowed and is_folder:
                        continue  # Skip folders not in selected list

                file_obj = {
                    "id": item['id'],
                    "name": item['name'],
                    "type": "folder" if is_folder else get_file_type(item['name']),
                    "mime_type": item['mimeType'],
                    "size": item.get('size', 0),
                    "thumbnail": item.get('thumbnailLink'),
                    "web_link": item.get('webViewLink'),
                    "modified": item.get('modifiedTime'),
                    "source": "google_drive"
                }

                if is_folder:
                    folders_list.append(file_obj)
                else:
                    files_list.append(file_obj)

            logger.info(f"Returning {len(files_list)} files and {len(folders_list)} folders for org {organization_id}")
            logger.info(f"Folders: {[f['name'] for f in folders_list[:5]]}")  # Log first 5 folder names

            return {
                "success": True,
                "provider": "google_drive",
                "current_folder_id": folder_id or "root",
                "files": files_list,
                "folders": folders_list
            }

    except httpx.HTTPError as e:
        logger.error(f"HTTP error browsing Google Drive: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to browse Google Drive: {str(e)}")
    except HTTPException as e:
        # Re-raise HTTPException with original detail preserved
        logger.error(f"HTTPException browsing Google Drive: {e.detail}", exc_info=True)
        raise
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Error browsing Google Drive: {error_msg}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error browsing Google Drive: {error_msg}")


@router.get("/cloud-storage/file/google_drive/{file_id}")
async def get_google_drive_file_link(request: Request, file_id: str, context: Dict = Depends(get_user_context)):
    """Get download link for Google Drive file"""
    organization_id = context['organization_id']
    user_id = context['user_id']
    connection = get_organization_cloud_connection(organization_id, 'google_drive', user_id)

    access_token = connection['access_token']

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get file metadata including download link
            response = await client.get(
                f"https://www.googleapis.com/drive/v3/files/{file_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"fields": "id,name,mimeType,size,webContentLink,thumbnailLink"}
            )

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=f"Failed to get file: {response.text}")

            data = response.json()

            # Google Drive files have webContentLink for download
            download_link = data.get('webContentLink')

            if not download_link:
                # For Google Docs/Sheets/Slides, we need to export them
                if 'google-apps' in data.get('mimeType', ''):
                    raise HTTPException(status_code=400, detail="Google Docs/Sheets/Slides export not yet supported. Please download as PDF from Google Drive first.")

            return {
                "success": True,
                "link": download_link,
                "metadata": {
                    "id": data.get('id'),
                    "name": data.get('name'),
                    "mime_type": data.get('mimeType'),
                    "size": data.get('size'),
                    "thumbnail": data.get('thumbnailLink')
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Google Drive file: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get Google Drive file")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_file_type(filename: str) -> str:
    """Determine file type from filename"""
    ext = filename.lower().split('.')[-1] if '.' in filename else ''

    if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg']:
        return 'image'
    elif ext in ['mp4', 'mov', 'avi', 'mkv', 'webm', 'flv']:
        return 'video'
    elif ext in ['pdf', 'doc', 'docx', 'txt', 'rtf']:
        return 'document'
    elif ext in ['xls', 'xlsx', 'csv']:
        return 'spreadsheet'
    elif ext in ['ppt', 'pptx']:
        return 'presentation'
    elif ext in ['zip', 'rar', '7z', 'tar', 'gz']:
        return 'archive'
    else:
        return 'file'


# ============================================================================
# FOLDER SELECTION (Privacy & Permissions)
# ============================================================================

class FolderSelectionRequest(BaseModel):
    """Request model for saving folder selections"""
    provider: str  # 'dropbox', 'onedrive', or 'google_drive'
    selected_folders: List[dict]  # Array of {id, name, path} objects


@router.post("/cloud-storage/folders/select")
async def save_folder_selection(request: Request, body: FolderSelectionRequest):
    """
    Save user's folder selections for a cloud storage provider

    Allows users to limit which folders the app can access
    """
    user_id = get_user_id(request)

    # Validate provider
    if body.provider not in ['dropbox', 'onedrive', 'google_drive']:
        raise HTTPException(status_code=400, detail="Invalid provider")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                # Update selected_folders in database
                cursor.execute("""
                    UPDATE user_cloud_storage_tokens
                    SET selected_folders = %s, updated_at = NOW()
                    WHERE user_id = %s AND provider = %s
                """, (json.dumps(body.selected_folders), user_id, body.provider))

                if cursor.rowcount == 0:
                    raise HTTPException(status_code=404, detail=f"{body.provider} not connected")

                conn.commit()

                logger.info(f"✅ Folder selections saved for {body.provider}: {len(body.selected_folders)} folders")

                return {
                    "success": True,
                    "message": f"Saved {len(body.selected_folders)} folder selections",
                    "provider": body.provider,
                    "folder_count": len(body.selected_folders)
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error saving folder selections: {e}")
                conn.rollback()
                raise HTTPException(status_code=500, detail="Failed to save folder selections")
            finally:
                cursor.close()

    except HTTPException:
        raise


@router.get("/cloud-storage/folders/selected/{provider}")
async def get_selected_folders(request: Request, provider: str):
    """
    Get user's selected folders for a provider
    """
    user_id = get_user_id(request)

    if provider not in ['dropbox', 'onedrive', 'google_drive']:
        raise HTTPException(status_code=400, detail="Invalid provider")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT selected_folders
                    FROM user_cloud_storage_tokens
                    WHERE user_id = %s AND provider = %s AND is_active = true
                    LIMIT 1
                """, (user_id, provider))

                result = cursor.fetchone()

                if not result:
                    raise HTTPException(status_code=404, detail=f"{provider} not connected")

                selected_folders = result['selected_folders'] if result['selected_folders'] else []

                return {
                    "success": True,
                    "provider": provider,
                    "selected_folders": selected_folders,
                    "has_restrictions": len(selected_folders) > 0
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting selected folders: {e}")
                raise HTTPException(status_code=500, detail="Failed to get selected folders")
            finally:
                cursor.close()

    except HTTPException:
        raise


@router.get("/cloud-storage/folders/all/{provider}")
async def list_all_folders(request: Request, provider: str):
    """
    List ALL folders from provider (for folder picker UI)

    This endpoint is used during initial setup to let users choose folders.
    It returns all folders regardless of selected_folders setting.
    """
    user_id = get_user_id(request)
    connection = get_user_cloud_connection(user_id, provider)

    access_token = connection['access_token']

    try:
        if provider == 'dropbox':
            return await _list_all_dropbox_folders(access_token)
        elif provider == 'onedrive':
            return await _list_all_onedrive_folders(access_token)
        elif provider == 'google_drive':
            return {
                "success": True,
                "message": "Use /media/folders endpoint for Google Drive",
                "folders": []
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid provider")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing folders for {provider}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list cloud storage folders")


async def _list_all_dropbox_folders(access_token: str) -> dict:
    """Recursively list all Dropbox folders"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.dropboxapi.com/2/files/list_folder",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json={
                "path": "",
                "recursive": True,  # Get all folders recursively
                "include_deleted": False
            }
        )

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to list Dropbox folders")

        data = response.json()
        folders = [
            {
                "id": entry['id'],
                "name": entry['name'],
                "path": entry['path_display']
            }
            for entry in data.get('entries', [])
            if entry['.tag'] == 'folder'
        ]

        return {
            "success": True,
            "provider": "dropbox",
            "folders": folders
        }


async def _list_all_onedrive_folders(access_token: str) -> dict:
    """List all OneDrive folders (root level only for simplicity)"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            "https://graph.microsoft.com/v1.0/me/drive/root/children",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"$filter": "folder ne null"}  # Only folders
        )

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to list OneDrive folders")

        data = response.json()
        folders = [
            {
                "id": item['id'],
                "name": item['name'],
                "path": item.get('parentReference', {}).get('path', '') + '/' + item['name']
            }
            for item in data.get('value', [])
            if 'folder' in item
        ]

        return {
            "success": True,
            "provider": "onedrive",
            "folders": folders
        }
