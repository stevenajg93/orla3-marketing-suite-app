"""
Super Admin Portal API
Full platform management and analytics for super administrators
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List, Dict
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime, timedelta
from utils.auth_dependency import get_current_user_id
from logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")


def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


async def verify_super_admin(user_id: str = Depends(get_current_user_id)) -> str:
    """
    Verify user is a super admin
    Raises 403 if user is not a super admin
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT is_super_admin
            FROM users
            WHERE id = %s
        """, (user_id,))

        result = cursor.fetchone()

        if not result or not result['is_super_admin']:
            raise HTTPException(
                status_code=403,
                detail="Unauthorized: Super admin access required"
            )

        return user_id
    finally:
        cursor.close()
        conn.close()


# ============================================================================
# PLATFORM STATISTICS
# ============================================================================

@router.get("/admin/stats/overview")
async def get_platform_overview(admin_id: str = Depends(verify_super_admin)):
    """
    Get comprehensive platform statistics

    Returns:
    - Total users, organizations, credits used
    - Revenue metrics (Stripe)
    - Active subscriptions
    - Content generation stats
    - Growth trends
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # User & Organization Metrics
        cursor.execute("""
            SELECT
                COUNT(DISTINCT u.id) as total_users,
                COUNT(DISTINCT o.id) as total_organizations,
                COUNT(DISTINCT CASE WHEN u.email_verified = true THEN u.id END) as verified_users,
                COUNT(DISTINCT CASE WHEN u.account_status = 'active' THEN u.id END) as active_users,
                COUNT(DISTINCT CASE WHEN u.account_status = 'trial' THEN u.id END) as trial_users,
                COUNT(DISTINCT CASE WHEN u.account_status = 'suspended' THEN u.id END) as suspended_users
            FROM users u
            LEFT JOIN organizations o ON u.current_organization_id = o.id
        """)
        user_stats = dict(cursor.fetchone())

        # Subscription Breakdown
        cursor.execute("""
            SELECT
                o.subscription_tier,
                COUNT(*) as count,
                SUM(o.max_users) as total_seats,
                SUM(o.current_user_count) as used_seats
            FROM organizations o
            GROUP BY o.subscription_tier
            ORDER BY
                CASE o.subscription_tier
                    WHEN 'starter' THEN 1
                    WHEN 'professional' THEN 2
                    WHEN 'business' THEN 3
                    WHEN 'enterprise' THEN 4
                END
        """)
        subscription_breakdown = [dict(row) for row in cursor.fetchall()]

        # Credit Metrics
        cursor.execute("""
            SELECT
                SUM(credit_balance) as total_credits_balance,
                AVG(credit_balance) as avg_credits_per_user,
                (SELECT SUM(ABS(amount)) FROM credit_transactions WHERE transaction_type IN ('social_caption', 'blog', 'image', 'video', 'strategy', 'competitor')) as total_credits_used,
                (SELECT SUM(amount) FROM credit_transactions WHERE transaction_type = 'credit_purchase') as total_credits_purchased,
                (SELECT SUM(amount) FROM credit_transactions WHERE transaction_type = 'subscription') as total_credits_granted
            FROM users
            WHERE credits_exempt = false
        """)
        credit_stats = dict(cursor.fetchone())

        # Content Generation Stats (Last 30 days)
        cursor.execute("""
            SELECT
                content_type,
                COUNT(*) as count,
                AVG(LENGTH(content::text)) as avg_content_length
            FROM content_library
            WHERE created_at > NOW() - INTERVAL '30 days'
            GROUP BY content_type
            ORDER BY count DESC
        """)
        content_stats = [dict(row) for row in cursor.fetchall()]

        # Recent Activity (Last 7 days)
        cursor.execute("""
            SELECT
                DATE(created_at) as date,
                COUNT(DISTINCT user_id) as active_users,
                COUNT(*) as actions_count
            FROM credit_transactions
            WHERE created_at > NOW() - INTERVAL '7 days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """)
        activity_trend = [dict(row) for row in cursor.fetchall()]

        # Revenue Metrics (Stripe subscriptions)
        cursor.execute("""
            SELECT
                COUNT(DISTINCT stripe_customer_id) as paying_customers,
                COUNT(DISTINCT stripe_subscription_id) as active_subscriptions
            FROM users
            WHERE stripe_customer_id IS NOT NULL
        """)
        revenue_stats = dict(cursor.fetchone())

        return {
            "overview": user_stats,
            "subscriptions": subscription_breakdown,
            "credits": credit_stats,
            "content_generation": content_stats,
            "activity_trend": activity_trend,
            "revenue": revenue_stats,
            "last_updated": datetime.utcnow().isoformat()
        }

    finally:
        cursor.close()
        conn.close()


