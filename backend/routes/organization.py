"""
Organization and Team Management Routes
Handles organization info, team members, invitations, and role management
"""

from fastapi import APIRouter, HTTPException, Request, status, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import os
import secrets
from datetime import datetime, timedelta
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import setup_logger
from db_pool import get_db_connection
from utils.auth import decode_token
from utils.email import send_team_invitation_email

router = APIRouter()
logger = setup_logger(__name__)


# ============================================================================
# AUTHENTICATION HELPER
# ============================================================================

async def get_current_user(request: Request) -> str:
    """
    Extract user_id from request token

    Reads token from:
    1. HttpOnly cookie (preferred, more secure)
    2. Authorization header (fallback for API clients)
    """
    # Try to get token from cookie first (HttpOnly cookie approach)
    token = request.cookies.get('access_token')

    # Fallback to Authorization header for API clients/backward compatibility
    if not token:
        auth_header = request.headers.get('authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization"
        )

    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    return user_id


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


def get_user_organization(user_id: str):
    """Get user's current organization"""
    with get_db_connection() as conn:
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


def check_permission(user_id: str, organization_id: str, required_role: str = 'admin'):
    """Check if user has required role in organization"""
    with get_db_connection() as conn:
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

    with get_db_connection() as conn:
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

    with get_db_connection() as conn:
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
                # For new users, create a pending invitation and send email

                # Check if there's already a pending invitation
                cur.execute("""
                    SELECT id FROM pending_invitations
                    WHERE organization_id = %s AND email = %s AND status = 'pending'
                """, (organization_id, request_data.email.lower()))

                if cur.fetchone():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="An invitation has already been sent to this email"
                    )

                # Generate secure invitation token
                invitation_token = secrets.token_urlsafe(32)
                expires_at = datetime.utcnow() + timedelta(days=7)

                # Create pending invitation
                cur.execute("""
                    INSERT INTO pending_invitations
                    (organization_id, email, role, invitation_token, invited_by, expires_at, status)
                    VALUES (%s, %s, %s, %s, %s, %s, 'pending')
                    RETURNING id
                """, (organization_id, request_data.email.lower(), request_data.role,
                      invitation_token, user_id, expires_at))

                invitation_id = cur.fetchone()['id']

                # Get inviter name and org name for email
                cur.execute("""
                    SELECT u.name as inviter_name, o.name as org_name
                    FROM users u
                    JOIN organizations o ON o.id = %s
                    WHERE u.id = %s
                """, (organization_id, user_id))

                names = cur.fetchone()
                inviter_name = names['inviter_name'] or 'A team member'
                org_name = names['org_name'] or 'the organization'

                conn.commit()

                # Send invitation email
                email_sent = send_team_invitation_email(
                    to_email=request_data.email,
                    invitation_token=invitation_token,
                    organization_name=org_name,
                    inviter_name=inviter_name,
                    role=request_data.role
                )

                if not email_sent:
                    logger.warning(f"Failed to send invitation email to {request_data.email}")

                logger.info(f"Created pending invitation for {request_data.email} to organization {organization_id}")

                return {
                    "success": True,
                    "message": f"Invitation sent to {request_data.email}",
                    "invitation_id": str(invitation_id),
                    "email_sent": email_sent
                }

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

    with get_db_connection() as conn:
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

    with get_db_connection() as conn:
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


# ============================================================================
# GET PENDING INVITATIONS
# ============================================================================

@router.get("/organization/invitations")
async def get_pending_invitations(request: Request):
    """
    Get all pending invitations for the organization

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
            detail="Only admins and owners can view invitations"
        )

    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT
                    pi.id,
                    pi.email,
                    pi.role,
                    pi.expires_at,
                    pi.created_at,
                    pi.status,
                    u.name as invited_by_name
                FROM pending_invitations pi
                JOIN users u ON pi.invited_by = u.id
                WHERE pi.organization_id = %s AND pi.status = 'pending'
                ORDER BY pi.created_at DESC
            """, (organization_id,))

            invitations = cur.fetchall()

            return [{
                "id": str(inv['id']),
                "email": inv['email'],
                "role": inv['role'],
                "expires_at": inv['expires_at'].isoformat() if inv['expires_at'] else None,
                "created_at": inv['created_at'].isoformat() if inv['created_at'] else None,
                "status": inv['status'],
                "invited_by": inv['invited_by_name']
            } for inv in invitations]

        finally:
            cur.close()


# ============================================================================
# CANCEL INVITATION
# ============================================================================

