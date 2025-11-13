"""
Social Media OAuth Routes - Multi-Platform Authentication
Handles OAuth flows for all 9 supported social platforms
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import httpx
import os
import secrets
import hashlib
import base64

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import setup_logger
from utils.auth import decode_token

logger = setup_logger(__name__)
router = APIRouter()

DATABASE_URL = os.getenv("DATABASE_URL")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# OAuth Credentials - All platforms
INSTAGRAM_CLIENT_ID = os.getenv("INSTAGRAM_CLIENT_ID")
INSTAGRAM_CLIENT_SECRET = os.getenv("INSTAGRAM_CLIENT_SECRET")

LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")

FACEBOOK_CLIENT_ID = os.getenv("FACEBOOK_CLIENT_ID")
FACEBOOK_CLIENT_SECRET = os.getenv("FACEBOOK_CLIENT_SECRET")

TWITTER_CLIENT_ID = os.getenv("TWITTER_CLIENT_ID")
TWITTER_CLIENT_SECRET = os.getenv("TWITTER_CLIENT_SECRET")

TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")

YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")

TUMBLR_CONSUMER_KEY = os.getenv("TUMBLR_CONSUMER_KEY")
TUMBLR_CONSUMER_SECRET = os.getenv("TUMBLR_CONSUMER_SECRET")

WORDPRESS_CLIENT_ID = os.getenv("WORDPRESS_CLIENT_ID")
WORDPRESS_CLIENT_SECRET = os.getenv("WORDPRESS_CLIENT_SECRET")


# OAuth Configuration for each platform
PLATFORM_CONFIG = {
    "instagram": {
        # Instagram uses Facebook OAuth (Meta owns Instagram)
        "auth_url": "https://www.facebook.com/v18.0/dialog/oauth",
        "token_url": "https://graph.facebook.com/v18.0/oauth/access_token",
        "scopes": ["instagram_basic", "instagram_content_publish", "pages_show_list", "pages_read_engagement"],
        "client_id": INSTAGRAM_CLIENT_ID,
        "client_secret": INSTAGRAM_CLIENT_SECRET,
    },
    "linkedin": {
        "auth_url": "https://www.linkedin.com/oauth/v2/authorization",
        "token_url": "https://www.linkedin.com/oauth/v2/accessToken",
        "scopes": ["w_member_social", "r_liteprofile", "r_emailaddress"],
        "client_id": LINKEDIN_CLIENT_ID,
        "client_secret": LINKEDIN_CLIENT_SECRET,
    },
    "facebook": {
        "auth_url": "https://www.facebook.com/v18.0/dialog/oauth",
        "token_url": "https://graph.facebook.com/v18.0/oauth/access_token",
        "scopes": ["pages_manage_posts", "pages_read_engagement", "pages_show_list"],
        "client_id": FACEBOOK_CLIENT_ID,
        "client_secret": FACEBOOK_CLIENT_SECRET,
    },
    "twitter": {
        "auth_url": "https://twitter.com/i/oauth2/authorize",
        "token_url": "https://api.twitter.com/2/oauth2/token",
        "scopes": ["tweet.read", "tweet.write", "users.read", "offline.access"],
        "client_id": TWITTER_CLIENT_ID,
        "client_secret": TWITTER_CLIENT_SECRET,
    },
    "tiktok": {
        "auth_url": "https://www.tiktok.com/v2/auth/authorize/",
        "token_url": "https://open.tiktokapis.com/v2/oauth/token/",
        "scopes": ["user.info.basic", "video.upload", "video.publish"],
        "client_id": TIKTOK_CLIENT_KEY,
        "client_secret": TIKTOK_CLIENT_SECRET,
    },
    "youtube": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scopes": ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"],
        "client_id": YOUTUBE_CLIENT_ID,
        "client_secret": YOUTUBE_CLIENT_SECRET,
    },
    "reddit": {
        "auth_url": "https://www.reddit.com/api/v1/authorize",
        "token_url": "https://www.reddit.com/api/v1/access_token",
        "scopes": ["identity", "submit", "read"],
        "client_id": REDDIT_CLIENT_ID,
        "client_secret": REDDIT_CLIENT_SECRET,
    },
    "tumblr": {
        "auth_url": "https://www.tumblr.com/oauth2/authorize",
        "token_url": "https://api.tumblr.com/v2/oauth2/token",
        "scopes": ["basic", "write"],
        "client_id": TUMBLR_CONSUMER_KEY,
        "client_secret": TUMBLR_CONSUMER_SECRET,
    },
    "wordpress": {
        "auth_url": "https://public-api.wordpress.com/oauth2/authorize",
        "token_url": "https://public-api.wordpress.com/oauth2/token",
        "scopes": ["posts"],
        "client_id": WORDPRESS_CLIENT_ID,
        "client_secret": WORDPRESS_CLIENT_SECRET,
    },
}


class OAuthState(BaseModel):
    platform: str
    user_id: str
    state: str
    created_at: datetime


def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def get_user_from_token(request: Request) -> str:
    """Extract user_id from JWT token"""
    auth_header = request.headers.get('authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Missing authorization token")

    token = auth_header.replace('Bearer ', '')
    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload.get('sub')  # user_id


def generate_pkce_pair():
    """Generate PKCE code_verifier and code_challenge for Twitter OAuth"""
    # Generate random code_verifier (43-128 characters)
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')

    # Create code_challenge (SHA256 hash of verifier)
    challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(challenge).decode('utf-8').rstrip('=')

    return code_verifier, code_challenge


def store_oauth_state(user_id: str, platform: str, state: str, code_verifier: Optional[str] = None):
    """Store OAuth state for CSRF protection (optionally with PKCE verifier)"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Store state temporarily (expires in 10 minutes)
        # Note: table uses 'provider' column name (from cloud storage OAuth)
        # code_verifier stored in metadata column as JSON
        metadata = None
        if code_verifier:
            import json
            metadata = json.dumps({"code_verifier": code_verifier})

        cur.execute("""
            INSERT INTO oauth_states (user_id, provider, state, expires_at, metadata)
            VALUES (%s, %s, %s, NOW() + INTERVAL '10 minutes', %s)
            ON CONFLICT (state)
            DO UPDATE SET expires_at = EXCLUDED.expires_at, metadata = EXCLUDED.metadata
        """, (user_id, platform, state, metadata))

        conn.commit()
        logger.info(f"Stored OAuth state for user {user_id}, platform {platform}")
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to store OAuth state: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def verify_oauth_state(state: str) -> tuple[str, str, Optional[str]]:
    """Verify OAuth state and return user_id, platform, and optional code_verifier"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Note: table uses 'provider' column name (from cloud storage OAuth)
        cur.execute("""
            SELECT user_id, provider, metadata
            FROM oauth_states
            WHERE state = %s AND expires_at > NOW()
        """, (state,))

        result = cur.fetchone()

        if not result:
            raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

        user_id = result['user_id']
        provider = result['provider']
        metadata = result.get('metadata')

        # Extract code_verifier from metadata if present
        code_verifier = None
        if metadata:
            import json
            try:
                meta_dict = json.loads(metadata) if isinstance(metadata, str) else metadata
                code_verifier = meta_dict.get("code_verifier")
            except:
                pass

        # Delete used state
        cur.execute("DELETE FROM oauth_states WHERE state = %s", (state,))
        conn.commit()

        return user_id, provider, code_verifier
    finally:
        cur.close()
        conn.close()


@router.get("/get-auth-url/{platform}")
async def get_auth_url(platform: str, request: Request):
    """
    Get OAuth authorization URL for a platform (requires JWT auth)
    Frontend should call this, then redirect to the returned URL
    """
    if platform not in PLATFORM_CONFIG:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")

    config = PLATFORM_CONFIG[platform]

    if not config['client_id'] or not config['client_secret']:
        raise HTTPException(
            status_code=500,
            detail=f"{platform.title()} OAuth credentials not configured"
        )

    # Get user_id from JWT token (this is why we need this endpoint)
    user_id = get_user_from_token(request)

    # Generate CSRF state token
    state = secrets.token_urlsafe(32)

    # Twitter requires PKCE (Proof Key for Code Exchange)
    code_verifier = None
    if platform == "twitter":
        code_verifier, code_challenge = generate_pkce_pair()
        store_oauth_state(user_id, platform, state, code_verifier)
    else:
        store_oauth_state(user_id, platform, state)

    # Build authorization URL
    # Instagram uses Facebook's callback (Meta owns Instagram)
    callback_platform = "facebook" if platform == "instagram" else platform
    redirect_uri = f"{BACKEND_URL}/social-auth/callback/{callback_platform}"
    scope = " ".join(config['scopes'])

    params = {
        "client_id": config['client_id'],
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state,
        "response_type": "code",
    }

    # Platform-specific parameters
    if platform == "twitter":
        params["code_challenge"] = code_challenge
        params["code_challenge_method"] = "S256"

    # Build URL
    auth_url = config['auth_url'] + "?" + "&".join([f"{k}={v}" for k, v in params.items()])

    logger.info(f"Generated OAuth URL for user {user_id}, platform {platform}")

    return {
        "success": True,
        "auth_url": auth_url,
        "platform": platform
    }


@router.get("/connect/{platform}")
async def connect_platform(platform: str, request: Request):
    """
    Initiate OAuth flow for a social platform (legacy endpoint)
    Use /get-auth-url instead for better security with JWT auth
    """
    if platform not in PLATFORM_CONFIG:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")

    config = PLATFORM_CONFIG[platform]

    if not config['client_id'] or not config['client_secret']:
        raise HTTPException(
            status_code=500,
            detail=f"{platform.title()} OAuth credentials not configured"
        )

    # Get user_id from token
    user_id = get_user_from_token(request)

    # Generate CSRF state token
    state = secrets.token_urlsafe(32)

    # Twitter requires PKCE (Proof Key for Code Exchange)
    code_verifier = None
    if platform == "twitter":
        code_verifier, code_challenge = generate_pkce_pair()
        store_oauth_state(user_id, platform, state, code_verifier)
    else:
        store_oauth_state(user_id, platform, state)

    # Build authorization URL
    # Instagram uses Facebook's callback (Meta owns Instagram)
    callback_platform = "facebook" if platform == "instagram" else platform
    redirect_uri = f"{BACKEND_URL}/social-auth/callback/{callback_platform}"
    scope = " ".join(config['scopes'])

    params = {
        "client_id": config['client_id'],
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state,
        "response_type": "code",
    }

    # Platform-specific parameters
    if platform == "twitter":
        params["code_challenge"] = code_challenge
        params["code_challenge_method"] = "S256"

    # Build URL
    auth_url = config['auth_url'] + "?" + "&".join([f"{k}={v}" for k, v in params.items()])

    logger.info(f"Redirecting user {user_id} to {platform} OAuth")
    return RedirectResponse(url=auth_url)


@router.get("/callback/{platform}")
async def oauth_callback(platform: str, code: str, state: str):
    """
    Handle OAuth callback from social platform
    """
    if platform not in PLATFORM_CONFIG:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")

    # Verify state (also retrieves code_verifier for Twitter PKCE)
    user_id, verified_platform, code_verifier = verify_oauth_state(state)

    # Instagram OAuth uses Facebook's callback (both are OK)
    if verified_platform == "instagram" and platform == "facebook":
        # Instagram OAuth came through Facebook callback - this is expected
        actual_platform = "instagram"
        config = PLATFORM_CONFIG["instagram"]
    elif verified_platform != platform:
        raise HTTPException(status_code=400, detail="Platform mismatch")
    else:
        actual_platform = platform
        config = PLATFORM_CONFIG[platform]

    # Use the callback URL that was originally sent
    callback_platform = "facebook" if actual_platform == "instagram" else actual_platform
    redirect_uri = f"{BACKEND_URL}/social-auth/callback/{callback_platform}"

    # Exchange code for tokens
    try:
        async with httpx.AsyncClient() as client:
            token_data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": config['client_id'],
                "client_secret": config['client_secret'],
            }

            # Twitter requires code_verifier for PKCE
            if platform == "twitter" and code_verifier:
                token_data["code_verifier"] = code_verifier

            # Platform-specific token exchange
            if platform == "twitter":
                # Twitter OAuth 2.0 requires Basic auth (NOT in body)
                # Remove client credentials from body
                token_data_clean = {k: v for k, v in token_data.items() if k not in ['client_id', 'client_secret']}
                auth = (config['client_id'], config['client_secret'])
                response = await client.post(
                    config['token_url'],
                    data=token_data_clean,
                    auth=auth,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
            elif platform == "reddit":
                # Reddit requires Basic auth
                auth = (config['client_id'], config['client_secret'])
                response = await client.post(
                    config['token_url'],
                    data=token_data,
                    auth=auth,
                    headers={"User-Agent": "Orla3-Marketing-Suite/1.0"}
                )
            else:
                response = await client.post(config['token_url'], data=token_data)

            if response.status_code != 200:
                logger.error(f"{platform} token exchange failed: {response.text}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to exchange {platform} authorization code"
                )

            tokens = response.json()
            access_token = tokens.get("access_token")
            refresh_token = tokens.get("refresh_token")
            expires_in = tokens.get("expires_in", 3600)

            if not access_token:
                raise HTTPException(status_code=500, detail="No access token returned")

            # Get platform-specific user info
            service_id = await get_platform_user_id(actual_platform, access_token)

            # Store tokens in database
            conn = get_db_connection()
            cur = conn.cursor()

            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

            try:
                # Format service_name (e.g., "twitter" -> "Twitter")
                service_name = actual_platform.capitalize()

                cur.execute("""
                    INSERT INTO connected_services
                    (user_id, service_type, service_name, service_id, access_token, refresh_token,
                     token_expires_at, service_metadata, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, true)
                    ON CONFLICT (user_id, service_type)
                    DO UPDATE SET
                        service_name = EXCLUDED.service_name,
                        service_id = EXCLUDED.service_id,
                        access_token = EXCLUDED.access_token,
                        refresh_token = EXCLUDED.refresh_token,
                        token_expires_at = EXCLUDED.token_expires_at,
                        service_metadata = EXCLUDED.service_metadata,
                        is_active = true,
                        updated_at = NOW()
                """, (
                    user_id,
                    actual_platform,
                    service_name,
                    service_id,
                    access_token,
                    refresh_token,
                    expires_at,
                    None  # service_metadata
                ))

                conn.commit()
                logger.info(f"Stored {actual_platform} tokens for user {user_id}")

            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to store tokens: {e}")
                raise HTTPException(status_code=500, detail="Failed to store credentials")
            finally:
                cur.close()
                conn.close()

            # Redirect back to frontend settings page
            return RedirectResponse(
                url=f"{FRONTEND_URL}/dashboard/settings/social-accounts?success={actual_platform}"
            )

    except httpx.RequestError as e:
        logger.error(f"HTTP error during {actual_platform} OAuth: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to connect to {platform}")


async def get_platform_user_id(platform: str, access_token: str) -> str:
    """
    Get the user's platform-specific ID
    """
    endpoints = {
        "instagram": "https://graph.instagram.com/me?fields=id,username",
        "linkedin": "https://api.linkedin.com/v2/me",
        "facebook": "https://graph.facebook.com/me?fields=id,name",
        "twitter": "https://api.twitter.com/2/users/me",
        "youtube": "https://www.googleapis.com/youtube/v3/channels?part=id&mine=true",
        "reddit": "https://oauth.reddit.com/api/v1/me",
        "tumblr": "https://api.tumblr.com/v2/user/info",
        "wordpress": "https://public-api.wordpress.com/rest/v1/me",
    }

    if platform == "tiktok":
        # TikTok uses different endpoint
        return "tiktok_user"  # Placeholder - need to implement TikTok user info endpoint

    endpoint = endpoints.get(platform)
    if not endpoint:
        return f"{platform}_user"

    try:
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}

            # Reddit requires User-Agent
            if platform == "reddit":
                headers["User-Agent"] = "Orla3-Marketing-Suite/1.0"

            response = await client.get(endpoint, headers=headers)

            if response.status_code != 200:
                logger.warning(f"Failed to get {platform} user ID: {response.text}")
                return f"{platform}_user"

            data = response.json()

            # Extract ID based on platform
            if platform == "instagram":
                return data.get("id", "instagram_user")
            elif platform == "linkedin":
                return data.get("id", "linkedin_user")
            elif platform == "facebook":
                return data.get("id", "facebook_user")
            elif platform == "twitter":
                return data.get("data", {}).get("id", "twitter_user")
            elif platform == "youtube":
                items = data.get("items", [])
                return items[0].get("id") if items else "youtube_user"
            elif platform == "reddit":
                return data.get("name", "reddit_user")
            elif platform == "tumblr":
                return data.get("response", {}).get("user", {}).get("name", "tumblr_user")
            elif platform == "wordpress":
                return str(data.get("ID", "wordpress_user"))

            return f"{platform}_user"

    except Exception as e:
        logger.error(f"Error getting {platform} user ID: {e}")
        return f"{platform}_user"


@router.post("/disconnect/{platform}")
async def disconnect_platform(platform: str, request: Request):
    """
    Disconnect a social platform
    """
    if platform not in PLATFORM_CONFIG:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")

    user_id = get_user_from_token(request)

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            UPDATE connected_services
            SET is_active = false, updated_at = NOW()
            WHERE user_id = %s AND service_type = %s
        """, (user_id, platform))

        conn.commit()

        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"{platform} connection not found")

        logger.info(f"Disconnected {platform} for user {user_id}")

        return {"success": True, "message": f"{platform.title()} disconnected successfully"}

    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to disconnect {platform}: {e}")
        raise HTTPException(status_code=500, detail="Failed to disconnect platform")
    finally:
        cur.close()
        conn.close()


@router.get("/status")
async def get_connection_status(request: Request):
    """
    Get connection status for all platforms
    """
    user_id = get_user_from_token(request)

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT service_type, service_id, is_active, token_expires_at, updated_at
            FROM connected_services
            WHERE user_id = %s AND is_active = true
        """, (user_id,))

        connections = cur.fetchall()

        # Build status dict
        status = {}
        for conn_data in connections:
            status[conn_data['service_type']] = {
                "connected": True,
                "service_id": conn_data['service_id'],
                "expires_at": conn_data['token_expires_at'].isoformat() if conn_data['token_expires_at'] else None,
                "updated_at": conn_data['updated_at'].isoformat()
            }

        # Add disconnected platforms
        for platform in PLATFORM_CONFIG.keys():
            if platform not in status:
                status[platform] = {"connected": False}

        return {"success": True, "connections": status}

    finally:
        cur.close()
        conn.close()
