from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import anthropic
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)

class CaptionRequest(BaseModel):
    prompt: str
    platforms: List[str]
    postType: str
    hasMedia: bool
    mediaCount: int

@router.post("/generate-caption")
async def generate_caption(request: CaptionRequest):
    """Generate contextual caption based on user prompt and post details"""
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Build context for Claude
        platform_limits = []
        if "x" in request.platforms:
            platform_limits.append("X/Twitter (280 chars max)")
        if "instagram" in request.platforms:
            platform_limits.append("Instagram (2200 chars max)")
        if "linkedin" in request.platforms:
            platform_limits.append("LinkedIn (3000 chars max)")
        if "facebook" in request.platforms:
            platform_limits.append("Facebook (63,206 chars max)")
            
        platform_text = ", ".join(platform_limits) if platform_limits else "general social media"
        media_text = f"{request.mediaCount} image(s)" if request.hasMedia else "no media"
        
        prompt = f"""Create an engaging social media caption for {platform_text}.

User's request: {request.prompt}

Post details:
- Post type: {request.postType}
- Attached media: {media_text}
- Target platforms: {", ".join(request.platforms) if request.platforms else "general"}

Requirements:
- Match the tone and style appropriate for the selected platforms
- Keep it within character limits if posting to X/Twitter
- Include relevant emojis where appropriate
- Add 3-5 relevant hashtags at the end
- Make it engaging and action-oriented

Return ONLY the caption text, no explanations or meta-commentary."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        caption = message.content[0].text.strip()
        
        logger.info(f"Generated caption for: {request.prompt}")
        return {"caption": caption, "success": True}
        
    except Exception as e:
        logger.error(f"Caption generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
