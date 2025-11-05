from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import List
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor, Json as PgJson
from datetime import datetime
import shutil
from pathlib import Path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

# Storage paths
BRAND_VOICE_DIR = "brand_voice_assets"
UPLOAD_CATEGORIES = ["guidelines", "voice_samples", "community_videographer", "community_client"]

# Ensure directories exist
for category in UPLOAD_CATEGORIES:
    Path(f"{BRAND_VOICE_DIR}/{category}").mkdir(parents=True, exist_ok=True)

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def extract_text_from_file(filepath: str) -> str:
    """Extract text from various file types"""
    ext = filepath.lower().split('.')[-1]
    
    try:
        # Plain text files
        if ext in ['txt', 'md', 'json']:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        
        # DOCX files
        elif ext == 'docx':
            import docx
            doc = docx.Document(filepath)
            return '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        
        # PDF files
        elif ext == 'pdf':
            import PyPDF2
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ''
                for page in reader.pages:
                    text += page.extract_text()
                return text
        
        # CSV/Excel files
        elif ext in ['csv', 'xlsx', 'xls']:
            import pandas as pd
            if ext == 'csv':
                df = pd.read_csv(filepath)
            else:
                df = pd.read_excel(filepath)
            return df.to_string()
        
        # Discord chat exports (assume JSON format)
        elif 'discord' in filepath.lower() or ext == 'json':
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return '\n'.join([msg.get('content', '') for msg in data if 'content' in msg])
                return json.dumps(data, indent=2)
        
        return ""
        
    except Exception as e:
        logger.error(f"Error extracting text from {filepath}: {str(e)}")
        return ""

def resolve_drive_shortcut(service, file_id):
    """Resolve Google Drive shortcut to actual target file"""
    try:
        from config import Config
        
        file_metadata = service.files().get(
            fileId=file_id,
            fields='id, name, mimeType, shortcutDetails',
            supportsAllDrives=True
        ).execute()
        
        mime_type = file_metadata.get('mimeType')
        filename = file_metadata.get('name')
        
        if mime_type == 'application/vnd.google-apps.shortcut':
            shortcut_details = file_metadata.get('shortcutDetails', {})
            target_id = shortcut_details.get('targetId')
            target_mime_type = shortcut_details.get('targetMimeType')
            
            if not target_id:
                raise HTTPException(status_code=400, detail="Shortcut has no target")
            
            logger.info(f"🔗 Resolved shortcut: {filename}")
            logger.info(f"   Original ID: {file_id}")
            logger.info(f"   Target ID: {target_id}")
            logger.info(f"   Target Type: {target_mime_type}")
            
            return target_id, target_mime_type, filename
        else:
            logger.info(f"📄 Regular file (not a shortcut): {filename}")
            return file_id, mime_type, filename
            
    except Exception as e:
        logger.error(f"Error resolving shortcut: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Could not resolve file: {str(e)}")

@router.post("/upload")
async def upload_brand_assets(
    files: List[UploadFile] = File(...),
    category: str = "guidelines"
):
    """Upload brand voice training files"""
    try:
        if category not in UPLOAD_CATEGORIES:
            raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of: {UPLOAD_CATEGORIES}")
        
        conn = get_db_connection()
        cur = conn.cursor()
        uploaded_files = []
        
        for file in files:
            # Save file to disk
            file_path = f"{BRAND_VOICE_DIR}/{category}/{file.filename}"
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            file_size = os.path.getsize(file_path)
            file_ext = os.path.splitext(file.filename)[1].lower().lstrip('.')
            if not file_ext:
                file_ext = "unknown"
            
            # Extract text content
            text_content = extract_text_from_file(file_path)
            
            # Insert into PostgreSQL
            cur.execute("""
                INSERT INTO brand_voice_assets (
                    filename, category, file_type, file_path, 
                    file_size_bytes, content_preview, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, filename, category, file_size_bytes, content_preview
            """, (
                file.filename,
                category,
                file_ext,
                file_path,
                file_size,
                text_content[:500] if text_content else "No text extracted",
                PgJson({"full_text": text_content})
            ))
            
            asset = cur.fetchone()
            uploaded_files.append(dict(asset))
        
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info(f"Uploaded {len(files)} files to category: {category}")
        return {"success": True, "uploaded": uploaded_files}
        
    except Exception as e:
        logger.error(f"Error uploading brand assets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/assets")
