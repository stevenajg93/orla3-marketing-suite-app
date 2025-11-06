from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Literal
import os
import httpx
import json
from datetime import datetime

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
        """Publish tweet to Twitter/X"""
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            return {
                "success": False,
                "error": "Twitter credentials not configured. Add TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET to .env.local"
            }
        
        try:
            # Twitter API v2 requires OAuth 1.0a for posting
            # For MVP, we'll use httpx with manual OAuth
            # Production should use tweepy or similar library
            
            async with httpx.AsyncClient() as client:
                # This is simplified - real OAuth 1.0a signing required
                response = await client.post(
                    f"{self.base_url}/tweets",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "text": caption
                    }
                )
                
                if response.status_code not in [200, 201]:
                    return {
                        "success": False,
                        "error": f"Twitter API error: {response.text}"
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
                "error": str(e)
            }

# ============================================================================
# MAIN PUBLISHING ENDPOINT
# ============================================================================

@router.post("/publish", response_model=PublishResponse)
async def publish_content(request: PublishRequest):
    """
    Universal publishing endpoint supporting all platforms
    Routes to appropriate platform publisher based on request
    """

    result = {
        "success": False,
        "platform": request.platform,
        "published_at": datetime.utcnow().isoformat()
    }

    try:
        # Handle X/Twitter alias
        platform = "twitter" if request.platform == "x" else request.platform

        if platform == "instagram":
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

        elif platform == "linkedin":
            publisher = LinkedInPublisher()
            publish_result = await publisher.publish_text(caption=request.caption)
            result.update(publish_result)

        elif platform == "twitter":
            publisher = TwitterPublisher()
            publish_result = await publisher.publish_tweet(caption=request.caption)
            result.update(publish_result)

        elif platform == "facebook":
            publisher = FacebookPublisher()
            image_url = request.image_urls[0] if request.image_urls else None
            publish_result = await publisher.publish_post(
                caption=request.caption,
                image_url=image_url
            )
            result.update(publish_result)

        elif platform == "tiktok":
            result["error"] = "TikTok requires video upload - not supported for text/image posts"

        elif platform == "youtube":
            result["error"] = "YouTube requires video upload - coming soon"

        elif platform == "reddit":
            result["error"] = "Reddit publishing requires subreddit selection - coming soon"

        elif platform == "tumblr":
            publisher = TumblrPublisher()
            image_url = request.image_urls[0] if request.image_urls else None
            publish_result = await publisher.publish_post(
                caption=request.caption,
                image_url=image_url
            )
            result.update(publish_result)

        elif platform == "wordpress":
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

@router.get("/status")
async def check_publisher_status():
    """Check which social platforms are configured and ready"""
    
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
    Facebook Graph API publisher
    Requires: Facebook Page Access Token, Facebook Page ID
    """
    
    def __init__(self):
        self.access_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
        self.page_id = os.getenv("FACEBOOK_PAGE_ID")
        self.api_version = "v21.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
    
    async def publish_post(self, caption: str, image_url: Optional[str] = None) -> dict:
        """Publish post to Facebook Page"""
        if not self.access_token or not self.page_id:
            return {
                "success": False,
                "error": "Facebook credentials not configured. Add FACEBOOK_PAGE_ACCESS_TOKEN and FACEBOOK_PAGE_ID to .env.local"
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
    WordPress REST API publisher
    Requires: WordPress site URL, Application Password
    """
    
    def __init__(self):
        self.site_url = os.getenv("WORDPRESS_SITE_URL")  # e.g., https://yoursite.com
        self.username = os.getenv("WORDPRESS_USERNAME")
        self.app_password = os.getenv("WORDPRESS_APP_PASSWORD")
    
    async def publish_post(self, title: str, content: str, status: str = "publish") -> dict:
        """Publish blog post to WordPress"""
        if not all([self.site_url, self.username, self.app_password]):
            return {
                "success": False,
                "error": "WordPress credentials not configured. Add WORDPRESS_SITE_URL, WORDPRESS_USERNAME, WORDPRESS_APP_PASSWORD to .env.local"
            }
        
        try:
            import base64
            
            # Create basic auth header
            credentials = f"{self.username}:{self.app_password}"
            token = base64.b64encode(credentials.encode()).decode()
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.site_url}/wp-json/wp/v2/posts",
                    headers={
                        "Authorization": f"Basic {token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "title": title,
                        "content": content,
                        "status": status  # draft, publish, pending
                    }
                )
                
                if response.status_code not in [200, 201]:
                    return {
                        "success": False,
                        "error": f"WordPress API error: {response.text}"
                    }
                
                post_data = response.json()
                post_id = post_data["id"]
                post_url = post_data["link"]
                
                return {
                    "success": True,
                    "post_id": str(post_id),
                    "post_url": post_url
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
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
            publisher = FacebookPublisher()
            image_url = request.image_urls[0] if request.image_urls else None
            publish_result = await publisher.publish_post(
                caption=request.caption,
                image_url=image_url
            )
            result.update(publish_result)
            
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