# ============================================================================
# USER MANAGEMENT
# ============================================================================

@router.get("/admin/users")
async def list_all_users(
    admin_id: str = Depends(verify_super_admin),
    search: Optional[str] = Query(None, description="Search by email or name"),
    status: Optional[str] = Query(None, description="Filter by account status"),
    plan: Optional[str] = Query(None, description="Filter by plan"),
    limit: int = Query(50, le=200),
    offset: int = Query(0)
):
    """
    List all users with search and filtering

    Returns:
    - User details including credits, plan, organization
    - Stripe connection status
    - Last activity
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Build query with filters
        where_clauses = []
        params = []

        if search:
            where_clauses.append("(u.email ILIKE %s OR u.name ILIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])

        if status:
            where_clauses.append("u.account_status = %s")
            params.append(status)

        if plan:
            where_clauses.append("u.plan = %s")
            params.append(plan)

        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        # Get users with organization info
        cursor.execute(f"""
            SELECT
                u.id,
                u.email,
                u.name,
                u.plan,
                u.credit_balance,
                u.credits_exempt,
                u.is_super_admin,
                u.account_status,
                u.email_verified,
                u.stripe_customer_id,
                u.stripe_subscription_id,
                u.created_at,
                u.last_login_at,
                o.name as organization_name,
                o.subscription_tier as org_tier,
                om.role as org_role,
                (
                    SELECT COUNT(*)
                    FROM content_library cl
                    WHERE cl.user_id = u.id
                ) as total_content,
                (
                    SELECT SUM(ABS(amount))
                    FROM credit_transactions ct
                    WHERE ct.user_id = u.id
                      AND ct.transaction_type IN ('social_caption', 'blog', 'image', 'video', 'strategy', 'competitor')
                ) as total_credits_used
            FROM users u
            LEFT JOIN organizations o ON u.current_organization_id = o.id
            LEFT JOIN organization_members om ON om.user_id = u.id AND om.organization_id = o.id
            {where_sql}
            ORDER BY u.created_at DESC
            LIMIT %s OFFSET %s
        """, params + [limit, offset])

        users = [dict(row) for row in cursor.fetchall()]

        # Get total count
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM users u
            {where_sql}
        """, params)

        total_count = cursor.fetchone()['count']

        return {
            "users": users,
            "total": total_count,
            "limit": limit,
            "offset": offset
        }

    finally:
        cursor.close()
        conn.close()


