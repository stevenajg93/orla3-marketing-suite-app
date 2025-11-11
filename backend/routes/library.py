from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
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
    content: str
    created_at: Optional[str] = None
    status: str
    platform: Optional[str] = None
    tags: Optional[List[str]] = []
    media_url: Optional[str] = None

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

@router.get("/content")
def get_library_content(request: Request):
    try:
        user_id = get_user_id(request)
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM content_library WHERE user_id = %s ORDER BY created_at DESC",
            (str(user_id),)
        )
        items = cur.fetchall()
        cur.close()
        conn.close()
        logger.info(f"Loaded {len(items)} library items for user {user_id}")
        return {"items": items}
    except Exception as e:
        logger.error(f"Error loading library: {e}")
        return {"items": []}

@router.post("/content")
def save_content(item: ContentItem, request: Request):
    try:
        user_id = get_user_id(request)
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO content_library (user_id, title, content_type, content, status, platform, tags, media_url, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, user_id, title, content_type, content, status, platform, tags, media_url, created_at
        """, (
            str(user_id),
            item.title,
            item.content_type,
            item.content,
            item.status,
            item.platform,
            item.tags or [],
            item.media_url,
            datetime.now()
        ))

        saved_item = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"Saved content to PostgreSQL for user {user_id}: {item.title}")
        return {"success": True, "item": saved_item}
    except Exception as e:
        logger.error(f"Error saving content: {e}")
        return {"success": False, "error": str(e)}

@router.patch("/content/{item_id}")
def update_content(item_id: str, item: ContentItem, request: Request):
    try:
        user_id = get_user_id(request)
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            UPDATE content_library
            SET title = %s, content_type = %s, content = %s, status = %s,
                platform = %s, tags = %s, media_url = %s
            WHERE id = %s AND user_id = %s
            RETURNING id, user_id, title, content_type, content, status, platform, tags, media_url, created_at
        """, (
            item.title,
            item.content_type,
            item.content,
            item.status,
            item.platform,
            item.tags or [],
            item.media_url,
            item_id,
            str(user_id)
        ))

        updated_item = cur.fetchone()
        if not updated_item:
            conn.close()
            raise HTTPException(status_code=404, detail="Content not found or not owned by user")

        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"Updated content in PostgreSQL for user {user_id}: {item_id}")
        return {"success": True, "item": updated_item}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating content: {e}")
        return {"success": False, "error": str(e)}

@router.delete("/content/{item_id}")
def delete_content(item_id: str, request: Request):
    try:
        user_id = get_user_id(request)
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "DELETE FROM content_library WHERE id = %s AND user_id = %s RETURNING id",
            (item_id, str(user_id))
        )

        deleted_item = cur.fetchone()
        if not deleted_item:
            conn.close()
            raise HTTPException(status_code=404, detail="Content not found or not owned by user")

        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"Deleted content from PostgreSQL for user {user_id}: {item_id}")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting content: {e}")
        return {"success": False, "error": str(e)}
