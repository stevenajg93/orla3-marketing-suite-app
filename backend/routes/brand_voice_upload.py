from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import List
import os
import json
from datetime import datetime
import shutil
from pathlib import Path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)

# Storage paths
BRAND_VOICE_DIR = "brand_voice_assets"
UPLOAD_CATEGORIES = ["guidelines", "voice_samples", "community_videographer", "community_client", "logos"]

# Ensure directories exist
for category in UPLOAD_CATEGORIES:
    Path(f"{BRAND_VOICE_DIR}/{category}").mkdir(parents=True, exist_ok=True)

BRAND_INDEX_FILE = "brand_voice_index.json"

def load_brand_index():
    """Load the brand voice asset index"""
    if os.path.exists(BRAND_INDEX_FILE):
        with open(BRAND_INDEX_FILE, 'r') as f:
            return json.load(f)
    return {"assets": [], "last_updated": None}

def save_brand_index(index):
    """Save the brand voice asset index"""
    index['last_updated'] = datetime.now().isoformat()
    with open(BRAND_INDEX_FILE, 'w') as f:
        json.dump(index, f, indent=2)

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
        
        # Discord chat exports (assume JSON format)
        elif 'discord' in filepath.lower() or ext == 'json':
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Handle various Discord export formats
                if isinstance(data, list):
                    return '\n'.join([msg.get('content', '') for msg in data if 'content' in msg])
                return json.dumps(data, indent=2)
        
        return ""
        
    except Exception as e:
        logger.error(f"Error extracting text from {filepath}: {str(e)}")
        return ""

def resolve_drive_shortcut(service, file_id):
    """
    Resolve Google Drive shortcut to actual target file.
    
    Args:
        service: Google Drive API service
        file_id: File ID (might be a shortcut)
    
    Returns:
        tuple: (target_file_id, mime_type, actual_filename)
    """
    try:
        from config import Config
        
        # Get file metadata with shortcutDetails
        file_metadata = service.files().get(
            fileId=file_id,
            fields='id, name, mimeType, shortcutDetails',
            supportsAllDrives=True
        ).execute()
        
        mime_type = file_metadata.get('mimeType')
        filename = file_metadata.get('name')
        
        # Check if it's a shortcut
        if mime_type == 'application/vnd.google-apps.shortcut':
            shortcut_details = file_metadata.get('shortcutDetails', {})
            target_id = shortcut_details.get('targetId')
            target_mime_type = shortcut_details.get('targetMimeType')
            
            if not target_id:
                raise HTTPException(status_code=400, detail="Shortcut has no target file")
            
            logger.info(f"🔗 Resolved shortcut: {filename}")
            logger.info(f"   Original ID: {file_id}")
            logger.info(f"   Target ID: {target_id}")
            logger.info(f"   Target Type: {target_mime_type}")
            
            return target_id, target_mime_type, filename
        else:
            # Not a shortcut, return as-is
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
        
        index = load_brand_index()
        uploaded_files = []
        
        for file in files:
            # Save file
            file_path = f"{BRAND_VOICE_DIR}/{category}/{file.filename}"
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Extract text content
            text_content = extract_text_from_file(file_path)
            
            # Add to index
            asset_entry = {
                "id": f"asset_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(index['assets'])}",
                "filename": file.filename,
                "category": category,
                "path": file_path,
                "size": os.path.getsize(file_path),
                "text_preview": text_content[:500] if text_content else "No text extracted",
                "full_text": text_content,
                "uploaded_at": datetime.now().isoformat()
            }
            
            index['assets'].append(asset_entry)
            uploaded_files.append({
                "filename": file.filename,
                "category": category,
                "size": asset_entry['size'],
                "preview": asset_entry['text_preview']
            })
        
        save_brand_index(index)
        
        logger.info(f"Uploaded {len(files)} files to category: {category}")
        return {"success": True, "uploaded": uploaded_files, "total_assets": len(index['assets'])}
        
    except Exception as e:
        logger.error(f"Error uploading brand assets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/assets")
async def list_brand_assets(category: str = None):
    """List all brand voice assets, optionally filtered by category"""
    try:
        index = load_brand_index()
        assets = index['assets']
        
        if category:
            assets = [a for a in assets if a['category'] == category]
        
        # Don't return full_text in list view (too large)
        assets_preview = [{k: v for k, v in asset.items() if k != 'full_text'} for asset in assets]
        
        return {
            "assets": assets_preview,
            "total": len(assets_preview),
            "categories": UPLOAD_CATEGORIES
        }
        
    except Exception as e:
        logger.error(f"Error listing assets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/assets/{asset_id}")
