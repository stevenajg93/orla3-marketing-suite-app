from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:pcrmiSUNKiEyfEAIWKmfgfehGpKZzHmZ@switchyard.proxy.rlwy.net:34978/railway")

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
def get_library_content():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM content_library ORDER BY created_at DESC")
        items = cur.fetchall()
        cur.close()
        conn.close()
        logger.info(f"Loaded {len(items)} library items from PostgreSQL")
        return {"items": items}
    except Exception as e:
        logger.error(f"Error loading library: {e}")
        return {"items": []}

@router.post("/content")
def save_content(item: ContentItem):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO content_library (title, content_type, content, status, platform, tags, media_url, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, title, content_type, content, status, platform, tags, media_url, created_at
        """, (
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
        
        logger.info(f"Saved content to PostgreSQL: {item.title}")
        return {"success": True, "item": saved_item}
    except Exception as e:
        logger.error(f"Error saving content: {e}")
        return {"success": False, "error": str(e)}

@router.delete("/content/{item_id}")
def delete_content(item_id: str):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM content_library WHERE id = %s", (item_id,))
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"Deleted content from PostgreSQL: {item_id}")
        return {"success": True}
    except Exception as e:
        logger.error(f"Error deleting content: {e}")
        return {"success": False, "error": str(e)}
