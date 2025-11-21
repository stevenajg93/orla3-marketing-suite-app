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
from db_pool import get_db_connection  # Use connection pool
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


@router.get("/content")
def get_library_content(request: Request, limit: int = 100, offset: int = 0):
    """
    Get library content with pagination

    Args:
        limit: Maximum number of items to return (default 100, max 500)
        offset: Number of items to skip (default 0)

    Returns paginated library items WITHOUT the large 'content' field for performance
    """
    try:
        # Validate and cap limit
        limit = min(limit, 500)

        user_id = get_user_id(request)
        # Convert UUID to string for PostgreSQL compatibility
        user_id_str = str(user_id)
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                # Get total count
                cur.execute(
                    "SELECT COUNT(*) as total FROM content_library WHERE user_id = %s",
                    (user_id_str,)
                )
                total = cur.fetchone()['total']

                # Get paginated items WITHOUT the large 'content' field to reduce response size
                cur.execute(
                    """SELECT id, user_id, title, content_type, status, platform, tags,
                              media_url, created_at
                       FROM content_library
                       WHERE user_id = %s
                       ORDER BY created_at DESC
                       LIMIT %s OFFSET %s""",
                    (user_id_str, limit, offset)
                )
                items = cur.fetchall()

                logger.info(f"Loaded {len(items)}/{total} library items for user {user_id} (limit={limit}, offset={offset})")
                return {
                    "items": items,
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                    "has_more": (offset + len(items)) < total
                }
            finally:
                cur.close()
    except Exception as e:
        logger.error(f"Error loading library: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to load content: {str(e)}")

@router.get("/content/{item_id}")
def get_single_content(item_id: str, request: Request):
    """
    Get a single content item by ID.

    Unlike the list endpoint, this returns the FULL content including the 'content' field.
    Returns HTTP 200 on success, HTTP 404 if not found, HTTP 500 on database errors.
    """
    user_id = get_user_id(request)
    # Convert UUID to string for PostgreSQL compatibility
    user_id_str = str(user_id)

    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                # Query for specific item with user_id filter for data isolation
                cur.execute("""
                    SELECT id, user_id, title, content_type, content, status, platform, tags, media_url, created_at
                    FROM content_library
                    WHERE id = %s AND user_id = %s
                """, (item_id, user_id_str))

                item = cur.fetchone()

                if not item:
                    logger.warning(f"Content not found or not owned by user {user_id}: {item_id}")
                    raise HTTPException(status_code=404, detail="Content not found or not owned by user")

                logger.info(f"Retrieved content for user {user_id}: {item_id}")
                return item
            finally:
                cur.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving content: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve content: {str(e)}")

@router.post("/content")
def save_content(item: ContentItem, request: Request):
    """
    Create a new content item in the library.

    Returns HTTP 201 on success, HTTP 500 on database errors.
    """
    user_id = get_user_id(request)
    # Convert UUID to string for PostgreSQL compatibility
    user_id_str = str(user_id)

    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("""
                    INSERT INTO content_library (user_id, title, content_type, content, status, platform, tags, media_url, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, user_id, title, content_type, content, status, platform, tags, media_url, created_at
                """, (
                    user_id_str,
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

                logger.info(f"Saved content to PostgreSQL for user {user_id}: {item.title}")
                return {"success": True, "item": saved_item}
            finally:
                cur.close()
    except Exception as e:
        logger.error(f"Error saving content: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save content: {str(e)}")

@router.patch("/content/{item_id}")
def update_content(item_id: str, item: ContentItem, request: Request):
    """
    Update an existing content item.

    Returns HTTP 200 on success, HTTP 404 if not found, HTTP 500 on database errors.
    """
    user_id = get_user_id(request)
    # Convert UUID to string for PostgreSQL compatibility
    user_id_str = str(user_id)

    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
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
                    user_id_str
                ))

                updated_item = cur.fetchone()
                conn.commit()

                if not updated_item:
                    logger.warning(f"Content not found or not owned by user {user_id}: {item_id}")
                    raise HTTPException(status_code=404, detail="Content not found or not owned by user")

                logger.info(f"Updated content in PostgreSQL for user {user_id}: {item_id}")
                return {"success": True, "item": updated_item}
            finally:
                cur.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating content: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update content: {str(e)}")

@router.delete("/content/{item_id}")
def delete_content(item_id: str, request: Request):
    """
    Delete a content item from the library.

    Returns HTTP 200 on success, HTTP 404 if not found, HTTP 500 on database errors.
    """
    user_id = get_user_id(request)
    # Convert UUID to string for PostgreSQL compatibility
    user_id_str = str(user_id)

    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    "DELETE FROM content_library WHERE id = %s AND user_id = %s RETURNING id",
                    (item_id, user_id_str)
                )

                deleted_item = cur.fetchone()
                conn.commit()

                if not deleted_item:
                    logger.warning(f"Content not found or not owned by user {user_id}: {item_id}")
                    raise HTTPException(status_code=404, detail="Content not found or not owned by user")

                logger.info(f"Deleted content from PostgreSQL for user {user_id}: {item_id}")
                return {"success": True}
            finally:
                cur.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting content: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete content: {str(e)}")
