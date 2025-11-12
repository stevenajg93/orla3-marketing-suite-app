from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import setup_logger
from middleware import get_user_id

router = APIRouter()
logger = setup_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

class ContentItem(BaseModel):
    id: Optional[str] = None
    title: str
    content_type: str
    scheduled_date: str
    status: str
    platform: Optional[str] = None
    content: Optional[str] = None
    media_url: Optional[str] = None

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

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
        conn.close()

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
        conn.close()

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
            conn.close()
            raise HTTPException(status_code=404, detail="Event not found or not owned by user")

        conn.commit()
        cur.close()
        conn.close()

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
            conn.close()
            raise HTTPException(status_code=404, detail="Event not found or not owned by user")

        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"Deleted event for user {user_id}: {event_id}")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting event: {e}")
        return {"success": False, "error": str(e)}
