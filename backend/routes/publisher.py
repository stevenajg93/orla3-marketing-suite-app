from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional, Literal, Dict
import os
import httpx
import json
from datetime import datetime
from requests_oauthlib import OAuth1Session
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.auth import decode_token
from logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

# ============================================================================
# MULTI-TENANT AUTH HELPERS
# ============================================================================

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


def get_user_service_credentials(user_id: str, service_type: str) -> Optional[Dict]:
    """
    Get user's OAuth credentials for a specific service from connected_services table

    Args:
        user_id: The user's UUID
        service_type: Platform name (instagram, linkedin, twitter, etc.)

    Returns:
        Dict with access_token and other service metadata, or None if not connected
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT
                access_token,
                refresh_token,
                token_expires_at,
                service_id,
                service_metadata,
                is_active
            FROM connected_services
            WHERE user_id = %s AND service_type = %s AND is_active = true
            ORDER BY connected_at DESC
            LIMIT 1
        """, (user_id, service_type))

        result = cur.fetchone()

        if not result:
            logger.warning(f"No active {service_type} connection for user {user_id}")
            return None

        return dict(result)

    except Exception as e:
        logger.error(f"Error fetching service credentials for user {user_id}: {e}")
        return None
    finally:
        cur.close()
        conn.close()


router = APIRouter()

# ============================================================================
# MODELS
# ============================================================================

class PublishRequest(BaseModel):
    platform: Literal["instagram", "linkedin", "twitter", "x", "facebook", "tiktok", "youtube", "reddit", "tumblr", "wordpress"]
    content_type: Literal["text", "image", "video", "carousel", "reel", "story"]
    caption: str
    image_urls: Optional[List[str]] = []
    video_url: Optional[str] = None  # For TikTok, YouTube video publishing, Instagram Reels
    link_url: Optional[str] = None  # For Reddit link posts
    subreddit: Optional[str] = None  # For Reddit - subreddit name (without r/ prefix)
    account_id: Optional[str] = None  # For multi-account support later
    title: Optional[str] = None  # For WordPress blog posts, Reddit titles, YouTube video title
    content: Optional[str] = None  # For WordPress full content (if different from caption)
    cover_url: Optional[str] = None  # For Instagram Reels cover image
    share_to_feed: Optional[bool] = True  # For Instagram Reels - share to feed
    # YouTube-specific fields
    privacy: Optional[str] = "private"  # YouTube privacy: public, private, unlisted
    category_id: Optional[str] = "22"  # YouTube category (22 = People & Blogs)
    is_short: Optional[bool] = False  # YouTube Shorts flag
    thumbnail_url: Optional[str] = None  # YouTube custom thumbnail

class PublishResponse(BaseModel):
    success: bool
    platform: str
    post_id: Optional[str] = None
    post_url: Optional[str] = None
    error: Optional[str] = None
    message: Optional[str] = None  # Success message from publisher
    published_at: str

# ============================================================================
# INSTAGRAM PUBLISHER
# ============================================================================

class InstagramPublisher:
    """
    Instagram Graph API publisher
    Requires: Instagram Business Account, Facebook Page Access Token
    """

    def __init__(self, access_token: str = None, business_account_id: str = None):
        # Accept credentials as parameters for multi-tenant support
        # Falls back to environment variables for backwards compatibility
        self.access_token = access_token or os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.business_account_id = business_account_id or os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
        self.api_version = "v21.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

    async def publish(self, post_data: dict) -> dict:
        """
        Generic publish method for scheduler compatibility
        Routes to appropriate method based on content type
        """
        caption = post_data.get('text', '')
        image_urls = post_data.get('imageUrls', [])

        if not image_urls:
            # Instagram requires images - cannot post text-only
            return {
                "success": False,
                "error": "Instagram requires at least one image. Text-only posts are not supported."
            }

        if len(image_urls) == 1:
            return await self.publish_single_image(caption, image_urls[0])
        else:
            return await self.publish_carousel(caption, image_urls)

    async def publish_single_image(self, caption: str, image_url: str) -> dict:
        """Publish single image post to Instagram"""
        if not self.access_token or not self.business_account_id:
            return {
                "success": False,
                "error": "Instagram credentials not configured. Add INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_BUSINESS_ACCOUNT_ID to .env.local"
            }
        
        try:
            async with httpx.AsyncClient() as client:
                # Step 1: Create media container
                container_response = await client.post(
                    f"{self.base_url}/{self.business_account_id}/media",
                    data={
                        "image_url": image_url,
                        "caption": caption,
                        "access_token": self.access_token
                    }
                )
                
                if container_response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Failed to create media container: {container_response.text}"
                    }
                
                container_id = container_response.json()["id"]
                
                # Step 2: Publish media container
                publish_response = await client.post(
                    f"{self.base_url}/{self.business_account_id}/media_publish",
                    data={
                        "creation_id": container_id,
                        "access_token": self.access_token
                    }
                )
                
                if publish_response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Failed to publish: {publish_response.text}"
                    }
                
                post_id = publish_response.json()["id"]
                
                return {
                    "success": True,
                    "post_id": post_id,
                    "post_url": f"https://www.instagram.com/p/{post_id}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def publish_carousel(self, caption: str, image_urls: List[str]) -> dict:
        """Publish carousel (multiple images) to Instagram"""
        if not self.access_token or not self.business_account_id:
            return {
                "success": False,
                "error": "Instagram credentials not configured"
            }
        
        try:
            async with httpx.AsyncClient() as client:
                # Step 1: Create media containers for each image
                media_ids = []
                
                for image_url in image_urls:
                    container_response = await client.post(
                        f"{self.base_url}/{self.business_account_id}/media",
                        data={
                            "image_url": image_url,
                            "is_carousel_item": True,
                            "access_token": self.access_token
                        }
                    )
                    
                    if container_response.status_code != 200:
                        return {
                            "success": False,
                            "error": f"Failed to create carousel item: {container_response.text}"
                        }
                    
                    media_ids.append(container_response.json()["id"])
                
                # Step 2: Create carousel container
                carousel_response = await client.post(
                    f"{self.base_url}/{self.business_account_id}/media",
                    data={
                        "media_type": "CAROUSEL",
                        "caption": caption,
                        "children": ",".join(media_ids),
                        "access_token": self.access_token
                    }
                )
                
                if carousel_response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Failed to create carousel: {carousel_response.text}"
                    }
                
                carousel_id = carousel_response.json()["id"]
                
                # Step 3: Publish carousel
                publish_response = await client.post(
                    f"{self.base_url}/{self.business_account_id}/media_publish",
                    data={
                        "creation_id": carousel_id,
                        "access_token": self.access_token
                    }
                )
                
                if publish_response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Failed to publish carousel: {publish_response.text}"
                    }
                
                post_id = publish_response.json()["id"]
                
                return {
                    "success": True,
                    "post_id": post_id,
                    "post_url": f"https://www.instagram.com/p/{post_id}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def publish_reel(self, caption: str, video_url: str, cover_url: str = None, share_to_feed: bool = True) -> dict:
        """
        Publish Reel to Instagram
        Uses Instagram Graph API REELS endpoint

        Args:
            caption: Caption for the Reel (max 2,200 chars)
            video_url: URL to the video file (must be publicly accessible)
            cover_url: Optional cover image URL
            share_to_feed: Whether to share Reel to main feed (default: True)

        Returns:
            dict with success status, post_id, and post_url
        """
        if not self.access_token or not self.business_account_id:
            return {
                "success": False,
                "error": "Instagram credentials not configured"
            }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Step 1: Create Reel container
                container_data = {
                    "media_type": "REELS",
                    "video_url": video_url,
                    "caption": caption,
                    "share_to_feed": share_to_feed,
                    "access_token": self.access_token
                }

                # Add cover image if provided
                if cover_url:
                    container_data["cover_url"] = cover_url

                container_response = await client.post(
                    f"{self.base_url}/{self.business_account_id}/media",
                    data=container_data
                )

                if container_response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Failed to create Reel container: {container_response.text}"
                    }

                container_id = container_response.json()["id"]

                # Step 2: Publish Reel (may take time to process video)
                publish_response = await client.post(
                    f"{self.base_url}/{self.business_account_id}/media_publish",
                    data={
                        "creation_id": container_id,
                        "access_token": self.access_token
                    }
                )

                if publish_response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Failed to publish Reel: {publish_response.text}"
                    }

                post_id = publish_response.json()["id"]

                return {
                    "success": True,
                    "post_id": post_id,
                    "post_url": f"https://www.instagram.com/reel/{post_id}",
                    "message": "Reel published successfully"
                }

        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Video processing timeout. Large videos may take time to process. Please check Instagram for the post."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Reel publishing error: {str(e)}"
            }

    async def publish_story(self, media_url: str, media_type: str = "IMAGE") -> dict:
        """
        Publish Story to Instagram
        Stories expire after 24 hours automatically

        Note: REST API only supports basic media upload. Text overlays, stickers,
        polls, and location tags are not supported via REST API.

        Args:
            media_url: URL to the image or video file
            media_type: "IMAGE" or "VIDEO"

        Returns:
            dict with success status and post_id
        """
        if not self.access_token or not self.business_account_id:
            return {
                "success": False,
                "error": "Instagram credentials not configured"
            }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Step 1: Create Story container
                container_data = {
                    "media_type": "STORIES",
                    "access_token": self.access_token
                }

                # Add media based on type
                if media_type.upper() == "VIDEO":
                    container_data["video_url"] = media_url
                else:
                    container_data["image_url"] = media_url

                # Note: Instagram Stories API has limited text overlay support
                # Advanced overlays (stickers, polls) require Facebook SDK

                container_response = await client.post(
                    f"{self.base_url}/{self.business_account_id}/media",
                    data=container_data
                )

                if container_response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Failed to create Story container: {container_response.text}"
                    }

                container_id = container_response.json()["id"]

                # Step 2: Publish Story
                publish_response = await client.post(
                    f"{self.base_url}/{self.business_account_id}/media_publish",
                    data={
                        "creation_id": container_id,
                        "access_token": self.access_token
                    }
                )

                if publish_response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Failed to publish Story: {publish_response.text}"
                    }

                post_id = publish_response.json()["id"]

                return {
                    "success": True,
                    "post_id": post_id,
                    "message": "Story published successfully (expires in 24 hours)"
                }

        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Story upload timeout. Please check Instagram for the post."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Story publishing error: {str(e)}"
            }

