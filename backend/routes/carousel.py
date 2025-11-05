from dotenv import load_dotenv; load_dotenv('.env.local', override=True)
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Literal
from anthropic import Anthropic
import os, json, re, httpx
import psycopg2
from psycopg2.extras import RealDictCursor

router = APIRouter()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

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

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

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
        print(f"Error loading brand strategy: {e}")
        return None

def build_brand_context(strategy: dict) -> str:
    """Build brand context string from strategy"""
    if not strategy:
        return ""
    
    context = "\n\n=== ORLA³ BRAND STRATEGY (CRITICAL - FOLLOW EXACTLY) ===\n"
    
    # Handle JSONB fields
    brand_voice = strategy.get('brand_voice', {})
    if isinstance(brand_voice, str):
        brand_voice = json.loads(brand_voice)
    
    language_patterns = strategy.get('language_patterns', {})
    if isinstance(language_patterns, str):
        language_patterns = json.loads(language_patterns)
    
    competitive_positioning = strategy.get('competitive_positioning', {})
    if isinstance(competitive_positioning, str):
        competitive_positioning = json.loads(competitive_positioning)
    
    # Brand Voice
    context += f"\nBRAND VOICE & TONE:\n{brand_voice.get('tone', '')}\n"
    context += f"PERSONALITY: {', '.join(brand_voice.get('personality', []))}\n"
    
    # Messaging Pillars
    context += f"\nMESSAGING PILLARS (weave into slides):\n"
    for pillar in strategy.get('messaging_pillars', []):
        context += f"• {pillar}\n"
    
    # Language Patterns
    context += f"\nWRITING STYLE: {language_patterns.get('writing_style', '')}\n"
    context += f"PREFERRED PHRASES: {', '.join(language_patterns.get('preferred_phrases', [])[:3])}\n"
    
    # Competitive Positioning
    if competitive_positioning:
        context += f"\nCOMPETITIVE POSITIONING:\n"
        context += f"Our Unique Value: {competitive_positioning.get('unique_value', '')}\n"
        
        if competitive_positioning.get('gaps_to_exploit'):
            context += f"\nExploit These Content Gaps:\n"
            for gap in competitive_positioning.get('gaps_to_exploit', [])[:2]:
                context += f"• {gap}\n"
    
    context += "\n=== END BRAND STRATEGY ===\n\n"
    
    return context

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
    
    # Load brand strategy from PostgreSQL
    strategy = load_brand_strategy()
    brand_context = build_brand_context(strategy) if strategy else ""
    
    system_prompt = f"""You create high-performing Instagram/LinkedIn carousels that are UNIQUE to each topic.

{brand_context}

CRITICAL RULES:
1. READ the user's post_summary carefully and create CUSTOM content based on THEIR specific topic
2. DO NOT use generic "hiring videographer" content unless that's explicitly their topic
3. Apply Orla³'s brand voice, tone, and messaging pillars throughout ALL slides
4. Use Orla³'s preferred phrases and writing style naturally
5. Leverage our competitive positioning - exploit content gaps competitors miss
6. Slide 1 (HOOK): Short punchy title (3-4 words) + compelling 2-sentence hook
7. Slides 2-7: Short title (3-4 words) + detailed body text (2-3 sentences, 120-180 chars)

BRAND VOICE COMPLIANCE:
- Every slide must reflect Orla³'s personality and tone
- Use language patterns that align with our brand strategy
- Position content according to our competitive advantages

Return JSON ONLY without markdown code blocks."""
    
    user_prompt = f"""Create a CUSTOM 7-slide carousel specifically about this topic:

TOPIC: {data.post_summary}

Platform: {data.target_platform}
Brand tone: {data.brand_tone_rules}
Content angle: {data.angle}

IMPORTANT: 
- Create content that is DIRECTLY relevant to the topic above
- Apply Orla³'s brand strategy throughout all slides
- This content must sound authentically like Orla³
- Leverage our competitive positioning and exploit content gaps

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

Remember: Create UNIQUE content based on the specific topic provided, applying Orla³'s brand strategy throughout."""

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
