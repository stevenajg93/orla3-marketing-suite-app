from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
import sys
import httpx
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import setup_logger
from db_pool import get_db_connection  # Use connection pool
from middleware import get_user_id

router = APIRouter()
logger = setup_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

# Import PublishRequest for publishing
from routes.publisher import PublishRequest

class ContentItem(BaseModel):
    id: Optional[str] = None
    title: str
    content_type: str
    scheduled_date: str
    status: str
    platform: Optional[str] = None
    content: Optional[str] = None
    media_url: Optional[str] = None


@router.get("/events")
def get_calendar_events(request: Request):
    """Get all calendar events for the authenticated user"""
    try:
        user_id = get_user_id(request)
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM content_calendar WHERE user_id = %s ORDER BY scheduled_date ASC",
            (str(user_id),)
        )

        events = cur.fetchall()
        cur.close()

        logger.info(f"Loaded {len(events)} calendar events for user {user_id}")
        return {"events": events}
    except Exception as e:
        logger.error(f"Error loading calendar: {e}")
        return {"events": []}

@router.post("/events")
def create_event(item: ContentItem, request: Request):
    """Create a new calendar event for the authenticated user"""
    try:
        user_id = get_user_id(request)
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO content_calendar (
                user_id, title, content_type, scheduled_date, status,
                platform, content, media_url, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, user_id, title, content_type, scheduled_date, status,
                      platform, content, media_url, created_at
        """, (
            str(user_id),
            item.title,
            item.content_type,
            item.scheduled_date,
            item.status,
            item.platform,
            item.content,
            item.media_url,
            datetime.now()
        ))

        event = cur.fetchone()
        conn.commit()
        cur.close()

        logger.info(f"Created event for user {user_id}: {item.title}")
        return {"success": True, "event": event}
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        return {"success": False, "error": str(e)}

@router.put("/events/{event_id}")
def update_event(event_id: str, item: ContentItem, request: Request):
    """Update a calendar event (user can only update their own events)"""
    try:
        user_id = get_user_id(request)
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            UPDATE content_calendar
            SET title = %s, content_type = %s, scheduled_date = %s, status = %s,
                platform = %s, content = %s, media_url = %s
            WHERE id = %s AND user_id = %s
            RETURNING id, user_id, title, content_type, scheduled_date, status,
                      platform, content, media_url, created_at
        """, (
            item.title,
            item.content_type,
            item.scheduled_date,
            item.status,
            item.platform,
            item.content,
            item.media_url,
            event_id,
            str(user_id)
        ))

        event = cur.fetchone()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found or not owned by user")

        conn.commit()
        cur.close()

        logger.info(f"Updated event for user {user_id}: {event_id}")
        return {"success": True, "event": event}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating event: {e}")
        return {"success": False, "error": str(e)}

@router.delete("/events/{event_id}")
def delete_event(event_id: str, request: Request):
    """Delete a calendar event (user can only delete their own events)"""
    try:
        user_id = get_user_id(request)
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "DELETE FROM content_calendar WHERE id = %s AND user_id = %s RETURNING id",
            (event_id, str(user_id))
        )

        deleted_event = cur.fetchone()
        if not deleted_event:
            raise HTTPException(status_code=404, detail="Event not found or not owned by user")

        conn.commit()
        cur.close()

        logger.info(f"Deleted event for user {user_id}: {event_id}")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting event: {e}")
        return {"success": False, "error": str(e)}


