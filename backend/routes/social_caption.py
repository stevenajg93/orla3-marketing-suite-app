from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
import anthropic
import httpx
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import setup_logger
import google.generativeai as genai
from openai import OpenAI
from utils.auth import decode_token
from utils.credits import deduct_credits, InsufficientCreditsError

router = APIRouter()
logger = setup_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

class CaptionRequest(BaseModel):
    prompt: str
    platforms: List[str]
    postType: str
    hasMedia: bool
    mediaCount: int

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def get_user_from_request(request: Request) -> str:
    """Extract user_id from JWT token in Authorization header"""
    auth_header = request.headers.get('authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Missing authorization token")

    token = auth_header.replace('Bearer ', '')
    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload.get('sub')  # user_id

def load_brand_strategy():
    """Load brand strategy from PostgreSQL"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM brand_strategy ORDER BY created_at DESC LIMIT 1")
        strategy = cur.fetchone()
        cur.close()
        conn.close()
        return dict(strategy) if strategy else None
    except Exception as e:
        logger.error(f"Error loading brand strategy: {e}")
        return None

def build_brand_context(strategy: dict) -> str:
    """Build brand context string from strategy"""
    if not strategy:
        return ""
    
    context = "\n\n=== ORLA³ BRAND STRATEGY (CRITICAL - APPLY TO CAPTION) ===\n"
    
    # Handle JSONB fields
    brand_voice = strategy.get('brand_voice', {})
    if isinstance(brand_voice, str):
        brand_voice = json.loads(brand_voice)
    
    language_patterns = strategy.get('language_patterns', {})
    if isinstance(language_patterns, str):
        language_patterns = json.loads(language_patterns)
    
    dos_and_donts = strategy.get('dos_and_donts', {})
    if isinstance(dos_and_donts, str):
        dos_and_donts = json.loads(dos_and_donts)
    
    competitive_positioning = strategy.get('competitive_positioning', {})
    if isinstance(competitive_positioning, str):
        competitive_positioning = json.loads(competitive_positioning)
    
    # Brand Voice
    context += f"\nBRAND VOICE & TONE: {brand_voice.get('tone', '')}\n"
    context += f"PERSONALITY: {', '.join(brand_voice.get('personality', []))}\n"
    
    # Messaging Pillars
    context += f"\nMESSAGING PILLARS:\n"
    for pillar in strategy.get('messaging_pillars', []):
        context += f"• {pillar}\n"
    
    # Language Patterns
    context += f"\nWRITING STYLE: {language_patterns.get('writing_style', '')}\n"
    context += f"PREFERRED PHRASES: {', '.join(language_patterns.get('preferred_phrases', [])[:3])}\n"
    context += f"KEY VOCABULARY: {', '.join(language_patterns.get('vocabulary', [])[:5])}\n"
    
    # Do's and Don'ts
    context += f"\nDO: {', '.join(dos_and_donts.get('dos', [])[:2])}\n"
    context += f"DON'T: {', '.join(dos_and_donts.get('donts', [])[:2])}\n"
    
    # Competitive Positioning
    if competitive_positioning:
        context += f"\nOUR UNIQUE VALUE: {competitive_positioning.get('unique_value', '')}\n"
        
        if competitive_positioning.get('gaps_to_exploit'):
            context += f"EXPLOIT THESE ANGLES: {', '.join(competitive_positioning.get('gaps_to_exploit', [])[:2])}\n"
    
    context += "\n=== END BRAND STRATEGY ===\n\n"
    
    return context

@router.post("/generate-caption")
async def generate_caption(caption_request: CaptionRequest, request: Request):
    """Generate contextual caption based on user prompt and post details"""
    try:
        # Get user_id from JWT token
        user_id = get_user_from_request(request)

        # Check and deduct credits BEFORE generating
        try:
            deduct_credits(
                user_id=user_id,
                operation_type="social_caption",
                operation_details={
                    "prompt": caption_request.prompt[:100],
                    "platforms": caption_request.platforms,
                    "post_type": caption_request.postType
                },
                description=f"Generated social caption for {', '.join(caption_request.platforms)}"
            )
        except InsufficientCreditsError as e:
            logger.warning(f"❌ Insufficient credits for user {user_id}: {e}")
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "insufficient_credits",
                    "message": f"Insufficient credits. Required: {e.required}, Available: {e.available}",
                    "required": e.required,
                    "available": e.available
                }
            )

        # Configure OpenAI API
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise HTTPException(status_code=503, detail="OpenAI API not configured")

        client = OpenAI(api_key=openai_key)

        # Load brand strategy from PostgreSQL
        strategy = load_brand_strategy()
        brand_context = build_brand_context(strategy) if strategy else ""

        # Build context for GPT-4o
        platform_limits = []
        if "x" in caption_request.platforms:
            platform_limits.append("X/Twitter (280 chars max)")
        if "instagram" in caption_request.platforms:
            platform_limits.append("Instagram (2200 chars max)")
        if "linkedin" in caption_request.platforms:
            platform_limits.append("LinkedIn (3000 chars max)")
        if "facebook" in caption_request.platforms:
            platform_limits.append("Facebook (63,206 chars max)")

        platform_text = ", ".join(platform_limits) if platform_limits else "general social media"
        media_text = f"{caption_request.mediaCount} image(s)" if caption_request.hasMedia else "no media"

        prompt = f"""{brand_context}Create an engaging social media caption for {platform_text}.

User's request: {caption_request.prompt}

Post details:
- Post type: {caption_request.postType}
- Attached media: {media_text}
- Target platforms: {", ".join(caption_request.platforms) if caption_request.platforms else "general"}

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

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024
        )

        caption = response.choices[0].message.content.strip()

        logger.info(f"✅ Generated brand-aligned caption (GPT-4o) for user {user_id}: {caption_request.prompt[:50]}")
        return {"caption": caption, "success": True}

    except Exception as e:
        logger.error(f"Caption generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trending-topics")
async def get_trending_topics():
    """Use Perplexity to research what's trending on social media in videography"""
    try:
        perplexity_key = os.getenv("PERPLEXITY_API_KEY")
        if not perplexity_key:
            raise HTTPException(status_code=503, detail="Perplexity API not configured")

        query = """What are the top trending topics, hashtags, and content themes on Instagram, TikTok, and LinkedIn right now in the videography and video production industry?

Focus on:
1. Viral trends and challenges
2. Popular hashtags
3. Content formats getting high engagement
4. Topics videographers are discussing
5. Client pain points being addressed

Provide 5-8 specific, actionable content ideas with suggested hashtags."""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {perplexity_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-sonar-large-128k-online",
                    "messages": [
                        {"role": "user", "content": query}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000
                },
                timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()
                trends = data["choices"][0]["message"]["content"]
                logger.info(f"✅ Retrieved social trends: {len(trends)} chars")
                return {"success": True, "trends": trends}
            else:
                logger.error(f"Perplexity API error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch trends")

    except httpx.TimeoutException:
        logger.error("Perplexity API timeout")
        raise HTTPException(status_code=504, detail="Trend research timed out")
    except Exception as e:
        logger.error(f"Error fetching trends: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
