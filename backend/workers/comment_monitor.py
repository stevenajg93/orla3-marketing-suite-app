"""
Background comment monitor worker
Polls social media comments and automatically replies based on user settings
Runs every 15 minutes via APScheduler
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import httpx
import asyncio
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional
import json

logger = logging.getLogger(__name__)


# ============================================================================
# SENTIMENT ANALYSIS (Simple keyword-based)
# ============================================================================

def analyze_sentiment(text: str) -> str:
    """
    Simple keyword-based sentiment analysis
    Returns: 'positive', 'negative', 'neutral', or 'question'
    """
    text_lower = text.lower()

    # Check for questions first
    question_indicators = ['?', 'how', 'what', 'when', 'where', 'why', 'who', 'can you', 'could you', 'would you']
    if any(indicator in text_lower for indicator in question_indicators):
        return 'question'

    # Positive keywords
    positive_keywords = ['love', 'great', 'awesome', 'amazing', 'excellent', 'fantastic', 'wonderful', 'perfect', 'thank', 'thanks', 'appreciate', 'good', 'nice', 'best', 'helpful', '😊', '❤️', '👍', '🎉']
    positive_count = sum(1 for keyword in positive_keywords if keyword in text_lower)

    # Negative keywords
    negative_keywords = ['bad', 'terrible', 'awful', 'hate', 'worst', 'horrible', 'poor', 'disappointing', 'disappointed', 'sucks', 'useless', 'waste', 'scam', '😡', '😠', '👎']
    negative_count = sum(1 for keyword in negative_keywords if keyword in text_lower)

    if negative_count > positive_count:
        return 'negative'
    elif positive_count > 0:
        return 'positive'
    else:
        return 'neutral'


# ============================================================================
# AI REPLY GENERATION
# ============================================================================

async def generate_ai_reply(comment_text: str, settings: Dict, context: Optional[str] = None) -> str:
    """
    Generate AI reply using OpenAI based on user settings

    Args:
        comment_text: The comment to reply to
        settings: User's auto-reply settings (tone, length, custom_instructions)
        context: Optional post context

    Returns:
        Generated reply text
    """
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not set")
        return "Thanks for your comment!"

    # Build prompt based on settings
    tone = settings.get('reply_tone', 'friendly')
    length = settings.get('reply_length', 'short')
    custom_instructions = settings.get('custom_instructions', '')

    length_guidelines = {
        'short': 'Keep it very brief (1-2 sentences max)',
        'medium': 'Keep it concise (2-3 sentences)',
        'long': 'Provide a detailed response (3-5 sentences)'
    }

    system_prompt = f"""You are a helpful social media manager replying to comments.
Tone: {tone}
Length: {length_guidelines.get(length, length_guidelines['short'])}

{custom_instructions if custom_instructions else ''}

