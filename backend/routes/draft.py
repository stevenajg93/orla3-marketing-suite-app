from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from anthropic import Anthropic
import os, json

router = APIRouter()

class DraftInput(BaseModel):
    keyword: str
    search_intent: str
    outline: Optional[str] = None
    entities: Optional[List[str]] = None
    competitor_notes: Optional[str] = None
    brand_tone_rules: Optional[str] = None
    target_length_words: Optional[int] = 1500
    internal_links: Optional[list] = None
    external_links_allowlist: Optional[list] = None

class CTA(BaseModel):
    headline: str
    button_label: str
    url: str

class DraftOutput(BaseModel):
    title: str
    slug: str
    meta_title: str
    meta_description: str
    og_title: str
    og_description: str
    tags: List[str]
    category: str
    estimated_read_time_min: int
    body_md: str
    cta: CTA
    internal_links_used: Optional[list] = None
    sources: Optional[List[str]] = None

@router.post("/content/draft", response_model=DraftOutput)
def generate_draft(data: DraftInput):
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    prompt = f"""
You are Orla3’s senior content writer and SEO strategist.
Write authoritative, cinematic, practical longform content for videography buyers and sellers.
Respect UK English. Enforce Orla brand tone via centroid guidance.

Input summary:
Keyword: {data.keyword}
Intent: {data.search_intent}
Outline: {data.outline}
Entities: {data.entities}
Competitor Notes: {data.competitor_notes}
Brand Tone Rules: {data.brand_tone_rules}

Return ONLY valid JSON matching A.schema.
    """

    completion = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    try:
        content = json.loads(completion.content[0].text)
        return content
    except Exception as e:
        return {"error": f"Invalid JSON: {str(e)}", "raw": completion.content[0].text}