@router.delete("/organization/invitation/{invitation_id}")
async def cancel_invitation(invitation_id: str, request: Request):
    """
    Cancel a pending invitation

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
            detail="Only admins and owners can cancel invitations"
        )

    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            # Verify invitation exists and belongs to this org
            cur.execute("""
                SELECT email FROM pending_invitations
                WHERE id = %s AND organization_id = %s AND status = 'pending'
            """, (invitation_id, organization_id))

            invitation = cur.fetchone()

            if not invitation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Invitation not found"
                )

            # Cancel the invitation
            cur.execute("""
                UPDATE pending_invitations
                SET status = 'cancelled'
                WHERE id = %s
            """, (invitation_id,))

            conn.commit()

            logger.info(f"Cancelled invitation {invitation_id} for {invitation['email']}")

            return {
                "success": True,
                "message": f"Invitation to {invitation['email']} has been cancelled"
            }

        except HTTPException:
            raise
        except Exception as e:
            conn.rollback()
            logger.error(f"Cancel invitation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel invitation"
            )
        finally:
            cur.close()


# ============================================================================
# RESEND INVITATION
# ============================================================================

@router.post("/organization/invitation/{invitation_id}/resend")
async def resend_invitation(invitation_id: str, request: Request):
    """
    Resend an invitation email and extend expiry

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
            detail="Only admins and owners can resend invitations"
        )

    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            # Get invitation details
            cur.execute("""
                SELECT pi.email, pi.role, pi.invitation_token, o.name as org_name
                FROM pending_invitations pi
                JOIN organizations o ON pi.organization_id = o.id
                WHERE pi.id = %s AND pi.organization_id = %s AND pi.status = 'pending'
            """, (invitation_id, organization_id))

            invitation = cur.fetchone()

            if not invitation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Invitation not found"
                )

            # Get inviter name
            cur.execute("SELECT name FROM users WHERE id = %s", (user_id,))
            inviter = cur.fetchone()
            inviter_name = inviter['name'] if inviter else 'A team member'

            # Extend expiry
            new_expiry = datetime.utcnow() + timedelta(days=7)
            cur.execute("""
                UPDATE pending_invitations
                SET expires_at = %s
                WHERE id = %s
            """, (new_expiry, invitation_id))

            conn.commit()

            # Resend email
            email_sent = send_team_invitation_email(
                to_email=invitation['email'],
                invitation_token=invitation['invitation_token'],
                organization_name=invitation['org_name'],
                inviter_name=inviter_name,
                role=invitation['role']
            )

            logger.info(f"Resent invitation to {invitation['email']}")

            return {
                "success": True,
                "message": f"Invitation resent to {invitation['email']}",
                "email_sent": email_sent
            }

        except HTTPException:
            raise
        except Exception as e:
            conn.rollback()
            logger.error(f"Resend invitation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to resend invitation"
            )
        finally:
            cur.close()


# ============================================================================
# ACCEPT INVITATION (PUBLIC ENDPOINT)
# ============================================================================

@router.get("/organization/invitation/validate/{token}")
async def validate_invitation(token: str):
    """
    Validate an invitation token (public endpoint)

    Returns invitation details if valid
    """
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT
                    pi.email,
                    pi.role,
                    pi.expires_at,
                    pi.status,
                    o.name as organization_name
                FROM pending_invitations pi
                JOIN organizations o ON pi.organization_id = o.id
                WHERE pi.invitation_token = %s
            """, (token,))

            invitation = cur.fetchone()

            if not invitation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Invalid invitation token"
                )

            if invitation['status'] != 'pending':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invitation has been {invitation['status']}"
                )

            if invitation['expires_at'] < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invitation has expired"
                )

            return {
                "valid": True,
                "email": invitation['email'],
                "role": invitation['role'],
                "organization_name": invitation['organization_name']
            }

        finally:
            cur.close()


@router.post("/organization/invitation/accept/{token}")
async def accept_invitation(token: str, request: Request):
    """
    Accept an invitation after signing up

    Requires: authenticated user with matching email
    """
    user_id = await get_current_user(request)

    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            # Get user email
            cur.execute("SELECT email FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Get invitation
            cur.execute("""
                SELECT
                    pi.id,
                    pi.organization_id,
                    pi.email,
                    pi.role,
                    pi.expires_at,
                    pi.status,
                    o.name as organization_name,
                    o.max_users,
                    o.current_user_count
                FROM pending_invitations pi
                JOIN organizations o ON pi.organization_id = o.id
                WHERE pi.invitation_token = %s
            """, (token,))

            invitation = cur.fetchone()

            if not invitation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Invalid invitation token"
                )

            if invitation['status'] != 'pending':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invitation has been {invitation['status']}"
                )

            if invitation['expires_at'] < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invitation has expired"
                )

            # Verify email matches
            if user['email'].lower() != invitation['email'].lower():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="This invitation was sent to a different email address"
                )

            # Check organization capacity
            if invitation['current_user_count'] >= invitation['max_users']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Organization is at capacity"
                )

            # Check if already a member
            cur.execute("""
                SELECT id FROM organization_members
                WHERE organization_id = %s AND user_id = %s
            """, (invitation['organization_id'], user_id))

            if cur.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You are already a member of this organization"
                )

            # Add user to organization
            cur.execute("""
                INSERT INTO organization_members
                (organization_id, user_id, role, is_active, joined_at)
                VALUES (%s, %s, %s, true, NOW())
            """, (invitation['organization_id'], user_id, invitation['role']))

            # Update organization user count
            cur.execute("""
                UPDATE organizations
                SET current_user_count = current_user_count + 1
                WHERE id = %s
            """, (invitation['organization_id'],))

            # Mark invitation as accepted
            cur.execute("""
                UPDATE pending_invitations
                SET status = 'accepted', accepted_at = NOW()
                WHERE id = %s
            """, (invitation['id'],))

            conn.commit()

            logger.info(f"User {user_id} accepted invitation to org {invitation['organization_id']}")

            return {
                "success": True,
                "message": f"Welcome to {invitation['organization_name']}!",
                "organization_id": str(invitation['organization_id']),
                "role": invitation['role']
            }

        except HTTPException:
            raise
        except Exception as e:
            conn.rollback()
            logger.error(f"Accept invitation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to accept invitation"
            )
        finally:
            cur.close()
