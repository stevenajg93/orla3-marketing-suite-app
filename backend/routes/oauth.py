"""
OAuth Routes for Social Media Platform Authentication
Handles OAuth 2.0 flows for connecting user accounts to social platforms
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
import httpx
import os
import secrets
from datetime import datetime, timedelta
import psycopg2
from typing import Optional
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import setup_logger
from middleware import get_user_id

router = APIRouter()
logger = setup_logger(__name__)

# OAuth state store (in production, use Redis or database)
oauth_states = {}

# ============================================================================
# DATABASE HELPERS
# ============================================================================

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def save_social_account(platform: str, account_data: dict, user_id: str):
    """Save or update social account in database"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO social_accounts (
                user_id, platform, access_token, refresh_token, token_expires_at,
                account_name, account_id, account_username, account_email,
                profile_image_url, account_metadata, is_default
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (platform, account_id) DO UPDATE SET
                user_id = EXCLUDED.user_id,
                access_token = EXCLUDED.access_token,
                refresh_token = EXCLUDED.refresh_token,
                token_expires_at = EXCLUDED.token_expires_at,
                account_name = EXCLUDED.account_name,
                account_username = EXCLUDED.account_username,
                account_email = EXCLUDED.account_email,
                profile_image_url = EXCLUDED.profile_image_url,
                account_metadata = EXCLUDED.account_metadata,
                is_active = true,
                updated_at = NOW()
            RETURNING id
        """, (
            user_id,
            platform,
            account_data['access_token'],
            account_data.get('refresh_token'),
            account_data.get('expires_at'),
            account_data['account_name'],
            account_data['account_id'],
            account_data.get('account_username'),
            account_data.get('account_email'),
            account_data.get('profile_image_url'),
            account_data.get('metadata', {}),
            account_data.get('is_default', False)
        ))

        account_id = cur.fetchone()[0]
        conn.commit()
        logger.info(f"✅ Saved {platform} account: {account_data['account_name']} (ID: {account_id})")
        return account_id

    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to save {platform} account: {e}")
        raise
    finally:
        cur.close()
        conn.close()

# ============================================================================
# LINKEDIN OAUTH
# ============================================================================

@router.get("/auth/linkedin")
async def linkedin_oauth_start(request: Request):
    """
    Start LinkedIn OAuth 2.0 flow

    Scopes requested:
    - openid: Required for OAuth 2.0
    - profile: Basic profile info (name, photo)
    - email: Email address
    - w_member_social: Post on behalf of user
    """
    client_id = os.getenv("LINKEDIN_CLIENT_ID")
    redirect_uri = f"{Config.BACKEND_URL}/auth/linkedin/callback"

    if not client_id:
        raise HTTPException(status_code=500, detail="LinkedIn OAuth not configured")

    # Get user_id from request context
    user_id = get_user_id(request)

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {
        'platform': 'linkedin',
        'user_id': str(user_id),
        'created_at': datetime.now()
    }

    # LinkedIn OAuth 2.0 authorization URL
    scope = "openid profile email w_member_social"
    auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&state={state}"
        f"&scope={scope}"
    )

    logger.info(f"🔗 Starting LinkedIn OAuth flow with state: {state}")
    return RedirectResponse(url=auth_url)

@router.get("/auth/linkedin/callback")
async def linkedin_oauth_callback(code: str, state: str):
    """
    Handle LinkedIn OAuth callback

    Exchange authorization code for access token and save account
    """
    # Verify state to prevent CSRF
    if state not in oauth_states:
        logger.error(f"❌ Invalid OAuth state: {state}")
        return RedirectResponse(
            url=f"{Config.FRONTEND_URL}/settings?error=invalid_state"
        )

    # Retrieve user_id from state
    user_id = oauth_states[state]['user_id']
    del oauth_states[state]  # Clean up used state

    client_id = os.getenv("LINKEDIN_CLIENT_ID")
    client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
    redirect_uri = f"{Config.BACKEND_URL}/auth/linkedin/callback"

    try:
        async with httpx.AsyncClient() as client:
            # Step 1: Exchange code for access token
            token_response = await client.post(
                "https://www.linkedin.com/oauth/v2/accessToken",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if token_response.status_code != 200:
                logger.error(f"LinkedIn token exchange failed: {token_response.text}")
                return RedirectResponse(
                    url=f"{Config.FRONTEND_URL}/settings?error=token_failed"
                )

            token_data = token_response.json()
            access_token = token_data['access_token']
            expires_in = token_data.get('expires_in', 5184000)  # Default: 60 days

            # Step 2: Get user profile
            profile_response = await client.get(
                "https://api.linkedin.com/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )

            if profile_response.status_code != 200:
                logger.error(f"LinkedIn profile fetch failed: {profile_response.text}")
                return RedirectResponse(
                    url=f"{Config.FRONTEND_URL}/settings?error=profile_failed"
                )

            profile = profile_response.json()

            # Step 3: Save account to database
            account_data = {
                'access_token': access_token,
                'refresh_token': token_data.get('refresh_token'),
                'expires_at': datetime.now() + timedelta(seconds=expires_in),
                'account_name': profile.get('name'),
                'account_id': profile.get('sub'),  # LinkedIn's user ID
                'account_email': profile.get('email'),
                'profile_image_url': profile.get('picture'),
                'metadata': {
                    'locale': profile.get('locale'),
                    'given_name': profile.get('given_name'),
                    'family_name': profile.get('family_name')
                },
                'is_default': True  # Make first account default
            }

            account_id = save_social_account('linkedin', account_data, user_id)

            logger.info(f"✅ LinkedIn account connected: {profile.get('name')}")
            return RedirectResponse(
                url=f"{Config.FRONTEND_URL}/settings?success=linkedin_connected&account_id={account_id}"
            )

    except Exception as e:
        logger.error(f"LinkedIn OAuth error: {e}")
        return RedirectResponse(
            url=f"{Config.FRONTEND_URL}/settings?error=oauth_failed"
        )

# ============================================================================
# ACCOUNT MANAGEMENT
# ============================================================================

@router.get("/auth/accounts")
async def get_connected_accounts(request: Request):
    """Get all connected social media accounts for the current user"""
    user_id = get_user_id(request)
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT
                id, platform, account_name, account_username,
                account_email, profile_image_url, is_active,
                is_default, connected_at, last_used_at
            FROM social_accounts
            WHERE user_id = %s AND is_active = true
            ORDER BY platform, is_default DESC, connected_at DESC
        """, (str(user_id),))

        accounts = []
        for row in cur.fetchall():
            accounts.append({
                'id': str(row[0]),
                'platform': row[1],
                'account_name': row[2],
                'account_username': row[3],
                'account_email': row[4],
                'profile_image_url': row[5],
                'is_active': row[6],
                'is_default': row[7],
                'connected_at': row[8].isoformat() if row[8] else None,
                'last_used_at': row[9].isoformat() if row[9] else None
            })

        return {
            'success': True,
            'accounts': accounts,
            'total': len(accounts)
        }

    finally:
        cur.close()
        conn.close()

