from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Literal
from anthropic import Anthropic
import os, json, re

router = APIRouter()

class MediaItem(BaseModel):
    id: str
    filename: str
    file_type: Literal["video", "image", "audio", "document"]
    file_path: str
    file_size_mb: float
    uploaded_by: str
    uploaded_at: str
    tags: List[str]
    metadata: dict

class SearchInput(BaseModel):
    query: str
    file_type: Optional[str] = None
    tags: Optional[List[str]] = None
    uploaded_by: Optional[str] = None

class MediaLibraryInput(BaseModel):
    media_items: List[MediaItem]
    search_query: Optional[SearchInput] = None

class MediaRecommendation(BaseModel):
    media_id: str
    filename: str
    relevance_score: float
    reason: str

class MediaOutput(BaseModel):
    results: List[MediaRecommendation]
    total_found: int

def extract_json_from_response(text: str) -> dict:
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()
    return json.loads(text)

@router.post("/media/search", response_model=MediaOutput)
def search_media(data: MediaLibraryInput):
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    if not data.search_query:
        return {"results": [], "total_found": 0}
    
    system_prompt = """You are a media asset search engine.
Analyze media library and return relevant results with relevance scoring.
Return JSON ONLY without markdown code blocks."""
    
    user_prompt = f"""Search this media library:

MEDIA ITEMS:
{json.dumps([m.dict() for m in data.media_items[:20]], indent=2)}

SEARCH QUERY: {data.search_query.query}
FILE TYPE FILTER: {data.search_query.file_type or 'any'}
TAGS FILTER: {data.search_query.tags or 'any'}

Find relevant media assets based on:
- Filename match
- Tag relevance
- Metadata content
- File type match

Return top 10 results with:
- media_id
- filename
- relevance_score (0.0-1.0)
- reason (why it's relevant)

Sort by relevance_score descending.

Return ONLY this JSON:
{{
  "results": [
    {{
      "media_id": "string",
      "filename": "string",
      "relevance_score": 0.95,
      "reason": "Exact match for corporate interview setup"
    }}
  ],
  "total_found": 10
}}"""

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
        return {"error": f"Invalid JSON: {str(e)}", "raw": completion.content[0].text[:500]}

@router.post("/media/upload")
async def upload_media(file: UploadFile = File(...)):
    """Placeholder for media upload - would integrate with R2/S3"""
    return {
        "status": "success",
        "message": "Media upload endpoint ready - integrate with R2/S3 storage",
        "filename": file.filename
    }
