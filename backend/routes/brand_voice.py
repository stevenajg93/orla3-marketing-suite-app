from fastapi import APIRouter
from pydantic import BaseModel
from anthropic import Anthropic
import os, json, re

router = APIRouter()

class BrandVoiceInput(BaseModel):
    text: str
    brand_tone_rules: str = "Cinematic, confident, fair, buyer-seller balanced, practical, authoritative"
    target_similarity: float = 0.90

class BrandVoiceOutput(BaseModel):
    original: str
    rewritten: str
    similarity: float

def extract_json_from_response(text: str) -> dict:
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()
    return json.loads(text)

@router.post("/brand/rewrite", response_model=BrandVoiceOutput)
def enforce_brand_voice(data: BrandVoiceInput):
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    system_prompt = """You are a brand voice enforcement layer.
Align text to match brand tone while preserving facts and meaning.
Return JSON ONLY without markdown code blocks."""
    
    user_prompt = f"""Rewrite this text to match the Orla3 brand voice:

ORIGINAL TEXT:
{data.text}

BRAND TONE RULES:
{data.brand_tone_rules}

Requirements:
- Preserve all factual claims and information
- Match the brand tone perfectly
- Target similarity: {data.target_similarity}
- UK English spelling
- Maintain professional credibility

Return ONLY this JSON:
{{
  "original": "{data.text[:100]}...",
  "rewritten": "your rewritten version here",
  "similarity": 0.95
}}

The similarity score should be your honest assessment (0.0 to 1.0) of how well the rewrite matches the brand tone."""

    completion = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )

    try:
        raw_text = completion.content[0].text
        content = extract_json_from_response(raw_text)
        return content
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}", "raw": completion.content[0].text[:500]}
