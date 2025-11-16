"""
Organization and Team Management Routes
Handles organization info, team members, invitations, and role management
"""

from fastapi import APIRouter, HTTPException, Request, status, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import setup_logger
from utils.auth import decode_token

router = APIRouter()
logger = setup_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: str  # viewer, member, admin


class ChangeRoleRequest(BaseModel):
    user_id: str
    role: str  # viewer, member, admin


# ============================================================================
# DATABASE HELPERS
# ============================================================================

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


async def get_current_user(request: Request):
    """Extract user from JWT token"""
    auth_header = request.headers.get('authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )

    token = auth_header.replace('Bearer ', '')
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    return payload.get('sub')


def get_user_organization(user_id: str):
    """Get user's current organization"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Get user's organization membership
        cur.execute("""
            SELECT om.organization_id, om.role, o.name, o.subscription_tier,
                   o.max_users, o.current_user_count
            FROM organization_members om
            JOIN organizations o ON om.organization_id = o.id
            JOIN users u ON om.user_id = u.id
            WHERE u.id = %s AND om.is_active = true
            LIMIT 1
        """, (user_id,))

        return cur.fetchone()
    finally:
        cur.close()
        conn.close()


def check_permission(user_id: str, organization_id: str, required_role: str = 'admin'):
    """Check if user has required role in organization"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT role
            FROM organization_members
            WHERE user_id = %s AND organization_id = %s AND is_active = true
        """, (user_id, organization_id))

        member = cur.fetchone()
        if not member:
            return False

        role = member['role']

        # Role hierarchy: owner > admin > member > viewer
        role_hierarchy = {'viewer': 0, 'member': 1, 'admin': 2, 'owner': 3}

        user_level = role_hierarchy.get(role, 0)
        required_level = role_hierarchy.get(required_role, 0)

        return user_level >= required_level
    finally:
        cur.close()
        conn.close()


# ============================================================================
# GET ORGANIZATION INFO
# ============================================================================

@router.get("/organization/info")
async def get_organization_info(request: Request):
    """
    Get current user's organization information

    Returns:
    - Organization name, tier, max_users, current_user_count
    """
    user_id = await get_current_user(request)
    org_info = get_user_organization(user_id)

    if not org_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No organization found for user"
        )

    return {
        "id": str(org_info['organization_id']),
        "name": org_info['name'],
        "subscription_tier": org_info['subscription_tier'],
        "max_users": org_info['max_users'],
        "current_user_count": org_info['current_user_count']
    }


# ============================================================================
# GET TEAM MEMBERS
# ============================================================================

@router.get("/organization/members")
async def get_team_members(request: Request):
    """
    Get all members of user's organization

    Returns:
    - List of team members with roles, joined dates, and activity status
    """
    user_id = await get_current_user(request)
    org_info = get_user_organization(user_id)

    if not org_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No organization found for user"
        )

    organization_id = org_info['organization_id']

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT
                u.id as user_id,
                u.email,
                u.name,
                om.role,
                om.joined_at,
                u.last_login_at,
                om.is_active
            FROM organization_members om
            JOIN users u ON om.user_id = u.id
            WHERE om.organization_id = %s
            ORDER BY
                CASE om.role
                    WHEN 'owner' THEN 1
                    WHEN 'admin' THEN 2
                    WHEN 'member' THEN 3
                    WHEN 'viewer' THEN 4
                END,
                om.joined_at ASC
        """, (organization_id,))

        members = cur.fetchall()

        return [{
            "user_id": str(m['user_id']),
            "email": m['email'],
            "name": m['name'],
            "role": m['role'],
            "joined_at": m['joined_at'].isoformat() if m['joined_at'] else None,
            "last_login_at": m['last_login_at'].isoformat() if m['last_login_at'] else None,
            "is_active": m['is_active']
        } for m in members]

    finally:
        cur.close()
        conn.close()


# ============================================================================
# INVITE TEAM MEMBER
# ============================================================================

