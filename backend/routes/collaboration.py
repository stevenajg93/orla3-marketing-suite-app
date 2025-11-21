from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from typing import List, Literal, Optional
from anthropic import Anthropic
import os, json, re
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.auth import decode_token
from logger import setup_logger
from db_pool import get_db_connection  # Use connection pool

router = APIRouter()
logger = setup_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

class User(BaseModel):
    """
    User model for collaboration workflows.

    Note: This model contains TWO different role concepts:
    - org_role: Permission level in organization (owner/admin/member/viewer)
    - job_function: What they do for workflow assignment (editor/designer/etc.)

    org_role is used for authorization checks.
    job_function is used by AI for task assignment suggestions.
    """
    id: str
    name: str
    email: str
    org_role: Literal["owner", "admin", "member", "viewer"]  # Permission level
    job_function: Optional[Literal["editor", "designer", "content_creator", "reviewer", "approver"]] = None  # What they do

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
    assigned_job_function: str  # What they'll do (editor, designer, etc.)
    next_action: str
    deadline_suggestion: str
    reason: str

class CollaborationOutput(BaseModel):
    assignments: List[WorkflowAssignment]
    notifications: List[str]


def get_user_organization(user_id: str):
    """Get user's current organization"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT om.organization_id, om.role, o.name, o.subscription_tier
                FROM organization_members om
                JOIN organizations o ON om.organization_id = o.id
                WHERE om.user_id = %s AND om.is_active = true
                LIMIT 1
            """, (user_id,))

            return cur.fetchone()
        finally:
            cur.close()


def validate_user_can_perform_action(org_role: str, next_action: str) -> bool:
    """
    Validate that a user's organization role permits the requested action.

    Organization role hierarchy:
    - owner/admin: Can do everything (create, edit, review, approve, publish)
    - member: Can create and edit, but not publish
    - viewer: Read-only, cannot be assigned work

    Returns True if user has permission, False otherwise.
    """
    # Actions that require elevated permissions
    publish_actions = ["publish", "approve", "final approval", "go live"]

    # Check for publish actions
    action_lower = next_action.lower()
    requires_publish = any(keyword in action_lower for keyword in publish_actions)

    if org_role in ["owner", "admin"]:
        return True  # Can do everything
    elif org_role == "member":
        return not requires_publish  # Can do everything except publish
    else:  # viewer
        return False  # Cannot be assigned work


def extract_json_from_response(text: str) -> dict:
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()
    return json.loads(text)

@router.post("/collab/workflow", response_model=CollaborationOutput)
async def manage_workflow(data: CollaborationInput, request: Request):
    """
    Manage team collaboration workflows with AI suggestions.

    **Authentication Required**: Must be logged in with valid JWT token.
    **Organization Scope**: Can only manage workflows for users in your organization.
    """
    # Authenticate user
    user_id = await get_current_user(request)
    logger.info(f"Collaboration workflow request from user {user_id}")

    # Get user's organization
    org_info = get_user_organization(user_id)
    if not org_info:
        logger.warning(f"User {user_id} has no active organization")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be part of an organization to use collaboration features"
        )

    organization_id = org_info['organization_id']
    user_role = org_info['role']
    logger.info(f"User {user_id} is {user_role} in organization {organization_id}")

    # Verify all users in the request belong to the same organization
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            user_ids = [u.id for u in data.users]
            if user_ids:
                # Check that all users are members of the organization
                cur.execute("""
                    SELECT user_id
                    FROM organization_members
                    WHERE organization_id = %s AND user_id = ANY(%s) AND is_active = true
                """, (str(organization_id), user_ids))

                valid_users = {row['user_id'] for row in cur.fetchall()}
                invalid_users = set(user_ids) - valid_users

                if invalid_users:
                    logger.warning(f"User {user_id} attempted to access users outside their organization: {invalid_users}")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Some users are not in your organization: {list(invalid_users)}"
                    )
        finally:
            cur.close()

    # All security checks passed - proceed with AI workflow
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

IMPORTANT: Each user has TWO role types:
1. org_role: Permission level (owner/admin/member/viewer)
   - owner/admin: Can approve and publish everything
   - member: Can create and edit content
   - viewer: Can only view, no editing

2. job_function: What they do (editor/designer/content_creator/reviewer/approver)
   - editor: Writes and edits text content
   - designer: Creates visuals, graphics, video edits
   - content_creator: Creates original content (videos, photos)
   - reviewer: Reviews content for quality/compliance
   - approver: Reviews and approves for publishing

ASSIGNMENT RULES:
- Only assign tasks users have permission for (check org_role)
- Match job_function to the type of work needed
- owner/admin can do anything
- member can create/edit but not publish
- viewer cannot be assigned work

For each content item in "draft" or "review" status:
1. Check user's org_role for permission
2. Match their job_function to the task
3. Define next_action (e.g., "Edit draft", "Design graphics")
4. Suggest realistic deadline (1-5 days based on complexity)
5. Provide reason for assignment

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
      "assigned_job_function": "editor",
      "next_action": "Review and edit draft",
      "deadline_suggestion": "2025-10-22",
      "reason": "Best available editor with relevant experience and member permissions"
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

        # Validate assignments respect organization permissions
        user_lookup = {u.id: u for u in data.users}
        validated_assignments = []
        filtered_count = 0

        for assignment in content.get('assignments', []):
            assigned_user_id = assignment.get('assigned_to')
            next_action = assignment.get('next_action', '')

            if assigned_user_id in user_lookup:
                user = user_lookup[assigned_user_id]
                if validate_user_can_perform_action(user.org_role, next_action):
                    validated_assignments.append(assignment)
                else:
                    filtered_count += 1
                    logger.warning(
                        f"Filtered invalid assignment: {user.name} ({user.org_role}) "
                        f"cannot perform '{next_action}'"
                    )

        content['assignments'] = validated_assignments

        if filtered_count > 0:
            content['notifications'].append(
                f"Note: {filtered_count} assignment(s) were filtered due to insufficient permissions"
            )

        logger.info(
            f"Successfully generated {len(validated_assignments)} workflow assignments "
            f"for user {user_id} ({filtered_count} filtered)"
        )
        return content
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse AI response: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error generating workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate workflow suggestions: {str(e)}"
        )
