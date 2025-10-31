from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import json
import os
from datetime import datetime
import anthropic
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)

COMPETITOR_FILE = "competitor_data.json"
BRAND_STRATEGY_FILE = "brand_strategy.json"

class SocialHandles(BaseModel):
    instagram: Optional[str] = None
    linkedin: Optional[str] = None
    x: Optional[str] = None
    tiktok: Optional[str] = None
    youtube: Optional[str] = None

class Competitor(BaseModel):
    name: str
    handles: SocialHandles
    industry: Optional[str] = None
    location: Optional[str] = None

class CompetitorData(BaseModel):
    id: str
    name: str
    handles: SocialHandles
    industry: Optional[str] = None
    location: Optional[str] = None
    analysis: Optional[Dict] = None
    last_analyzed: Optional[str] = None
    added_at: str

def load_competitors():
    """Load competitors from JSON file"""
    if os.path.exists(COMPETITOR_FILE):
        with open(COMPETITOR_FILE, 'r') as f:
            return json.load(f)
    return {"competitors": []}

def save_competitors(data):
    """Save competitors to JSON file"""
    with open(COMPETITOR_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_brand_strategy():
    """Load brand strategy if it exists"""
    if os.path.exists(BRAND_STRATEGY_FILE):
        with open(BRAND_STRATEGY_FILE, 'r') as f:
            return json.load(f)
    return None

def extract_json_from_text(text: str) -> dict:
    """Extract JSON from text that might be wrapped in markdown or other formatting"""
    # Remove any leading/trailing whitespace
    text = text.strip()
    
    # Try to extract from markdown code blocks
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        # Generic code block
        parts = text.split("```")
        if len(parts) >= 3:
            text = parts[1].strip()
            # Remove language identifier if present
            if text.startswith("json\n"):
                text = text[5:]
    
    # Try to parse
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        logger.error(f"Text was: {text[:500]}")
        raise

@router.post("/add")
async def add_competitor(competitor: Competitor):
    """Add a new competitor to track"""
    try:
        data = load_competitors()
        
        # Generate unique ID
        competitor_id = f"comp_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        competitor_data = {
            "id": competitor_id,
            "name": competitor.name,
            "handles": competitor.handles.dict(),
            "industry": competitor.industry,
            "location": competitor.location,
            "analysis": None,
            "last_analyzed": None,
            "added_at": datetime.now().isoformat()
        }
        
        data["competitors"].append(competitor_data)
        save_competitors(data)
        
        logger.info(f"Added competitor: {competitor.name}")
        return {"success": True, "competitor": competitor_data}
        
    except Exception as e:
        logger.error(f"Error adding competitor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_competitors():
    """Get all tracked competitors"""
    try:
        data = load_competitors()
        return {"competitors": data["competitors"]}
    except Exception as e:
        logger.error(f"Error listing competitors: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{competitor_id}")
async def delete_competitor(competitor_id: str):
    """Remove a competitor"""
    try:
        data = load_competitors()
        data["competitors"] = [c for c in data["competitors"] if c["id"] != competitor_id]
        save_competitors(data)
        
        logger.info(f"Deleted competitor: {competitor_id}")
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error deleting competitor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{competitor_id}/analyze")
async def analyze_competitor(competitor_id: str):
    """Run brand-aware MARKETING analysis on competitor"""
    try:
        data = load_competitors()
        competitor = next((c for c in data["competitors"] if c["id"] == competitor_id), None)
        
        if not competitor:
            raise HTTPException(status_code=404, detail="Competitor not found")
        
        # Load brand strategy for context
        brand_strategy = load_brand_strategy()
        
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Build brand context if available
        brand_context = ""
        if brand_strategy:
            brand_context = f"""
OUR BRAND (Orla³):
- Voice & Tone: {brand_strategy['brand_voice']['tone']}
- Personality: {', '.join(brand_strategy['brand_voice']['personality'])}
- Messaging Pillars: {', '.join(brand_strategy['messaging_pillars'])}
- Target Audience: {brand_strategy['target_audience']['primary']}
- Key Differentiators: {', '.join(brand_strategy['brand_voice']['key_characteristics'])}
"""
        else:
            brand_context = """
OUR BRAND (Orla³):
- Video production marketplace
- Professional videographers
- Quality-focused, community-driven
"""
        
        prompt = f"""You are a MARKETING strategist analyzing a competitor's CONTENT & MESSAGING strategy for Orla³.

{brand_context}

COMPETITOR TO ANALYZE:
Name: {competitor['name']}
Industry: {competitor.get('industry', 'Unknown')}
Social Media Presence:
- Instagram: {competitor['handles'].get('instagram', 'N/A')}
- LinkedIn: {competitor['handles'].get('linkedin', 'N/A')}
- X/Twitter: {competitor['handles'].get('x', 'N/A')}
- TikTok: {competitor['handles'].get('tiktok', 'N/A')}
- YouTube: {competitor['handles'].get('youtube', 'N/A')}

CRITICAL: This is a MARKETING ANALYSIS ONLY. Focus ONLY on:
- Content strategy (topics, themes, formats)
- Messaging & positioning (how they talk about themselves)
- Brand voice & tone (writing style, personality)
- Marketing tactics (social strategy, content types, SEO focus)

DO NOT analyze:
- Product features or business models
- Operational processes
- Pricing strategies
- Technical implementations

Analyze their MARKETING through the lens of Orla³'s positioning:

1. **marketing_they_do_well**: What CONTENT/MESSAGING strategies are working for them that we could adapt to our voice
2. **content_gaps**: What TOPICS or CONTENT TYPES are they not covering that Orla³ could own
3. **positioning_messaging**: How should Orla³ MESSAGE differently compared to their positioning
4. **content_opportunities**: Specific CONTENT IDEAS and MESSAGING ANGLES that exploit their weaknesses
5. **threat_level**: How directly do they compete with us in MARKETING/MESSAGING (direct/indirect/minimal)

Return ONLY valid JSON with these exact keys. Do not wrap in markdown code blocks:
{{
  "marketing_they_do_well": ["content/messaging point1", "content/messaging point2", "content/messaging point3"],
  "content_gaps": ["content gap1", "content gap2", "content gap3"],
  "positioning_messaging": "How Orla³ should MESSAGE differently (not build differently)",
  "content_opportunities": ["content idea1", "content idea2", "content idea3"],
  "threat_level": "direct|indirect|minimal",
  "strategic_summary": "2-3 sentence MARKETING strategy summary"
}}"""

        logger.info(f"Calling Claude API for {competitor['name']}...")
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        
        analysis_text = message.content[0].text
        
        logger.info(f"Claude response received: {len(analysis_text)} chars")
        logger.info(f"First 200 chars: {analysis_text[:200]}")
        
        # Try to parse as JSON with improved extraction
        try:
            analysis = extract_json_from_text(analysis_text)
            logger.info(f"Successfully parsed JSON with keys: {list(analysis.keys())}")
        except Exception as parse_error:
            logger.error(f"Failed to parse competitor analysis as JSON: {parse_error}")
            analysis = {
                "insights": analysis_text,
                "threat_level": "unknown",
                "strategic_summary": "Analysis format error - please re-analyze"
            }
        
        # Update competitor with analysis
        competitor["analysis"] = analysis
        competitor["last_analyzed"] = datetime.now().isoformat()
        
        save_competitors(data)
        
        logger.info(f"✅ Analyzed competitor: {competitor['name']}")
        return {"success": True, "analysis": analysis}
        
    except Exception as e:
        logger.error(f"Error analyzing competitor: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights")
async def get_insights():
    """Get overall competitive MARKETING insights across all competitors"""
    try:
        data = load_competitors()
        competitors = data["competitors"]
        
        if not competitors:
            return {"insights": "No competitors added yet. Add competitors to get insights."}
        
        # Load brand strategy
        brand_strategy = load_brand_strategy()
        
        # Build brand context
        brand_context = ""
        if brand_strategy:
            brand_context = f"""
OUR BRAND (Orla³):
- Voice: {brand_strategy['brand_voice']['tone']}
- Pillars: {', '.join(brand_strategy['messaging_pillars'])}
- Target: {brand_strategy['target_audience']['primary']}
"""
        
        # Use Claude to generate strategic insights
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        competitor_summary = "\n".join([
            f"- {c['name']}: {c.get('industry', 'Unknown industry')} (Threat: {c.get('analysis', {}).get('threat_level', 'not analyzed')})"
            for c in competitors
        ])
        
        prompt = f"""You are a CONTENT MARKETING strategist for Orla³.

{brand_context}

COMPETITORS:
{competitor_summary}

Based on our brand positioning and these competitors, provide 5 actionable CONTENT & MARKETING recommendations:

FOCUS ONLY ON:
- Content strategy (topics, formats, channels)
- Messaging & positioning
- Brand voice differentiation
- Content calendar priorities
- Marketing tactics

DO NOT recommend:
- Product features
- Business model changes
- Operational improvements
- Pricing strategies

Provide tactical MARKETING recommendations:
1. What CONTENT/MESSAGING should we COPY (adapted to our voice)?
2. What CONTENT GAPS should we exploit?
3. How should we MESSAGE differently?
4. What content themes to PRIORITIZE?
5. What competitive MESSAGING THREATS to watch?

Be specific and tactical about CONTENT & MARKETING only."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        insights = message.content[0].text
        
        return {"success": True, "insights": insights, "competitor_count": len(competitors)}
        
    except Exception as e:
        logger.error(f"Error getting insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary")
async def get_competitor_summary():
    """Get structured summary of all competitor MARKETING analyses for Strategy Planner"""
    try:
        data = load_competitors()
        competitors = data["competitors"]
        
        if not competitors:
            return {"success": False, "message": "No competitors added"}
        
        # Filter analyzed competitors
        analyzed = [c for c in competitors if c.get('analysis')]
        
        if not analyzed:
            return {"success": False, "message": "No competitors analyzed yet"}
        
        # Aggregate insights
        summary = {
            "total_competitors": len(competitors),
            "analyzed_count": len(analyzed),
            "marketing_they_do_well": [],
            "content_gaps": [],
            "positioning_opportunities": [],
            "content_opportunities": [],
            "threat_assessment": {
                "direct": [],
                "indirect": [],
                "minimal": []
            }
        }
        
        for comp in analyzed:
            analysis = comp.get('analysis', {})
            comp_name = comp['name']
            
            # Aggregate what they do well (marketing)
            if 'marketing_they_do_well' in analysis:
                for item in analysis['marketing_they_do_well']:
                    summary['marketing_they_do_well'].append(f"{comp_name}: {item}")
            
            # Aggregate content gaps
            if 'content_gaps' in analysis:
                for gap in analysis['content_gaps']:
                    summary['content_gaps'].append(gap)
            
            # Aggregate content opportunities
            if 'content_opportunities' in analysis:
                summary['content_opportunities'].extend(analysis['content_opportunities'])
            
            # Positioning messaging
            if 'positioning_messaging' in analysis:
                summary['positioning_opportunities'].append({
                    'competitor': comp_name,
                    'positioning': analysis['positioning_messaging']
                })
            
            # Threat level
            threat = analysis.get('threat_level', 'unknown')
            if threat in summary['threat_assessment']:
                summary['threat_assessment'][threat].append(comp_name)
        
        return {"success": True, "summary": summary}
        
    except Exception as e:
        logger.error(f"Error getting competitor summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
