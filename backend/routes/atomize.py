from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from anthropic import Anthropic
import os, json, re, httpx
import google.generativeai as genai

router = APIRouter()

class AtomizeRequest(BaseModel):
    blog_title: str
    blog_content: str
    blog_url: Optional[str] = None
    keyword: str

class PlatformPost(BaseModel):
    platform: str
    content: str
    hashtags: List[str]
    character_count: int
    media_url: Optional[str] = None

class AtomizeResponse(BaseModel):
    posts: List[PlatformPost]
    hero_image_url: str

def extract_json_from_response(text: str) -> dict:
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    return json.loads(text.strip())

async def get_unsplash_image(keyword: str) -> str:
    """Fetch relevant image from Unsplash"""
    access_key = os.getenv("UNSPLASH_ACCESS_KEY")
    if not access_key:
        return "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?w=1200"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.unsplash.com/search/photos",
                params={"query": keyword, "per_page": 1, "orientation": "landscape"},
                headers={"Authorization": f"Client-ID {access_key}"}
            )
            data = response.json()
            if data.get("results"):
                return data["results"][0]["urls"]["regular"]
    except:
        pass
    
    return "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?w=1200"

@router.post("/atomize/blog-to-social", response_model=AtomizeResponse)
async def atomize_blog_to_social(data: AtomizeRequest):
    """Takes a blog post and creates optimized posts for 8 social platforms"""
    # Configure Gemini API
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        raise HTTPException(status_code=503, detail="Gemini API not configured")

    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')

    # Get hero image
    hero_image = await get_unsplash_image(data.keyword)

    combined_prompt = f"""You are ORLA³'s social media atomization specialist.
Your job: transform long-form blog content into engaging, platform-optimized social posts.

PLATFORM RULES:
- LinkedIn: Professional, 1300 chars max, 3-5 hashtags, focus on insights
- Twitter/X: Punchy, 280 chars max, 2-3 hashtags, hook in first 10 words
- Facebook: Conversational, 400 chars optimal, 2-3 hashtags, storytelling
- Instagram: Visual-first caption, 150 chars, 5-10 hashtags, emoji-friendly
- TikTok: Trendy, 150 chars, 3-5 hashtags, call-to-action
- YouTube: Keyword-rich, 5000 chars max, descriptive, SEO-focused
- Reddit: Authentic, no hashtags, question or insight format
- Tumblr: Creative, 500 chars, 3-5 tags, conversational

ORLA³ CONTEXT:
- P2P videography marketplace in UK
- Escrow payments for safety
- No subscriptions or pay-to-rank
- Fast videographer payouts (2-3 days)

Return ONLY valid JSON.

---

Transform this blog into 8 platform-optimized posts:

Blog Title: {data.blog_title}
Blog Content: {data.blog_content[:2000]}...
Blog URL: {data.blog_url or 'https://orla3.com/blog'}
Keyword: {data.keyword}

Return JSON in this exact format:
{{
  "posts": [
    {{
      "platform": "linkedin",
      "content": "Professional post content here...",
      "hashtags": ["VideoProduction", "UKBusiness", "Videography"],
      "character_count": 450
    }},
    {{
      "platform": "twitter",
      "content": "Punchy tweet here...",
      "hashtags": ["VideoUK", "Videographer"],
      "character_count": 200
    }}
  ]
}}

Create engaging posts that drive clicks to the blog while respecting each platform's culture.
Include ORLA³ context naturally where relevant.
NO asterisks, NO hyphens, write like a human."""

    try:
        response = model.generate_content(combined_prompt)
        raw_text = response.text
        content = extract_json_from_response(raw_text)

        # Add hero image URL to each post
        for post in content["posts"]:
            post["media_url"] = hero_image

        return {
            "posts": content["posts"],
            "hero_image_url": hero_image
        }
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}", "raw": raw_text[:500]}
