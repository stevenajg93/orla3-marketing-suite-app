from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import anthropic
import os
import json
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)

BRAND_STRATEGY_FILE = "brand_strategy.json"

class CaptionRequest(BaseModel):
    prompt: str
    platforms: List[str]
    postType: str
    hasMedia: bool
    mediaCount: int

def load_brand_strategy():
    """Load brand strategy if it exists"""
    if os.path.exists(BRAND_STRATEGY_FILE):
        with open(BRAND_STRATEGY_FILE, 'r') as f:
            return json.load(f)
    return None

def build_brand_context(strategy: dict) -> str:
    """Build brand context string from strategy"""
    if not strategy:
        return ""
    
    context = "\n\n=== ORLA³ BRAND STRATEGY (CRITICAL - APPLY TO CAPTION) ===\n"
    
    # Brand Voice
    context += f"\nBRAND VOICE & TONE: {strategy['brand_voice']['tone']}\n"
    context += f"PERSONALITY: {', '.join(strategy['brand_voice']['personality'])}\n"
    
    # Messaging Pillars
    context += f"\nMESSAGING PILLARS:\n"
    for pillar in strategy['messaging_pillars']:
        context += f"• {pillar}\n"
    
    # Language Patterns
    context += f"\nWRITING STYLE: {strategy['language_patterns']['writing_style']}\n"
    context += f"PREFERRED PHRASES: {', '.join(strategy['language_patterns']['preferred_phrases'][:3])}\n"
    context += f"KEY VOCABULARY: {', '.join(strategy['language_patterns']['vocabulary'][:5])}\n"
    
    # Do's and Don'ts
    context += f"\nDO: {', '.join(strategy['dos_and_donts']['dos'][:2])}\n"
    context += f"DON'T: {', '.join(strategy['dos_and_donts']['donts'][:2])}\n"
    
    # Competitive Positioning (if available)
    if 'competitive_positioning' in strategy:
        comp_pos = strategy['competitive_positioning']
        context += f"\nOUR UNIQUE VALUE: {comp_pos['unique_value']}\n"
        
        if comp_pos.get('gaps_to_exploit'):
            context += f"EXPLOIT THESE ANGLES: {', '.join(comp_pos['gaps_to_exploit'][:2])}\n"
    
    context += "\n=== END BRAND STRATEGY ===\n\n"
    
    return context

@router.post("/generate-caption")
async def generate_caption(request: CaptionRequest):
    """Generate contextual caption based on user prompt and post details"""
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Load brand strategy
        strategy = load_brand_strategy()
        brand_context = build_brand_context(strategy) if strategy else ""
        
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
        
        prompt = f"""{brand_context}Create an engaging social media caption for {platform_text}.

User's request: {request.prompt}

Post details:
- Post type: {request.postType}
- Attached media: {media_text}
- Target platforms: {", ".join(request.platforms) if request.platforms else "general"}

Requirements:
- CRITICAL: Apply Orla³'s brand voice, tone, and messaging pillars throughout
- Use Orla³'s preferred phrases and vocabulary naturally
- Reflect Orla³'s personality traits
- Leverage our competitive positioning and unique value
- Match the tone appropriate for the selected platforms
- Keep it within character limits if posting to X/Twitter
- Include relevant emojis where appropriate (but aligned with brand personality)
- Add 3-5 relevant hashtags at the end
- Make it engaging and action-oriented
- The caption must sound authentically like Orla³

Return ONLY the caption text, no explanations or meta-commentary."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        caption = message.content[0].text.strip()
        
        logger.info(f"Generated brand-aligned caption for: {request.prompt}")
        return {"caption": caption, "success": True}
        
    except Exception as e:
        logger.error(f"Caption generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
