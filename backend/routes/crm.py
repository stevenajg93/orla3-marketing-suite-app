from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from anthropic import Anthropic
import os, json, re

router = APIRouter()

class Contact(BaseModel):
    id: str
    email_hash: str
    tags: List[str]
    last_touch: str
    source: str

class Interaction(BaseModel):
    contact_id: str
    content_slug: str
    event: str
    ts: str

class Campaign(BaseModel):
    id: str
    name: str
    objective: str
    start_at: str
    end_at: str

class CRMInput(BaseModel):
    contacts: List[Contact]
    interactions: List[Interaction]
    campaigns: List[Campaign]

class Association(BaseModel):
    contact_id: str
    campaign_id: Optional[str]
    top_content: List[str]
    engagement_score: float

class NextAction(BaseModel):
    contact_id: str
    action: str
    reason: str
    not_before: str

class CRMOutput(BaseModel):
    associations: List[Association]
    next_actions: List[NextAction]

def extract_json_from_response(text: str) -> dict:
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()
    return json.loads(text)

@router.post("/crm/associate", response_model=CRMOutput)
def crm_associate(data: CRMInput):
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    system_prompt = """You maintain a lightweight marketing CRM graph linking contacts to campaigns and content.
Return JSON ONLY. No PII beyond fields provided. Return pure JSON without markdown code blocks."""
    
    user_prompt = f"""Analyze these CRM data points:

CONTACTS: {json.dumps([c.dict() for c in data.contacts], indent=2)}
INTERACTIONS: {json.dumps([i.dict() for i in data.interactions], indent=2)}
CAMPAIGNS: {json.dumps([c.dict() for c in data.campaigns], indent=2)}

Tasks:
1. Associate contacts to active campaigns based on tags, interactions, and timing
2. Identify top-engaged content per contact
3. Calculate engagement_score (0.0-1.0) based on interaction frequency and recency
4. Suggest next-action for top 20 contacts (personalized follow-up suggestions)

Rules:
- No duplicate actions per contact within 7 days
- Actions must be specific and actionable
- Include not_before date (YYYY-MM-DD format)

Return ONLY this JSON:
{{
  "associations": [
    {{
      "contact_id": "string",
      "campaign_id": "string",
      "top_content": ["slug1", "slug2"],
      "engagement_score": 0.85
    }}
  ],
  "next_actions": [
    {{
      "contact_id": "string",
      "action": "Send personalized video demo follow-up",
      "reason": "High engagement with pricing content",
      "not_before": "2025-10-26"
    }}
  ]
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
