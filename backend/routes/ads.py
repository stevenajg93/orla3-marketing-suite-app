from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Literal
from anthropic import Anthropic
import os, json, re

router = APIRouter()

class ProofAsset(BaseModel):
    type: Literal["case", "testimonial", "stat"]
    content: str

class AdsInput(BaseModel):
    offer: str
    audience: str
    pain_points: List[str]
    proof_assets: List[ProofAsset]
    channels: List[Literal["meta", "linkedin", "x"]]
    brand_tone_rules: str = "Cinematic, confident, fair, buyer-seller balanced"

class TargetingSet(BaseModel):
    name: str
    definition: str

class ChannelSet(BaseModel):
    channel: str
    headlines: List[str]
    primary_texts: List[str]
    descriptions: List[str]
    ctas: List[str]
    targeting: List[TargetingSet]
    creative_angles: List[str]

class AdsOutput(BaseModel):
    channel_sets: List[ChannelSet]

def extract_json_from_response(text: str) -> dict:
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()
    return json.loads(text)

@router.post("/ads/generate", response_model=AdsOutput)
def generate_ads(data: AdsInput):
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    system_prompt = """You generate compliant, high-performance ad variants per channel.
Respect platform policies and brand rules. Return JSON ONLY without markdown code blocks."""
    
    user_prompt = f"""Create ad variants for these channels: {', '.join(data.channels)}

OFFER: {data.offer}
AUDIENCE: {data.audience}
PAIN POINTS: {', '.join(data.pain_points)}
PROOF ASSETS: {json.dumps([p.dict() for p in data.proof_assets])}
BRAND TONE: {data.brand_tone_rules}

For each channel, provide:
- 3 headlines (short, punchy)
- 3 primary_texts (benefit-driven, 2-3 sentences)
- 3 descriptions (if used by platform)
- 3 CTAs
- 3 targeting sets (broad, lookalike_hint, interest_stack)
- 3 creative_angles

Return ONLY this JSON:
{{
  "channel_sets": [
    {{
      "channel": "meta",
      "headlines": ["string"],
      "primary_texts": ["string"],
      "descriptions": ["string"],
      "ctas": ["string"],
      "targeting": [
        {{"name": "broad", "definition": "string"}},
        {{"name": "lookalike_hint", "definition": "string"}},
        {{"name": "interest_stack", "definition": "string"}}
      ],
      "creative_angles": ["string"]
    }}
  ]
}}"""

    completion = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=3000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )

    try:
        raw_text = completion.content[0].text
        content = extract_json_from_response(raw_text)
        return content
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}", "raw": completion.content[0].text[:500]}
