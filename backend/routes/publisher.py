from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Literal, Optional
from anthropic import Anthropic
import os, json, re

router = APIRouter()

class PublishInput(BaseModel):
    content: str
    platforms: List[Literal["wordpress", "youtube", "linkedin", "x", "instagram", "facebook", "tiktok", "reddit", "tumblr"]]
    content_type: Literal["article", "video", "image", "carousel"]
    brand_tone_rules: str = "Cinematic, confident, fair"

class PlatformContent(BaseModel):
    platform: str
    title: str
    body: str
    hashtags: List[str]
    character_count: int
    aspect_ratio: Optional[str] = None
    optimal_post_time: str

class PublishOutput(BaseModel):
    adaptations: List[PlatformContent]

def extract_json_from_response(text: str) -> dict:
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()
    return json.loads(text)

@router.post("/publish/adapt", response_model=PublishOutput)
def adapt_for_platforms(data: PublishInput):
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    system_prompt = """You adapt content for multiple social platforms with platform-specific optimization.
Return JSON ONLY without markdown code blocks."""
    
    user_prompt = f"""Adapt this content for these platforms: {', '.join(data.platforms)}

ORIGINAL CONTENT:
{data.content[:500]}...

CONTENT TYPE: {data.content_type}
BRAND TONE: {data.brand_tone_rules}

For each platform, provide:
- title (platform-appropriate length)
- body (adapted to character limits and platform style)
- hashtags (3-5 relevant, platform-appropriate)
- character_count (total chars used)
- aspect_ratio (for visual content: "16:9", "1:1", "9:16")
- optimal_post_time (best time to post, e.g., "Tuesday 10:00 GMT")

Platform specs to follow:
- WordPress: Long-form, SEO-focused
- YouTube: Video description, keywords, chapters
- LinkedIn: Professional, max 3000 chars
- X: Concise, max 280 chars (thread if needed)
- Instagram: Visual-first, max 2200 chars
- Facebook: Conversational, max 63206 chars
- TikTok: Short, trendy, max 2200 chars
- Reddit: Community-focused, conversational
- Tumblr: Creative, blog-style

Return ONLY this JSON:
{{
  "adaptations": [
    {{
      "platform": "linkedin",
      "title": "string",
      "body": "string",
      "hashtags": ["tag1", "tag2"],
      "character_count": 250,
      "aspect_ratio": "1:1",
      "optimal_post_time": "Tuesday 10:00 GMT"
    }}
  ]
}}"""

    completion = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=3500,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )

    try:
        raw_text = completion.content[0].text
        content = extract_json_from_response(raw_text)
        return content
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}", "raw": completion.content[0].text[:500]}
