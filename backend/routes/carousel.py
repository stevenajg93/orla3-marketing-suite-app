from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Literal
from anthropic import Anthropic
import os, json, re, httpx

router = APIRouter()

class CarouselInput(BaseModel):
    post_summary: str
    brand_tone_rules: str = "Cinematic, confident, fair, buyer-seller balanced"
    target_platform: Literal["linkedin", "instagram"] = "linkedin"
    angle: Literal["problem-solution", "myth-busting", "checklist", "case-study"] = "problem-solution"
    cta_url: str = "https://orla3.com"

class Slide(BaseModel):
    id: int
    role: str
    title: str
    body: str
    alt_hint: str
    image_url: str = ""

class CarouselOutput(BaseModel):
    platform: str
    slides: List[Slide]

def extract_json_from_response(text: str) -> dict:
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()
    return json.loads(text)

async def get_unsplash_image(query: str) -> str:
    access_key = os.getenv("UNSPLASH_ACCESS_KEY")
    if not access_key:
        return "https://images.unsplash.com/photo-1557804506-669a67965ba0?w=800"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.unsplash.com/search/photos",
                params={"query": query, "per_page": 1, "orientation": "landscape"},
                headers={"Authorization": f"Client-ID {access_key}"}
            )
            data = response.json()
            if data.get("results"):
                return data["results"][0]["urls"]["regular"]
    except:
        pass
    
    return "https://images.unsplash.com/photo-1557804506-669a67965ba0?w=800"

@router.post("/social/carousel", response_model=CarouselOutput)
async def generate_carousel(data: CarouselInput):
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    system_prompt = """You create high-performing Instagram/LinkedIn carousels that are UNIQUE to each topic.

CRITICAL RULES:
1. READ the user's post_summary carefully and create CUSTOM content based on THEIR specific topic
2. DO NOT use generic "hiring videographer" content unless that's explicitly their topic
3. Slide 1 (HOOK): Short punchy title (3-4 words) + compelling 2-sentence hook
4. Slides 2-7: Short title (3-4 words) + detailed body text (2-3 sentences, 120-180 chars)

Return JSON ONLY without markdown code blocks."""
    
    user_prompt = f"""Create a CUSTOM 7-slide carousel specifically about this topic:

TOPIC: {data.post_summary}

Platform: {data.target_platform}
Brand tone: {data.brand_tone_rules}
Content angle: {data.angle}

IMPORTANT: Create content that is DIRECTLY relevant to the topic above. Do not use generic examples.

SLIDE STRUCTURE:
1. HOOK (Slide 1):
   - title: 3-4 words max, ultra punchy and relevant to THIS specific topic
   - body: 2 compelling sentences about THIS topic that make them want to swipe (100-120 chars)
   
2. CONTENT SLIDES (Slides 2-7):
   - title: 3-4 words max, each about a different aspect of THIS topic
   - body: 2-3 detailed sentences explaining that specific point (120-180 chars)

Create 7 slides with these exact roles:
1. HOOK - Attention-grabbing problem/opportunity statement about THIS topic
2. CONTEXT - Why this specific topic matters right now
3. INSIGHT_1 - First key insight about THIS topic with details
4. INSIGHT_2 - Second key insight about THIS topic with details  
5. INSIGHT_3 - Third key insight about THIS topic with details
6. HOW_TO - Actionable advice specifically for THIS topic
7. CTA - Strong call to action with ORLA³ as the solution

TITLE LENGTH LIMITS:
- Slide 1 title: Maximum 20 characters
- All other titles: Maximum 25 characters

Return ONLY valid JSON in this exact format:
{{
  "platform": "{data.target_platform}",
  "slides": [
    {{"id": 1, "role": "HOOK", "title": "short punchy title", "body": "Two compelling sentences about the topic.", "alt_hint": "relevant image"}},
    {{"id": 2, "role": "CONTEXT", "title": "3-4 word title", "body": "Two to three sentences with details about this aspect.", "alt_hint": "relevant image"}},
    {{"id": 3, "role": "INSIGHT_1", "title": "3-4 word title", "body": "Two to three sentences with details about this aspect.", "alt_hint": "relevant image"}},
    {{"id": 4, "role": "INSIGHT_2", "title": "3-4 word title", "body": "Two to three sentences with details about this aspect.", "alt_hint": "relevant image"}},
    {{"id": 5, "role": "INSIGHT_3", "title": "3-4 word title", "body": "Two to three sentences with details about this aspect.", "alt_hint": "relevant image"}},
    {{"id": 6, "role": "HOW_TO", "title": "3-4 word title", "body": "Two to three sentences with actionable steps.", "alt_hint": "relevant image"}},
    {{"id": 7, "role": "CTA", "title": "3-4 word title", "body": "Two to three sentences with ORLA³ as the solution.", "alt_hint": "success"}}
  ]
}}

Remember: Create UNIQUE content based on the specific topic provided, not generic examples."""

    completion = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2500,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )

    try:
        raw_text = completion.content[0].text
        content = extract_json_from_response(raw_text)
        
        # Fetch images for each slide
        for slide in content["slides"]:
            query = slide.get("alt_hint", "business professional")
            slide["image_url"] = await get_unsplash_image(query)
        
        return content
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}", "raw": completion.content[0].text[:500]}
