from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from anthropic import Anthropic
import os, json, re
import psycopg2
from psycopg2.extras import RealDictCursor

router = APIRouter()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

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

class FAQItem(BaseModel):
    question: str
    answer: str

class SchemaMarkup(BaseModel):
    article_schema: dict
    faq_schema: Optional[dict] = None

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
    faq: Optional[List[FAQItem]] = None
    schema_markup: Optional[SchemaMarkup] = None
    people_also_ask: Optional[List[str]] = None
    key_takeaways: Optional[List[str]] = None
    internal_links_used: Optional[list] = None
    sources: Optional[List[str]] = None


def load_brand_strategy():
    """Load brand strategy from PostgreSQL"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("SELECT * FROM brand_strategy ORDER BY created_at DESC LIMIT 1")
                strategy = cur.fetchone()
                return dict(strategy) if strategy else None
            finally:
                cur.close()
    except Exception as e:
        print(f"Error loading brand strategy: {e}")
        return None

def build_brand_context(strategy: dict) -> str:
    """Build brand context string from strategy"""
    if not strategy:
        return ""
    
    context = "\n\n=== ORLA³ BRAND STRATEGY (CRITICAL - FOLLOW EXACTLY) ===\n"
    
    # Handle JSONB fields that might be dicts or need parsing
    brand_voice = strategy.get('brand_voice', {})
    if isinstance(brand_voice, str):
        brand_voice = json.loads(brand_voice)
    
    language_patterns = strategy.get('language_patterns', {})
    if isinstance(language_patterns, str):
        language_patterns = json.loads(language_patterns)
    
    dos_and_donts = strategy.get('dos_and_donts', {})
    if isinstance(dos_and_donts, str):
        dos_and_donts = json.loads(dos_and_donts)
    
    target_audience = strategy.get('target_audience', {})
    if isinstance(target_audience, str):
        target_audience = json.loads(target_audience)
    
    competitive_positioning = strategy.get('competitive_positioning', {})
    if isinstance(competitive_positioning, str):
        competitive_positioning = json.loads(competitive_positioning)
    
    # Brand Voice
    context += f"\nBRAND VOICE & TONE:\n{brand_voice.get('tone', '')}\n"
    context += f"\nPERSONALITY TRAITS: {', '.join(brand_voice.get('personality', []))}\n"
    context += f"KEY CHARACTERISTICS: {', '.join(brand_voice.get('key_characteristics', []))}\n"
    
    # Messaging Pillars
    context += f"\nMESSAGING PILLARS (weave these into content):\n"
    for i, pillar in enumerate(strategy.get('messaging_pillars', []), 1):
        context += f"{i}. {pillar}\n"
    
    # Language Patterns
    context += f"\nWRITING STYLE:\n{language_patterns.get('writing_style', '')}\n"
    context += f"\nPREFERRED PHRASES: {', '.join(language_patterns.get('preferred_phrases', []))}\n"
    context += f"KEY VOCABULARY: {', '.join(language_patterns.get('vocabulary', []))}\n"
    
    # Do's and Don'ts
    context += f"\nDO:\n"
    for do in dos_and_donts.get('dos', []):
        context += f"✓ {do}\n"
    context += f"\nDON'T:\n"
    for dont in dos_and_donts.get('donts', []):
        context += f"✗ {dont}\n"
    
    # Target Audience
    context += f"\nTARGET AUDIENCE:\n{target_audience.get('primary', '')}\n"
    context += f"CHARACTERISTICS: {', '.join(target_audience.get('characteristics', []))}\n"
    
    # Competitive Positioning
    if competitive_positioning:
        context += f"\n=== COMPETITIVE POSITIONING ===\n"
        context += f"\nOUR UNIQUE VALUE:\n{competitive_positioning.get('unique_value', '')}\n"
        
        if competitive_positioning.get('copy_and_adapt'):
            context += f"\nADAPT THESE SUCCESSFUL TACTICS (in our voice):\n"
            for item in competitive_positioning.get('copy_and_adapt', [])[:3]:
                context += f"• {item}\n"
        
        if competitive_positioning.get('gaps_to_exploit'):
            context += f"\nCONTENT GAPS TO EXPLOIT:\n"
            for gap in competitive_positioning.get('gaps_to_exploit', [])[:3]:
                context += f"• {gap}\n"
        
        if competitive_positioning.get('avoid'):
            context += f"\nAVOID (competitor mistakes):\n"
            for avoid in competitive_positioning.get('avoid', [])[:2]:
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
    
    # Load brand strategy from PostgreSQL
    strategy = load_brand_strategy()
    brand_context = build_brand_context(strategy) if strategy else ""
    
    system_prompt = f"""You are Orla3's senior content writer and AI search optimization expert.
Write authoritative, cinematic, practical longform content optimized for BOTH traditional SEO AND AI search engines (ChatGPT, Perplexity, Google AI Overview).
Respect UK English. Return ONLY valid JSON matching the exact schema provided - no markdown, no code blocks, just pure JSON.

{brand_context}