async def delete_brand_asset(asset_id: str):
    """Delete a brand voice asset"""
    try:
        index = load_brand_index()
        asset = next((a for a in index['assets'] if a['id'] == asset_id), None)
        
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Delete file
        if os.path.exists(asset['path']):
            os.remove(asset['path'])
        
        # Remove from index
        index['assets'] = [a for a in index['assets'] if a['id'] != asset_id]
        save_brand_index(index)
        
        logger.info(f"Deleted asset: {asset['filename']}")
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error deleting asset: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/context/full")
async def get_full_brand_context():
    """Get complete brand context from all assets for AI training"""
    try:
        index = load_brand_index()
        
        # Organize content by category
        context_by_category = {}
        for category in UPLOAD_CATEGORIES:
            category_assets = [a for a in index['assets'] if a['category'] == category]
            context_by_category[category] = '\n\n---\n\n'.join([
                f"File: {a['filename']}\n{a['full_text']}" 
                for a in category_assets if a.get('full_text')
            ])
        
        # Build comprehensive context string
        full_context = f"""BRAND VOICE TRAINING CONTEXT

{'='*80}
BRAND GUIDELINES
{'='*80}
{context_by_category.get('guidelines', 'No guidelines uploaded')}

{'='*80}
VOICE SAMPLES (Your actual writing)
{'='*80}
{context_by_category.get('voice_samples', 'No voice samples uploaded')}

{'='*80}
VIDEOGRAPHER COMMUNITY CONVERSATIONS
{'='*80}
{context_by_category.get('community_videographer', 'No community chats uploaded')}

{'='*80}
CLIENT COMMUNITY CONVERSATIONS
{'='*80}
{context_by_category.get('community_client', 'No client chats uploaded')}

INSTRUCTION: Use this context to understand the brand voice, industry language, real pain points, 
and authentic communication style. Write content that matches this voice naturally."""

        return {
            "context": full_context,
            "asset_count": len(index['assets']),
            "categories": {cat: len([a for a in index['assets'] if a['category'] == cat]) for cat in UPLOAD_CATEGORIES}
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
        
        # CRITICAL FIX: Resolve shortcut to actual target file
        target_file_id, mime_type, actual_filename = resolve_drive_shortcut(service, file_id)
        
        # Use resolved target ID for download
        logger.info(f"📥 Downloading file (MIME: {mime_type})")
        
        # Handle Google Docs files (export as plain text)
        if 'google-apps' in mime_type:
            logger.info(f"Exporting Google Workspace file")
            if 'document' in mime_type:
                # Export Google Doc as plain text
                request = service.files().export_media(fileId=target_file_id, mimeType='text/plain')
                filename = actual_filename.replace('.gdoc', '.txt') if '.gdoc' in actual_filename else actual_filename + '.txt'
            elif 'spreadsheet' in mime_type:
                # Export Google Sheet as CSV
                request = service.files().export_media(fileId=target_file_id, mimeType='text/csv')
                filename = actual_filename.replace('.gsheet', '.csv') if '.gsheet' in actual_filename else actual_filename + '.csv'
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported Google file type: {mime_type}")
            file_content = request.execute()
        else:
            # Regular file download using TARGET ID with supportsAllDrives
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
        
        # Extract text
        text_content = extract_text_from_file(file_path)
        
        # Add to index
        index = load_brand_index()
        asset_entry = {
            "id": f"asset_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(index['assets'])}",
            "filename": filename,
            "category": category,
            "path": file_path,
            "size": os.path.getsize(file_path),
            "text_preview": text_content[:500] if text_content else "No text extracted",
            "full_text": text_content,
            "uploaded_at": datetime.now().isoformat(),
            "source": "google_drive",
            "drive_file_id": file_id,
            "drive_target_id": target_file_id
        }
        
        index['assets'].append(asset_entry)
        save_brand_index(index)
        
        logger.info(f"🎉 Import complete: {filename}")
        return {"success": True, "asset": asset_entry}
        
    except Exception as e:
        logger.error(f"❌ Error importing from Drive: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
