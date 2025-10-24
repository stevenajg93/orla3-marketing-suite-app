from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
import json
import os
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)

LIBRARY_FILE = "content_library.json"

class ContentItem(BaseModel):
    id: str
    title: str
    content_type: str
    content: str
    created_at: str
    status: str
    platform: Optional[str] = None
    tags: Optional[List[str]] = []
    media_url: Optional[str] = None

def load_library():
    if os.path.exists(LIBRARY_FILE):
        with open(LIBRARY_FILE, 'r') as f:
            return json.load(f)
    return []

def save_library(data):
    with open(LIBRARY_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@router.get("/content")
def get_library_content():
    try:
        items = load_library()
        logger.info(f"Loaded {len(items)} library items")
        return {"items": items}
    except Exception as e:
        logger.error(f"Error loading library: {e}")
        return {"items": []}

@router.post("/content")
def save_content(item: ContentItem):
    try:
        items = load_library()
        items.append(item.dict())
        save_library(items)
        logger.info(f"Saved content: {item.title}")
        return {"success": True, "item": item.dict()}
    except Exception as e:
        logger.error(f"Error saving content: {e}")
        return {"success": False, "error": str(e)}

@router.delete("/content/{item_id}")
def delete_content(item_id: str):
    try:
        items = load_library()
        items = [i for i in items if i['id'] != item_id]
        save_library(items)
        logger.info(f"Deleted content: {item_id}")
        return {"success": True}
    except Exception as e:
        logger.error(f"Error deleting content: {e}")
        return {"success": False, "error": str(e)}
