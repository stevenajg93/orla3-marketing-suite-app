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
    """Run AI analysis on competitor (placeholder for now)"""
    try:
        data = load_competitors()
        competitor = next((c for c in data["competitors"] if c["id"] == competitor_id), None)
        
        if not competitor:
            raise HTTPException(status_code=404, detail="Competitor not found")
        
        # Placeholder analysis - we'll implement real scraping later
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        prompt = f"""Analyze this competitor and provide strategic insights:

Competitor: {competitor['name']}
Industry: {competitor.get('industry', 'Unknown')}
Social Media:
- Instagram: {competitor['handles'].get('instagram', 'N/A')}
- LinkedIn: {competitor['handles'].get('linkedin', 'N/A')}
- X/Twitter: {competitor['handles'].get('x', 'N/A')}

Provide:
1. Likely content themes they focus on
2. Recommended content gaps to exploit
3. Platform strategy suggestions
4. Engagement tactics to consider

Format as JSON with keys: content_themes, content_gaps, platform_strategy, engagement_tactics"""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        
        analysis_text = message.content[0].text
        
        # Try to parse as JSON, fallback to text
        try:
            analysis = json.loads(analysis_text)
        except:
            analysis = {"insights": analysis_text}
        
        # Update competitor with analysis
        competitor["analysis"] = analysis
        competitor["last_analyzed"] = datetime.now().isoformat()
        
        save_competitors(data)
        
        logger.info(f"Analyzed competitor: {competitor['name']}")
        return {"success": True, "analysis": analysis}
        
    except Exception as e:
        logger.error(f"Error analyzing competitor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights")
async def get_insights():
    """Get overall competitive insights across all competitors"""
    try:
        data = load_competitors()
        competitors = data["competitors"]
        
        if not competitors:
            return {"insights": "No competitors added yet. Add competitors to get insights."}
        
        # Use Claude to generate strategic insights
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        competitor_summary = "\n".join([
            f"- {c['name']}: {c.get('industry', 'Unknown industry')}"
            for c in competitors
        ])
        
        prompt = f"""You are a marketing strategist. Based on these competitors:

{competitor_summary}

Provide 5 actionable recommendations for differentiating and competing effectively. Be specific and tactical."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        insights = message.content[0].text
        
        return {"insights": insights, "competitor_count": len(competitors)}
        
    except Exception as e:
        logger.error(f"Error getting insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
