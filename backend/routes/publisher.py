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
    content_type: Literal["text", "image", "video", "carousel"]
    caption: str
    image_urls: Optional[List[str]] = []
    account_id: Optional[str] = None  # For multi-account support later
    title: Optional[str] = None  # For WordPress blog posts
    content: Optional[str] = None  # For WordPress full content (if different from caption)

class PublishResponse(BaseModel):
    success: bool
    platform: str
    post_id: Optional[str] = None
    post_url: Optional[str] = None
    error: Optional[str] = None
    published_at: str

# ============================================================================
# INSTAGRAM PUBLISHER
# ============================================================================

class InstagramPublisher:
    """
    Instagram Graph API publisher
    Requires: Instagram Business Account, Facebook Page Access Token
    """
    
    def __init__(self):
        self.access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.business_account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
        self.api_version = "v21.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
    
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

# ============================================================================
# LINKEDIN PUBLISHER
# ============================================================================

class LinkedInPublisher:
    """
    LinkedIn API publisher
    Requires: LinkedIn Access Token, LinkedIn Person/Organization URN
    """
    
    def __init__(self):
        self.access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        self.person_urn = os.getenv("LINKEDIN_PERSON_URN")  # e.g., urn:li:person:ABC123
        self.api_version = "202410"
        self.base_url = "https://api.linkedin.com/rest"
    
    async def publish_text(self, caption: str) -> dict:
        """Publish text-only post to LinkedIn"""
        if not self.access_token or not self.person_urn:
            return {
                "success": False,
                "error": "LinkedIn credentials not configured. Add LINKEDIN_ACCESS_TOKEN and LINKEDIN_PERSON_URN to .env.local"
            }
        
        try:
            async with httpx.AsyncClient() as client:
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
                        "commentary": caption,
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
                    return {
                        "success": False,
                        "error": f"LinkedIn API error: {response.text}"
                    }
                
                post_data = response.json()
                post_id = post_data.get("id", "")
                
                return {
                    "success": True,
                    "post_id": post_id,
                    "post_url": f"https://www.linkedin.com/feed/update/{post_id}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def publish_image(self, caption: str, image_url: str) -> dict:
        """Publish image post to LinkedIn"""
        # LinkedIn image publishing is more complex (requires asset registration)
        # For MVP, we'll implement text-only and document image flow
        return {
            "success": False,
            "error": "LinkedIn image publishing coming soon - use text posts for now"
        }

# ============================================================================
# TWITTER/X PUBLISHER
# ============================================================================

class TwitterPublisher:
    """
    Twitter/X API v2 publisher
    Requires: Twitter API Key, API Secret, Access Token, Access Token Secret
    """
    
    def __init__(self):
        self.api_key = os.getenv("TWITTER_API_KEY")
        self.api_secret = os.getenv("TWITTER_API_SECRET")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        self.base_url = "https://api.twitter.com/2"
    
    async def publish_tweet(self, caption: str) -> dict:
        """Publish tweet to Twitter/X using OAuth 1.0a"""
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            return {
                "success": False,
                "error": "Twitter credentials not configured. Add TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET to .env"
            }

        try:
            # Create OAuth 1.0a session (required for Twitter API v2 posting)
            oauth = OAuth1Session(
                self.api_key,
                client_secret=self.api_secret,
                resource_owner_key=self.access_token,
                resource_owner_secret=self.access_token_secret
            )

            # Post tweet using OAuth 1.0a
            payload = {"text": caption}
            response = oauth.post(
                f"{self.base_url}/tweets",
                json=payload
            )

            if response.status_code not in [200, 201]:
                return {
                    "success": False,
                    "error": f"Twitter API error ({response.status_code}): {response.text}"
                }

            tweet_data = response.json()["data"]
            tweet_id = tweet_data["id"]

            return {
                "success": True,
                "post_id": tweet_id,
                "post_url": f"https://twitter.com/i/web/status/{tweet_id}"
            }

        except Exception as e:
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

        if not credentials:
            return PublishResponse(
                success=False,
                platform=publish_request.platform,
                error=f"No active {platform} connection found. Please connect your {platform} account in settings.",
                published_at=result["published_at"]
            )

        if platform == "instagram":
            publisher = InstagramPublisher()

            if publish_request.content_type == "carousel" and len(publish_request.image_urls) > 1:
                publish_result = await publisher.publish_carousel(
                    caption=publish_request.caption,
                    image_urls=publish_request.image_urls
                )
            elif publish_request.image_urls:
                publish_result = await publisher.publish_single_image(
                    caption=publish_request.caption,
                    image_url=publish_request.image_urls[0]
                )
            else:
                return PublishResponse(
                    success=False,
                    platform=publish_request.platform,
                    error="Instagram posts require at least one image",
                    published_at=result["published_at"]
                )

            result.update(publish_result)

        elif platform == "linkedin":
            publisher = LinkedInPublisher()
            publish_result = await publisher.publish_text(caption=publish_request.caption)
            result.update(publish_result)

        elif platform == "twitter":
            publisher = TwitterPublisher()
            publish_result = await publisher.publish_tweet(caption=publish_request.caption)
            result.update(publish_result)

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
            result["error"] = "TikTok requires video upload - not supported for text/image posts"

        elif platform == "youtube":
            result["error"] = "YouTube requires video upload - coming soon"

        elif platform == "reddit":
            result["error"] = "Reddit publishing requires subreddit selection - coming soon"

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
    TikTok API publisher
    Requires: TikTok Access Token
    Note: TikTok API is video-only, no text posts
    """
    
    def __init__(self):
        self.access_token = os.getenv("TIKTOK_ACCESS_TOKEN")
        self.base_url = "https://open-api.tiktok.com"
    
    async def publish_video(self, caption: str, video_url: str) -> dict:
        """Publish video to TikTok"""
        if not self.access_token:
            return {
                "success": False,
                "error": "TikTok credentials not configured. Add TIKTOK_ACCESS_TOKEN to .env.local"
            }
        
        return {
            "success": False,
            "error": "TikTok video publishing requires video upload flow - text/image posts not supported on TikTok"
        }

# ============================================================================
# YOUTUBE PUBLISHER
# ============================================================================

class YouTubePublisher:
    """
    YouTube Data API v3 publisher
    Requires: YouTube API credentials, video upload
    Note: YouTube is video-only platform
    """
    
    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        self.access_token = os.getenv("YOUTUBE_ACCESS_TOKEN")
    
    async def publish_video(self, title: str, description: str, video_url: str) -> dict:
        """Upload video to YouTube"""
        if not self.access_token:
            return {
                "success": False,
                "error": "YouTube credentials not configured. Add YOUTUBE_ACCESS_TOKEN to .env.local"
            }
        
        return {
            "success": False,
            "error": "YouTube video publishing requires video upload flow - coming soon"
        }

# ============================================================================
# REDDIT PUBLISHER
# ============================================================================

class RedditPublisher:
    """
    Reddit API publisher
    Requires: Reddit Client ID, Client Secret, Access Token
    """
    
    def __init__(self):
        self.client_id = os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.access_token = os.getenv("REDDIT_ACCESS_TOKEN")
        self.username = os.getenv("REDDIT_USERNAME")
        self.base_url = "https://oauth.reddit.com"
    
    async def publish_post(self, subreddit: str, title: str, text: str) -> dict:
        """Publish text post to Reddit"""
        if not all([self.client_id, self.client_secret, self.access_token]):
            return {
                "success": False,
                "error": "Reddit credentials not configured. Add REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_ACCESS_TOKEN to .env.local"
            }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/submit",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "User-Agent": "Orla3MarketingSuite/1.0"
                    },
                    data={
                        "sr": subreddit,
                        "kind": "self",
                        "title": title,
                        "text": text
                    }
                )
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Reddit API error: {response.text}"
                    }
                
                result = response.json()
                post_url = result["json"]["data"]["url"]
                
                return {
                    "success": True,
                    "post_url": post_url
                }
                
        except Exception as e:
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

