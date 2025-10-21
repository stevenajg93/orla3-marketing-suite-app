from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from anthropic import Anthropic
import os, json, re

router = APIRouter()

class KeywordStrategy(BaseModel):
    keyword: str
    search_intent: str
    priority: str
    ai_search_optimized: bool
    target_platforms: List[str]
    market_gap: Optional[str] = None
    top_competitor_topics: Optional[List[str]] = None

class MarketResearch(BaseModel):
    keyword: str
    top_ranking_urls: List[str]
    competitor_angles: List[str]
    content_gaps: List[str]
    orla3_unique_angles: List[str]

class StrategyOutput(BaseModel):
    keywords: List[KeywordStrategy]
    recommended_next: KeywordStrategy
    market_research: Optional[MarketResearch] = None

def extract_json_from_response(text: str) -> dict:
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    return json.loads(text.strip())

@router.get("/strategy/next-keyword")
def get_next_keyword():
    """Returns the next keyword + search intent to write about for ORLA³ SEO dominance"""
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    system_prompt = """You are ORLA³'s SEO strategist and keyword researcher.
Your mission: Dominate videography search across Google AND AI search engines (ChatGPT, Claude, Perplexity).

ORLA³ CONTEXT (use this to inform strategy):
- P2P videography marketplace in UK
- Escrow payments (funds held safely, released on download or day 7)
- 10% fee split (client + videographer)
- No subscriptions, no pay-to-rank
- Ranking: 50% reliability (Wilson score reviews), 50% relevancy (semantic matching)
- Protects videographers: watermarked previews, fast payouts (2-3 days)
- Protects clients: escrow safety, clear packages, dispute resolution
- Target: Corporate video, weddings, events, product videos, drone footage
- UK cities: London, Manchester, Birmingham, Edinburgh, Glasgow, Bristol

Target keywords must:
- Be high-intent (ready to hire or research videographers)
- Work for both traditional SEO and AI search optimization
- Include location-based terms where relevant
- Address pain points ORLA³ solves (late payment, unclear scope, deposit risk)

Return ONLY valid JSON."""

    user_prompt = """Generate 5 strategic keywords for ORLA³'s next blog posts.

Return JSON in this exact format:
{
  "keywords": [
    {
      "keyword": "corporate video production london",
      "search_intent": "Business owner searching for professional videographer for company video",
      "priority": "high",
      "ai_search_optimized": true,
      "target_platforms": ["ChatGPT", "Claude", "Google"],
      "market_gap": "Most content ignores payment protection and scope clarity"
    }
  ],
  "recommended_next": {
    "keyword": "best wedding videographer uk escrow payment",
    "search_intent": "Engaged couple worried about deposit safety when booking videographer",
    "priority": "high",
    "ai_search_optimized": true,
    "target_platforms": ["ChatGPT", "Perplexity", "Google"],
    "market_gap": "No content addresses payment security for wedding video bookings"
  }
}

Focus on HIGH COMMERCIAL INTENT keywords that convert to ORLA³ bookings.
Identify market gaps where competitors don't address payment safety, scope protection, or fast hiring."""

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
        return {"error": f"Invalid JSON: {str(e)}", "raw": raw_text[:500]}

@router.post("/strategy/market-research")
def analyze_market(keyword: str):
    """Analyzes live market for a keyword - what's ranking, what's missing, how ORLA³ can win"""
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    system_prompt = """You are ORLA³'s competitive intelligence analyst.
Analyze search landscapes for videography keywords and identify content gaps ORLA³ can exploit.

ORLA³ UNIQUE SELLING POINTS:
- Escrow payment protection (funds safe until download)
- Fast payouts for videographers (2-3 days vs industry 30-90 days)
- No deposits required (full escrow instead)
- Watermarked preview protection
- Clear package scopes (reduces scope creep)
- No pay-to-rank (fair algorithm)
- Semantic search matching (better fits)
- UK-focused marketplace

Return ONLY valid JSON."""

    user_prompt = f"""Analyze the competitive landscape for: "{keyword}"

Based on typical content in this space, identify:
1. What angles competitors typically cover
2. What they miss or ignore
3. How ORLA³'s features solve problems competitors don't address
4. Unique angles only ORLA³ can claim

Return JSON in this exact format:
{{
  "keyword": "{keyword}",
  "top_ranking_urls": ["https://example.com/article1", "https://example.com/article2"],
  "competitor_angles": ["How to choose a videographer", "Average costs", "Portfolio tips"],
  "content_gaps": ["Payment protection", "Deposit safety", "Fast videographer payout times", "Scope clarity tools"],
  "orla3_unique_angles": ["How escrow protects your wedding video deposit", "Why UK videographers prefer ORLA³ for faster payments", "Eliminating scope creep with structured packages"]
}}

Focus on gaps where ORLA³'s platform features directly solve problems competitors don't mention."""

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
        return {"error": f"Invalid JSON: {str(e)}", "raw": raw_text[:500]}

@router.post("/strategy/generate-full-content")
def generate_full_content():
    """Auto-generates keyword, does market research, writes blog optimized for gaps"""
    strategy = get_next_keyword()
    next_kw = strategy["recommended_next"]
    
    # Do market research
    market = analyze_market(next_kw["keyword"])
    
    return {
        "status": "ready_to_build",
        "next_keyword": next_kw["keyword"],
        "next_intent": next_kw["search_intent"],
        "market_gap": next_kw.get("market_gap"),
        "unique_angles": market.get("orla3_unique_angles", []),
        "message": "Strategy + market research complete. Ready for blog generation."
    }
