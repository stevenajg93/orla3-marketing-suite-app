"""
Draft Campaign Routes
Handles temporary draft campaigns for cross-feature workflows (e.g., Blog → Social)
"""

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime, timedelta
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import setup_logger
from db_pool import get_db_connection  # Use connection pool
from middleware import get_user_id
import uuid

router = APIRouter()
logger = setup_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")


class DraftCampaign(BaseModel):
    """
    Temporary draft campaign for cross-feature workflows.

    Used when one feature wants to pass data to another feature
    (e.g., Blog Writer passing blog content to Social Manager)
    """
    campaign_type: str  # 'blog_to_social', 'carousel_to_social', etc.
    data: Dict[str, Any]  # Flexible JSON data
    expires_hours: Optional[int] = 24  # Auto-cleanup after 24 hours



def create_draft_campaigns_table():
    """Create draft_campaigns table if it doesn't exist (migration-safe)"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS draft_campaigns (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL,
                campaign_type VARCHAR(100) NOT NULL,
                data JSONB NOT NULL,
                expires_at TIMESTAMPTZ NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                consumed BOOLEAN DEFAULT FALSE,
                consumed_at TIMESTAMPTZ
            );

            CREATE INDEX IF NOT EXISTS idx_draft_campaigns_user_id ON draft_campaigns(user_id);
            CREATE INDEX IF NOT EXISTS idx_draft_campaigns_expires_at ON draft_campaigns(expires_at);
            CREATE INDEX IF NOT EXISTS idx_draft_campaigns_consumed ON draft_campaigns(consumed);
        """)
        conn.commit()
        logger.info("Draft campaigns table initialized")
    except Exception as e:
        logger.error(f"Error creating draft_campaigns table: {e}")
        conn.rollback()
    finally:
        cur.close()


# Initialize table on module load
try:
    create_draft_campaigns_table()
except Exception as e:
    logger.warning(f"Could not initialize draft_campaigns table: {e}")


@router.post("/draft-campaigns")
def create_draft_campaign(campaign: DraftCampaign, request: Request):
    """
    Create a temporary draft campaign.

    Returns a campaign_id that can be passed via URL to another feature.
    Campaign auto-expires after specified hours (default 24).
    """
    user_id = get_user_id(request)
    user_id_str = str(user_id)

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Calculate expiration
        expires_at = datetime.now() + timedelta(hours=campaign.expires_hours)

        # Insert campaign
        cur.execute("""
            INSERT INTO draft_campaigns (user_id, campaign_type, data, expires_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id, user_id, campaign_type, data, expires_at, created_at, consumed
        """, (
            user_id_str,
            campaign.campaign_type,
            psycopg2.extras.Json(campaign.data),
            expires_at
        ))

        created_campaign = cur.fetchone()
        conn.commit()
        cur.close()

        logger.info(
            f"Created draft campaign {created_campaign['id']} for user {user_id} "
            f"(type: {campaign.campaign_type}, expires: {expires_at})"
        )

        return {
            "success": True,
            "campaign_id": str(created_campaign['id']),
            "expires_at": created_campaign['expires_at'].isoformat()
        }
    except Exception as e:
        logger.error(f"Error creating draft campaign: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create draft campaign: {str(e)}")


@router.get("/draft-campaigns/{campaign_id}")
def get_draft_campaign(campaign_id: str, request: Request):
    """
    Get a draft campaign by ID.

    - Returns HTTP 200 with campaign data if found and not expired
    - Returns HTTP 404 if not found or expired
    - Marks campaign as consumed (can still be retrieved multiple times)
    """
    user_id = get_user_id(request)
    user_id_str = str(user_id)

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Query campaign with user_id filter and expiration check
        cur.execute("""
            SELECT id, user_id, campaign_type, data, expires_at, created_at, consumed, consumed_at
            FROM draft_campaigns
            WHERE id = %s AND user_id = %s
        """, (campaign_id, user_id_str))

        campaign = cur.fetchone()

        if not campaign:
            cur.close()
            logger.warning(f"Draft campaign not found or not owned by user {user_id}: {campaign_id}")
            raise HTTPException(status_code=404, detail="Draft campaign not found or not owned by user")

        # Check if expired
        if campaign['expires_at'] < datetime.now():
            cur.close()
            logger.warning(f"Draft campaign expired for user {user_id}: {campaign_id}")
            raise HTTPException(status_code=404, detail="Draft campaign has expired")

        # Mark as consumed if not already
        if not campaign['consumed']:
            cur.execute("""
                UPDATE draft_campaigns
                SET consumed = TRUE, consumed_at = NOW()
                WHERE id = %s
            """, (campaign_id,))
            conn.commit()
            logger.info(f"Marked draft campaign {campaign_id} as consumed by user {user_id}")

        cur.close()

        logger.info(f"Retrieved draft campaign {campaign_id} for user {user_id}")

        return {
            "id": str(campaign['id']),
            "campaign_type": campaign['campaign_type'],
            "data": campaign['data'],
            "created_at": campaign['created_at'].isoformat(),
            "expires_at": campaign['expires_at'].isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving draft campaign: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve draft campaign: {str(e)}")


@router.delete("/draft-campaigns/{campaign_id}")
def delete_draft_campaign(campaign_id: str, request: Request):
    """
    Delete a draft campaign.

    Used for cleanup after campaign is no longer needed.
    """
    user_id = get_user_id(request)
    user_id_str = str(user_id)

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "DELETE FROM draft_campaigns WHERE id = %s AND user_id = %s RETURNING id",
            (campaign_id, user_id_str)
        )

        deleted_campaign = cur.fetchone()
        conn.commit()
        cur.close()

        if not deleted_campaign:
            logger.warning(f"Draft campaign not found or not owned by user {user_id}: {campaign_id}")
            raise HTTPException(status_code=404, detail="Draft campaign not found or not owned by user")

        logger.info(f"Deleted draft campaign {campaign_id} for user {user_id}")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting draft campaign: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete draft campaign: {str(e)}")


@router.post("/draft-campaigns/cleanup-expired")
def cleanup_expired_campaigns(request: Request):
    """
    Cleanup expired draft campaigns.

    Can be called manually or via cron job.
    Only cleans up campaigns owned by requesting user.
    """
    user_id = get_user_id(request)
    user_id_str = str(user_id)

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Delete expired campaigns for this user
        cur.execute("""
            DELETE FROM draft_campaigns
            WHERE user_id = %s AND expires_at < NOW()
            RETURNING id
        """, (user_id_str,))

        deleted_campaigns = cur.fetchall()
        deleted_count = len(deleted_campaigns)

        conn.commit()
        cur.close()

        logger.info(f"Cleaned up {deleted_count} expired draft campaigns for user {user_id}")

        return {
            "success": True,
            "deleted_count": deleted_count
        }
    except Exception as e:
        logger.error(f"Error cleaning up expired campaigns: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to cleanup expired campaigns: {str(e)}")
