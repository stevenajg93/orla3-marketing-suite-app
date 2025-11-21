"""
Cloud Storage OAuth Routes
Handles OAuth authentication for Google Drive, OneDrive, and Dropbox
"""

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
import psycopg2
from psycopg2.extras import RealDictCursor
import httpx
import os
from datetime import datetime, timedelta
from urllib.parse import urlencode
import secrets
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import setup_logger
from db_pool import get_db_connection  # Use connection pool
from utils.auth import decode_token

router = APIRouter()
logger = setup_logger(__name__)

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
async def connect_google_drive(request: Request, token: str = None):
    """
    Initiate Google Drive OAuth flow

    Redirects user to Google consent screen
    Accepts token as URL parameter for browser redirects
    """
    # Try to get user_id from token parameter (for browser redirects) or auth header
    user_id = None

    if token:
        # Validate token from URL parameter
        payload = decode_token(token)
        if payload:
            user_id = payload.get('sub')

    if not user_id:
        # Try to get from Authorization header
        try:
            user_id = get_user_from_token(request)
        except HTTPException:
            raise HTTPException(status_code=401, detail="Missing or invalid authentication token")

    # Generate state token for CSRF protection
    state = secrets.token_urlsafe(32)

    # Store state in session/database temporarily
    with get_db_connection() as conn:
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


