from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from anthropic import Anthropic
import os, json, re
from openai import OpenAI

router = APIRouter()

class PrimerInput(BaseModel):
    post_html: str

class FAQ(BaseModel):
    q: str
    a: str

class PrimerOutput(BaseModel):
    summary: str
    key_takeaways: List[str]
    faq: List[FAQ]
    sources: List[str]

def extract_json_from_response(text: str) -> dict:
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()
    return json.loads(text)

@router.post("/content/primer", response_model=PrimerOutput)
def generate_primer(data: PrimerInput):
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    system_prompt = """You convert HTML/Markdown into AI-search primers.
Output JSON ONLY. No prose. Use neutral, factual wording, UK English.
Return pure JSON without markdown code blocks."""
    
    user_prompt = f"""Given this article content:

{data.post_html}

Create a primer with:
- summary (2-3 sentences, concise overview)
- key_takeaways (5-8 punchy bullet points, 1-2 lines each)
- faq (4-6 Q&A pairs, answers ≤80 words)
- sources (list of credible URLs if any are mentioned)

Return ONLY this JSON structure:
{{
  "summary": "string",
  "key_takeaways": ["string"],
  "faq": [{{"q": "string", "a": "string"}}],
  "sources": ["https://..."]
}}"""

    # Use GPT-4o-mini for content summarization
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise HTTPException(status_code=503, detail="OpenAI API not configured")

    openai_client = OpenAI(api_key=openai_key)

    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=2000
    )

    try:
        raw_text = completion.choices[0].message.content
        content = extract_json_from_response(raw_text)
        return content
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}", "raw": raw_text[:500]}
