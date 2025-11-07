from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Literal
from anthropic import Anthropic
import os, json, re
from openai import OpenAI

router = APIRouter()

class GSCRow(BaseModel):
    url: str
    query: str
    position: float
    clicks_delta_28d: int
    impressions_delta_28d: int

class GA4Data(BaseModel):
    url: str
    sessions_28d: int
    avg_engagement_time: int

class InventoryItem(BaseModel):
    slug: str
    last_updated: str
    primary_keyword: str

class RefreshInput(BaseModel):
    gsc_rows: List[GSCRow]
    ga4: List[GA4Data]
    inventory: List[InventoryItem]

class RefreshCandidate(BaseModel):
    url: str
    query: str
    avg_position: float
    recommended_action: Literal["refresh_draft", "internal_link_boost", "add_faq", "expand_EEAT", "new_video_embed", "add_schema"]
    rationale: str
    target_entities: List[str]

class RefreshOutput(BaseModel):
    candidates: List[RefreshCandidate]

def extract_json_from_response(text: str) -> dict:
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()
    return json.loads(text)

@router.post("/analytics/refresh", response_model=RefreshOutput)
def detect_refresh_candidates(data: RefreshInput):
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    system_prompt = """You detect content sitting on SERP positions 8-15 and propose refresh/boost actions.
Return deterministic JSON. No free text. Return pure JSON without markdown code blocks."""
    
    # Filter positions 8-15
    candidates = [row for row in data.gsc_rows if 8 <= row.position <= 15]
    
    if not candidates:
        return {"candidates": []}
    
    # Limit to top 10 opportunities
    candidates = sorted(candidates, key=lambda x: (x.impressions_delta_28d, -x.position), reverse=True)[:10]
    
    user_prompt = f"""Analyze these content pieces currently ranking 8-15 in Google:

{json.dumps([c.dict() for c in candidates], indent=2)}

For each URL, suggest ONE action from:
- refresh_draft (rewrite with fresh info)
- internal_link_boost (add internal links)
- add_faq (add FAQ schema)
- expand_EEAT (add expertise signals)
- new_video_embed (add video content)
- add_schema (add structured data)

Provide rationale and 2-3 target entities to add.

Return ONLY this JSON:
{{
  "candidates": [
    {{
      "url": "string",
      "query": "string",
      "avg_position": 10.5,
      "recommended_action": "add_faq",
      "rationale": "string",
      "target_entities": ["entity1", "entity2"]
    }}
  ]
}}"""

    # Use GPT-4o-mini for SEO analytics
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise HTTPException(status_code=503, detail="OpenAI API not configured")

    openai_client = OpenAI(api_key=openai_key)

    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=2000
    )

    try:
        raw_text = completion.choices[0].message.content
        content = extract_json_from_response(raw_text)
        return content
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}", "raw": raw_text[:500]}