@router.post("/events/{event_id}/publish")
async def publish_event_now(event_id: str, request: Request):
    """
    Publish a scheduled calendar event immediately
    Updates event status to 'published' or 'failed' after attempt
    """
    try:
        user_id = get_user_id(request)
        conn = get_db_connection()
        cur = conn.cursor()

        # Get event details
        cur.execute("""
            SELECT id, title, content_type, platform, content, media_url, notes
            FROM content_calendar
            WHERE id = %s AND user_id = %s
        """, (event_id, str(user_id)))

        event = cur.fetchone()

        if not event:
            cur.close()
            raise HTTPException(status_code=404, detail="Event not found or not owned by user")

        # Extract event data
        platform = event['platform']
        content = event['content'] or ""
        media_url = event['media_url']

        # Parse notes for additional data (like subreddit, video_url)
        import json
        notes_data = {}
        if event.get('notes'):
            try:
                notes_data = json.loads(event['notes']) if isinstance(event['notes'], str) else event['notes']
            except (json.JSONDecodeError, ValueError, TypeError):
                pass

        # Call the publisher endpoint
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Get authorization header from request
            auth_header = request.headers.get('authorization')

            publish_payload = {
                "platform": platform,
                "content_type": event['content_type'],
                "caption": content,
                "image_urls": [media_url] if media_url and media_url.startswith('http') else [],
                "video_url": notes_data.get('video_url'),
                "subreddit": notes_data.get('subreddit'),
                "title": event['title'],
                "link_url": notes_data.get('link_url')
            }

            # Call internal publisher endpoint
            backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
            response = await client.post(
                f"{backend_url}/publisher/publish",
                json=publish_payload,
                headers={"Authorization": auth_header} if auth_header else {}
            )

            result = response.json()

            # Update event status based on result
            new_status = "published" if result.get("success") else "failed"

            cur.execute("""
                UPDATE content_calendar
                SET status = %s, published_at = %s
                WHERE id = %s AND user_id = %s
            """, (new_status, datetime.utcnow(), event_id, str(user_id)))

            conn.commit()
            cur.close()

            logger.info(f"Published event {event_id} for user {user_id}: {result.get('success')}")

            return {
                "success": result.get("success"),
                "message": result.get("message") or ("Published successfully" if result.get("success") else result.get("error")),
                "post_url": result.get("post_url"),
                "event_id": event_id,
                "status": new_status
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publishing event {event_id}: {e}")
        return {"success": False, "error": str(e)}


@router.post("/publish-all-due")
async def publish_all_due_events(request: Request):
    """
    Publish all events that are scheduled for now or earlier
    Returns summary of published, failed, and total events
    """
    try:
        user_id = get_user_id(request)
        conn = get_db_connection()
        cur = conn.cursor()

        # Get all due events
        cur.execute("""
            SELECT id, title, content_type, platform, content, media_url, notes, scheduled_date
            FROM content_calendar
            WHERE user_id = %s
            AND status = 'scheduled'
            AND scheduled_date <= NOW()
            ORDER BY scheduled_date ASC
        """, (str(user_id),))

        due_events = cur.fetchall()
        cur.close()

        logger.info(f"Found {len(due_events)} due events for user {user_id}")

        results = {
            "total": len(due_events),
            "published": 0,
            "failed": 0,
            "results": []
        }

        # Publish each event
        for event in due_events:
            try:
                publish_result = await publish_event_now(event['id'], request)

                if publish_result.get("success"):
                    results["published"] += 1
                else:
                    results["failed"] += 1

                results["results"].append({
                    "event_id": event['id'],
                    "title": event['title'],
                    "platform": event['platform'],
                    "success": publish_result.get("success"),
                    "message": publish_result.get("message"),
                    "post_url": publish_result.get("post_url")
                })

            except Exception as e:
                logger.error(f"Error publishing event {event['id']}: {e}")
                results["failed"] += 1
                results["results"].append({
                    "event_id": event['id'],
                    "title": event['title'],
                    "platform": event['platform'],
                    "success": False,
                    "error": str(e)
                })

        logger.info(f"Bulk publish complete: {results['published']} published, {results['failed']} failed")

        return {
            "success": True,
            "summary": results
        }

    except Exception as e:
        logger.error(f"Error in bulk publish: {e}")
        return {"success": False, "error": str(e)}
