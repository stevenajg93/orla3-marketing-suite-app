from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Literal
from anthropic import Anthropic
import os, json, re

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

class CarouselOutput(BaseModel):
    platform: str
    slides: List[Slide]

def extract_json_from_response(text: str) -> dict:
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()
    return json.loads(text)

@router.post("/social/carousel", response_model=CarouselOutput)
def generate_carousel(data: CarouselInput):
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    system_prompt = """You create platform-native carousels that teach, persuade, and convert.
Return JSON ONLY. Each slide has a role and copy. No images generated here.
Return pure JSON without markdown code blocks."""
    
    user_prompt = f"""Create a 7-slide carousel for {data.target_platform}:

Content summary: {data.post_summary}
Brand tone: {data.brand_tone_rules}
Angle: {data.angle}
CTA URL: {data.cta_url}

Produce 7 slides with these exact roles:
1. HOOK - Grab attention immediately
2. CONTEXT - Set up the problem/topic
3. INSIGHT_1 - First key insight
4. INSIGHT_2 - Second key insight
5. INSIGHT_3 - Third key insight
6. HOW_TO - Actionable steps
7. CTA - Call to action

Each slide needs:
- title (short, punchy, max 6 words)
- body (concise copy, 2-3 sentences max)
- alt_hint (design notes: "Bold title, dark bg" etc)

Return ONLY this JSON:
{{
  "platform": "{data.target_platform}",
  "slides": [
    {{"id": 1, "role": "HOOK", "title": "string", "body": "string", "alt_hint": "string"}},
    {{"id": 2, "role": "CONTEXT", "title": "string", "body": "string", "alt_hint": "string"}},
    {{"id": 3, "role": "INSIGHT_1", "title": "string", "body": "string", "alt_hint": "string"}},
    {{"id": 4, "role": "INSIGHT_2", "title": "string", "body": "string", "alt_hint": "string"}},
    {{"id": 5, "role": "INSIGHT_3", "title": "string", "body": "string", "alt_hint": "string"}},
    {{"id": 6, "role": "HOW_TO", "title": "string", "body": "string", "alt_hint": "string"}},
    {{"id": 7, "role": "CTA", "title": "string", "body": "string", "alt_hint": "string"}}
  ]
}}"""

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
