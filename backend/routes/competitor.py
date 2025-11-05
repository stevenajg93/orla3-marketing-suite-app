from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor, Json as PgJson
from datetime import datetime
import anthropic
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

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
        logger.error(f"Error loading brand strategy: {e}")
        return None

def extract_json_from_text(text: str) -> dict:
    """Extract JSON from text that might be wrapped in markdown or other formatting"""
    text = text.strip()
    
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        parts = text.split("```")
        if len(parts) >= 3:
            text = parts[1].strip()
            if text.startswith("json\n"):
                text = text[5:]
    
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
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO competitors (name, industry, location, social_handles)
            VALUES (%s, %s, %s, %s)
            RETURNING id, name, industry, location, social_handles, added_at
        """, (
            competitor.name,
            competitor.industry,
            competitor.location,
            PgJson(competitor.handles.dict())
        ))
        
        competitor_data = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info(f"Added competitor: {competitor.name}")
        return {"success": True, "competitor": competitor_data}
        
    except Exception as e:
        logger.error(f"Error adding competitor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_competitors():
    """Get all tracked competitors with their analyses"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                c.*,
                ca.marketing_they_do_well,
                ca.gaps_they_miss as content_gaps,
                ca.positioning_messaging,
                ca.content_opportunities,
                ca.threat_level,
                ca.strategic_summary
            FROM competitors c
            LEFT JOIN competitor_analyses ca ON c.id = ca.competitor_id
            ORDER BY c.added_at DESC
        """)
        
        competitors = cur.fetchall()
        cur.close()
        conn.close()
        
        # Format response to match original structure
        formatted = []
        for comp in competitors:
            comp_dict = dict(comp)
            
            # Build analysis object if data exists
            if comp_dict.get('marketing_they_do_well'):
                comp_dict['analysis'] = {
                    'marketing_they_do_well': comp_dict.pop('marketing_they_do_well'),
                    'content_gaps': comp_dict.pop('content_gaps'),
                    'positioning_messaging': comp_dict.pop('positioning_messaging'),
                    'content_opportunities': comp_dict.pop('content_opportunities'),
                    'threat_level': comp_dict.pop('threat_level'),
                    'strategic_summary': comp_dict.pop('strategic_summary')
                }
            else:
                comp_dict['analysis'] = None
                comp_dict.pop('marketing_they_do_well', None)
                comp_dict.pop('content_gaps', None)
                comp_dict.pop('positioning_messaging', None)
                comp_dict.pop('content_opportunities', None)
                comp_dict.pop('threat_level', None)
                comp_dict.pop('strategic_summary', None)
            
            formatted.append(comp_dict)
        
        return {"competitors": formatted}
        
    except Exception as e:
        logger.error(f"Error listing competitors: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{competitor_id}")
async def delete_competitor(competitor_id: str):
    """Remove a competitor"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Delete competitor (cascade will delete analysis)
        cur.execute("DELETE FROM competitors WHERE id = %s", (competitor_id,))
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info(f"Deleted competitor: {competitor_id}")
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error deleting competitor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{competitor_id}/analyze")
async def analyze_competitor(competitor_id: str):
    """Run brand-aware MARKETING analysis on competitor"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get competitor
        cur.execute("SELECT * FROM competitors WHERE id = %s", (competitor_id,))
        competitor = cur.fetchone()
        
        if not competitor:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Competitor not found")
        
        competitor = dict(competitor)
        
        # Load brand strategy for context
        brand_strategy = load_brand_strategy()
        
        brand_context = ""
        if brand_strategy:
            brand_context = f"""
OUR BRAND (Orla³):
- Voice: {brand_strategy['brand_voice']['tone'] if isinstance(brand_strategy.get('brand_voice'), dict) else 'Professional'}
- Pillars: {', '.join(brand_strategy.get('messaging_pillars', []))}
- Target: {brand_strategy['target_audience']['primary'] if isinstance(brand_strategy.get('target_audience'), dict) else 'Creative professionals'}
"""
        
        # Call Claude API
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        prompt = f"""You are a CONTENT MARKETING analyst for Orla³, a videographer marketplace.

{brand_context}

