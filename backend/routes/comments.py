from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Literal
from anthropic import Anthropic
import os, json, re

router = APIRouter()

class Comment(BaseModel):
    id: str
    platform: str
    post_id: str
    author: str
    text: str
    timestamp: str

class CommentsInput(BaseModel):
    comments: List[Comment]
    brand_tone_rules: str = "Cinematic, confident, fair, helpful"
    auto_reply_enabled: bool = False

class Reply(BaseModel):
    comment_id: str
    platform: str
    reply_text: str
    sentiment: Literal["positive", "neutral", "negative"]
    priority: Literal["high", "medium", "low"]
    requires_human_review: bool

class CommentsOutput(BaseModel):
    replies: List[Reply]

def extract_json_from_response(text: str) -> dict:
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()
    return json.loads(text)

@router.post("/comments/reply", response_model=CommentsOutput)
def generate_replies(data: CommentsInput):
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    system_prompt = """You generate brand-voice compliant comment replies.
Analyze sentiment, prioritize responses, flag those needing human review.
Return JSON ONLY without markdown code blocks."""
    
    user_prompt = f"""Generate replies for these comments:

{json.dumps([c.dict() for c in data.comments], indent=2)}

BRAND TONE: {data.brand_tone_rules}
AUTO-REPLY: {data.auto_reply_enabled}

For each comment:
1. Analyze sentiment (positive/neutral/negative)
2. Set priority (high=complaint/question, medium=engagement, low=spam)
3. Generate helpful, brand-aligned reply
4. Flag if human review needed (complaints, complex questions, negative sentiment)

Reply guidelines:
- Be helpful and genuine
- Keep replies concise (1-3 sentences)
- Use UK English
- Thank positive comments
- Address questions directly
- Handle complaints empathetically
- No generic responses

Return ONLY this JSON:
{{
  "replies": [
    {{
      "comment_id": "string",
      "platform": "linkedin",
      "reply_text": "string",
      "sentiment": "positive",
      "priority": "medium",
      "requires_human_review": false
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
