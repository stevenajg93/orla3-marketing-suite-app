from fastapi import APIRouter
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

@router.post("/social/caption", response_model=CaptionOutput)
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
