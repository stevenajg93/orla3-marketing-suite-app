from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal, List
from anthropic import Anthropic
import os, json, re

router = APIRouter()

class CaptionInput(BaseModel):
    topic: str
    platform: Literal["instagram", "linkedin", "twitter"] = "instagram"
    tone: Literal["professional", "casual", "inspirational", "humorous"] = "professional"
    include_hashtags: bool = True
    include_emojis: bool = True
    variations: int = 3

class CaptionOutput(BaseModel):
    captions: List[str]
    platform: str
    hashtags: List[str]

def extract_json_from_response(text: str) -> dict:
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()
    return json.loads(text)

def resolve_drive_shortcut(service, file_id):
    """
    Resolve Google Drive shortcut to actual target file.
    Returns: (target_file_id, mime_type)
    """
    try:
        from config import Config
        
        file_metadata = service.files().get(
            fileId=file_id,
            fields='id, name, mimeType, shortcutDetails',
            supportsAllDrives=True
        ).execute()
        
        mime_type = file_metadata.get('mimeType')
        
        # Check if it's a shortcut
        if mime_type == 'application/vnd.google-apps.shortcut':
            shortcut_details = file_metadata.get('shortcutDetails', {})
            target_id = shortcut_details.get('targetId')
            target_mime_type = shortcut_details.get('targetMimeType')
            
            if not target_id:
                raise HTTPException(status_code=400, detail="Shortcut has no target")
            
            return target_id, target_mime_type
        else:
            return file_id, mime_type
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not resolve file: {str(e)}")

@router.post("/caption", response_model=CaptionOutput)
async def generate_caption(data: CaptionInput):
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    platform_guides = {
        "instagram": "Instagram: 125-150 chars for optimal engagement. Use line breaks and emojis naturally.",
        "linkedin": "LinkedIn: 150-200 chars. Professional but conversational. Limit emojis.",
        "twitter": "Twitter: Under 280 chars (aim for 200-250 for retweets). Punchy and direct."
    }
    
    system_prompt = f"""You create high-performing social media captions optimized for {data.platform}.

BRAND: ORLA³ - A fair P2P marketplace for creative services (videography, photography, design)
BRAND TONE: Confident, fair, empowering, authentic

{platform_guides[data.platform]}

Return JSON ONLY without markdown code blocks."""
    
    emoji_instruction = "Use emojis strategically (2-4 per caption)" if data.include_emojis else "NO emojis"
    hashtag_instruction = f"Include 5-8 relevant hashtags" if data.include_hashtags else "NO hashtags"
    
    user_prompt = f"""Create {data.variations} unique {data.platform} captions about: {data.topic}

Tone: {data.tone}
{emoji_instruction}
{hashtag_instruction}

Each caption should:
- Hook attention in the first line
- Be valuable and actionable
- End with a clear CTA (question, instruction, or engagement prompt)
- Feel authentic and human (not corporate fluff)

Return ONLY this JSON format:
{{
  "platform": "{data.platform}",
  "captions": [
    "caption text here...",
    "caption text here...",
    "caption text here..."
  ],
  "hashtags": ["hashtag1", "hashtag2", "hashtag3", "hashtag4", "hashtag5"]
}}

Make each caption UNIQUE - different hooks, angles, and CTAs."""

    completion = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )

    try:
        raw_text = completion.content[0].text
        content = extract_json_from_response(raw_text)
        return content
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}", "raw": completion.content[0].text[:500]}

@router.get("/drive-file/{file_id}")
async def get_drive_file_url(file_id: str):
    """Get a usable URL for a Drive file (resolves shortcuts)"""
    try:
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from routes.drive import get_drive_service
        
        service = get_drive_service()
        if not service:
            raise HTTPException(status_code=503, detail="Google Drive not connected")
        
        # Resolve shortcut if needed
        target_file_id, mime_type = resolve_drive_shortcut(service, file_id)
        
        # Get file metadata with webContentLink
        file_metadata = service.files().get(
            fileId=target_file_id,
            fields='id, name, mimeType, webViewLink, webContentLink, thumbnailLink',
            supportsAllDrives=True
        ).execute()
        
        return {
            "success": True,
            "file_id": target_file_id,
            "name": file_metadata.get('name'),
            "mime_type": file_metadata.get('mimeType'),
            "web_view_link": file_metadata.get('webViewLink'),
            "web_content_link": file_metadata.get('webContentLink'),
            "thumbnail_link": file_metadata.get('thumbnailLink')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