async def list_brand_assets(category: str = None):
    """List all brand voice assets, optionally filtered by category"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        if category:
            cur.execute("""
                SELECT id, filename, category, file_type, file_path, 
                       file_size_bytes, content_preview, uploaded_at
                FROM brand_voice_assets 
                WHERE category = %s
                ORDER BY uploaded_at DESC
            """, (category,))
        else:
            cur.execute("""
                SELECT id, filename, category, file_type, file_path, 
                       file_size_bytes, content_preview, uploaded_at
                FROM brand_voice_assets 
                ORDER BY uploaded_at DESC
            """)
        
        assets = cur.fetchall()
        cur.close()
        conn.close()
        
        return {
            "assets": assets,
            "total": len(assets),
            "categories": UPLOAD_CATEGORIES
        }
        
    except Exception as e:
        logger.error(f"Error listing assets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/assets/{asset_id}")
async def delete_brand_asset(asset_id: str):
    """Delete a brand voice asset"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get asset to delete file
        cur.execute("SELECT file_path FROM brand_voice_assets WHERE id = %s", (asset_id,))
        asset = cur.fetchone()
        
        if not asset:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Delete file from disk
        if os.path.exists(asset['file_path']):
            os.remove(asset['file_path'])
        
        # Delete from database
        cur.execute("DELETE FROM brand_voice_assets WHERE id = %s", (asset_id,))
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info(f"Deleted asset: {asset_id}")
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error deleting asset: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/context/full")
async def get_full_brand_context():
    """Get complete brand context from all assets for AI training"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get all assets with their text
        cur.execute("""
            SELECT filename, category, content_preview, metadata
            FROM brand_voice_assets
            ORDER BY category, uploaded_at
        """)
        assets = cur.fetchall()
        cur.close()
        conn.close()
        
        # Organize content by category
        context_by_category = {cat: [] for cat in UPLOAD_CATEGORIES}
        
        for asset in assets:
            category = asset['category']
            full_text = ""
            
            # Try to get full text from metadata
            if asset.get('metadata') and isinstance(asset['metadata'], dict):
                full_text = asset['metadata'].get('full_text', '')
            
            # Fallback to content_preview
            if not full_text:
                full_text = asset.get('content_preview', '')
            
            if full_text and full_text != "No text extracted":
                context_by_category[category].append(
                    f"File: {asset['filename']}\n{full_text}"
                )
        
        # Build comprehensive context string
        full_context = f"""BRAND VOICE TRAINING CONTEXT

{'='*80}
BRAND GUIDELINES
{'='*80}
{chr(10).join(context_by_category.get('guidelines', [])) or 'No guidelines uploaded'}

{'='*80}
VOICE SAMPLES (Your actual writing)
{'='*80}
{chr(10).join(context_by_category.get('voice_samples', [])) or 'No voice samples uploaded'}

{'='*80}
VIDEOGRAPHER COMMUNITY CONVERSATIONS
{'='*80}
{chr(10).join(context_by_category.get('community_videographer', [])) or 'No community chats uploaded'}

{'='*80}
CLIENT COMMUNITY CONVERSATIONS
{'='*80}
{chr(10).join(context_by_category.get('community_client', [])) or 'No client chats uploaded'}

INSTRUCTION: Use this context to understand the brand voice, industry language, real pain points, 
and authentic communication style. Write content that matches this voice naturally."""

        return {
            "context": full_context,
            "asset_count": len(assets),
            "categories": {cat: len(items) for cat, items in context_by_category.items()}
        }
        
    except Exception as e:
        logger.error(f"Error getting full context: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import-from-drive")
async def import_from_drive(file_id: str, filename: str, category: str):
    """Import a file from Google Drive into brand voice assets"""
    try:
        if category not in UPLOAD_CATEGORIES:
            raise HTTPException(status_code=400, detail=f"Invalid category")
        
        # Import Drive service
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from routes.drive import get_drive_service
        from config import Config
        
        service = get_drive_service()
        if not service:
            raise HTTPException(status_code=503, detail="Google Drive not connected")
        
        logger.info(f"🚀 Starting Drive import: {filename} (ID: {file_id})")
        
        # Resolve shortcut to actual target file
        target_file_id, mime_type, actual_filename = resolve_drive_shortcut(service, file_id)
        
        logger.info(f"📥 Downloading file (MIME: {mime_type})")
        
        # Handle Google Docs files (export as plain text)
        if 'google-apps' in mime_type:
            logger.info(f"Exporting Google Workspace file")
            if 'document' in mime_type:
                request = service.files().export_media(fileId=target_file_id, mimeType='text/plain')
                filename = actual_filename.replace('.gdoc', '.txt') if '.gdoc' in actual_filename else actual_filename + '.txt'
            elif 'spreadsheet' in mime_type:
                request = service.files().export_media(fileId=target_file_id, mimeType='text/csv')
                filename = actual_filename.replace('.gsheet', '.csv') if '.gsheet' in actual_filename else actual_filename + '.csv'
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported Google file type: {mime_type}")
            file_content = request.execute()
        else:
            # Regular file download
            request = service.files().get_media(
                fileId=target_file_id,
                supportsAllDrives=True
            )
            file_content = request.execute()
        
        logger.info(f"✅ Downloaded {len(file_content)} bytes")
        
        # Save to brand voice directory
        file_path = f"{BRAND_VOICE_DIR}/{category}/{filename}"
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        logger.info(f"💾 Saved to: {file_path}")
        
        file_size = os.path.getsize(file_path)
        file_ext = os.path.splitext(filename)[1].lower().lstrip('.')
        if not file_ext:
            file_ext = "unknown"
        
        # Extract text
        text_content = extract_text_from_file(file_path)
        
        # Insert into PostgreSQL
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO brand_voice_assets (
                filename, category, file_type, file_path,
                file_size_bytes, content_preview, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, filename, category, file_size_bytes, uploaded_at
        """, (
            filename,
            category,
            file_ext,
            file_path,
            file_size,
            text_content[:500] if text_content else "No text extracted",
            PgJson({
                "full_text": text_content,
                "source": "google_drive",
                "drive_file_id": file_id,
                "drive_target_id": target_file_id
            })
        ))
        
        asset = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info(f"🎉 Import complete: {filename}")
        return {"success": True, "asset": asset}
        
    except Exception as e:
        logger.error(f"❌ Error importing from Drive: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
