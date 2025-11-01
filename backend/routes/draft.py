from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from anthropic import Anthropic
import os, json, re

router = APIRouter()

BRAND_STRATEGY_FILE = "brand_strategy.json"

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

def load_brand_strategy():
    """Load brand strategy if it exists"""
    if os.path.exists(BRAND_STRATEGY_FILE):
        with open(BRAND_STRATEGY_FILE, 'r') as f:
            return json.load(f)
    return None

def build_brand_context(strategy: dict) -> str:
    """Build brand context string from strategy"""
    if not strategy:
        return ""
    
    context = "\n\n=== ORLA³ BRAND STRATEGY (CRITICAL - FOLLOW EXACTLY) ===\n"
    
    # Brand Voice
    context += f"\nBRAND VOICE & TONE:\n{strategy['brand_voice']['tone']}\n"
    context += f"\nPERSONALITY TRAITS: {', '.join(strategy['brand_voice']['personality'])}\n"
    context += f"KEY CHARACTERISTICS: {', '.join(strategy['brand_voice']['key_characteristics'])}\n"
    
    # Messaging Pillars
    context += f"\nMESSAGING PILLARS (weave these into content):\n"
    for i, pillar in enumerate(strategy['messaging_pillars'], 1):
        context += f"{i}. {pillar}\n"
    
    # Language Patterns
    context += f"\nWRITING STYLE:\n{strategy['language_patterns']['writing_style']}\n"
    context += f"\nPREFERRED PHRASES: {', '.join(strategy['language_patterns']['preferred_phrases'])}\n"
    context += f"KEY VOCABULARY: {', '.join(strategy['language_patterns']['vocabulary'])}\n"
    
    # Do's and Don'ts
    context += f"\nDO:\n"
    for do in strategy['dos_and_donts']['dos']:
        context += f"✓ {do}\n"
    context += f"\nDON'T:\n"
    for dont in strategy['dos_and_donts']['donts']:
        context += f"✗ {dont}\n"
    
    # Target Audience
    context += f"\nTARGET AUDIENCE:\n{strategy['target_audience']['primary']}\n"
    context += f"CHARACTERISTICS: {', '.join(strategy['target_audience']['characteristics'])}\n"
    
    # Competitive Positioning (if available)
    if 'competitive_positioning' in strategy:
        comp_pos = strategy['competitive_positioning']
        context += f"\n=== COMPETITIVE POSITIONING ===\n"
        context += f"\nOUR UNIQUE VALUE:\n{comp_pos['unique_value']}\n"
        
        if comp_pos.get('copy_and_adapt'):
            context += f"\nADAPT THESE SUCCESSFUL TACTICS (in our voice):\n"
            for item in comp_pos['copy_and_adapt'][:3]:
                context += f"• {item}\n"
        
        if comp_pos.get('gaps_to_exploit'):
            context += f"\nCONTENT GAPS TO EXPLOIT:\n"
            for gap in comp_pos['gaps_to_exploit'][:3]:
                context += f"• {gap}\n"
        
        if comp_pos.get('avoid'):
            context += f"\nAVOID (competitor mistakes):\n"
            for avoid in comp_pos['avoid'][:2]:
                context += f"✗ {avoid}\n"
    
    context += "\n=== END BRAND STRATEGY ===\n\n"
    
    return context

def extract_json_from_response(text: str) -> dict:
    """Extract JSON from Claude's response, handling markdown code blocks"""
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()
    return json.loads(text)

@router.post("/content/draft", response_model=DraftOutput)
def generate_draft(data: DraftInput):
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    # Load brand strategy
    strategy = load_brand_strategy()
    brand_context = build_brand_context(strategy) if strategy else ""
    
    system_prompt = f"""You are Orla3's senior content writer and SEO strategist.
Write authoritative, cinematic, practical longform content for videography buyers and sellers.
Respect UK English. Return ONLY valid JSON matching the exact schema provided - no markdown, no code blocks, just pure JSON.

{brand_context}

CRITICAL WRITING RULES TO SOUND HUMAN:
- Write naturally like a seasoned expert, not an AI
- NO asterisks for emphasis - use strong word choice instead
- ABSOLUTE RULE: NO hashtags (#) anywhere in the content
- ABSOLUTE RULE: NO Markdown headers (##, ###, ####) - use PLAIN TEXT ONLY with blank lines between sections
- NO bullet points with hyphens at the start of paragraphs
- Use section breaks with blank lines, NOT header symbols
- Use varied sentence structures and lengths
- Include specific examples and real scenarios
- Write with confidence and authority
- Avoid corporate jargon and buzzwords
- Use contractions naturally (don't, can't, won't)
- Write like you're having an informed conversation with a colleague
- Use active voice predominantly
- Vary paragraph lengths for natural rhythm

BRAND VOICE COMPLIANCE:
- Every sentence must reflect Orla³'s tone, personality, and messaging pillars
- Use the preferred phrases and vocabulary naturally throughout
- Position content according to our competitive strategy
- Exploit content gaps our competitors are missing
- Write for our specific target audience with their characteristics in mind"""
    
    user_prompt = f"""Generate a blog article with these inputs:
- Keyword: {data.keyword}
- Search Intent: {data.search_intent}
- Outline: {data.outline}
- Target Length: {data.target_length_words} words

CRITICAL: Apply Orla³'s brand strategy throughout the entire article. This content must sound authentically like Orla³ and leverage our competitive positioning.

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
