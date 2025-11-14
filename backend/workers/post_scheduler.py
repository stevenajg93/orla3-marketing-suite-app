"""
Scheduled post worker - checks for due posts and publishes them
"""
import psycopg2
from datetime import datetime, timezone
import logging
import json
import os

logger = logging.getLogger(__name__)


def check_scheduled_posts():
    """
    Check for scheduled posts that are due and publish them
    Runs every minute via APScheduler
    """
    try:
        logger.info("🔍 Checking for scheduled posts...")

        # Connect to database
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            logger.error("❌ DATABASE_URL not set")
            return

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # Find scheduled posts that are due (scheduled_date <= now AND status='scheduled')
        cursor.execute("""
            SELECT
                id,
                user_id,
                content_id,
                title,
                content_type,
                platform,
                scheduled_date,
                notes
            FROM content_calendar
            WHERE status = 'scheduled'
            AND scheduled_date <= NOW()
            ORDER BY scheduled_date ASC
            LIMIT 50
        """)

        due_posts = cursor.fetchall()

        if not due_posts:
            logger.info("✅ No scheduled posts due")
            cursor.close()
            conn.close()
            return

        logger.info(f"📬 Found {len(due_posts)} scheduled post(s) to publish")

        # Process each scheduled post
        for post in due_posts:
            post_id, user_id, content_id, title, content_type, platform, scheduled_date, notes = post

            try:
                logger.info(f"🚀 Publishing: {title} to {platform}")

                # Get post content from content_library (if content_id provided)
                if content_id:
                    cursor.execute("""
                        SELECT content
                        FROM content_library
                        WHERE id = %s AND user_id = %s
                    """, (content_id, user_id))

                    content_row = cursor.fetchone()
                    if content_row:
                        content_json = content_row[0]
                        post_content = content_json.get('text', '') if isinstance(content_json, dict) else notes
                    else:
                        post_content = notes  # Fallback to notes if content not found
                else:
                    # No content_id, use notes as content
                    post_content = notes if notes else title

                # Get user's OAuth token for the platform
                cursor.execute("""
                    SELECT access_token, service_metadata
                    FROM connected_services
                    WHERE user_id = %s
                    AND service_type = %s
                    AND is_active = true
                """, (user_id, platform))

                token_row = cursor.fetchone()

                if not token_row:
                    logger.error(f"❌ No OAuth token found for user {user_id} on {platform}")
                    # Mark as failed
                    cursor.execute("""
                        UPDATE content_calendar
                        SET status = 'failed', notes = 'No OAuth token found'
                        WHERE id = %s
                    """, (post_id,))
                    conn.commit()
                    continue

                access_token, service_metadata = token_row

                # Publish the post via publisher
                publish_result = publish_post(
                    user_id=user_id,
                    platform=platform,
                    content=post_content,
                    access_token=access_token,
                    service_metadata=service_metadata
                )

                if publish_result['success']:
                    # Mark as published
                    cursor.execute("""
                        UPDATE content_calendar
                        SET status = 'published', updated_at = NOW()
                        WHERE id = %s
                    """, (post_id,))
                    conn.commit()
                    logger.info(f"✅ Published: {title} to {platform}")
                else:
                    # Mark as failed
                    error_msg = publish_result.get('error', 'Unknown error')
                    cursor.execute("""
                        UPDATE content_calendar
                        SET status = 'failed', notes = %s
                        WHERE id = %s
                    """, (f"Failed: {error_msg}", post_id))
                    conn.commit()
                    logger.error(f"❌ Failed to publish {title}: {error_msg}")

            except Exception as post_error:
                logger.error(f"❌ Error publishing post {post_id}: {post_error}")
                # Mark as failed
                try:
                    cursor.execute("""
                        UPDATE content_calendar
                        SET status = 'failed', notes = %s
                        WHERE id = %s
                    """, (f"Error: {str(post_error)}", post_id))
                    conn.commit()
                except Exception as update_error:
                    logger.error(f"❌ Failed to update status: {update_error}")

        cursor.close()
        conn.close()
        logger.info("✅ Scheduled post check complete")

    except Exception as e:
        logger.error(f"❌ Error in scheduled post checker: {e}")


def publish_post(user_id: str, platform: str, content: str, access_token: str, service_metadata: dict) -> dict:
    """
    Publish a post to the specified platform

    Args:
        user_id: User ID
        platform: Platform name
        content: Post content (text)
        access_token: OAuth access token
        service_metadata: Platform-specific metadata (e.g., Facebook page_id)

    Returns:
        dict: {'success': bool, 'error': str (if failed)}
    """
    try:
        # Import publisher classes
        from routes.publisher import (
            InstagramPublisher,
            LinkedInPublisher,
            TwitterPublisher,
            FacebookPublisher,
            TikTokPublisher,
            YouTubePublisher,
            RedditPublisher,
            TumblrPublisher,
            WordPressPublisher
        )

        # Map platform to publisher class
        publishers = {
            'instagram': InstagramPublisher,
            'linkedin': LinkedInPublisher,
            'twitter': TwitterPublisher,
            'x': TwitterPublisher,
            'facebook': FacebookPublisher,
            'tiktok': TikTokPublisher,
            'youtube': YouTubePublisher,
            'reddit': RedditPublisher,
            'tumblr': TumblrPublisher,
            'wordpress': WordPressPublisher
        }

        publisher_class = publishers.get(platform.lower())

        if not publisher_class:
            return {'success': False, 'error': f'Unknown platform: {platform}'}

        # Create publisher instance
        publisher = publisher_class(access_token)

        # Prepare post data
        post_data = {
            'text': content,
            'imageUrls': [],  # Scheduled posts are text-only for now (Phase 5 will add media)
        }

        # Add platform-specific data
        if platform.lower() == 'facebook' and service_metadata:
            post_data['page_id'] = service_metadata.get('selected_page_id')

        if platform.lower() == 'reddit':
            post_data['subreddit'] = service_metadata.get('subreddit', 'test')

        # Publish
        result = publisher.publish(post_data)

        return {'success': True, 'result': result}

    except Exception as e:
        logger.error(f"❌ Publish error: {e}")
        return {'success': False, 'error': str(e)}