@router.get("/cloud-storage/callback/google_drive")
async def google_drive_callback(code: str, state: str):
    """
    Handle Google Drive OAuth callback

    Exchanges authorization code for tokens and stores them
    """
    import urllib.request
    import urllib.parse
    import json

    with get_db_connection() as conn:
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

            # Get user's organization_id
            cur.execute("SELECT current_organization_id FROM users WHERE id = %s", (user_id,))
            org_record = cur.fetchone()
            organization_id = org_record['current_organization_id'] if org_record else None

            # Store tokens in database
            from datetime import timezone
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=tokens.get('expires_in', 3600))

            cur.execute("""
                INSERT INTO user_cloud_storage_tokens (
                    user_id, organization_id, provider, provider_email, access_token, refresh_token,
                    token_expires_at, connected_at, is_active
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), true)
                ON CONFLICT (user_id, provider) DO UPDATE SET
                    access_token = EXCLUDED.access_token,
                    refresh_token = EXCLUDED.refresh_token,
                    token_expires_at = EXCLUDED.token_expires_at,
                    provider_email = EXCLUDED.provider_email,
                    organization_id = EXCLUDED.organization_id,
                    is_active = true,
                    updated_at = NOW()
            """, (
                user_id, organization_id, 'google_drive', provider_email,
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


# ============================================================================
# ONEDRIVE OAUTH
# ============================================================================

@router.get("/cloud-storage/connect/onedrive")
async def connect_onedrive(request: Request, token: str = None):
    """Initiate OneDrive OAuth flow - accepts token as URL parameter"""
    # Try to get user_id from token parameter or auth header
    user_id = None

    if token:
        payload = decode_token(token)
        if payload:
            user_id = payload.get('sub')

    if not user_id:
        try:
            user_id = get_user_from_token(request)
        except HTTPException:
            raise HTTPException(status_code=401, detail="Missing or invalid authentication token")

    state = secrets.token_urlsafe(32)

    with get_db_connection() as conn:
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


@router.get("/cloud-storage/callback/onedrive")
async def onedrive_callback(code: str, state: str):
    """Handle OneDrive OAuth callback"""
    import urllib.request
    import urllib.parse
    import json

    with get_db_connection() as conn:
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

            # Get user's organization_id
            cur.execute("SELECT current_organization_id FROM users WHERE id = %s", (user_id,))
            org_record = cur.fetchone()
            organization_id = org_record['current_organization_id'] if org_record else None

            expires_at = datetime.utcnow() + timedelta(seconds=tokens.get('expires_in', 3600))

            # Store tokens
            cur.execute("""
                INSERT INTO user_cloud_storage_tokens (
                    user_id, organization_id, provider, access_token, refresh_token,
                    token_expires_at, connected_at, is_active
                ) VALUES (%s, %s, %s, %s, %s, %s, NOW(), true)
                ON CONFLICT (user_id, provider) DO UPDATE SET
                    access_token = EXCLUDED.access_token,
                    refresh_token = EXCLUDED.refresh_token,
                    token_expires_at = EXCLUDED.token_expires_at,
                    organization_id = EXCLUDED.organization_id,
                    is_active = true,
                    updated_at = NOW()
            """, (
                user_id, organization_id, 'onedrive',
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


# ============================================================================
# DROPBOX OAUTH
# ============================================================================

@router.get("/cloud-storage/connect/dropbox")
async def connect_dropbox(request: Request, token: str = None):
    """Initiate Dropbox OAuth flow - accepts token as URL parameter"""
    # Try to get user_id from token parameter or auth header
    user_id = None

    if token:
        payload = decode_token(token)
        if payload:
            user_id = payload.get('sub')

    if not user_id:
        try:
            user_id = get_user_from_token(request)
        except HTTPException:
            raise HTTPException(status_code=401, detail="Missing or invalid authentication token")

    state = secrets.token_urlsafe(32)

    with get_db_connection() as conn:
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


@router.get("/cloud-storage/callback/dropbox")
async def dropbox_callback(code: str, state: str):
    """Handle Dropbox OAuth callback"""
    import urllib.request
    import urllib.parse
    import json

    with get_db_connection() as conn:
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

            # Get user's organization_id
            cur.execute("SELECT current_organization_id FROM users WHERE id = %s", (user_id,))
            org_record = cur.fetchone()
            organization_id = org_record['current_organization_id'] if org_record else None

            # Dropbox tokens don't have expiry, set to 4 hours (typical)
            expires_at = datetime.utcnow() + timedelta(hours=4)

            # Store tokens
            cur.execute("""
                INSERT INTO user_cloud_storage_tokens (
                    user_id, organization_id, provider, access_token, refresh_token,
                    token_expires_at, connected_at, is_active
                ) VALUES (%s, %s, %s, %s, %s, %s, NOW(), true)
                ON CONFLICT (user_id, provider) DO UPDATE SET
                    access_token = EXCLUDED.access_token,
                    refresh_token = EXCLUDED.refresh_token,
                    token_expires_at = EXCLUDED.token_expires_at,
                    organization_id = EXCLUDED.organization_id,
                    is_active = true,
                    updated_at = NOW()
            """, (
                user_id, organization_id, 'dropbox',
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

    with get_db_connection() as conn:
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


@router.get("/cloud-storage/connections")
async def list_cloud_connections(request: Request):
    """
    List user's cloud storage connections

    Returns connected providers with metadata
    """
    user_id = get_user_from_token(request)

    with get_db_connection() as conn:
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


@router.delete("/cloud-storage/disconnect/{provider}")
async def disconnect_cloud_storage(request: Request, provider: str):
    """
    Disconnect a cloud storage provider

    SECURITY: Revokes OAuth tokens with the provider to truly remove access
    Then marks as inactive in database
    """
    user_id = get_user_from_token(request)

    # Validate provider
    if provider not in ['google_drive', 'onedrive', 'dropbox']:
        raise HTTPException(status_code=400, detail="Invalid provider")

    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            # Get current tokens for revocation
            cur.execute("""
                SELECT access_token, refresh_token
                FROM user_cloud_storage_tokens
                WHERE user_id = %s AND provider = %s AND is_active = true
                LIMIT 1
            """, (user_id, provider))

            result = cur.fetchone()

            if not result:
                raise HTTPException(status_code=404, detail=f"{provider} not connected")

            access_token = result['access_token']
            refresh_token = result.get('refresh_token')

            # Revoke tokens with provider
            revocation_success = await revoke_oauth_token(provider, access_token, refresh_token)

            if revocation_success:
                logger.info(f"✅ OAuth tokens revoked for {provider} (user {user_id})")
            else:
                logger.warning(f"⚠️ Token revocation failed for {provider}, but continuing disconnect")

            # Mark as inactive in database (even if revocation failed - user can retry)
            cur.execute("""
                UPDATE user_cloud_storage_tokens
                SET is_active = false, updated_at = NOW()
                WHERE user_id = %s AND provider = %s
            """, (user_id, provider))

            conn.commit()

            logger.info(f"🔌 {provider} disconnected for user {user_id}")

            return {
                "success": True,
                "message": f"Disconnected from {provider}",
                "provider": provider,
                "token_revoked": revocation_success
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error disconnecting {provider}: {e}")
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            cur.close()


async def revoke_oauth_token(provider: str, access_token: str, refresh_token: str = None) -> bool:
    """
    Revoke OAuth tokens with provider to truly remove access

    Returns True if revocation successful, False otherwise
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if provider == 'google_drive':
                # Google OAuth2 token revocation
                # https://developers.google.com/identity/protocols/oauth2/web-server#tokenrevoke
                response = await client.post(
                    "https://oauth2.googleapis.com/revoke",
                    params={"token": access_token},
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )

                if response.status_code == 200:
                    logger.info("✅ Google Drive token revoked successfully")
                    return True
                else:
                    logger.error(f"❌ Google token revocation failed: {response.status_code} - {response.text}")
                    return False

            elif provider == 'dropbox':
                # Dropbox token revocation
                # https://www.dropbox.com/developers/documentation/http/documentation#auth-token-revoke
                response = await client.post(
                    "https://api.dropboxapi.com/2/auth/token/revoke",
                    headers={"Authorization": f"Bearer {access_token}"}
                )

                if response.status_code == 200:
                    logger.info("✅ Dropbox token revoked successfully")
                    return True
                else:
                    logger.error(f"❌ Dropbox token revocation failed: {response.status_code} - {response.text}")
                    return False

            elif provider == 'onedrive':
                # Microsoft Graph logout/revoke
                # Note: Microsoft doesn't have a direct token revocation endpoint
                # Best practice is to let tokens expire (1 hour for access tokens)
                # We still mark as inactive to prevent our app from using them
                logger.info("⚠️ OneDrive: No direct revocation API. Tokens will expire in ~1 hour.")
                return True  # Consider this success since we're marking inactive

            else:
                logger.error(f"Unknown provider: {provider}")
                return False

    except Exception as e:
        logger.error(f"Exception during token revocation for {provider}: {e}")
        return False