COMPETITOR TO ANALYZE:
Name: {competitor['name']}
Industry: {competitor.get('industry', 'Unknown')}
Social: {json.dumps(competitor.get('social_handles', {}))}

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
        
        # Parse JSON
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
        
        # Save or update analysis in PostgreSQL
        # Check if analysis exists
        cur.execute("SELECT id FROM competitor_analyses WHERE competitor_id = %s", (competitor_id,))
        existing = cur.fetchone()
        
        if existing:
            # Update existing
            cur.execute("""
                UPDATE competitor_analyses
                SET marketing_they_do_well = %s,
                    gaps_they_miss = %s,
                    positioning_messaging = %s,
                    content_opportunities = %s,
                    threat_level = %s,
                    strategic_summary = %s,
                    raw_analysis = %s,
                    updated_at = NOW()
                WHERE competitor_id = %s
            """, (
                analysis.get('marketing_they_do_well', []),
                analysis.get('content_gaps', []),
                analysis.get('positioning_messaging'),
                analysis.get('content_opportunities', []),
                analysis.get('threat_level', 'unknown'),
                analysis.get('strategic_summary'),
                PgJson(analysis),
                competitor_id
            ))
        else:
            # Insert new
            cur.execute("""
                INSERT INTO competitor_analyses (
                    competitor_id, marketing_they_do_well, gaps_they_miss,
                    positioning_messaging, content_opportunities,
                    threat_level, strategic_summary, raw_analysis
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                competitor_id,
                analysis.get('marketing_they_do_well', []),
                analysis.get('content_gaps', []),
                analysis.get('positioning_messaging'),
                analysis.get('content_opportunities', []),
                analysis.get('threat_level', 'unknown'),
                analysis.get('strategic_summary'),
                PgJson(analysis)
            ))
        
        # Update competitor last_analyzed timestamp
        cur.execute("UPDATE competitors SET last_analyzed = NOW() WHERE id = %s", (competitor_id,))
        
        conn.commit()
        cur.close()
        conn.close()
        
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
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM competitors ORDER BY added_at DESC")
        competitors = cur.fetchall()
        cur.close()
        conn.close()
        
        if not competitors:
            return {"insights": "No competitors added yet. Add competitors to get insights."}
        
        # Load brand strategy
        brand_strategy = load_brand_strategy()
        
        brand_context = ""
        if brand_strategy:
            brand_context = f"""
OUR BRAND (Orla³):
- Voice: {brand_strategy['brand_voice']['tone'] if isinstance(brand_strategy.get('brand_voice'), dict) else 'Professional'}
- Pillars: {', '.join(brand_strategy.get('messaging_pillars', []))}
- Target: {brand_strategy['target_audience']['primary'] if isinstance(brand_strategy.get('target_audience'), dict) else 'Creative professionals'}
"""
        
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        competitor_summary = "\n".join([
            f"- {c['name']}: {c.get('industry', 'Unknown industry')}"
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
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT c.*, ca.*
            FROM competitors c
            LEFT JOIN competitor_analyses ca ON c.id = ca.competitor_id
            ORDER BY c.added_at DESC
        """)
        competitors = cur.fetchall()
        cur.close()
        conn.close()
        
        if not competitors:
            return {"success": False, "message": "No competitors added"}
        
        # Filter analyzed competitors
        analyzed = [c for c in competitors if c.get('marketing_they_do_well')]
        
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
            comp_name = comp['name']
            
            # Aggregate what they do well (marketing)
            if comp.get('marketing_they_do_well'):
                for item in comp['marketing_they_do_well']:
                    summary['marketing_they_do_well'].append(f"{comp_name}: {item}")
            
            # Aggregate content gaps
            if comp.get('gaps_they_miss'):
                for gap in comp['gaps_they_miss']:
                    summary['content_gaps'].append(gap)
            
            # Aggregate content opportunities
            if comp.get('content_opportunities'):
                summary['content_opportunities'].extend(comp['content_opportunities'])
            
            # Positioning messaging
            if comp.get('positioning_messaging'):
                summary['positioning_opportunities'].append({
                    'competitor': comp_name,
                    'positioning': comp['positioning_messaging']
                })
            
            # Threat level
            threat = comp.get('threat_level', 'unknown')
            if threat in summary['threat_assessment']:
                summary['threat_assessment'][threat].append(comp_name)
        
        return {"success": True, "summary": summary}
        
    except Exception as e:
        logger.error(f"Error getting competitor summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
