from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from anthropic import Anthropic
import os, json, re

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

def extract_json_from_response(text: str) -> dict:
    """Extract JSON from Claude's response, handling markdown code blocks"""
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()
    return json.loads(text)

@router.post("/content/draft", response_model=DraftOutput)
def generate_draft(data: DraftInput):
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    system_prompt = """You are Orla3's senior content writer and SEO strategist.
Write authoritative, cinematic, practical longform content for videography buyers and sellers.
Respect UK English. Return ONLY valid JSON matching the exact schema provided - no markdown, no code blocks, just pure JSON.

CRITICAL WRITING RULES TO SOUND HUMAN:
- Write naturally like a seasoned expert, not an AI
- NO asterisks for emphasis - use strong word choice instead
- NO hashtags anywhere in the content
- NO bullet points with hyphens at the start of paragraphs
- Use varied sentence structures and lengths
- Include specific examples and real scenarios
- Write with confidence and authority
- Avoid corporate jargon and buzzwords
- Use contractions naturally (don't, can't, won't)
- Write like you're having an informed conversation with a colleague
- Use active voice predominantly
- Vary paragraph lengths for natural rhythm"""
    
    user_prompt = f"""Generate a blog article with these inputs:
- Keyword: {data.keyword}
- Search Intent: {data.search_intent}
- Outline: {data.outline}
- Target Length: {data.target_length_words} words

Return ONLY a JSON object with these exact fields:
{{
  "title": "SEO-optimized title",
  "slug": "kebab-case-slug",
  "meta_title": "60 chars max",
  "meta_description": "155 chars max",
  "og_title": "Same as meta_title",
  "og_description": "Same as meta_description",
  "tags": ["tag1", "tag2", "tag3"],
  "category": "Videography",
  "estimated_read_time_min": 5,
  "body_md": "Full markdown content here",
  "cta": {{
    "headline": "Ready to find your perfect videographer?",
    "button_label": "Browse Orla3",
    "url": "https://orla3.com"
  }},
  "internal_links_used": [],
  "sources": []
}}

Write the article now. Return ONLY the JSON, nothing else."""

    completion = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )

    try:
        raw_text = completion.content[0].text
        content = extract_json_from_response(raw_text)
        return content
    except json.JSONDecodeError as e:
        return {
            "error": f"Invalid JSON: {str(e)}",
            "raw": completion.content[0].text[:500]
        }