Rules:
- Be authentic and engaging
- Match the tone of the original comment
- Do NOT use hashtags in replies
- Do NOT include emojis unless the original comment has them
- Keep it conversational and natural
"""

    user_prompt = f"Reply to this comment: \"{comment_text}\""
    if context:
        user_prompt += f"\n\nPost context: {context}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.8,
                    "max_tokens": 150
                }
            )

            if response.status_code == 200:
                data = response.json()
                reply = data['choices'][0]['message']['content'].strip()
                return reply
            else:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return "Thanks for your comment!"

    except Exception as e:
        logger.error(f"Error generating AI reply: {e}")
        return "Thanks for your comment!"


# ============================================================================
# COMMENT FETCHING
# ============================================================================

async def fetch_instagram_comments(access_token: str, since: datetime) -> List[Dict]:
    """Fetch recent Instagram comments"""
    comments = []
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get recent media
            media_response = await client.get(
                f"https://graph.facebook.com/v18.0/me/media",
                params={
                    "access_token": access_token,
                    "fields": "id,caption,timestamp",
                    "limit": 10  # Last 10 posts
                }
            )

            if media_response.status_code != 200:
                return comments

            media_data = media_response.json()

            for media in media_data.get('data', []):
                media_id = media['id']

                # Get comments for this media
                comments_response = await client.get(
                    f"https://graph.facebook.com/v18.0/{media_id}/comments",
                    params={
                        "access_token": access_token,
                        "fields": "id,username,text,timestamp",
                        "limit": 50
                    }
                )

                if comments_response.status_code == 200:
                    comment_data = comments_response.json()

                    for comment in comment_data.get('data', []):
                        comment_time = datetime.fromisoformat(comment['timestamp'].replace('Z', '+00:00'))

                        if comment_time > since:
                            comments.append({
                                'id': comment['id'],
                                'platform': 'instagram',
                                'post_id': media_id,
                                'author': comment.get('username', 'Unknown'),
                                'text': comment.get('text', ''),
                                'timestamp': comment['timestamp'],
                                'sentiment': analyze_sentiment(comment.get('text', ''))
                            })

    except Exception as e:
        logger.error(f"Error fetching Instagram comments: {e}")

    return comments


async def fetch_twitter_mentions(access_token: str, api_key: str, api_secret: str, access_token_secret: str, since: datetime) -> List[Dict]:
    """Fetch recent Twitter mentions"""
    # Note: Simplified version - production would use OAuth 1.0a properly
    # For now, return empty to focus on Instagram/Facebook
    return []


async def fetch_facebook_comments(page_access_token: str, page_id: str, since: datetime) -> List[Dict]:
    """Fetch recent Facebook Page comments"""
    comments = []
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get recent posts
            posts_response = await client.get(
                f"https://graph.facebook.com/v18.0/{page_id}/feed",
                params={
                    "access_token": page_access_token,
                    "fields": "id,message,created_time",
                    "limit": 10
                }
            )

            if posts_response.status_code != 200:
                return comments

            posts_data = posts_response.json()

            for post in posts_data.get('data', []):
                post_id = post['id']

                # Get comments for this post
                comments_response = await client.get(
                    f"https://graph.facebook.com/v18.0/{post_id}/comments",
                    params={
                        "access_token": page_access_token,
                        "fields": "id,from,message,created_time",
                        "limit": 50
                    }
                )

                if comments_response.status_code == 200:
                    comment_data = comments_response.json()

                    for comment in comment_data.get('data', []):
                        comment_time = datetime.fromisoformat(comment['created_time'].replace('Z', '+00:00'))

                        if comment_time > since:
                            comments.append({
                                'id': comment['id'],
                                'platform': 'facebook',
                                'post_id': post_id,
                                'author': comment.get('from', {}).get('name', 'Unknown'),
                                'author_id': comment.get('from', {}).get('id', ''),
                                'text': comment.get('message', ''),
                                'timestamp': comment['created_time'],
                                'sentiment': analyze_sentiment(comment.get('message', ''))
                            })

    except Exception as e:
        logger.error(f"Error fetching Facebook comments: {e}")

    return comments


# ============================================================================
# REPLY POSTING
# ============================================================================

async def post_instagram_reply(comment_id: str, reply_text: str, access_token: str) -> bool:
    """Post reply to Instagram comment"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"https://graph.facebook.com/v18.0/{comment_id}/replies",
                data={
                    "message": reply_text,
                    "access_token": access_token
                }
            )

            if response.status_code == 200:
                logger.info(f"Posted Instagram reply to comment {comment_id}")
                return True
            else:
                logger.error(f"Failed to post Instagram reply: {response.status_code} - {response.text}")
                return False

    except Exception as e:
        logger.error(f"Error posting Instagram reply: {e}")
        return False