# ============================================================================
# LINKEDIN PUBLISHER
# ============================================================================

class LinkedInPublisher:
    """
    LinkedIn API publisher
    Requires: LinkedIn Access Token, LinkedIn Person/Organization URN
    Supports: Text posts, image posts (single image)
    """

    def __init__(self, access_token: str, person_urn: str):
        self.access_token = access_token
        self.person_urn = person_urn  # e.g., urn:li:person:ABC123
        self.api_version = "202410"
        self.base_url = "https://api.linkedin.com/rest"

    async def publish_text(self, caption: str) -> dict:
        """Publish text-only post to LinkedIn"""
        if not self.access_token or not self.person_urn:
            return {
                "success": False,
                "error": "LinkedIn not connected. Please connect your LinkedIn account."
            }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/posts",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json",
                        "X-Restli-Protocol-Version": "2.0.0",
                        "LinkedIn-Version": self.api_version
                    },
                    json={
                        "author": self.person_urn,
                        "commentary": caption[:3000],  # LinkedIn max 3000 chars
                        "visibility": "PUBLIC",
                        "distribution": {
                            "feedDistribution": "MAIN_FEED",
                            "targetEntities": [],
                            "thirdPartyDistributionChannels": []
                        },
                        "lifecycleState": "PUBLISHED"
                    }
                )

                if response.status_code not in [200, 201]:
                    logger.error(f"LinkedIn API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"LinkedIn API error: {response.status_code}"
                    }

                post_data = response.json()
                post_id = post_data.get("id", "")

                return {
                    "success": True,
                    "post_id": post_id,
                    "post_url": f"https://www.linkedin.com/feed/update/{post_id}"
                }

        except Exception as e:
            logger.error(f"LinkedIn publish error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def publish_image(self, caption: str, image_url: str) -> dict:
        """
        Publish image post to LinkedIn using asset registration

        Args:
            caption: Post caption/commentary (max 3000 chars)
            image_url: Public URL to image file

        Returns:
            dict: {success: bool, post_id: str, post_url: str}
        """
        if not self.access_token or not self.person_urn:
            return {
                "success": False,
                "error": "LinkedIn not connected. Please connect your LinkedIn account."
            }

        try:
            from utils.media_upload import download_url_to_file, validate_media_file
            import tempfile

            async with httpx.AsyncClient(timeout=60.0) as client:
                # Download image to temp file for validation and upload
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                    tmp_path = tmp_file.name

                # Download image
                await download_url_to_file(image_url, tmp_path)

                # Validate image
                validate_media_file(tmp_path, "linkedin", "image")

                # Step 1: Register upload
                register_payload = {
                    "registerUploadRequest": {
                        "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                        "owner": self.person_urn,
                        "serviceRelationships": [
                            {
                                "relationshipType": "OWNER",
                                "identifier": "urn:li:userGeneratedContent"
                            }
                        ]
                    }
                }

                register_response = await client.post(
                    "https://api.linkedin.com/v2/assets?action=registerUpload",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    },
                    json=register_payload
                )

                if register_response.status_code != 200:
                    logger.error(f"LinkedIn asset registration failed: {register_response.status_code} - {register_response.text}")
                    return {
                        "success": False,
                        "error": f"LinkedIn asset registration failed: {register_response.status_code}"
                    }

                register_data = register_response.json()
                upload_url = register_data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
                asset_urn = register_data['value']['asset']

                # Step 2: Upload image binary
                with open(tmp_path, 'rb') as f:
                    upload_response = await client.put(
                        upload_url,
                        headers={
                            "Authorization": f"Bearer {self.access_token}"
                        },
                        content=f.read()
                    )

                    if upload_response.status_code != 201:
                        logger.error(f"LinkedIn image upload failed: {upload_response.status_code} - {upload_response.text}")
                        return {
                            "success": False,
                            "error": f"LinkedIn image upload failed: {upload_response.status_code}"
                        }

                # Step 3: Create post with image
                post_response = await client.post(
                    f"{self.base_url}/posts",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json",
                        "X-Restli-Protocol-Version": "2.0.0",
                        "LinkedIn-Version": self.api_version
                    },
                    json={
                        "author": self.person_urn,
                        "commentary": caption[:3000],
                        "visibility": "PUBLIC",
                        "distribution": {
                            "feedDistribution": "MAIN_FEED",
                            "targetEntities": [],
                            "thirdPartyDistributionChannels": []
                        },
                        "content": {
                            "media": {
                                "title": "Image",
                                "id": asset_urn
                            }
                        },
                        "lifecycleState": "PUBLISHED"
                    }
                )

                if post_response.status_code not in [200, 201]:
                    logger.error(f"LinkedIn post creation failed: {post_response.status_code} - {post_response.text}")
                    return {
                        "success": False,
                        "error": f"LinkedIn post creation failed: {post_response.status_code}"
                    }

                post_data = post_response.json()
                post_id = post_data.get("id", "")

                # Cleanup temp file
                os.unlink(tmp_path)

                return {
                    "success": True,
                    "post_id": post_id,
                    "post_url": f"https://www.linkedin.com/feed/update/{post_id}",
                    "message": "Image post published to LinkedIn"
                }

        except Exception as e:
            logger.error(f"LinkedIn image publish error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# ============================================================================
# TWITTER/X PUBLISHER
# ============================================================================

class TwitterPublisher:
    """
    Twitter/X API v2 publisher
    Requires: Twitter OAuth 1.0a credentials
    Supports: Text tweets, tweets with images (up to 4)
    """

    def __init__(self, api_key: str, api_secret: str, access_token: str, access_token_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.base_url = "https://api.twitter.com/2"
        self.upload_url = "https://upload.twitter.com/1.1"

    async def publish_tweet(self, caption: str, image_urls: Optional[List[str]] = None) -> dict:
        """
        Publish tweet to Twitter/X using OAuth 1.0a

        Args:
            caption: Tweet text (max 280 chars)
            image_urls: List of image URLs (max 4 images)

        Returns:
            dict: {success: bool, post_id: str, post_url: str}
        """
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            return {
                "success": False,
                "error": "Twitter not connected. Please connect your Twitter account."
            }

        try:
            # Create OAuth 1.0a session (required for Twitter API v2 posting)
            oauth = OAuth1Session(
                self.api_key,
                client_secret=self.api_secret,
                resource_owner_key=self.access_token,
                resource_owner_secret=self.access_token_secret
            )

            media_ids = []

            # Upload images if provided (max 4)
            if image_urls:
                if len(image_urls) > 4:
                    return {
                        "success": False,
                        "error": "Twitter supports maximum 4 images per tweet"
                    }

                from utils.media_upload import download_url_to_file, validate_media_file
                import tempfile

                for image_url in image_urls:
                    # Download image to temp file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                        tmp_path = tmp_file.name

                    # Download and validate
                    await download_url_to_file(image_url, tmp_path)
                    validate_media_file(tmp_path, "twitter", "image")

                    # Upload to Twitter
                    with open(tmp_path, 'rb') as f:
                        files = {'media': f}
                        media_response = oauth.post(
                            f"{self.upload_url}/media/upload.json",
                            files=files
                        )

                        if media_response.status_code != 200:
                            logger.error(f"Twitter media upload failed: {media_response.status_code} - {media_response.text}")
                            os.unlink(tmp_path)
                            return {
                                "success": False,
                                "error": f"Twitter media upload failed: {media_response.status_code}"
                            }

                        media_data = media_response.json()
                        media_ids.append(media_data['media_id_string'])

                    # Cleanup temp file
                    os.unlink(tmp_path)

            # Post tweet using OAuth 1.0a
            payload = {"text": caption}

            # Add media IDs if images were uploaded
            if media_ids:
                payload["media"] = {"media_ids": media_ids}

            response = oauth.post(
                f"{self.base_url}/tweets",
                json=payload
            )

            if response.status_code not in [200, 201]:
                logger.error(f"Twitter API error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"Twitter API error ({response.status_code}): {response.text}"
                }

            tweet_data = response.json()["data"]
            tweet_id = tweet_data["id"]

            return {
                "success": True,
                "post_id": tweet_id,
                "post_url": f"https://twitter.com/i/web/status/{tweet_id}",
                "message": f"Tweet published{' with ' + str(len(media_ids)) + ' image(s)' if media_ids else ''}"
            }

        except Exception as e:
            logger.error(f"Twitter publish error: {e}")
            return {
                "success": False,
                "error": f"Twitter publish exception: {str(e)}"
            }

# ============================================================================
# MAIN PUBLISHING ENDPOINT
# ============================================================================

@router.post("/publish", response_model=PublishResponse)
async def publish_content(publish_request: PublishRequest, request: Request):
    """
    Universal publishing endpoint supporting all platforms
    Routes to appropriate platform publisher based on request

    MULTI-TENANT: Requires JWT authentication, publishes to user's connected accounts only
    """

    # Extract user_id from JWT token
    user_id = get_user_from_token(request)
    logger.info(f"Publishing to {publish_request.platform} for user {user_id}")

    # Validate character limits BEFORE attempting to publish
    from utils.validators import ContentValidator

    is_valid, error_message = ContentValidator.validate_character_limit(
        publish_request.caption or "",
        publish_request.platform
    )

    if not is_valid:
        return PublishResponse(
            success=False,
            platform=publish_request.platform,
            error=error_message,
            published_at=datetime.utcnow().isoformat()
        )

    result = {
        "success": False,
        "platform": publish_request.platform,
        "published_at": datetime.utcnow().isoformat()
    }

    try:
        # Handle X/Twitter alias
        platform = "twitter" if publish_request.platform == "x" else publish_request.platform

        # Get user's credentials for this platform
        credentials = get_user_service_credentials(user_id, platform)

        # Instagram supports both OAuth and environment variable credentials
        # Don't error out if no OAuth - let InstagramPublisher fall back to env vars
        if not credentials and platform != "instagram":
            return PublishResponse(
                success=False,
                platform=publish_request.platform,
                error=f"No active {platform} connection found. Please connect your {platform} account in settings.",
                published_at=result["published_at"]
            )

        if platform == "instagram":
            # Instagram supports both OAuth (database) and direct credentials (env vars)
            import json
            try:
                if credentials:
                    # Try OAuth credentials from database
                    metadata = credentials.get('service_metadata') or {}
                    meta_dict = json.loads(metadata) if isinstance(metadata, str) else metadata or {}
                    business_account_id = meta_dict.get('business_account_id', '') if meta_dict else ''
                    access_token = credentials.get('access_token')

                    if business_account_id and access_token:
                        # Use OAuth credentials
                        publisher = InstagramPublisher(
                            access_token=access_token,
                            business_account_id=business_account_id
                        )
                    else:
                        # OAuth incomplete, fall back to env vars
                        publisher = InstagramPublisher()
                else:
                    # No OAuth, use environment variables
                    publisher = InstagramPublisher()

                # Route based on content type
                if publish_request.content_type == "reel":
                    # Instagram Reels
                    if not publish_request.video_url:
                        return PublishResponse(
                            success=False,
                            platform=publish_request.platform,
                            error="Instagram Reels require a video",
                            published_at=result["published_at"]
                        )
                    publish_result = await publisher.publish_reel(
                        caption=publish_request.caption,
                        video_url=publish_request.video_url,
                        cover_url=publish_request.cover_url,
                        share_to_feed=publish_request.share_to_feed
                    )

                elif publish_request.content_type == "story":
                    # Instagram Stories
                    if not publish_request.image_urls and not publish_request.video_url:
                        return PublishResponse(
                            success=False,
                            platform=publish_request.platform,
                            error="Instagram Stories require media (image or video)",
                            published_at=result["published_at"]
                        )

                    # Determine media type and URL
                    if publish_request.video_url:
                        media_url = publish_request.video_url
                        media_type = "VIDEO"
                    else:
                        media_url = publish_request.image_urls[0]
                        media_type = "IMAGE"

                    publish_result = await publisher.publish_story(
                        media_url=media_url,
                        media_type=media_type
                    )

                elif publish_request.content_type == "carousel" and len(publish_request.image_urls) > 1:
                    # Instagram Carousel (2-10 images)
                    publish_result = await publisher.publish_carousel(
                        caption=publish_request.caption,
                        image_urls=publish_request.image_urls
                    )

                elif publish_request.image_urls:
                    # Instagram Feed Post (single image)
                    publish_result = await publisher.publish_single_image(
                        caption=publish_request.caption,
                        image_url=publish_request.image_urls[0]
                    )

                else:
                    return PublishResponse(
                        success=False,
                        platform=publish_request.platform,
                        error="Instagram posts require at least one image or video",
                        published_at=result["published_at"]
                    )

                result.update(publish_result)

            except Exception as e:
                logger.error(f"Instagram publish error: {e}")
                return PublishResponse(
                    success=False,
                    platform=publish_request.platform,
                    error=f"Instagram error: {str(e)}",
                    published_at=result["published_at"]
                )

        elif platform == "linkedin":
            # Get LinkedIn person URN from metadata
            import json
            try:
                metadata = credentials.get('service_metadata', {})
                meta_dict = json.loads(metadata) if isinstance(metadata, str) else metadata
                person_urn = meta_dict.get('person_urn', '')

                if not person_urn:
                    return PublishResponse(
                        success=False,
                        platform=publish_request.platform,
                        error="LinkedIn person URN not found. Please reconnect your LinkedIn account.",
                        published_at=result["published_at"]
                    )

                publisher = LinkedInPublisher(
                    access_token=credentials['access_token'],
                    person_urn=person_urn
                )

                # Publish with image if provided
                if publish_request.image_urls and len(publish_request.image_urls) > 0:
                    publish_result = await publisher.publish_image(
                        caption=publish_request.caption,
                        image_url=publish_request.image_urls[0]
                    )
                else:
                    publish_result = await publisher.publish_text(caption=publish_request.caption)

                result.update(publish_result)

            except Exception as e:
                logger.error(f"LinkedIn publish error: {e}")
                return PublishResponse(
                    success=False,
                    platform=publish_request.platform,
                    error=f"LinkedIn error: {str(e)}",
                    published_at=result["published_at"]
                )

        elif platform == "twitter":
            # Get Twitter OAuth 1.0a credentials from metadata
            import json
            try:
                metadata = credentials.get('service_metadata', {})
                meta_dict = json.loads(metadata) if isinstance(metadata, str) else metadata

                api_key = meta_dict.get('api_key', '')
                api_secret = meta_dict.get('api_secret', '')
                access_token_secret = meta_dict.get('access_token_secret', '')

                if not all([api_key, api_secret, access_token_secret]):
                    return PublishResponse(
                        success=False,
                        platform=publish_request.platform,
                        error="Twitter OAuth credentials incomplete. Please reconnect your Twitter account.",
                        published_at=result["published_at"]
                    )

                publisher = TwitterPublisher(
                    api_key=api_key,
                    api_secret=api_secret,
                    access_token=credentials['access_token'],
                    access_token_secret=access_token_secret
                )

                publish_result = await publisher.publish_tweet(
                    caption=publish_request.caption,
                    image_urls=publish_request.image_urls if publish_request.image_urls else None
                )
                result.update(publish_result)

            except Exception as e:
                logger.error(f"Twitter publish error: {e}")
                return PublishResponse(
                    success=False,
                    platform=publish_request.platform,
                    error=f"Twitter error: {str(e)}",
                    published_at=result["published_at"]
                )

        elif platform == "facebook":
            # Get Facebook Page credentials from service_metadata
            if not credentials.get('service_metadata'):
                return PublishResponse(
                    success=False,
                    platform=publish_request.platform,
                    error="No Facebook Page selected. Please select a page in settings.",
                    published_at=result["published_at"]
                )

            import json
            try:
                metadata = credentials['service_metadata']
                meta_dict = json.loads(metadata) if isinstance(metadata, str) else metadata
                page_access_token = meta_dict.get('page_access_token')
                page_id = meta_dict.get('selected_page_id')

                if not page_access_token or not page_id:
                    return PublishResponse(
                        success=False,
                        platform=publish_request.platform,
                        error="Facebook Page credentials incomplete. Please reconnect your page.",
                        published_at=result["published_at"]
                    )

                publisher = FacebookPublisher(
                    page_access_token=page_access_token,
                    page_id=page_id
                )
                image_url = publish_request.image_urls[0] if publish_request.image_urls else None
                publish_result = await publisher.publish_post(
                    caption=publish_request.caption,
                    image_url=image_url
                )
                result.update(publish_result)

            except Exception as e:
                logger.error(f"Failed to parse Facebook metadata: {e}")
                return PublishResponse(
                    success=False,
                    platform=publish_request.platform,
                    error="Failed to load Facebook Page credentials",
                    published_at=result["published_at"]
                )

        elif platform == "tiktok":
            # TikTok requires video URL
            if not publish_request.video_url:
                return PublishResponse(
                    success=False,
                    platform=publish_request.platform,
                    error="TikTok requires a video URL",
                    published_at=result["published_at"]
                )

            publisher = TikTokPublisher(access_token=credentials['access_token'])
            publish_result = await publisher.publish_video(
                caption=publish_request.caption,
                video_url=publish_request.video_url
            )
            result.update(publish_result)

        elif platform == "youtube":
            # YouTube requires video URL
            if not publish_request.video_url:
                return PublishResponse(
                    success=False,
                    platform=publish_request.platform,
                    error="YouTube requires a video URL",
                    published_at=result["published_at"]
                )

            publisher = YouTubePublisher(access_token=credentials['access_token'])

            # Use title field if provided, otherwise use caption
            video_title = publish_request.title if publish_request.title else publish_request.caption[:100] if publish_request.caption else "Video"
            video_description = publish_request.caption or ""

            publish_result = await publisher.publish_video(
                title=video_title,
                description=video_description,
                video_url=publish_request.video_url,
                privacy=publish_request.privacy or "private",
                category_id=publish_request.category_id or "22",
                is_short=publish_request.is_short or False,
                thumbnail_url=publish_request.thumbnail_url
            )
            result.update(publish_result)

        elif platform == "reddit":
            # Reddit requires subreddit
            if not publish_request.subreddit:
                return PublishResponse(
                    success=False,
                    platform=publish_request.platform,
                    error="Reddit requires a subreddit name",
                    published_at=result["published_at"]
                )

            # Reddit requires title
            if not publish_request.title:
                return PublishResponse(
                    success=False,
                    platform=publish_request.platform,
                    error="Reddit requires a post title",
                    published_at=result["published_at"]
                )

            publisher = RedditPublisher(access_token=credentials['access_token'])

            # Determine post type
            if publish_request.video_url:
                post_type = "video"
                url = publish_request.video_url
            elif publish_request.image_urls and len(publish_request.image_urls) > 0:
                post_type = "image"
                url = publish_request.image_urls[0]
            elif publish_request.link_url:
                post_type = "link"
                url = publish_request.link_url
            else:
                post_type = "text"
                url = None

            publish_result = await publisher.publish_post(
                subreddit=publish_request.subreddit,
                title=publish_request.title,
                text=publish_request.caption if post_type == "text" else None,
                url=url,
                post_type=post_type
            )
            result.update(publish_result)

        elif platform == "tumblr":
            publisher = TumblrPublisher()
            image_url = publish_request.image_urls[0] if publish_request.image_urls else None
            publish_result = await publisher.publish_post(
                caption=publish_request.caption,
                image_url=image_url
            )
            result.update(publish_result)

        elif platform == "wordpress":
            # Use provided title/content if available, otherwise extract from caption
            title = publish_request.title
            if not title:
                # Extract from caption first line if no title provided
                lines = publish_request.caption.split('\n')
                title = lines[0][:100] if lines else "Untitled Post"

            content = publish_request.content or publish_request.caption

            publisher = WordPressPublisher()
            publish_result = await publisher.publish_post(
                title=title,
                content=content
            )
            result.update(publish_result)

        else:
            result["error"] = f"Platform {publish_request.platform} not supported"

        return PublishResponse(**result)

    except Exception as e:
        logger.error(f"Publishing error for user {user_id}: {e}")
        return PublishResponse(
            success=False,
            platform=publish_request.platform,
            error=str(e),
            published_at=result["published_at"]
        )

@router.get("/status")
async def check_publisher_status(request: Request):
    """
    Check which social platforms the user has connected

    MULTI-TENANT: Returns only the authenticated user's connected platforms
    """

    # Extract user_id from JWT token
    user_id = get_user_from_token(request)
    logger.info(f"Checking publisher status for user {user_id}")

    # List of platforms to check
    platforms = ["instagram", "linkedin", "twitter", "facebook", "tiktok", "youtube", "reddit", "tumblr", "wordpress"]

    status = {}

    for platform in platforms:
        credentials = get_user_service_credentials(user_id, platform)
        status[platform] = {
            "connected": credentials is not None,
            "service_id": credentials.get('service_id') if credentials else None
        }

    return {
        "user_id": user_id,
        "platforms": status,
        "total_connected": sum(1 for p in status.values() if p['connected'])
    }


@router.get("/status-legacy")
async def check_publisher_status_legacy():
    """Legacy status check using environment variables (deprecated)"""

    instagram = InstagramPublisher()
    linkedin = LinkedInPublisher()
    twitter = TwitterPublisher()
    
    return {
        "instagram": {
            "configured": bool(instagram.access_token and instagram.business_account_id),
            "ready": bool(instagram.access_token and instagram.business_account_id)
        },
        "linkedin": {
            "configured": bool(linkedin.access_token and linkedin.person_urn),
            "ready": bool(linkedin.access_token and linkedin.person_urn)
        },
        "twitter": {
            "configured": bool(twitter.api_key and twitter.access_token),
            "ready": bool(twitter.api_key and twitter.access_token)
        }
    }

# ============================================================================
# FACEBOOK PUBLISHER
# ============================================================================

class FacebookPublisher:
    """
    Facebook Graph API publisher (Multi-Tenant)
    Uses OAuth tokens from connected_services table
    Requires: pages_manage_posts permission (Meta App Review required)
    """

    def __init__(self, page_access_token: str, page_id: str):
        """
        Initialize with user's Facebook Page credentials

        Args:
            page_access_token: Page-specific access token from /me/accounts
            page_id: Facebook Page ID to post to
        """
        self.access_token = page_access_token
        self.page_id = page_id
        self.api_version = "v21.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

    async def publish_post(self, caption: str, image_url: Optional[str] = None) -> dict:
        """Publish post to Facebook Page"""
        if not self.access_token or not self.page_id:
            return {
                "success": False,
                "error": "Facebook credentials not configured"
            }

        try:
            async with httpx.AsyncClient() as client:
                endpoint = f"{self.base_url}/{self.page_id}/feed"
                data = {
                    "message": caption,
                    "access_token": self.access_token
                }

                if image_url:
                    data["link"] = image_url

                response = await client.post(endpoint, data=data)

                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Facebook API error: {response.text}"
                    }

                post_id = response.json()["id"]

                return {
                    "success": True,
                    "post_id": post_id,
                    "post_url": f"https://www.facebook.com/{post_id}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# ============================================================================
# TIKTOK PUBLISHER
# ============================================================================

class TikTokPublisher:
    """
    TikTok Direct Post API publisher
    Requires: TikTok Access Token (OAuth 2.0)
    Note: TikTok is video-only platform
    """

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://open.tiktokapis.com"

    async def publish_video(self, caption: str, video_url: str) -> dict:
        """
        Publish video to TikTok using Direct Post API

        Args:
            caption: Video caption (max 2200 chars)
            video_url: Public URL to video file

        Returns:
            dict: {success: bool, post_id: str, error: str}
        """
        if not self.access_token:
            return {
                "success": False,
                "error": "TikTok not connected. Please connect your TikTok account."
            }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                # Step 1: Initialize video upload
                init_response = await client.post(
                    f"{self.base_url}/v2/post/publish/video/init/",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "post_info": {
                            "title": caption[:2200],  # Max 2200 chars
                            "privacy_level": "SELF_ONLY",  # Options: PUBLIC_TO_EVERYONE, SELF_ONLY, MUTUAL_FOLLOW_FRIENDS
                            "disable_duet": False,
                            "disable_comment": False,
                            "disable_stitch": False,
                            "video_cover_timestamp_ms": 1000
                        },
                        "source_info": {
                            "source": "PULL_FROM_URL",
                            "video_url": video_url
                        }
                    }
                )

                if init_response.status_code != 200:
                    logger.error(f"TikTok init failed: {init_response.status_code} - {init_response.text}")
                    return {
                        "success": False,
                        "error": f"TikTok upload init failed: {init_response.status_code}"
                    }

                init_data = init_response.json()
                publish_id = init_data.get('data', {}).get('publish_id')

                if not publish_id:
                    return {
                        "success": False,
                        "error": "Failed to get publish_id from TikTok"
                    }

                # Step 2: Check publish status (TikTok processes video asynchronously)
                # In production, you'd poll this endpoint until status is PUBLISH_COMPLETE
                # For now, we return the publish_id

                return {
                    "success": True,
                    "post_id": publish_id,
                    "post_url": f"https://www.tiktok.com/",
                    "message": "Video is being processed by TikTok. Check your TikTok profile in a few minutes."
                }

        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "TikTok API timeout - video upload may take several minutes"
            }
        except Exception as e:
            logger.error(f"TikTok publish error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# ============================================================================
# YOUTUBE PUBLISHER
# ============================================================================

class YouTubePublisher:
    """
    YouTube Data API v3 publisher
    Supports: Regular videos, YouTube Shorts, thumbnail upload
    Requires: YouTube OAuth 2.0 access token with youtube.upload scope
    """

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.upload_url = "https://www.googleapis.com/upload/youtube/v3"
        self.api_url = "https://www.googleapis.com/youtube/v3"

    async def publish_video(
        self,
        title: str,
        description: str,
        video_url: str,
        privacy: str = "private",
        category_id: str = "22",
        is_short: bool = False,
        thumbnail_url: str = None
    ) -> dict:
        """
        Upload video to YouTube using resumable upload

        Args:
            title: Video title (max 100 chars)
            description: Video description (max 5000 chars)
            video_url: Public URL to video file
            privacy: "public", "private", or "unlisted"
            category_id: YouTube category ID (default: "22" = People & Blogs)
            is_short: True for YouTube Shorts (<60s vertical video)
            thumbnail_url: Optional custom thumbnail URL

        Returns:
            dict: {success: bool, post_id: str (video_id), post_url: str}
        """
        if not self.access_token:
            return {
                "success": False,
                "error": "YouTube not connected. Please connect your YouTube account."
            }

        try:
            async with httpx.AsyncClient(timeout=600.0) as client:
                # Step 1: Download video from URL
                logger.info(f"Downloading video from {video_url}")
                video_response = await client.get(video_url)
                if video_response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Failed to fetch video: {video_response.status_code}"
                    }

                video_data = video_response.content
                video_size = len(video_data)
                logger.info(f"Video downloaded: {video_size} bytes")

                # Step 2: Prepare metadata
                metadata = {
                    "snippet": {
                        "title": title[:100],
                        "description": description[:5000],
                        "categoryId": category_id
                    },
                    "status": {
                        "privacyStatus": privacy,
                        "selfDeclaredMadeForKids": False
                    }
                }

                # Add #Shorts to description for YouTube Shorts
                if is_short:
                    if metadata["snippet"]["description"]:
                        metadata["snippet"]["description"] += "\n\n#Shorts"
                    else:
                        metadata["snippet"]["description"] = "#Shorts"

                # Step 3: Initialize resumable upload
                init_response = await client.post(
                    f"{self.upload_url}/videos",
                    params={
                        "part": "snippet,status",
                        "uploadType": "resumable"
                    },
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json",
                        "X-Upload-Content-Length": str(video_size),
                        "X-Upload-Content-Type": "video/*"
                    },
                    json=metadata
                )

                if init_response.status_code != 200:
                    logger.error(f"YouTube upload init failed: {init_response.status_code} - {init_response.text}")
                    return {
                        "success": False,
                        "error": f"YouTube upload initialization failed: {init_response.status_code}"
                    }

                # Get resumable upload URL from Location header
                upload_session_url = init_response.headers.get('Location')
                if not upload_session_url:
                    return {
                        "success": False,
                        "error": "Failed to get YouTube upload session URL"
                    }

                logger.info(f"Upload session created: {upload_session_url}")

                # Step 4: Upload video binary using resumable upload
                upload_response = await client.put(
                    upload_session_url,
                    content=video_data,
                    headers={
                        "Content-Type": "video/*"
                    }
                )

                if upload_response.status_code not in [200, 201]:
                    logger.error(f"YouTube video upload failed: {upload_response.status_code} - {upload_response.text}")
                    return {
                        "success": False,
                        "error": f"YouTube video upload failed: {upload_response.status_code}"
                    }

                video_response_data = upload_response.json()
                video_id = video_response_data.get('id')

                if not video_id:
                    return {
                        "success": False,
                        "error": "No video ID returned from YouTube"
                    }

                logger.info(f"Video uploaded successfully: {video_id}")

                # Step 5: Upload custom thumbnail if provided
                if thumbnail_url:
                    thumbnail_result = await self.upload_thumbnail(video_id, thumbnail_url, client)
                    if not thumbnail_result.get("success"):
                        logger.warning(f"Thumbnail upload failed: {thumbnail_result.get('error')}")
                        # Don't fail the whole operation if thumbnail fails

                video_type = "Short" if is_short else "video"
                watch_url = f"https://www.youtube.com/watch?v={video_id}"
                if is_short:
                    watch_url = f"https://www.youtube.com/shorts/{video_id}"

                return {
                    "success": True,
                    "post_id": video_id,
                    "post_url": watch_url,
                    "message": f"YouTube {video_type} uploaded successfully as {privacy}"
                }

        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "YouTube upload timeout - large videos may take 10+ minutes"
            }
        except Exception as e:
            logger.error(f"YouTube publish error: {e}")
            return {
                "success": False,
                "error": f"YouTube error: {str(e)}"
            }

    async def upload_thumbnail(self, video_id: str, thumbnail_url: str, client: httpx.AsyncClient = None) -> dict:
        """
        Upload custom thumbnail for a YouTube video

        Args:
            video_id: YouTube video ID
            thumbnail_url: Public URL to thumbnail image
            client: Optional httpx client (reuse if provided)

        Returns:
            dict: {success: bool, error: str}
        """
        if not self.access_token:
            return {"success": False, "error": "No access token"}

        try:
            should_close_client = False
            if not client:
                client = httpx.AsyncClient(timeout=60.0)
                should_close_client = True

            # Download thumbnail
            thumb_response = await client.get(thumbnail_url)
            if thumb_response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Failed to fetch thumbnail: {thumb_response.status_code}"
                }

            thumbnail_data = thumb_response.content

            # Upload thumbnail to YouTube
            upload_response = await client.post(
                f"{self.upload_url}/thumbnails/set",
                params={"videoId": video_id},
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "image/jpeg"
                },
                content=thumbnail_data
            )

            if should_close_client:
                await client.aclose()

            if upload_response.status_code not in [200, 201]:
                return {
                    "success": False,
                    "error": f"Thumbnail upload failed: {upload_response.status_code}"
                }

            logger.info(f"Thumbnail uploaded for video {video_id}")
            return {"success": True}

        except Exception as e:
            logger.error(f"Thumbnail upload error: {e}")
            return {"success": False, "error": str(e)}