@router.get("/admin/users/{user_id}")
async def get_user_details(
    user_id: str,
    admin_id: str = Depends(verify_super_admin)
):
    """
    Get comprehensive user details including:
    - Full account information
    - Credit history
    - Content generation history
    - Stripe billing details
    - Organization membership
    - Social media connections
    - Cloud storage connections
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # User basic info
        cursor.execute("""
            SELECT
                u.*,
                o.name as organization_name,
                o.subscription_tier as org_tier,
                om.role as org_role
            FROM users u
            LEFT JOIN organizations o ON u.current_organization_id = o.id
            LEFT JOIN organization_members om ON om.user_id = u.id AND om.organization_id = o.id
            WHERE u.id = %s
        """, (user_id,))

        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user = dict(user)

        # Credit history (last 50 transactions)
        cursor.execute("""
            SELECT
                id,
                amount,
                transaction_type,
                description,
                created_at
            FROM credit_transactions
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 50
        """, (user_id,))
        credit_history = [dict(row) for row in cursor.fetchall()]

        # Content generation stats by type
        cursor.execute("""
            SELECT
                content_type,
                COUNT(*) as count,
                MAX(created_at) as last_generated
            FROM content_library
            WHERE user_id = %s
            GROUP BY content_type
        """, (user_id,))
        content_stats = [dict(row) for row in cursor.fetchall()]

        # Connected social platforms
        cursor.execute("""
            SELECT
                service_type,
                connected_at,
                is_active
            FROM connected_services
            WHERE user_id = %s
        """, (user_id,))
        social_connections = [dict(row) for row in cursor.fetchall()]

        # Connected cloud storage
        cursor.execute("""
            SELECT
                provider,
                provider_email,
                storage_type,
                connected_at,
                is_active
            FROM user_cloud_storage_tokens
            WHERE user_id = %s
        """, (user_id,))
        cloud_storage = [dict(row) for row in cursor.fetchall()]

        return {
            "user": user,
            "credit_history": credit_history,
            "content_stats": content_stats,
            "social_connections": social_connections,
            "cloud_storage": cloud_storage
        }

    finally:
        cursor.close()
        conn.close()


# ============================================================================
# CREDIT MANAGEMENT
# ============================================================================

class GrantCreditsRequest(BaseModel):
    user_id: str
    credits: int
    reason: str


@router.post("/admin/credits/grant")
async def grant_credits(
    request: GrantCreditsRequest,
    admin_id: str = Depends(verify_super_admin)
):
    """
    Grant credits to a user (gift/refund/compensation)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Use the admin function
        cursor.execute("""
            SELECT admin_grant_credits(%s, %s, %s, %s)
        """, (admin_id, request.user_id, request.credits, request.reason))

        conn.commit()

        # Get updated balance
        cursor.execute("""
            SELECT credit_balance
            FROM users
            WHERE id = %s
        """, (request.user_id,))

        new_balance = cursor.fetchone()['credit_balance']

        logger.info(f"Admin {admin_id} granted {request.credits} credits to user {request.user_id}. New balance: {new_balance}")

        return {
            "success": True,
            "credits_granted": request.credits,
            "new_balance": new_balance,
            "reason": request.reason
        }

    except Exception as e:
        conn.rollback()
        logger.error(f"Error granting credits: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


# ============================================================================
# ACCOUNT MANAGEMENT
# ============================================================================

class UpdateAccountStatusRequest(BaseModel):
    user_id: str
    status: str  # 'active', 'suspended', 'banned', 'trial'
    reason: str


@router.post("/admin/users/status")
async def update_account_status(
    request: UpdateAccountStatusRequest,
    admin_id: str = Depends(verify_super_admin)
):
    """
    Update user account status (suspend/unsuspend/ban)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT admin_set_account_status(%s, %s, %s, %s)
        """, (admin_id, request.user_id, request.status, request.reason))

        conn.commit()

        logger.info(f"Admin {admin_id} set user {request.user_id} status to {request.status}")

        return {
            "success": True,
            "user_id": request.user_id,
            "new_status": request.status,
            "reason": request.reason
        }

    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating account status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


# ============================================================================
# ORGANIZATION MANAGEMENT
# ============================================================================

