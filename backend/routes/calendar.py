from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)

CALENDAR_FILE = "calendar_data.json"

class ContentItem(BaseModel):
    id: str
    title: str
    content_type: str
    scheduled_date: str
    status: str
    platform: Optional[str] = None
    content: Optional[str] = None
    media_url: Optional[str] = None

def load_calendar():
    if os.path.exists(CALENDAR_FILE):
        with open(CALENDAR_FILE, 'r') as f:
            return json.load(f)
    return []

def save_calendar(data):
    with open(CALENDAR_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@router.get("/events")
def get_calendar_events():
    try:
        events = load_calendar()
        logger.info(f"Loaded {len(events)} calendar events")
        return {"events": events}
    except Exception as e:
        logger.error(f"Error loading calendar: {e}")
        return {"events": []}

@router.post("/events")
def create_event(item: ContentItem):
    try:
        events = load_calendar()
        events.append(item.dict())
        save_calendar(events)
        logger.info(f"Created event: {item.title}")
        return {"success": True, "event": item.dict()}
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        return {"success": False, "error": str(e)}

@router.put("/events/{event_id}")
def update_event(event_id: str, item: ContentItem):
    try:
        events = load_calendar()
        for i, event in enumerate(events):
            if event['id'] == event_id:
                events[i] = item.dict()
                save_calendar(events)
                logger.info(f"Updated event: {event_id}")
                return {"success": True, "event": item.dict()}
        return {"success": False, "error": "Event not found"}
    except Exception as e:
        logger.error(f"Error updating event: {e}")
        return {"success": False, "error": str(e)}

@router.delete("/events/{event_id}")
def delete_event(event_id: str):
    try:
        events = load_calendar()
        events = [e for e in events if e['id'] != event_id]
        save_calendar(events)
        logger.info(f"Deleted event: {event_id}")
        return {"success": True}
    except Exception as e:
        logger.error(f"Error deleting event: {e}")
        return {"success": False, "error": str(e)}