# ============================================================================
# REDDIT PUBLISHER
# ============================================================================

class RedditPublisher:
    """
    Reddit API publisher
    Requires: Reddit OAuth 2.0 access token
    Supports: Text posts, link posts, image posts, video posts
    """

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://oauth.reddit.com"

    async def publish_post(self, subreddit: str, title: str, text: Optional[str] = None,
                          url: Optional[str] = None, post_type: str = "text") -> dict:
        """
        Publish post to Reddit subreddit

        Args:
            subreddit: Subreddit name (without r/ prefix)
            title: Post title (max 300 chars)
            text: Post text/selftext for text posts
            url: URL for link posts or image/video URL
            post_type: "text", "link", "image", or "video"

        Returns:
            dict: {success: bool, post_id: str, post_url: str}
        """
        if not self.access_token:
            return {
                "success": False,
                "error": "Reddit not connected. Please connect your Reddit account."
            }

        try:
            # Validate title length
            if len(title) > 300:
                return {
                    "success": False,
                    "error": f"Reddit titles must be under 300 characters (current: {len(title)})"
                }

            async with httpx.AsyncClient(timeout=60.0) as client:
                # Determine kind based on post_type
                kind_map = {
                    "text": "self",
                    "link": "link",
                    "image": "image",
                    "video": "video"
                }
                kind = kind_map.get(post_type, "self")

                # Build submission data
                submit_data = {
                    "sr": subreddit,
                    "kind": kind,
                    "title": title
                }

                # Add content based on post type
                if post_type == "text":
                    submit_data["text"] = text or ""
                elif post_type in ["link", "image", "video"]:
                    if not url:
                        return {
                            "success": False,
                            "error": f"URL required for {post_type} posts"
                        }
                    submit_data["url"] = url

                # Submit post
                response = await client.post(
                    f"{self.base_url}/api/submit",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "User-Agent": "ORLA3-Marketing-Suite/1.0"
                    },
                    data=submit_data
                )

                if response.status_code != 200:
                    logger.error(f"Reddit API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"Reddit API error: {response.status_code}"
                    }

                result = response.json()

                # Check for errors in response
                if result.get("json", {}).get("errors"):
                    errors = result["json"]["errors"]
                    return {
                        "success": False,
                        "error": f"Reddit error: {errors[0][1] if errors else 'Unknown error'}"
                    }

                post_data = result.get("json", {}).get("data", {})
                post_url = post_data.get("url", "")
                post_id = post_data.get("name", "")  # Format: t3_xxxxx

                return {
                    "success": True,
                    "post_id": post_id,
                    "post_url": post_url,
                    "message": f"Posted to r/{subreddit}"
                }

        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Reddit API timeout"
            }
        except Exception as e:
            logger.error(f"Reddit publish error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# ============================================================================
# TUMBLR PUBLISHER
# ============================================================================

class TumblrPublisher:
    """
    Tumblr API publisher
    Requires: Tumblr API Key, API Secret, OAuth Token
    """
    
    def __init__(self):
        self.api_key = os.getenv("TUMBLR_API_KEY")
        self.api_secret = os.getenv("TUMBLR_API_SECRET")
        self.access_token = os.getenv("TUMBLR_ACCESS_TOKEN")
        self.blog_name = os.getenv("TUMBLR_BLOG_NAME")
        self.base_url = "https://api.tumblr.com/v2"
    
    async def publish_post(self, caption: str, image_url: Optional[str] = None) -> dict:
        """Publish post to Tumblr"""
        if not all([self.api_key, self.access_token, self.blog_name]):
            return {
                "success": False,
                "error": "Tumblr credentials not configured. Add TUMBLR_API_KEY, TUMBLR_ACCESS_TOKEN, TUMBLR_BLOG_NAME to .env.local"
            }
        
        try:
            async with httpx.AsyncClient() as client:
                post_type = "photo" if image_url else "text"
                
                data = {
                    "type": post_type,
                    "body": caption
                }
                
                if image_url:
                    data["source"] = image_url
                
                response = await client.post(
                    f"{self.base_url}/blog/{self.blog_name}/post",
                    headers={
                        "Authorization": f"Bearer {self.access_token}"
                    },
                    data=data
                )
                
                if response.status_code not in [200, 201]:
                    return {
                        "success": False,
                        "error": f"Tumblr API error: {response.text}"
                    }
                
                post_id = response.json()["response"]["id"]
                
                return {
                    "success": True,
                    "post_id": str(post_id),
                    "post_url": f"https://{self.blog_name}.tumblr.com/post/{post_id}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# ============================================================================
# WORDPRESS PUBLISHER
# ============================================================================

class WordPressPublisher:
    """
    WordPress.com API publisher (supports both WordPress.com and self-hosted with Jetpack)
    Requires: WordPress.com OAuth Access Token OR WordPress site with Application Password
    """

    def __init__(self):
        self.site_url = os.getenv("WORDPRESS_SITE_URL")  # WordPress.com site or custom domain
        self.access_token = os.getenv("WORDPRESS_ACCESS_TOKEN")  # WordPress.com OAuth token
        self.username = os.getenv("WORDPRESS_USERNAME")
        self.app_password = os.getenv("WORDPRESS_APP_PASSWORD")
        self.site_id = os.getenv("WORDPRESS_SITE_ID")  # For WordPress.com API (e.g., sgillespiea7d7336966-wgdcj.wordpress.com)

    async def publish_post(self, title: str, content: str, status: str = "publish") -> dict:
        """Publish blog post to WordPress"""

        # Try WordPress.com OAuth API first (preferred for WordPress.com sites)
        if self.access_token and self.site_id:
            return await self._publish_via_wpcom_api(title, content, status)

        # Fallback to WordPress REST API with app password (self-hosted or Jetpack)
        if self.site_url and self.username and self.app_password:
            return await self._publish_via_rest_api(title, content, status)

        return {
            "success": False,
            "error": "WordPress not configured. Need either: (1) WORDPRESS_ACCESS_TOKEN + WORDPRESS_SITE_ID for WordPress.com, OR (2) WORDPRESS_SITE_URL + WORDPRESS_USERNAME + WORDPRESS_APP_PASSWORD for self-hosted"
        }

    async def _publish_via_wpcom_api(self, title: str, content: str, status: str) -> dict:
        """Publish via WordPress.com REST API (OAuth)"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"https://public-api.wordpress.com/rest/v1.1/sites/{self.site_id}/posts/new",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    data={
                        "title": title,
                        "content": content,
                        "status": status  # publish, draft, pending, private
                    }
                )

                # Check response status
                if response.status_code not in [200, 201]:
                    error_text = response.text[:300] if response.text else "No error message"
                    print(f"WordPress API error {response.status_code}: {error_text}")
                    return {
                        "success": False,
                        "error": f"WordPress.com API error ({response.status_code}): {error_text}"
                    }

                # Parse response
                try:
                    post_data = response.json()
                except Exception as json_error:
                    print(f"WordPress JSON parse error: {str(json_error)}, Response: {response.text[:300]}")
                    return {
                        "success": False,
                        "error": f"WordPress.com response parsing failed: {str(json_error)}"
                    }

                post_id = post_data.get("ID")
                post_url = post_data.get("URL")

                if not post_id:
                    print(f"WordPress response missing ID: {post_data}")
                    return {
                        "success": False,
                        "error": "WordPress.com response missing post ID"
                    }

                print(f"✅ WordPress post created: ID={post_id}, URL={post_url}")

                return {
                    "success": True,
                    "post_id": str(post_id),
                    "post_url": post_url or ""
                }

        except httpx.TimeoutException as e:
            print(f"WordPress timeout: {str(e)}")
            return {
                "success": False,
                "error": f"WordPress.com API timeout: {str(e)}"
            }
        except Exception as e:
            print(f"WordPress exception: {str(e)}, Type: {type(e).__name__}")
            return {
                "success": False,
                "error": f"WordPress.com API exception ({type(e).__name__}): {str(e)}"
            }

    async def _publish_via_rest_api(self, title: str, content: str, status: str) -> dict:
        """Publish via WordPress REST API (Application Password for self-hosted)"""
        try:
            import base64

            # Create basic auth header
            credentials = f"{self.username}:{self.app_password}"
            token = base64.b64encode(credentials.encode()).decode()

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.site_url}/wp-json/wp/v2/posts",
                    headers={
                        "Authorization": f"Basic {token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "title": title,
                        "content": content,
                        "status": status
                    }
                )

                if response.status_code not in [200, 201]:
                    return {
                        "success": False,
                        "error": f"WordPress REST API error ({response.status_code}): {response.text[:200]}"
                    }

                post_data = response.json()
                post_id = post_data.get("id")
                post_url = post_data.get("link")

                return {
                    "success": True,
                    "post_id": str(post_id),
                    "post_url": post_url
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"WordPress REST API exception: {str(e)}"
            }


# ============================================================================
# UPDATE MAIN PUBLISHING ENDPOINT WITH ALL PLATFORMS
# ============================================================================

# Update the existing publish_content function to handle all platforms
# This goes at the end of the file to override the earlier version

@router.post("/publish-all", response_model=PublishResponse)
async def publish_content_all_platforms(request: PublishRequest):
    """
    Universal publishing endpoint supporting all 9 platforms
    """
    
    result = {
        "success": False,
        "platform": request.platform,
        "published_at": datetime.utcnow().isoformat()
    }
    
    try:
        if request.platform == "instagram":
            publisher = InstagramPublisher()
            
            if request.content_type == "carousel" and len(request.image_urls) > 1:
                publish_result = await publisher.publish_carousel(
                    caption=request.caption,
                    image_urls=request.image_urls
                )
            elif request.image_urls:
                publish_result = await publisher.publish_single_image(
                    caption=request.caption,
                    image_url=request.image_urls[0]
                )
            else:
                return PublishResponse(
                    success=False,
                    platform=request.platform,
                    error="Instagram posts require at least one image",
                    published_at=result["published_at"]
                )
            
            result.update(publish_result)
            
        elif request.platform == "linkedin":
            publisher = LinkedInPublisher()
            publish_result = await publisher.publish_text(caption=request.caption)
            result.update(publish_result)
            
        elif request.platform == "twitter":
            publisher = TwitterPublisher()
            publish_result = await publisher.publish_tweet(caption=request.caption)
            result.update(publish_result)
            
        elif request.platform == "facebook":
            # Legacy endpoint not supported for Facebook multi-tenant
            result["error"] = "Facebook publishing requires authentication. Use /publisher/publish with JWT token."
            
        elif request.platform == "tiktok":
            result["error"] = "TikTok requires video upload - not supported for text/image posts"
            
        elif request.platform == "youtube":
            result["error"] = "YouTube requires video upload - coming soon"
            
        elif request.platform == "reddit":
            publisher = RedditPublisher()
            # Reddit needs subreddit - for now use generic error
            result["error"] = "Reddit publishing requires subreddit selection - use API directly with subreddit parameter"
            
        elif request.platform == "tumblr":
            publisher = TumblrPublisher()
            image_url = request.image_urls[0] if request.image_urls else None
            publish_result = await publisher.publish_post(
                caption=request.caption,
                image_url=image_url
            )
            result.update(publish_result)
            
        elif request.platform == "wordpress":
            # WordPress needs title - extract from caption first line or use default
            lines = request.caption.split('\n')
            title = lines[0][:100] if lines else "Untitled Post"
            content = request.caption
            
            publisher = WordPressPublisher()
            publish_result = await publisher.publish_post(
                title=title,
                content=content
            )
            result.update(publish_result)
            
        else:
            result["error"] = f"Platform {request.platform} not supported"
        
        return PublishResponse(**result)
        
    except Exception as e:
        return PublishResponse(
            success=False,
            platform=request.platform,
            error=str(e),
            published_at=result["published_at"]
        )

@router.get("/status-all")
async def check_all_publishers_status():
    """Check configuration status for all 9 social platforms"""
    
    instagram = InstagramPublisher()
    linkedin = LinkedInPublisher()
    twitter = TwitterPublisher()
    facebook = FacebookPublisher()
    tiktok = TikTokPublisher()
    youtube = YouTubePublisher()
    reddit = RedditPublisher()
    tumblr = TumblrPublisher()
    wordpress = WordPressPublisher()
    
    return {
        "instagram": {
            "configured": bool(instagram.access_token and instagram.business_account_id),
            "ready": bool(instagram.access_token and instagram.business_account_id),
            "supports": ["image", "carousel"]
        },
        "linkedin": {
            "configured": bool(linkedin.access_token and linkedin.person_urn),
            "ready": bool(linkedin.access_token and linkedin.person_urn),
            "supports": ["text"]
        },
        "twitter": {
            "configured": bool(twitter.api_key and twitter.access_token),
            "ready": bool(twitter.api_key and twitter.access_token),
            "supports": ["text", "image"]
        },
        "facebook": {
            "configured": bool(facebook.access_token and facebook.page_id),
            "ready": bool(facebook.access_token and facebook.page_id),
            "supports": ["text", "image"]
        },
        "tiktok": {
            "configured": bool(tiktok.access_token),
            "ready": False,
            "supports": ["video"],
            "note": "Video upload only - not yet implemented"
        },
        "youtube": {
            "configured": bool(youtube.access_token),
            "ready": False,
            "supports": ["video"],
            "note": "Video upload only - not yet implemented"
        },
        "reddit": {
            "configured": bool(reddit.client_id and reddit.access_token),
            "ready": bool(reddit.client_id and reddit.access_token),
            "supports": ["text"]
        },
        "tumblr": {
            "configured": bool(tumblr.api_key and tumblr.access_token),
            "ready": bool(tumblr.api_key and tumblr.access_token),
            "supports": ["text", "image"]
        },
        "wordpress": {
            "configured": bool(wordpress.site_url and wordpress.username),
            "ready": bool(wordpress.site_url and wordpress.username),
            "supports": ["text", "image"]
        }
    }

