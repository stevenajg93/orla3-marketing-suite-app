"""
Auto-reply settings endpoints
Manage user preferences for automated comment replies
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
import psycopg2
from psycopg2.extras import RealDictCursor
import os
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


# ============================================================================
# MODELS
# ============================================================================

class AutoReplySettings(BaseModel):
    enabled: bool = False
    platforms: List[str] = []  # ["instagram", "facebook", "twitter"]

    # Reply behavior
    reply_to_questions: bool = True
    reply_to_mentions: bool = True
    reply_to_all_comments: bool = False

    # Sentiment filters
    reply_to_positive: bool = True
    reply_to_neutral: bool = True
    reply_to_negative: bool = False

    # AI configuration
    reply_tone: str = "friendly"  # friendly, professional, casual, enthusiastic
    reply_length: str = "short"  # short, medium, long
    custom_instructions: Optional[str] = None

    # Rate limiting
    max_replies_per_hour: int = 10
    min_reply_interval_minutes: int = 15


class AutoReplySettingsResponse(AutoReplySettings):
    id: str
    user_id: str
    last_check_at: Optional[str] = None
    created_at: str
    updated_at: str


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


@router.get("/settings", response_model=AutoReplySettingsResponse)
async def get_auto_reply_settings(request: Request):
    """
    Get current auto-reply settings for authenticated user
    Creates default settings if none exist
    """
    try:
        user_id = str(get_user_id(request))
        conn = get_db_connection()
        cur = conn.cursor()

        # Try to get existing settings
        cur.execute("""
            SELECT
                id, user_id, enabled, platforms,
                reply_to_questions, reply_to_mentions, reply_to_all_comments,
                reply_to_positive, reply_to_neutral, reply_to_negative,
                reply_tone, reply_length, custom_instructions,
                max_replies_per_hour, min_reply_interval_minutes,
                last_check_at, created_at, updated_at
            FROM auto_reply_settings
            WHERE user_id = %s
        """, (user_id,))

        settings = cur.fetchone()

        # Create default settings if none exist
        if not settings:
            cur.execute("""
                INSERT INTO auto_reply_settings (user_id, enabled, platforms)
                VALUES (%s, false, '[]'::jsonb)
                RETURNING
                    id, user_id, enabled, platforms,
                    reply_to_questions, reply_to_mentions, reply_to_all_comments,
                    reply_to_positive, reply_to_neutral, reply_to_negative,
                    reply_tone, reply_length, custom_instructions,
                    max_replies_per_hour, min_reply_interval_minutes,
                    last_check_at, created_at, updated_at
            """, (user_id,))

            settings = cur.fetchone()
            conn.commit()

        cur.close()

        return dict(settings)

    except Exception as e:
        logger.error(f"Error fetching auto-reply settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings")
async def update_auto_reply_settings(settings: AutoReplySettings, request: Request):
    """
    Update auto-reply settings for authenticated user
    Creates settings if none exist
    """
    try:
        user_id = str(get_user_id(request))
        conn = get_db_connection()
        cur = conn.cursor()

        # Upsert settings
        cur.execute("""
            INSERT INTO auto_reply_settings (
                user_id, enabled, platforms,
                reply_to_questions, reply_to_mentions, reply_to_all_comments,
                reply_to_positive, reply_to_neutral, reply_to_negative,
                reply_tone, reply_length, custom_instructions,
                max_replies_per_hour, min_reply_interval_minutes,
                updated_at
            )
            VALUES (
                %s, %s, %s::jsonb,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s,
                NOW()
            )
            ON CONFLICT (user_id)
            DO UPDATE SET
                enabled = EXCLUDED.enabled,
                platforms = EXCLUDED.platforms,
                reply_to_questions = EXCLUDED.reply_to_questions,
                reply_to_mentions = EXCLUDED.reply_to_mentions,
                reply_to_all_comments = EXCLUDED.reply_to_all_comments,
                reply_to_positive = EXCLUDED.reply_to_positive,
                reply_to_neutral = EXCLUDED.reply_to_neutral,
                reply_to_negative = EXCLUDED.reply_to_negative,
                reply_tone = EXCLUDED.reply_tone,
                reply_length = EXCLUDED.reply_length,
                custom_instructions = EXCLUDED.custom_instructions,
                max_replies_per_hour = EXCLUDED.max_replies_per_hour,
                min_reply_interval_minutes = EXCLUDED.min_reply_interval_minutes,
                updated_at = NOW()
            RETURNING
                id, user_id, enabled, platforms,
                reply_to_questions, reply_to_mentions, reply_to_all_comments,
                reply_to_positive, reply_to_neutral, reply_to_negative,
                reply_tone, reply_length, custom_instructions,
                max_replies_per_hour, min_reply_interval_minutes,
                last_check_at, created_at, updated_at
        """, (
            user_id,
            settings.enabled,
            str(settings.platforms),  # Convert list to JSON string
            settings.reply_to_questions,
            settings.reply_to_mentions,
            settings.reply_to_all_comments,
            settings.reply_to_positive,
            settings.reply_to_neutral,
            settings.reply_to_negative,
            settings.reply_tone,
            settings.reply_length,
            settings.custom_instructions,
            settings.max_replies_per_hour,
            settings.min_reply_interval_minutes
        ))

        updated_settings = cur.fetchone()
        conn.commit()
        cur.close()

        logger.info(f"Updated auto-reply settings for user {user_id}")

        return {
            "success": True,
            "message": "Auto-reply settings updated",
            "settings": dict(updated_settings)
        }

    except Exception as e:
        logger.error(f"Error updating auto-reply settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings/toggle")
async def toggle_auto_reply(request: Request):
    """
    Quick toggle auto-reply on/off
    """
    try:
        user_id = str(get_user_id(request))
        conn = get_db_connection()
        cur = conn.cursor()

        # Toggle enabled status
        cur.execute("""
            UPDATE auto_reply_settings
            SET enabled = NOT enabled, updated_at = NOW()
            WHERE user_id = %s
            RETURNING enabled
        """, (user_id,))

        result = cur.fetchone()

        if not result:
            # Create default settings with enabled = true
            cur.execute("""
                INSERT INTO auto_reply_settings (user_id, enabled)
                VALUES (%s, true)
                RETURNING enabled
            """, (user_id,))
            result = cur.fetchone()

        conn.commit()
        cur.close()

        enabled = result['enabled']
        logger.info(f"Toggled auto-reply for user {user_id}: {enabled}")

        return {
            "success": True,
            "enabled": enabled,
            "message": f"Auto-reply {'enabled' if enabled else 'disabled'}"
        }

    except Exception as e:
        logger.error(f"Error toggling auto-reply: {e}")
        raise HTTPException(status_code=500, detail=str(e))
