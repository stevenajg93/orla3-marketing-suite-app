from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Literal, Optional
from anthropic import Anthropic
import os, json, re

router = APIRouter()

class User(BaseModel):
    id: str
    name: str
    role: Literal["admin", "editor", "designer", "client", "viewer"]
    email: str

class ContentItem(BaseModel):
    id: str
    title: str
    status: Literal["draft", "review", "approved", "scheduled", "published"]
    assigned_to: Optional[str] = None
    created_by: str
    created_at: str

class CollaborationInput(BaseModel):
    users: List[User]
    content_items: List[ContentItem]
    action: Literal["assign_workflow", "suggest_assignments", "check_permissions"]

class WorkflowAssignment(BaseModel):
    content_id: str
    content_title: str
    assigned_to: str
    assigned_role: str
    next_action: str
    deadline_suggestion: str
    reason: str

class CollaborationOutput(BaseModel):
    assignments: List[WorkflowAssignment]
    notifications: List[str]

def extract_json_from_response(text: str) -> dict:
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()
    return json.loads(text)

@router.post("/collab/workflow", response_model=CollaborationOutput)
def manage_workflow(data: CollaborationInput):
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    system_prompt = """You manage team collaboration workflows.
Assign tasks based on roles, suggest deadlines, generate notifications.
Return JSON ONLY without markdown code blocks."""
    
    user_prompt = f"""Manage workflow for this team:

USERS:
{json.dumps([u.dict() for u in data.users], indent=2)}

CONTENT ITEMS:
{json.dumps([c.dict() for c in data.content_items], indent=2)}

ACTION: {data.action}

Role capabilities:
- admin: All permissions, approve final content
- editor: Create, edit, review content
- designer: Create visuals, graphics, video edits
- client: Review and approve only
- viewer: Read-only access

For each content item in "draft" or "review" status:
1. Suggest best person to assign based on role and workload
2. Define next_action (e.g., "Edit draft", "Design graphics", "Client review")
3. Suggest realistic deadline (1-5 days based on complexity)
4. Provide reason for assignment

Generate notifications for:
- New assignments
- Approaching deadlines
- Status changes
- Required approvals

Return ONLY this JSON:
{{
  "assignments": [
    {{
      "content_id": "string",
      "content_title": "string",
      "assigned_to": "user_id",
      "assigned_role": "editor",
      "next_action": "Review and edit draft",
      "deadline_suggestion": "2025-10-22",
      "reason": "Best available editor with relevant experience"
    }}
  ],
  "notifications": [
    "New assignment: 'Blog Post' assigned to Sarah (editor)",
    "Deadline approaching: 'Video Script' due in 2 days"
  ]
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