@router.delete("/auth/accounts/{account_id}")
async def disconnect_account(account_id: str, request: Request):
    """Disconnect a social media account (only if owned by current user)"""
    user_id = get_user_id(request)
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            UPDATE social_accounts
            SET is_active = false, updated_at = NOW()
            WHERE id = %s AND user_id = %s
            RETURNING platform, account_name
        """, (account_id, str(user_id)))

        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Account not found")

        conn.commit()
        logger.info(f"🔌 Disconnected {result[0]} account: {result[1]}")

        return {
            'success': True,
            'message': f'{result[0]} account disconnected successfully'
        }

    finally:
        cur.close()
        conn.close()

@router.post("/auth/accounts/{account_id}/set-default")
async def set_default_account(account_id: str, request: Request):
    """Set an account as the default for its platform (only if owned by current user)"""
    user_id = get_user_id(request)
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Get the account's platform (verify ownership)
        cur.execute(
            "SELECT platform FROM social_accounts WHERE id = %s AND user_id = %s",
            (account_id, str(user_id))
        )
        result = cur.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Account not found")

        platform = result[0]

        # Unset all defaults for this platform and user
        cur.execute("""
            UPDATE social_accounts
            SET is_default = false
            WHERE platform = %s AND user_id = %s
        """, (platform, str(user_id)))

        # Set this account as default
        cur.execute("""
            UPDATE social_accounts
            SET is_default = true, updated_at = NOW()
            WHERE id = %s AND user_id = %s
        """, (account_id, str(user_id)))

        conn.commit()
        logger.info(f"⭐ Set default {platform} account: {account_id}")

        return {
            'success': True,
            'message': f'Default {platform} account updated'
        }

    finally:
        cur.close()
        conn.close()
