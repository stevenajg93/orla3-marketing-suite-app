"""
Cloud Storage OAuth Routes
Handles OAuth authentication for Google Drive, OneDrive, and Dropbox
"""

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime, timedelta
from urllib.parse import urlencode
import secrets
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import setup_logger
from utils.auth import decode_token

router = APIRouter()
logger = setup_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# OAuth Configuration
GOOGLE_DRIVE_CONFIG = {
    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
    "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
    "token_url": "https://oauth2.googleapis.com/token",
    "scopes": [
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/userinfo.email"
    ]
}

ONEDRIVE_CONFIG = {
    "client_id": os.getenv("ONEDRIVE_CLIENT_ID"),
    "client_secret": os.getenv("ONEDRIVE_CLIENT_SECRET"),
    "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
    "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
    "scopes": ["Files.Read", "Files.Read.All", "offline_access"]
}

DROPBOX_CONFIG = {
    "app_key": os.getenv("DROPBOX_APP_KEY"),
    "app_secret": os.getenv("DROPBOX_APP_SECRET"),
    "auth_url": "https://www.dropbox.com/oauth2/authorize",
    "token_url": "https://api.dropboxapi.com/oauth2/token"
}


def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def get_user_from_token(request: Request):
    """Extract user from JWT token"""
    auth_header = request.headers.get('authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Missing authorization token")

    token = auth_header.replace('Bearer ', '')
    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload.get('sub')  # user_id


# ============================================================================
# GOOGLE DRIVE OAUTH
# ============================================================================

@router.get("/cloud-storage/connect/google_drive")
async def connect_google_drive(request: Request):
    """
    Initiate Google Drive OAuth flow

    Redirects user to Google consent screen
    """
    user_id = get_user_from_token(request)

    # Generate state token for CSRF protection
    state = secrets.token_urlsafe(32)

    # Store state in session/database temporarily
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Store state with user_id (expires in 10 minutes)
        cur.execute("""
            INSERT INTO oauth_states (state, user_id, provider, expires_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (state) DO UPDATE SET user_id = EXCLUDED.user_id
        """, (state, user_id, 'google_drive', datetime.utcnow() + timedelta(minutes=10)))
        conn.commit()

        # Build OAuth URL
        params = {
            'client_id': GOOGLE_DRIVE_CONFIG['client_id'],
            'redirect_uri': f"{os.getenv('BACKEND_URL')}/cloud-storage/callback/google_drive",
            'response_type': 'code',
            'scope': ' '.join(GOOGLE_DRIVE_CONFIG['scopes']),
            'access_type': 'offline',
            'prompt': 'consent',
            'state': state
        }

        auth_url = f"{GOOGLE_DRIVE_CONFIG['auth_url']}?{urlencode(params)}"

        logger.info(f"🔐 Google Drive OAuth initiated for user {user_id}")

        return RedirectResponse(url=auth_url)

    finally:
        cur.close()
        conn.close()


@router.get("/cloud-storage/callback/google_drive")
async def google_drive_callback(code: str, state: str):
    """
    Handle Google Drive OAuth callback

    Exchanges authorization code for tokens and stores them
    """
    import urllib.request
    import urllib.parse
    import json

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Verify state token
        cur.execute("""
            SELECT user_id FROM oauth_states
            WHERE state = %s AND provider = 'google_drive' AND expires_at > NOW()
        """, (state,))

        state_record = cur.fetchone()
        if not state_record:
            raise HTTPException(status_code=400, detail="Invalid or expired state token")

        user_id = state_record['user_id']

        # Exchange code for tokens
        data = {
            'client_id': GOOGLE_DRIVE_CONFIG['client_id'],
            'client_secret': GOOGLE_DRIVE_CONFIG['client_secret'],
            'code': code,
            'redirect_uri': f"{os.getenv('BACKEND_URL')}/cloud-storage/callback/google_drive",
            'grant_type': 'authorization_code'
        }

        encoded_data = urllib.parse.urlencode(data).encode('utf-8')
        req = urllib.request.Request(GOOGLE_DRIVE_CONFIG['token_url'], data=encoded_data, method='POST')

        with urllib.request.urlopen(req) as response:
            tokens = json.loads(response.read().decode('utf-8'))

        # Get user email from Google
        user_info_url = f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={tokens['access_token']}"
        req = urllib.request.Request(user_info_url)
        with urllib.request.urlopen(req) as response:
            user_info = json.loads(response.read().decode('utf-8'))

        provider_email = user_info.get('email')

        # Store tokens in database
        expires_at = datetime.utcnow() + timedelta(seconds=tokens.get('expires_in', 3600))

        cur.execute("""
            INSERT INTO user_cloud_storage_tokens (
                user_id, provider, provider_email, access_token, refresh_token,
                token_expires_at, connected_at, is_active
            ) VALUES (%s, %s, %s, %s, %s, %s, NOW(), true)
            ON CONFLICT (user_id, provider) DO UPDATE SET
                access_token = EXCLUDED.access_token,
                refresh_token = EXCLUDED.refresh_token,
                token_expires_at = EXCLUDED.token_expires_at,
                provider_email = EXCLUDED.provider_email,
                is_active = true,
                updated_at = NOW()
        """, (
            user_id, 'google_drive', provider_email,
            tokens['access_token'], tokens['refresh_token'], expires_at
        ))

        # Delete used state token
        cur.execute("DELETE FROM oauth_states WHERE state = %s", (state,))

        conn.commit()

        logger.info(f"✅ Google Drive connected for user {user_id}: {provider_email}")

        # Redirect back to frontend settings page
        return RedirectResponse(url=f"{FRONTEND_URL}/dashboard/settings?cloud_connected=google_drive")

    except Exception as e:
        logger.error(f"❌ Google Drive OAuth error: {str(e)}")
        return RedirectResponse(url=f"{FRONTEND_URL}/dashboard/settings?error=oauth_failed")

    finally:
        cur.close()
        conn.close()


# ============================================================================
# ONEDRIVE OAUTH
# ============================================================================

@router.get("/cloud-storage/connect/onedrive")
async def connect_onedrive(request: Request):
    """Initiate OneDrive OAuth flow"""
    user_id = get_user_from_token(request)

    state = secrets.token_urlsafe(32)

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO oauth_states (state, user_id, provider, expires_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (state) DO UPDATE SET user_id = EXCLUDED.user_id
        """, (state, user_id, 'onedrive', datetime.utcnow() + timedelta(minutes=10)))
        conn.commit()

        params = {
            'client_id': ONEDRIVE_CONFIG['client_id'],
            'redirect_uri': f"{os.getenv('BACKEND_URL')}/cloud-storage/callback/onedrive",
            'response_type': 'code',
            'scope': ' '.join(ONEDRIVE_CONFIG['scopes']),
            'response_mode': 'query',
            'state': state
        }

        auth_url = f"{ONEDRIVE_CONFIG['auth_url']}?{urlencode(params)}"

        logger.info(f"🔐 OneDrive OAuth initiated for user {user_id}")

        return RedirectResponse(url=auth_url)

    finally:
        cur.close()
        conn.close()


@router.get("/cloud-storage/callback/onedrive")
async def onedrive_callback(code: str, state: str):
    """Handle OneDrive OAuth callback"""
    import urllib.request
    import urllib.parse
    import json

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Verify state
        cur.execute("""
            SELECT user_id FROM oauth_states
            WHERE state = %s AND provider = 'onedrive' AND expires_at > NOW()
        """, (state,))

        state_record = cur.fetchone()
        if not state_record:
            raise HTTPException(status_code=400, detail="Invalid or expired state token")

        user_id = state_record['user_id']

        # Exchange code for tokens
        data = {
            'client_id': ONEDRIVE_CONFIG['client_id'],
            'client_secret': ONEDRIVE_CONFIG['client_secret'],
            'code': code,
            'redirect_uri': f"{os.getenv('BACKEND_URL')}/cloud-storage/callback/onedrive",
            'grant_type': 'authorization_code'
        }

        encoded_data = urllib.parse.urlencode(data).encode('utf-8')
        req = urllib.request.Request(ONEDRIVE_CONFIG['token_url'], data=encoded_data, method='POST')

        with urllib.request.urlopen(req) as response:
            tokens = json.loads(response.read().decode('utf-8'))

        expires_at = datetime.utcnow() + timedelta(seconds=tokens.get('expires_in', 3600))

        # Store tokens
        cur.execute("""
            INSERT INTO user_cloud_storage_tokens (
                user_id, provider, access_token, refresh_token,
                token_expires_at, connected_at, is_active
            ) VALUES (%s, %s, %s, %s, %s, NOW(), true)
            ON CONFLICT (user_id, provider) DO UPDATE SET
                access_token = EXCLUDED.access_token,
                refresh_token = EXCLUDED.refresh_token,
                token_expires_at = EXCLUDED.token_expires_at,
                is_active = true,
                updated_at = NOW()
        """, (
            user_id, 'onedrive',
            tokens['access_token'], tokens['refresh_token'], expires_at
        ))

        cur.execute("DELETE FROM oauth_states WHERE state = %s", (state,))
        conn.commit()

        logger.info(f"✅ OneDrive connected for user {user_id}")

        return RedirectResponse(url=f"{FRONTEND_URL}/dashboard/settings?cloud_connected=onedrive")

    except Exception as e:
        logger.error(f"❌ OneDrive OAuth error: {str(e)}")
        return RedirectResponse(url=f"{FRONTEND_URL}/dashboard/settings?error=oauth_failed")

    finally:
        cur.close()
        conn.close()


# ============================================================================
# DROPBOX OAUTH
# ============================================================================

@router.get("/cloud-storage/connect/dropbox")
async def connect_dropbox(request: Request):
    """Initiate Dropbox OAuth flow"""
    user_id = get_user_from_token(request)

    state = secrets.token_urlsafe(32)

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO oauth_states (state, user_id, provider, expires_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (state) DO UPDATE SET user_id = EXCLUDED.user_id
        """, (state, user_id, 'dropbox', datetime.utcnow() + timedelta(minutes=10)))
        conn.commit()

        params = {
            'client_id': DROPBOX_CONFIG['app_key'],
            'redirect_uri': f"{os.getenv('BACKEND_URL')}/cloud-storage/callback/dropbox",
            'response_type': 'code',
            'token_access_type': 'offline',
            'state': state
        }

        auth_url = f"{DROPBOX_CONFIG['auth_url']}?{urlencode(params)}"

        logger.info(f"🔐 Dropbox OAuth initiated for user {user_id}")

        return RedirectResponse(url=auth_url)

    finally:
        cur.close()
        conn.close()


@router.get("/cloud-storage/callback/dropbox")
async def dropbox_callback(code: str, state: str):
    """Handle Dropbox OAuth callback"""
    import urllib.request
    import urllib.parse
    import json

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Verify state
        cur.execute("""
            SELECT user_id FROM oauth_states
            WHERE state = %s AND provider = 'dropbox' AND expires_at > NOW()
        """, (state,))

        state_record = cur.fetchone()
        if not state_record:
            raise HTTPException(status_code=400, detail="Invalid or expired state token")

        user_id = state_record['user_id']

        # Exchange code for tokens
        data = {
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': f"{os.getenv('BACKEND_URL')}/cloud-storage/callback/dropbox",
            'client_id': DROPBOX_CONFIG['app_key'],
            'client_secret': DROPBOX_CONFIG['app_secret']
        }

        encoded_data = urllib.parse.urlencode(data).encode('utf-8')
        req = urllib.request.Request(DROPBOX_CONFIG['token_url'], data=encoded_data, method='POST')

        with urllib.request.urlopen(req) as response:
            tokens = json.loads(response.read().decode('utf-8'))

        # Dropbox tokens don't have expiry, set to 4 hours (typical)
        expires_at = datetime.utcnow() + timedelta(hours=4)

        # Store tokens
        cur.execute("""
            INSERT INTO user_cloud_storage_tokens (
                user_id, provider, access_token, refresh_token,
                token_expires_at, connected_at, is_active
            ) VALUES (%s, %s, %s, %s, %s, NOW(), true)
            ON CONFLICT (user_id, provider) DO UPDATE SET
                access_token = EXCLUDED.access_token,
                refresh_token = EXCLUDED.refresh_token,
                token_expires_at = EXCLUDED.token_expires_at,
                is_active = true,
                updated_at = NOW()
        """, (
            user_id, 'dropbox',
            tokens['access_token'], tokens.get('refresh_token', ''), expires_at
        ))

        cur.execute("DELETE FROM oauth_states WHERE state = %s", (state,))
        conn.commit()

        logger.info(f"✅ Dropbox connected for user {user_id}")

        return RedirectResponse(url=f"{FRONTEND_URL}/dashboard/settings?cloud_connected=dropbox")

    except Exception as e:
        logger.error(f"❌ Dropbox OAuth error: {str(e)}")
        return RedirectResponse(url=f"{FRONTEND_URL}/dashboard/settings?error=oauth_failed")

    finally:
        cur.close()
        conn.close()


# ============================================================================
# DISCONNECT & LIST
# ============================================================================

@router.delete("/cloud-storage/disconnect/{provider}")
async def disconnect_cloud_storage(provider: str, request: Request):
    """
    Disconnect a cloud storage provider

    Removes OAuth tokens from database
    """
    user_id = get_user_from_token(request)

    if provider not in ['google_drive', 'onedrive', 'dropbox']:
        raise HTTPException(status_code=400, detail="Invalid provider")

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            DELETE FROM user_cloud_storage_tokens
            WHERE user_id = %s AND provider = %s
        """, (user_id, provider))

        conn.commit()

        logger.info(f"🔌 {provider} disconnected for user {user_id}")

        return {"success": True, "message": f"{provider} disconnected"}

    finally:
        cur.close()
        conn.close()


@router.get("/cloud-storage/connections")
async def list_cloud_connections(request: Request):
    """
    List user's cloud storage connections

    Returns connected providers with metadata
    """
    user_id = get_user_from_token(request)

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT provider, provider_email, connected_at, is_active,
                   token_expires_at, last_refreshed_at
            FROM user_cloud_storage_tokens
            WHERE user_id = %s AND is_active = true
            ORDER BY connected_at DESC
        """, (user_id,))

        connections = cur.fetchall()

        return {
            "success": True,
            "connections": [dict(conn) for conn in connections]
        }

    finally:
        cur.close()
        conn.close()
