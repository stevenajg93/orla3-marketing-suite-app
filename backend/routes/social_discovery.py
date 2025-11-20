"""
Social media post discovery endpoints
Search for relevant posts across platforms to engage with
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
import httpx
import logging
from datetime import datetime
from middleware.user_context import get_user_id
import psycopg2
import os

logger = logging.getLogger(__name__)
router = APIRouter()

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class DiscoveryPost(BaseModel):
    id: str
    platform: str
    author: str
    author_id: Optional[str] = None
    content: str
    url: Optional[str] = None
    hashtags: List[str] = []
    engagement: int  # likes + comments + shares
    timestamp: str
    media_url: Optional[str] = None


class DiscoveryRequest(BaseModel):
    query: str
    platforms: List[str] = ["twitter", "reddit"]  # Default platforms
    limit: int = 20


class DiscoveryResponse(BaseModel):
    success: bool
    platform: str
    posts: List[DiscoveryPost]
    total: int
    query: str
    error: Optional[str] = None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_user_oauth_token(user_id: str, platform: str):
    """Get user's OAuth token for platform from database"""
    try:
        if not DATABASE_URL:
            logger.error("DATABASE_URL not configured")
            return None

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT access_token, service_metadata
            FROM connected_services
            WHERE user_id = %s
            AND service_type = %s
            AND is_active = true
        """, (user_id, platform))

        result = cursor.fetchone()
        cursor.close()

        if result:
            return {"access_token": result[0], "metadata": result[1]}
        return None

    except Exception as e:
        logger.error(f"Error fetching OAuth token: {e}")
        return None


# ============================================================================
# TWITTER SEARCH
# ============================================================================

@router.post("/discover/twitter", response_model=DiscoveryResponse)
async def search_twitter(request: Request, discovery_request: DiscoveryRequest):
    """
    Search Twitter for posts matching keywords/hashtags

    Uses Twitter API v2 /tweets/search/recent endpoint
    Requires scope: tweet.read
    """
    user_id = str(get_user_id(request))
    query = discovery_request.query
    limit = min(discovery_request.limit, 100)  # Twitter API max

    logger.info(f"Searching Twitter for: {query} (user: {user_id})")

    # Get user's Twitter OAuth token
    credentials = get_user_oauth_token(user_id, "twitter")

    if not credentials:
        return DiscoveryResponse(
            success=False,
            platform="twitter",
            posts=[],
            total=0,
            query=query,
            error="Twitter account not connected. Please connect in settings."
        )

    access_token = credentials['access_token']

    try:
        posts = []

        async with httpx.AsyncClient() as client:
            # Search recent tweets
            response = await client.get(
                "https://api.twitter.com/2/tweets/search/recent",
                headers={
                    "Authorization": f"Bearer {access_token}"
                },
                params={
                    "query": query,
                    "max_results": limit,
                    "tweet.fields": "created_at,author_id,public_metrics,entities",
                    "expansions": "author_id",
                    "user.fields": "username,name"
                },
                timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()

                # Build user lookup map
                users = {}
                for user in data.get('includes', {}).get('users', []):
                    users[user['id']] = user

                # Process tweets
                for tweet in data.get('data', []):
                    author = users.get(tweet['author_id'], {})
                    metrics = tweet.get('public_metrics', {})

                    # Extract hashtags
                    hashtags = []
                    entities = tweet.get('entities', {})
                    if 'hashtags' in entities:
                        hashtags = [tag['tag'] for tag in entities['hashtags']]

                    # Calculate total engagement
                    engagement = (
                        metrics.get('like_count', 0) +
                        metrics.get('reply_count', 0) +
                        metrics.get('retweet_count', 0)
                    )

                    posts.append(DiscoveryPost(
                        id=tweet['id'],
                        platform="twitter",
                        author=f"@{author.get('username', 'Unknown')}",
                        author_id=tweet['author_id'],
                        content=tweet.get('text', ''),
                        url=f"https://twitter.com/{author.get('username', 'i')}/status/{tweet['id']}",
                        hashtags=hashtags,
                        engagement=engagement,
                        timestamp=tweet.get('created_at', '')
                    ))

                return DiscoveryResponse(
                    success=True,
                    platform="twitter",
                    posts=posts,
                    total=len(posts),
                    query=query
                )

            else:
                logger.error(f"Twitter API error: {response.status_code} - {response.text}")
                return DiscoveryResponse(
                    success=False,
                    platform="twitter",
                    posts=[],
                    total=0,
                    query=query,
                    error=f"Twitter API error: {response.status_code}"
                )

    except httpx.TimeoutException:
        logger.error("Twitter API timeout")
        return DiscoveryResponse(
            success=False,
            platform="twitter",
            posts=[],
            total=0,
            query=query,
            error="Request timeout - Twitter API took too long to respond"
        )
    except Exception as e:
        logger.error(f"Error searching Twitter: {e}")
        return DiscoveryResponse(
            success=False,
            platform="twitter",
            posts=[],
            total=0,
            query=query,
            error=str(e)
        )


# ============================================================================
# REDDIT SEARCH
# ============================================================================

@router.post("/discover/reddit", response_model=DiscoveryResponse)
async def search_reddit(request: Request, discovery_request: DiscoveryRequest):
    """
    Search Reddit for posts matching keywords

    Uses Reddit API /search endpoint
    Requires OAuth 2.0 with read scope
    """
    user_id = str(get_user_id(request))
    query = discovery_request.query
    limit = min(discovery_request.limit, 100)  # Reddit API max

    logger.info(f"Searching Reddit for: {query} (user: {user_id})")

    # Get user's Reddit OAuth token
    credentials = get_user_oauth_token(user_id, "reddit")

    if not credentials:
        return DiscoveryResponse(
            success=False,
            platform="reddit",
            posts=[],
            total=0,
            query=query,
            error="Reddit account not connected. Please connect in settings."
        )

    access_token = credentials['access_token']

    try:
        posts = []

        async with httpx.AsyncClient() as client:
            # Search across all subreddits
            response = await client.get(
                "https://oauth.reddit.com/search",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "User-Agent": "ORLA3-Marketing-Suite/1.0"
                },
                params={
                    "q": query,
                    "limit": limit,
                    "sort": "relevance",
                    "type": "link"  # Posts only, not comments
                },
                timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()

                # Process posts
                for post_data in data.get('data', {}).get('children', []):
                    post = post_data.get('data', {})

                    # Calculate total engagement
                    engagement = post.get('score', 0) + post.get('num_comments', 0)

                    # Extract text content (title + selftext)
                    content = post.get('title', '')
                    if post.get('selftext'):
                        content += f"\n\n{post.get('selftext')[:200]}..."  # Truncate long posts

                    posts.append(DiscoveryPost(
                        id=post.get('id', ''),
                        platform="reddit",
                        author=f"u/{post.get('author', 'Unknown')}",
                        author_id=post.get('author', ''),
                        content=content,
                        url=f"https://reddit.com{post.get('permalink', '')}",
                        hashtags=[post.get('subreddit', '')],  # Use subreddit as "hashtag"
                        engagement=engagement,
                        timestamp=datetime.fromtimestamp(post.get('created_utc', 0)).isoformat(),
                        media_url=post.get('thumbnail') if post.get('thumbnail', '').startswith('http') else None
                    ))

                return DiscoveryResponse(
                    success=True,
                    platform="reddit",
                    posts=posts,
                    total=len(posts),
                    query=query
                )

            else:
                logger.error(f"Reddit API error: {response.status_code} - {response.text}")
                return DiscoveryResponse(
                    success=False,
                    platform="reddit",
                    posts=[],
                    total=0,
                    query=query,
                    error=f"Reddit API error: {response.status_code}"
                )

    except httpx.TimeoutException:
        logger.error("Reddit API timeout")
        return DiscoveryResponse(
            success=False,
            platform="reddit",
            posts=[],
            total=0,
            query=query,
            error="Request timeout - Reddit API took too long to respond"
        )
    except Exception as e:
        logger.error(f"Error searching Reddit: {e}")
        return DiscoveryResponse(
            success=False,
            platform="reddit",
            posts=[],
            total=0,
            query=query,
            error=str(e)
        )


# ============================================================================
# LINKEDIN SEARCH (Perplexity Fallback)
# ============================================================================

@router.post("/discover/linkedin", response_model=DiscoveryResponse)
async def search_linkedin(request: Request, discovery_request: DiscoveryRequest):
    """
    Search LinkedIn for posts matching keywords

    Note: LinkedIn API doesn't have public post search
    Falls back to Perplexity AI for LinkedIn content discovery
    """
    user_id = str(get_user_id(request))
    query = discovery_request.query

    logger.info(f"Searching LinkedIn for: {query} (user: {user_id})")

    # LinkedIn API doesn't support post search for non-company accounts
    # Return informative message
    return DiscoveryResponse(
        success=False,
        platform="linkedin",
        posts=[],
        total=0,
        query=query,
        error="LinkedIn post search is not available via API. Use Twitter or Reddit discovery instead."
    )


# ============================================================================
# MULTI-PLATFORM DISCOVERY
# ============================================================================

@router.post("/discover/all", response_model=List[DiscoveryPost])
async def search_all_platforms(request: Request, discovery_request: DiscoveryRequest):
    """
    Search across multiple platforms simultaneously
    Returns aggregated list sorted by engagement
    """
    user_id = str(get_user_id(request))
    logger.info(f"Searching all platforms for: {discovery_request.query} (user: {user_id})")

    all_posts = []

    # Search Twitter if in platforms list
    if "twitter" in discovery_request.platforms or "x" in discovery_request.platforms:
        twitter_result = await search_twitter(request, discovery_request)
        if twitter_result.success:
            all_posts.extend(twitter_result.posts)

    # Search Reddit if in platforms list
    if "reddit" in discovery_request.platforms:
        reddit_result = await search_reddit(request, discovery_request)
        if reddit_result.success:
            all_posts.extend(reddit_result.posts)

    # Sort by engagement (highest first)
    all_posts.sort(key=lambda x: x.engagement, reverse=True)

    return all_posts[:discovery_request.limit]