@router.post("/organization/invite")
async def invite_member(request_data: InviteMemberRequest, request: Request):
    """
    Invite a new member to the organization

    Requires: admin or owner role
    """
    user_id = await get_current_user(request)
    org_info = get_user_organization(user_id)

    if not org_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No organization found for user"
        )

    organization_id = org_info['organization_id']

    # Check permission (must be admin or owner)
    if not check_permission(user_id, organization_id, 'admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and owners can invite members"
        )

    # Check if organization has available seats
    if org_info['current_user_count'] >= org_info['max_users']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Organization is at capacity ({org_info['max_users']} seats). Upgrade your plan to add more members."
        )

    # Validate role
    valid_roles = ['viewer', 'member', 'admin']
    if request_data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Check if user already exists
        cur.execute("SELECT id, name FROM users WHERE email = %s", (request_data.email.lower(),))
        existing_user = cur.fetchone()

        if existing_user:
            # Check if already in organization
            cur.execute("""
                SELECT id FROM organization_members
                WHERE organization_id = %s AND user_id = %s
            """, (organization_id, existing_user['id']))

            if cur.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is already a member of this organization"
                )

            # Add existing user to organization
            cur.execute("""
                INSERT INTO organization_members (organization_id, user_id, role, is_active, joined_at, invited_by)
                VALUES (%s, %s, %s, true, NOW(), %s)
            """, (organization_id, existing_user['id'], request_data.role, user_id))

            # Update organization user count
            cur.execute("""
                UPDATE organizations
                SET current_user_count = current_user_count + 1
                WHERE id = %s
            """, (organization_id,))

            conn.commit()

            logger.info(f"Added existing user {request_data.email} to organization {organization_id}")

            return {
                "success": True,
                "message": f"{existing_user['name']} has been added to your organization",
                "user_id": str(existing_user['id'])
            }

        else:
            # For new users, we would typically:
            # 1. Create a pending invitation record
            # 2. Send an invitation email
            # 3. User signs up and is automatically added to organization

            # For now, return error indicating user doesn't exist
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No user found with email {request_data.email}. They must create an account first."
            )

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Invite member error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to invite member"
        )
    finally:
        cur.close()
        conn.close()


# ============================================================================
# CHANGE MEMBER ROLE
# ============================================================================

@router.put("/organization/member/role")
async def change_member_role(request_data: ChangeRoleRequest, request: Request):
    """
    Change a team member's role

    Requires: admin or owner role
    Cannot change owner role
    """
    user_id = await get_current_user(request)
    org_info = get_user_organization(user_id)

    if not org_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No organization found for user"
        )

    organization_id = org_info['organization_id']

    # Check permission (must be admin or owner)
    if not check_permission(user_id, organization_id, 'admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and owners can change roles"
        )

    # Validate role
    valid_roles = ['viewer', 'member', 'admin']
    if request_data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Check target member exists and is not owner
        cur.execute("""
            SELECT role FROM organization_members
            WHERE organization_id = %s AND user_id = %s
        """, (organization_id, request_data.user_id))

        target_member = cur.fetchone()

        if not target_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found in organization"
            )

        if target_member['role'] == 'owner':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot change owner role"
            )

        # Update role
        cur.execute("""
            UPDATE organization_members
            SET role = %s
            WHERE organization_id = %s AND user_id = %s
        """, (request_data.role, organization_id, request_data.user_id))

        conn.commit()

        logger.info(f"Changed role for user {request_data.user_id} to {request_data.role} in org {organization_id}")

        return {
            "success": True,
            "message": f"Role updated to {request_data.role}"
        }

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Change role error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change role"
        )
    finally:
        cur.close()
        conn.close()


# ============================================================================
# REMOVE TEAM MEMBER
# ============================================================================

@router.delete("/organization/member/{member_user_id}")
async def remove_member(member_user_id: str, request: Request):
    """
    Remove a member from the organization

    Requires: admin or owner role
    Cannot remove owner
    Cannot remove yourself
    """
    user_id = await get_current_user(request)
    org_info = get_user_organization(user_id)

    if not org_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No organization found for user"
        )

    organization_id = org_info['organization_id']

    # Check permission (must be admin or owner)
    if not check_permission(user_id, organization_id, 'admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and owners can remove members"
        )

    # Cannot remove yourself
    if member_user_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself from the organization"
        )

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Check target member exists and is not owner
        cur.execute("""
            SELECT om.role, u.email
            FROM organization_members om
            JOIN users u ON om.user_id = u.id
            WHERE om.organization_id = %s AND om.user_id = %s
        """, (organization_id, member_user_id))

        target_member = cur.fetchone()

        if not target_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found in organization"
            )

        if target_member['role'] == 'owner':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot remove organization owner"
            )

        # Remove member
        cur.execute("""
            DELETE FROM organization_members
            WHERE organization_id = %s AND user_id = %s
        """, (organization_id, member_user_id))

        # Update organization user count
        cur.execute("""
            UPDATE organizations
            SET current_user_count = current_user_count - 1
            WHERE id = %s
        """, (organization_id,))

        conn.commit()

        logger.info(f"Removed user {member_user_id} from organization {organization_id}")

        return {
            "success": True,
            "message": f"{target_member['email']} has been removed from the organization"
        }

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Remove member error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove member"
        )
    finally:
        cur.close()
        conn.close()