CRITICAL WRITING RULES TO SOUND HUMAN:
- Write naturally like a seasoned expert, not an AI
- NO asterisks for emphasis - use strong word choice instead
- ABSOLUTE RULE: NO hashtags (#) anywhere in the content
- NO elongated hyphens or bullet points with hyphens at the start of paragraphs
- Use H2 headers (##) ONLY for main section titles - keep them natural and conversational
- Use varied sentence structures and lengths
- Include specific examples with real numbers and dates (especially 2025 data)
- Write with confidence and authority
- Avoid corporate jargon and buzzwords
- Use contractions naturally (don't, can't, won't)
- Write like you're having an informed conversation with a colleague
- Use active voice predominantly
- Vary paragraph lengths for natural rhythm

AI SEARCH OPTIMIZATION (CRITICAL):
1. ANSWER-FIRST FORMAT: Start each main section with a direct, citation-worthy answer (40-60 words) that AI can extract
2. NATURAL QUESTION INTEGRATION: Embed questions conversationally in text, not as formal headers
3. SPECIFIC NUMBERS & DATA: Include prices, percentages, timeframes (e.g., "UK videographers charge £800-£3000 in 2025")
4. AUTHORITY SIGNALS: Use phrases like "Based on industry data", "In our experience", "According to UK market trends"
5. SEMANTIC RICHNESS: Use related terms naturally (videographer → video producer, filmmaker, content creator)
6. COMPARISON TABLES: When comparing options, use markdown tables (AI engines extract these easily)
7. STEP-BY-STEP GUIDANCE: Number steps naturally in paragraphs, not as lists
8. CURRENT YEAR: Mention "2025" or "current" to signal recency
9. QUOTABLE SNIPPETS: Craft 2-3 sentence answers that AI can quote directly
10. COMPREHENSIVE COVERAGE: Address related questions users might ask

BRAND VOICE COMPLIANCE:
- Every sentence must reflect Orla³'s tone, personality, and messaging pillars
- Use the preferred phrases and vocabulary naturally throughout
- Position content according to our competitive strategy
- Exploit content gaps our competitors are missing
- Write for our specific target audience with their characteristics in mind"""
    
    user_prompt = f"""Generate an AI-search-optimized blog article with these inputs:
- Keyword: {data.keyword}
- Search Intent: {data.search_intent}
- Outline: {data.outline}
- Target Length: {data.target_length_words} words

CRITICAL: Apply Orla³'s brand strategy throughout. This content must sound authentically like Orla³ and leverage our competitive positioning.

STRUCTURE FOR MAXIMUM AI VISIBILITY:

1. OPENING PARAGRAPH (Answer-First):
   - Lead with a direct 40-60 word answer to the main question
   - Include the keyword naturally
   - Mention 2025 or current year for recency
   - Make it quotable for AI extraction

2. BODY SECTIONS (Use H2 headers):
   - Each section starts with a clear, quotable answer
   - Embed related questions naturally in the text
   - Include specific data: prices, percentages, timeframes
   - Use comparison tables where relevant (markdown tables)
   - Add authority signals: "Based on...", "Industry data shows..."
   - Cover semantic variations of the keyword

3. FAQ SECTION (Critical for AI Search):
   - 5-7 natural, conversational questions people actually ask
   - Each answer 40-60 words (perfect for AI extraction)
   - Questions should be long-tail searches (e.g., "How much does a wedding videographer cost in London in 2025?")

4. KEY TAKEAWAYS:
   - 3-5 bullet points summarizing main insights
   - Written as complete sentences, not fragments
   - Quotable and shareable

Return ONLY a JSON object with these exact fields:
{{
  "title": "SEO-optimized title with year if relevant",
  "slug": "kebab-case-slug",
  "meta_title": "60 chars max, include keyword",
  "meta_description": "155 chars max, answer-first format",
  "og_title": "Same as meta_title",
  "og_description": "Same as meta_description",
  "tags": ["primary-keyword", "semantic-variation-1", "semantic-variation-2"],
  "category": "Videography",
  "estimated_read_time_min": 5,
  "body_md": "Full markdown with H2 headers, tables, natural questions, quotable answers",
  "faq": [
    {{
      "question": "Natural long-tail question?",
      "answer": "Direct 40-60 word answer with specifics"
    }}
  ],
  "schema_markup": {{
    "article_schema": {{
      "@context": "https://schema.org",
      "@type": "Article",
      "headline": "Article title",
      "author": {{
        "@type": "Organization",
        "name": "Orla³"
      }},
      "datePublished": "2025-11-07",
      "description": "Meta description"
    }},
    "faq_schema": {{
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "mainEntity": [
        {{
          "@type": "Question",
          "name": "Question text",
          "acceptedAnswer": {{
            "@type": "Answer",
            "text": "Answer text"
          }}
        }}
      ]
    }}
  }},
  "people_also_ask": ["Related question 1?", "Related question 2?", "Related question 3?"],
  "key_takeaways": ["Takeaway 1 as complete sentence", "Takeaway 2 as complete sentence"],
  "cta": {{
    "headline": "Ready to find your perfect videographer?",
    "button_label": "Browse Orla3",
    "url": "https://orla3.com"
  }},
  "internal_links_used": [],
  "sources": ["https://source1.com", "https://source2.com"]
}}

Write the article now. Make every paragraph quotable for AI. Return ONLY the JSON, nothing else."""

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
