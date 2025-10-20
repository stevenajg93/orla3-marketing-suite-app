from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from anthropic import Anthropic
import os, json, re

router = APIRouter()

class CompetitorProfile(BaseModel):
    id: str
    name: str
    platform: str
    profile_url: str
    last_scraped_at: Optional[str] = None

class CompetitorPost(BaseModel):
    competitor_id: str
    post_url: str
    title: str
    content_snippet: str
    engagement: int
    posted_at: str

class CompetitorInput(BaseModel):
    competitors: List[CompetitorProfile]
    recent_posts: List[CompetitorPost]
    our_avg_engagement: int

class CompetitorInsight(BaseModel):
    competitor_id: str
    competitor_name: str
    posting_frequency: str
    avg_engagement: int
    performance_vs_us: str
    top_content_themes: List[str]
    content_gaps: List[str]
    recommendations: List[str]

class CompetitorOutput(BaseModel):
    insights: List[CompetitorInsight]
    alerts: List[str]

def extract_json_from_response(text: str) -> dict:
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()
    return json.loads(text)

@router.post("/competitor/analyze", response_model=CompetitorOutput)
def analyze_competitors(data: CompetitorInput):
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    system_prompt = """You analyze competitor content and benchmark performance.
Return JSON ONLY without markdown code blocks."""
    
    user_prompt = f"""Analyze these competitors and their recent posts:

COMPETITORS:
{json.dumps([c.dict() for c in data.competitors], indent=2)}

RECENT POSTS:
{json.dumps([p.dict() for p in data.recent_posts], indent=2)}

OUR AVG ENGAGEMENT: {data.our_avg_engagement}

For each competitor, provide:
1. Posting frequency estimate (daily, weekly, etc.)
2. Average engagement on recent posts
3. Performance comparison vs our engagement
4. Top 3-5 content themes they focus on
5. Content gaps (topics they cover that we don't)
6. 2-3 actionable recommendations

Also generate alerts for:
- Competitors launching major campaigns
- Sudden engagement spikes
- New content formats they're testing

Return ONLY this JSON:
{{
  "insights": [
    {{
      "competitor_id": "string",
      "competitor_name": "string",
      "posting_frequency": "3x per week",
      "avg_engagement": 450,
      "performance_vs_us": "30% higher engagement",
      "top_content_themes": ["pricing guides", "case studies"],
      "content_gaps": ["drone videography", "live streaming"],
      "recommendations": ["Consider adding FAQ content", "Increase video demos"]
    }}
  ],
  "alerts": ["Competitor X launched new service line"]
}}"""

    completion = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2500,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )

    try:
        raw_text = completion.content[0].text
        content = extract_json_from_response(raw_text)
        return content
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}", "raw": completion.content[0].text[:500]}
