"""
Social media engagement endpoints
Fetch comments, mentions, and interactions from connected platforms
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
import httpx
import logging
from datetime import datetime, timedelta
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

class Comment(BaseModel):
    id: str
    platform: str
    post_id: str
    author: str
    author_id: Optional[str] = None
    text: str
    timestamp: str
    sentiment: Optional[str] = None  # positive, negative, neutral, question
    media_url: Optional[str] = None


class CommentsResponse(BaseModel):
    success: bool
    platform: str
    comments: List[Comment]
    total: int
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


def analyze_sentiment(text: str) -> str:
    """
    Simple sentiment analysis based on keywords
    TODO: Replace with AI sentiment analysis in future
    """
    text_lower = text.lower()

    # Question indicators
    question_words = ['?', 'how', 'what', 'when', 'where', 'why', 'who', 'can you', 'could you', 'would you']
    if any(word in text_lower for word in question_words):
        return 'question'

    # Negative indicators
    negative_words = ['bad', 'hate', 'terrible', 'awful', 'worst', 'disappointed', 'angry', 'sad', 'poor', 'sucks']
    if any(word in text_lower for word in negative_words):
        return 'negative'

    # Positive indicators
    positive_words = ['great', 'love', 'awesome', 'amazing', 'excellent', 'fantastic', 'wonderful', 'best', 'perfect', 'thank']
    if any(word in text_lower for word in positive_words):
        return 'positive'

    return 'neutral'


# ============================================================================
# INSTAGRAM COMMENTS
# ============================================================================

@router.get("/comments/instagram", response_model=CommentsResponse)
async def get_instagram_comments(request: Request, post_id: Optional[str] = None, limit: int = 50):
    """
    Fetch recent Instagram comments from user's connected account

    Requires scope: instagram_manage_comments
    """
    user_id = str(get_user_id(request))
    logger.info(f"Fetching Instagram comments for user {user_id}")

    # Get user's Instagram OAuth token
    credentials = get_user_oauth_token(user_id, "instagram")

    if not credentials:
        return CommentsResponse(
            success=False,
            platform="instagram",
            comments=[],
            total=0,
            error="Instagram account not connected. Please connect in settings."
        )

    access_token = credentials['access_token']
    metadata = credentials.get('metadata', {})
    instagram_account_id = metadata.get('instagram_account_id')

    if not instagram_account_id:
        return CommentsResponse(
            success=False,
            platform="instagram",
            comments=[],
            total=0,
            error="Instagram Business Account ID not found. Please reconnect your account."
        )

    try:
        comments = []

        # If specific post_id provided, fetch comments for that post
        if post_id:
            async with httpx.AsyncClient() as client:
                # Get comments for specific media
                response = await client.get(
                    f"https://graph.facebook.com/v18.0/{post_id}/comments",
                    params={
                        "access_token": access_token,
                        "fields": "id,username,text,timestamp,like_count",
                        "limit": limit
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    for comment in data.get('data', []):
                        comments.append(Comment(
                            id=comment['id'],
                            platform="instagram",
                            post_id=post_id,
                            author=comment.get('username', 'Unknown'),
                            author_id=comment.get('id'),
                            text=comment.get('text', ''),
                            timestamp=comment.get('timestamp', ''),
                            sentiment=analyze_sentiment(comment.get('text', ''))
                        ))
                else:
                    logger.error(f"Instagram API error: {response.status_code} - {response.text}")
                    return CommentsResponse(
                        success=False,
                        platform="instagram",
                        comments=[],
                        total=0,
                        error=f"Instagram API error: {response.status_code}"
                    )

        else:
            # Fetch recent media, then get comments for each
            async with httpx.AsyncClient() as client:
                # Get recent media from Instagram account
                media_response = await client.get(
                    f"https://graph.facebook.com/v18.0/{instagram_account_id}/media",
                    params={
                        "access_token": access_token,
                        "fields": "id,caption,timestamp,comments_count",
                        "limit": 10  # Get last 10 posts
                    },
                    timeout=30.0
                )

                if media_response.status_code == 200:
                    media_data = media_response.json()

                    # For each media item, fetch comments
                    for media in media_data.get('data', [])[:5]:  # Limit to 5 most recent posts
                        if media.get('comments_count', 0) > 0:
                            comment_response = await client.get(
                                f"https://graph.facebook.com/v18.0/{media['id']}/comments",
                                params={
                                    "access_token": access_token,
                                    "fields": "id,username,text,timestamp",
                                    "limit": 10
                                },
                                timeout=30.0
                            )

                            if comment_response.status_code == 200:
                                comment_data = comment_response.json()
                                for comment in comment_data.get('data', []):
                                    comments.append(Comment(
                                        id=comment['id'],
                                        platform="instagram",
                                        post_id=media['id'],
                                        author=comment.get('username', 'Unknown'),
                                        text=comment.get('text', ''),
                                        timestamp=comment.get('timestamp', ''),
                                        sentiment=analyze_sentiment(comment.get('text', ''))
                                    ))

                                if len(comments) >= limit:
                                    break

        return CommentsResponse(
            success=True,
            platform="instagram",
            comments=comments[:limit],
            total=len(comments)
        )

    except httpx.TimeoutException:
        logger.error("Instagram API timeout")
        return CommentsResponse(
            success=False,
            platform="instagram",
            comments=[],
            total=0,
            error="Request timeout - Instagram API took too long to respond"
        )
    except Exception as e:
        logger.error(f"Error fetching Instagram comments: {e}")
        return CommentsResponse(
            success=False,
            platform="instagram",
            comments=[],
            total=0,
            error=str(e)
        )


# ============================================================================
# FACEBOOK COMMENTS
# ============================================================================

@router.get("/comments/facebook", response_model=CommentsResponse)
async def get_facebook_comments(request: Request, post_id: Optional[str] = None, limit: int = 50):
    """
    Fetch recent Facebook Page comments from user's connected account

    Requires scope: pages_manage_engagement
    """
    user_id = str(get_user_id(request))
    logger.info(f"Fetching Facebook comments for user {user_id}")

    # Get user's Facebook OAuth token
    credentials = get_user_oauth_token(user_id, "facebook")

    if not credentials:
        return CommentsResponse(
            success=False,
            platform="facebook",
            comments=[],
            total=0,
            error="Facebook account not connected. Please connect in settings."
        )

    metadata = credentials.get('metadata', {})
    page_access_token = metadata.get('page_access_token')
    page_id = metadata.get('selected_page_id')

    if not page_access_token or not page_id:
        return CommentsResponse(
            success=False,
            platform="facebook",
            comments=[],
            total=0,
            error="Facebook Page not selected. Please select a Page in settings."
        )

    try:
        comments = []

        async with httpx.AsyncClient() as client:
            if post_id:
                # Get comments for specific post
                response = await client.get(
                    f"https://graph.facebook.com/v18.0/{post_id}/comments",
                    params={
                        "access_token": page_access_token,
                        "fields": "id,from,message,created_time,like_count",
                        "limit": limit
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    for comment in data.get('data', []):
                        comments.append(Comment(
                            id=comment['id'],
                            platform="facebook",
                            post_id=post_id,
                            author=comment.get('from', {}).get('name', 'Unknown'),
                            author_id=comment.get('from', {}).get('id'),
                            text=comment.get('message', ''),
                            timestamp=comment.get('created_time', ''),
                            sentiment=analyze_sentiment(comment.get('message', ''))
                        ))
                else:
                    logger.error(f"Facebook API error: {response.status_code} - {response.text}")
                    return CommentsResponse(
                        success=False,
                        platform="facebook",
                        comments=[],
                        total=0,
                        error=f"Facebook API error: {response.status_code}"
                    )

            else:
                # Get recent posts from Page
                posts_response = await client.get(
                    f"https://graph.facebook.com/v18.0/{page_id}/feed",
                    params={
                        "access_token": page_access_token,
                        "fields": "id,message,created_time",
                        "limit": 10
                    },
                    timeout=30.0
                )

                if posts_response.status_code == 200:
                    posts_data = posts_response.json()

                    # For each post, fetch comments
                    for post in posts_data.get('data', [])[:5]:  # Limit to 5 recent posts
                        comment_response = await client.get(
                            f"https://graph.facebook.com/v18.0/{post['id']}/comments",
                            params={
                                "access_token": page_access_token,
                                "fields": "id,from,message,created_time",
                                "limit": 10
                            },
                            timeout=30.0
                        )

                        if comment_response.status_code == 200:
                            comment_data = comment_response.json()
                            for comment in comment_data.get('data', []):
                                comments.append(Comment(
                                    id=comment['id'],
                                    platform="facebook",
                                    post_id=post['id'],
                                    author=comment.get('from', {}).get('name', 'Unknown'),
                                    author_id=comment.get('from', {}).get('id'),
                                    text=comment.get('message', ''),
                                    timestamp=comment.get('created_time', ''),
                                    sentiment=analyze_sentiment(comment.get('message', ''))
                                ))

                            if len(comments) >= limit:
                                break

        return CommentsResponse(
            success=True,
            platform="facebook",
            comments=comments[:limit],
            total=len(comments)
        )

    except httpx.TimeoutException:
        logger.error("Facebook API timeout")
        return CommentsResponse(
            success=False,
            platform="facebook",
            comments=[],
            total=0,
            error="Request timeout - Facebook API took too long to respond"
        )
    except Exception as e:
        logger.error(f"Error fetching Facebook comments: {e}")
        return CommentsResponse(
            success=False,
            platform="facebook",
            comments=[],
            total=0,
            error=str(e)
        )


# ============================================================================
# TWITTER/X MENTIONS
# ============================================================================

@router.get("/comments/twitter", response_model=CommentsResponse)
async def get_twitter_mentions(request: Request, limit: int = 50):
    """
    Fetch recent Twitter/X mentions for user's connected account

    Requires scope: tweet.read
    Note: Twitter v2 API doesn't have direct comment threading, so we fetch mentions
    """
    user_id = str(get_user_id(request))
    logger.info(f"Fetching Twitter mentions for user {user_id}")

    # Get user's Twitter OAuth token
    credentials = get_user_oauth_token(user_id, "twitter")

    if not credentials:
        return CommentsResponse(
            success=False,
            platform="twitter",
            comments=[],
            total=0,
            error="Twitter account not connected. Please connect in settings."
        )

    access_token = credentials['access_token']
    metadata = credentials.get('metadata', {})
    twitter_user_id = metadata.get('user_id')

    if not twitter_user_id:
        return CommentsResponse(
            success=False,
            platform="twitter",
            comments=[],
            total=0,
            error="Twitter user ID not found. Please reconnect your account."
        )

    try:
        comments = []

        async with httpx.AsyncClient() as client:
            # Get mentions timeline for user
            response = await client.get(
                f"https://api.twitter.com/2/users/{twitter_user_id}/mentions",
                headers={
                    "Authorization": f"Bearer {access_token}"
                },
                params={
                    "max_results": min(limit, 100),  # Twitter API limit
                    "tweet.fields": "created_at,author_id,conversation_id,public_metrics",
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

                # Process mentions
                for tweet in data.get('data', []):
                    author = users.get(tweet['author_id'], {})
                    comments.append(Comment(
                        id=tweet['id'],
                        platform="twitter",
                        post_id=tweet.get('conversation_id', tweet['id']),
                        author=author.get('username', 'Unknown'),
                        author_id=tweet['author_id'],
                        text=tweet.get('text', ''),
                        timestamp=tweet.get('created_at', ''),
                        sentiment=analyze_sentiment(tweet.get('text', ''))
                    ))

                return CommentsResponse(
                    success=True,
                    platform="twitter",
                    comments=comments,
                    total=len(comments)
                )

            else:
                logger.error(f"Twitter API error: {response.status_code} - {response.text}")
                return CommentsResponse(
                    success=False,
                    platform="twitter",
                    comments=[],
                    total=0,
                    error=f"Twitter API error: {response.status_code}"
                )

    except httpx.TimeoutException:
        logger.error("Twitter API timeout")
        return CommentsResponse(
            success=False,
            platform="twitter",
            comments=[],
            total=0,
            error="Request timeout - Twitter API took too long to respond"
        )
    except Exception as e:
        logger.error(f"Error fetching Twitter mentions: {e}")
        return CommentsResponse(
            success=False,
            platform="twitter",
            comments=[],
            total=0,
            error=str(e)
        )


# ============================================================================
# ALL COMMENTS AGGREGATED
# ============================================================================

@router.get("/comments/all", response_model=List[Comment])
async def get_all_comments(request: Request, limit: int = 50):
    """
    Fetch recent comments from ALL connected platforms
    Returns aggregated list sorted by timestamp
    """
    user_id = str(get_user_id(request))
    logger.info(f"Fetching all comments for user {user_id}")

    all_comments = []

    # Fetch from Instagram
    instagram_result = await get_instagram_comments(request, limit=limit)
    if instagram_result.success:
        all_comments.extend(instagram_result.comments)

    # Fetch from Facebook
    facebook_result = await get_facebook_comments(request, limit=limit)
    if facebook_result.success:
        all_comments.extend(facebook_result.comments)

    # Fetch from Twitter
    twitter_result = await get_twitter_mentions(request, limit=limit)
    if twitter_result.success:
        all_comments.extend(twitter_result.comments)

    # Sort by timestamp (newest first)
    all_comments.sort(key=lambda x: x.timestamp, reverse=True)

    return all_comments[:limit]