@router.get("/admin/organizations")
async def list_all_organizations(
    admin_id: str = Depends(verify_super_admin),
    limit: int = Query(50, le=200),
    offset: int = Query(0)
):
    """
    List all organizations with user counts and details
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                o.id,
                o.name,
                o.slug,
                o.subscription_tier,
                o.current_user_count || '/' || o.max_users as users,
                o.stripe_customer_id,
                o.stripe_subscription_id,
                o.storage_provider,
                o.created_at,
                (
                    SELECT email
                    FROM users u
                    JOIN organization_members om ON om.user_id = u.id
                    WHERE om.organization_id = o.id AND om.role = 'owner'
                    LIMIT 1
                ) as owner_email
            FROM organizations o
            ORDER BY o.created_at DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))

        organizations = [dict(row) for row in cursor.fetchall()]

        cursor.execute("SELECT COUNT(*) FROM organizations")
        total_count = cursor.fetchone()['count']

        return {
            "organizations": organizations,
            "total": total_count,
            "limit": limit,
            "offset": offset
        }

    finally:
        cursor.close()
        conn.close()


# ============================================================================
# SUPER ADMIN MANAGEMENT
# ============================================================================

class GrantSuperAdminRequest(BaseModel):
    user_id: str
    reason: str


@router.post("/admin/super-admin/grant")
async def grant_super_admin(
    request: GrantSuperAdminRequest,
    admin_id: str = Depends(verify_super_admin)
):
    """
    Grant super admin privileges to a user
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Update user to super admin
        cursor.execute("""
            UPDATE users
            SET
                is_super_admin = true,
                credits_exempt = true,
                account_status = 'active',
                admin_notes = %s
            WHERE id = %s
        """, (f"Granted super admin by {admin_id}. Reason: {request.reason}", request.user_id))

        conn.commit()

        # Log admin action
        cursor.execute("""
            INSERT INTO admin_audit_log (
                admin_user_id,
                action_type,
                target_user_id,
                details
            ) VALUES (%s, %s, %s, %s)
        """, (
            admin_id,
            'grant_super_admin',
            request.user_id,
            {'reason': request.reason}
        ))

        conn.commit()

        logger.info(f"Admin {admin_id} granted super admin to user {request.user_id}")

        return {
            "success": True,
            "user_id": request.user_id,
            "reason": request.reason
        }

    except Exception as e:
        conn.rollback()
        logger.error(f"Error granting super admin: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@router.post("/admin/super-admin/revoke")
async def revoke_super_admin(
    request: GrantSuperAdminRequest,  # Reuse same model
    admin_id: str = Depends(verify_super_admin)
):
    """
    Revoke super admin privileges from a user
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Prevent self-revoke
        if request.user_id == admin_id:
            raise HTTPException(
                status_code=400,
                detail="Cannot revoke your own super admin privileges"
            )

        # Update user
        cursor.execute("""
            UPDATE users
            SET
                is_super_admin = false,
                admin_notes = %s
            WHERE id = %s
        """, (f"Super admin revoked by {admin_id}. Reason: {request.reason}", request.user_id))

        conn.commit()

        # Log admin action
        cursor.execute("""
            INSERT INTO admin_audit_log (
                admin_user_id,
                action_type,
                target_user_id,
                details
            ) VALUES (%s, %s, %s, %s)
        """, (
            admin_id,
            'revoke_super_admin',
            request.user_id,
            {'reason': request.reason}
        ))

        conn.commit()

        logger.info(f"Admin {admin_id} revoked super admin from user {request.user_id}")

        return {
            "success": True,
            "user_id": request.user_id,
            "reason": request.reason
        }

    except Exception as e:
        conn.rollback()
        logger.error(f"Error revoking super admin: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


# ============================================================================
# ADMIN AUDIT LOG
# ============================================================================

@router.get("/admin/audit-log")
async def get_audit_log(
    admin_id: str = Depends(verify_super_admin),
    limit: int = Query(100, le=500),
    offset: int = Query(0)
):
    """
    Get admin action audit log
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                aal.id,
                aal.action_type,
                aal.details,
                aal.created_at,
                admin_user.email as admin_email,
                target_user.email as target_user_email
            FROM admin_audit_log aal
            JOIN users admin_user ON aal.admin_user_id = admin_user.id
            LEFT JOIN users target_user ON aal.target_user_id = target_user.id
            ORDER BY aal.created_at DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))

        audit_log = [dict(row) for row in cursor.fetchall()]

        return {
            "audit_log": audit_log,
            "limit": limit,
            "offset": offset
        }

    finally:
        cursor.close()
        conn.close()