async def post_facebook_reply(comment_id: str, reply_text: str, page_access_token: str) -> bool:
    """Post reply to Facebook comment"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"https://graph.facebook.com/v18.0/{comment_id}/comments",
                data={
                    "message": reply_text,
                    "access_token": page_access_token
                }
            )

            if response.status_code == 200:
                logger.info(f"Posted Facebook reply to comment {comment_id}")
                return True
            else:
                logger.error(f"Failed to post Facebook reply: {response.status_code} - {response.text}")
                return False

    except Exception as e:
        logger.error(f"Error posting Facebook reply: {e}")
        return False


# ============================================================================
# MAIN MONITOR FUNCTION
# ============================================================================

def monitor_and_reply_to_comments():
    """
    Main function called by APScheduler every 15 minutes
    Checks for new comments and auto-replies based on user settings
    """
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        logger.error("DATABASE_URL not set")
        return

    logger.info("🔍 Starting comment monitor check...")

    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cursor = conn.cursor()

        # Get all users with auto-reply enabled
        cursor.execute("""
            SELECT
                ars.id as settings_id,
                ars.user_id,
                ars.platforms,
                ars.reply_to_questions,
                ars.reply_to_mentions,
                ars.reply_to_all_comments,
                ars.reply_to_positive,
                ars.reply_to_neutral,
                ars.reply_to_negative,
                ars.reply_tone,
                ars.reply_length,
                ars.custom_instructions,
                ars.max_replies_per_hour,
                ars.min_reply_interval_minutes,
                ars.last_check_at
            FROM auto_reply_settings ars
            WHERE ars.enabled = true
        """)

        users_with_auto_reply = cursor.fetchall()
        logger.info(f"Found {len(users_with_auto_reply)} users with auto-reply enabled")

        for user_settings in users_with_auto_reply:
            asyncio.run(process_user_auto_replies(user_settings, cursor, conn))

        cursor.close()
        conn.close()

        logger.info("✅ Comment monitor check complete")

    except Exception as e:
        logger.error(f"Error in comment monitor: {e}")


async def process_user_auto_replies(user_settings: Dict, cursor, conn):
    """Process auto-replies for a single user"""
    user_id = user_settings['user_id']
    platforms = user_settings.get('platforms', [])

    # Parse platforms JSON if it's a string
    if isinstance(platforms, str):
        try:
            platforms = json.loads(platforms)
        except (json.JSONDecodeError, ValueError, TypeError):
            platforms = []

    logger.info(f"Processing auto-replies for user {user_id}, platforms: {platforms}")

    # Determine since when to check for comments
    last_check = user_settings.get('last_check_at')
    if last_check:
        since = last_check
    else:
        since = datetime.utcnow() - timedelta(minutes=user_settings['min_reply_interval_minutes'])

    all_comments = []

    # Fetch comments from each enabled platform
    for platform in platforms:
        # Get user's OAuth credentials for this platform
        cursor.execute("""
            SELECT access_token, service_metadata
            FROM connected_services
            WHERE user_id = %s AND service_type = %s AND is_active = true
            LIMIT 1
        """, (user_id, platform))

        credentials = cursor.fetchone()

        if not credentials:
            logger.warning(f"No credentials for {platform} for user {user_id}")
            continue

        access_token = credentials['access_token']
        metadata = credentials.get('service_metadata', {})
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except (json.JSONDecodeError, ValueError, TypeError):
                metadata = {}

        # Fetch comments based on platform
        if platform == 'instagram':
            comments = await fetch_instagram_comments(access_token, since)
            all_comments.extend(comments)

        elif platform == 'facebook':
            page_access_token = metadata.get('page_access_token')
            page_id = metadata.get('selected_page_id')
            if page_access_token and page_id:
                comments = await fetch_facebook_comments(page_access_token, page_id, since)
                all_comments.extend(comments)

        # Note: Twitter/other platforms can be added here

    logger.info(f"Found {len(all_comments)} new comments for user {user_id}")

    # Filter comments based on user settings and generate replies
    replies_sent = 0

    for comment in all_comments:
        sentiment = comment['sentiment']

        # Check if we should reply based on sentiment filters
        should_reply = False

        if sentiment == 'question' and user_settings['reply_to_questions']:
            should_reply = True
        elif sentiment == 'positive' and user_settings['reply_to_positive']:
            should_reply = True
        elif sentiment == 'neutral' and user_settings['reply_to_neutral']:
            should_reply = True
        elif sentiment == 'negative' and user_settings['reply_to_negative']:
            should_reply = True

        if user_settings['reply_to_all_comments']:
            should_reply = True

        if not should_reply:
            continue

        # Check rate limit
        if replies_sent >= user_settings['max_replies_per_hour']:
            logger.info(f"Rate limit reached for user {user_id}")
            break

        # Generate AI reply
        reply_text = await generate_ai_reply(
            comment['text'],
            {
                'reply_tone': user_settings['reply_tone'],
                'reply_length': user_settings['reply_length'],
                'custom_instructions': user_settings['custom_instructions']
            }
        )

        # Post reply
        success = False
        if comment['platform'] == 'instagram':
            cursor.execute("""
                SELECT access_token
                FROM connected_services
                WHERE user_id = %s AND service_type = 'instagram' AND is_active = true
                LIMIT 1
            """, (user_id,))
            creds = cursor.fetchone()
            if creds:
                success = await post_instagram_reply(comment['id'], reply_text, creds['access_token'])

        elif comment['platform'] == 'facebook':
            cursor.execute("""
                SELECT service_metadata
                FROM connected_services
                WHERE user_id = %s AND service_type = 'facebook' AND is_active = true
                LIMIT 1
            """, (user_id,))
            creds = cursor.fetchone()
            if creds:
                metadata = json.loads(creds['service_metadata']) if isinstance(creds['service_metadata'], str) else creds['service_metadata']
                page_token = metadata.get('page_access_token')
                if page_token:
                    success = await post_facebook_reply(comment['id'], reply_text, page_token)

        if success:
            replies_sent += 1
            logger.info(f"✅ Auto-replied to {comment['platform']} comment by {comment['author']}")

    # Update last_check_at
    cursor.execute("""
        UPDATE auto_reply_settings
        SET last_check_at = NOW()
        WHERE user_id = %s
    """, (user_id,))
    conn.commit()

    logger.info(f"Sent {replies_sent} auto-replies for user {user_id}")
