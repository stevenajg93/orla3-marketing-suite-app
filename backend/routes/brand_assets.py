from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import setup_logger
from db_pool import get_db_connection  # Use connection pool
from lib.brand_asset_extractor import extract_brand_assets, find_logo_file, find_logo_from_database
from pathlib import Path

router = APIRouter()
logger = setup_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")


@router.get("/brand-assets")
async def get_brand_assets():
    """
    Get brand visual assets (colors, fonts, logo) for use in content generation.
    Returns the current brand colors, fonts, and logo URL from brand_strategy.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get latest brand strategy with visual assets
        cur.execute("""
            SELECT brand_colors, brand_fonts, logo_url,
                   primary_color, secondary_color
            FROM brand_strategy
            ORDER BY created_at DESC
            LIMIT 1
        """)

        brand_assets = cur.fetchone()
        cur.close()

        if not brand_assets:
            logger.warning("No brand strategy found - returning defaults")
            return {
                "success": True,
                "brand_colors": [],
                "brand_fonts": [],
                "logo_url": None,
                "primary_color": None,
                "secondary_color": None,
                "message": "No brand assets extracted yet. Upload brand guidelines to extract colors and fonts."
            }

        return {
            "success": True,
            "brand_colors": brand_assets['brand_colors'] or [],
            "brand_fonts": brand_assets['brand_fonts'] or [],
            "logo_url": brand_assets['logo_url'],
            "primary_color": brand_assets['primary_color'],
            "secondary_color": brand_assets['secondary_color']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching brand assets: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch brand assets")

@router.post("/brand-assets/extract")
async def extract_assets_from_guidelines():
    """
    Manually trigger extraction of brand assets from uploaded guidelines.
    Analyzes uploaded brand guidelines PDFs/docs for colors, fonts, and logos.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get all guideline assets
        cur.execute("""
            SELECT filename, file_path, metadata
            FROM brand_voice_assets
            WHERE category = 'guidelines'
            ORDER BY uploaded_at DESC
        """)

        guidelines = cur.fetchall()

        if not guidelines:
            cur.close()
            return {
                "success": False,
                "error": "No brand guidelines uploaded yet. Upload brand guidelines first."
            }

        # Extract text from all guidelines
        all_text = ""
        for guideline in guidelines:
            # Get full text from metadata
            if guideline.get('metadata') and isinstance(guideline['metadata'], dict):
                full_text = guideline['metadata'].get('full_text', '')
                if full_text:
                    all_text += f"\n\n{full_text}"

        if not all_text:
            cur.close()
            return {
                "success": False,
                "error": "Could not extract text from guidelines"
            }

        logger.info(f"Extracting brand assets from {len(all_text)} characters of text")

        # Extract brand assets
        assets = extract_brand_assets(all_text)

        # Find logo file (prefer database/GCS, fallback to filesystem)
        logo_url = find_logo_from_database(conn)
        if not logo_url:
            # Fallback to local filesystem for backwards compatibility
            brand_voice_dir = Path("brand_voice_assets")
            logo_url = find_logo_file(brand_voice_dir, "guidelines")
            if not logo_url:
                logo_url = find_logo_file(brand_voice_dir, "logos")

        assets['logo_url'] = logo_url

        logger.info(f"Extracted: {len(assets['brand_colors'])} colors, {len(assets['brand_fonts'])} fonts")

        # Update brand_strategy table
        cur.execute("""
            UPDATE brand_strategy
            SET brand_colors = %s,
                brand_fonts = %s,
                logo_url = %s,
                primary_color = %s,
                secondary_color = %s
            WHERE id = (SELECT id FROM brand_strategy ORDER BY created_at DESC LIMIT 1)
        """, (
            assets['brand_colors'],
            assets['brand_fonts'],
            assets['logo_url'],
            assets['primary_color'],
            assets['secondary_color']
        ))

        conn.commit()
        cur.close()

        logger.info("✅ Brand assets extracted and saved")

        return {
            "success": True,
            "extracted": {
                "colors": assets['brand_colors'],
                "fonts": assets['brand_fonts'],
                "logo_url": assets['logo_url'],
                "primary_color": assets['primary_color'],
                "secondary_color": assets['secondary_color']
            },
            "message": f"Extracted {len(assets['brand_colors'])} colors and {len(assets['brand_fonts'])} fonts"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting brand assets: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to extract brand assets")

@router.get("/brand-assets/logo")
async def get_logo_file():
    """
    Get the brand logo file.
    Returns the logo file path or GCS URL.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # First check brand_strategy table
        cur.execute("""
            SELECT logo_url
            FROM brand_strategy
            ORDER BY created_at DESC
            LIMIT 1
        """)

        result = cur.fetchone()

        if result and result['logo_url']:
            cur.close()
            return {"success": True, "logo_url": result['logo_url']}

        # If not in brand_strategy, look in brand_voice_assets (database)
        logo_url = find_logo_from_database(conn)

        cur.close()

        if logo_url:
            return {"success": True, "logo_url": logo_url}

        # Final fallback: check local filesystem (legacy)
        brand_voice_dir = Path("brand_voice_assets")
        logo_url = find_logo_file(brand_voice_dir, "guidelines")
        if not logo_url:
            logo_url = find_logo_file(brand_voice_dir, "logos")

        if logo_url:
            return {"success": True, "logo_url": logo_url}
        else:
            return {"success": False, "error": "No logo found"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching logo: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch logo")
