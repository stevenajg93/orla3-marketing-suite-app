"""
Admin Pricing Management API
Allows super admins to manage subscription plans and credit packages
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional, List
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import setup_logger
from utils.auth_dependency import get_current_user_id
from db_pool import get_db_connection  # Use connection pool
import json

router = APIRouter()
logger = setup_logger(__name__)


async def require_super_admin(user_id: str = Depends(get_current_user_id)):
    """Ensure user is a super admin"""

    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("SELECT is_super_admin FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()

            if not user or not user['is_super_admin']:
                raise HTTPException(status_code=403, detail="Super admin access required")

            return user_id

        finally:
            cur.close()


# ============================================================================
# SUBSCRIPTION PLANS MANAGEMENT
# ============================================================================

class SubscriptionPlanUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[int] = None  # Price in pence
    currency: Optional[str] = None
    interval: Optional[str] = None
    credits: Optional[int] = None
    stripe_price_id: Optional[str] = None
    features: Optional[List[str]] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


@router.get("/admin/pricing/plans")
async def get_all_subscription_plans(request: Request):
    """Get all subscription plans (including inactive)"""
    await require_super_admin(request)

    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, plan_key, name, price, currency, interval, credits,
                       stripe_price_id, features, is_active, sort_order,
                       created_at, updated_at
                FROM subscription_plans
                ORDER BY sort_order
            """)

            plans = cur.fetchall()

            return {
                "success": True,
                "plans": [dict(plan) for plan in plans]
            }

        finally:
            cur.close()


@router.get("/admin/pricing/plans/{plan_key}")
async def get_subscription_plan(plan_key: str, request: Request):
    """Get single subscription plan details"""
    await require_super_admin(request)

    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, plan_key, name, price, currency, interval, credits,
                       stripe_price_id, features, is_active, sort_order,
                       created_at, updated_at
                FROM subscription_plans
                WHERE plan_key = %s
            """, (plan_key,))

            plan = cur.fetchone()

            if not plan:
                raise HTTPException(status_code=404, detail="Plan not found")

            return {
                "success": True,
                "plan": dict(plan)
            }

        finally:
            cur.close()


@router.patch("/admin/pricing/plans/{plan_key}")
async def update_subscription_plan(plan_key: str, updates: SubscriptionPlanUpdate, request: Request):
    """Update subscription plan pricing/details"""
    admin_user_id = await require_super_admin(request)

    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            # Get current plan
            cur.execute("SELECT * FROM subscription_plans WHERE plan_key = %s", (plan_key,))
            old_plan = cur.fetchone()

            if not old_plan:
                raise HTTPException(status_code=404, detail="Plan not found")

            # Build dynamic UPDATE query
            update_fields = []
            update_values = []

            if updates.name is not None:
                update_fields.append("name = %s")
                update_values.append(updates.name)

            if updates.price is not None:
                update_fields.append("price = %s")
                update_values.append(updates.price)

            if updates.currency is not None:
                update_fields.append("currency = %s")
                update_values.append(updates.currency)

            if updates.interval is not None:
                update_fields.append("interval = %s")
                update_values.append(updates.interval)

            if updates.credits is not None:
                update_fields.append("credits = %s")
                update_values.append(updates.credits)

            if updates.stripe_price_id is not None:
                update_fields.append("stripe_price_id = %s")
                update_values.append(updates.stripe_price_id)

            if updates.features is not None:
                update_fields.append("features = %s")
                update_values.append(psycopg2.extras.Json(updates.features))

            if updates.is_active is not None:
                update_fields.append("is_active = %s")
                update_values.append(updates.is_active)

            if updates.sort_order is not None:
                update_fields.append("sort_order = %s")
                update_values.append(updates.sort_order)

            if not update_fields:
                raise HTTPException(status_code=400, detail="No fields to update")

            # Perform update
            update_values.append(plan_key)
            update_query = f"""
                UPDATE subscription_plans
                SET {', '.join(update_fields)}
                WHERE plan_key = %s
                RETURNING *
            """

            cur.execute(update_query, update_values)
            updated_plan = cur.fetchone()

            # Log to pricing_history
            for field in updates.dict(exclude_unset=True).keys():
                old_value = old_plan[field]
                new_value = updated_plan[field]

                if old_value != new_value:
                    cur.execute("""
                        INSERT INTO pricing_history
                        (item_type, item_id, field_changed, old_value, new_value, changed_by)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        'subscription_plan',
                        updated_plan['id'],
                        field,
                        json.dumps(str(old_value)) if old_value is not None else None,
                        json.dumps(str(new_value)) if new_value is not None else None,
                        admin_user_id
                    ))

            conn.commit()

            logger.info(f"✅ Super admin {admin_user_id} updated plan {plan_key}")

            return {
                "success": True,
                "plan": dict(updated_plan)
            }

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Error updating plan {plan_key}: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

        finally:
            cur.close()


# ============================================================================
# CREDIT PACKAGES MANAGEMENT
# ============================================================================

class CreditPackageUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[int] = None  # Price in pence
    currency: Optional[str] = None
    credits: Optional[int] = None
    stripe_price_id: Optional[str] = None
    description: Optional[str] = None
    badge: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


@router.get("/admin/pricing/packages")
async def get_all_credit_packages(request: Request):
    """Get all credit packages (including inactive)"""
    await require_super_admin(request)

    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, package_key, name, price, currency, credits,
                       stripe_price_id, description, badge, price_per_credit,
                       is_active, sort_order, created_at, updated_at
                FROM credit_packages
                ORDER BY sort_order
            """)

            packages = cur.fetchall()

            return {
                "success": True,
                "packages": [dict(pkg) for pkg in packages]
            }

        finally:
            cur.close()


@router.get("/admin/pricing/packages/{package_key}")
async def get_credit_package(package_key: str, request: Request):
    """Get single credit package details"""
    await require_super_admin(request)

    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, package_key, name, price, currency, credits,
                       stripe_price_id, description, badge, price_per_credit,
                       is_active, sort_order, created_at, updated_at
                FROM credit_packages
                WHERE package_key = %s
            """, (package_key,))

            package = cur.fetchone()

            if not package:
                raise HTTPException(status_code=404, detail="Package not found")

            return {
                "success": True,
                "package": dict(package)
            }

        finally:
            cur.close()


@router.patch("/admin/pricing/packages/{package_key}")
async def update_credit_package(package_key: str, updates: CreditPackageUpdate, request: Request):
    """Update credit package pricing/details"""
    admin_user_id = await require_super_admin(request)

    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            # Get current package
            cur.execute("SELECT * FROM credit_packages WHERE package_key = %s", (package_key,))
            old_package = cur.fetchone()

            if not old_package:
                raise HTTPException(status_code=404, detail="Package not found")

            # Build dynamic UPDATE query
            update_fields = []
            update_values = []

            if updates.name is not None:
                update_fields.append("name = %s")
                update_values.append(updates.name)

            if updates.price is not None:
                update_fields.append("price = %s")
                update_values.append(updates.price)

            if updates.currency is not None:
                update_fields.append("currency = %s")
                update_values.append(updates.currency)

            if updates.credits is not None:
                update_fields.append("credits = %s")
                update_values.append(updates.credits)

            if updates.stripe_price_id is not None:
                update_fields.append("stripe_price_id = %s")
                update_values.append(updates.stripe_price_id)

            if updates.description is not None:
                update_fields.append("description = %s")
                update_values.append(updates.description)

            if updates.badge is not None:
                update_fields.append("badge = %s")
                update_values.append(updates.badge)

            if updates.is_active is not None:
                update_fields.append("is_active = %s")
                update_values.append(updates.is_active)

            if updates.sort_order is not None:
                update_fields.append("sort_order = %s")
                update_values.append(updates.sort_order)

            # Auto-calculate price_per_credit if price or credits changed
            if updates.price is not None or updates.credits is not None:
                price = updates.price if updates.price is not None else old_package['price']
                credits = updates.credits if updates.credits is not None else old_package['credits']
                price_per_credit = price / credits if credits > 0 else 0

                update_fields.append("price_per_credit = %s")
                update_values.append(price_per_credit)

            if not update_fields:
                raise HTTPException(status_code=400, detail="No fields to update")

            # Perform update
            update_values.append(package_key)
            update_query = f"""
                UPDATE credit_packages
                SET {', '.join(update_fields)}
                WHERE package_key = %s
                RETURNING *
            """

            cur.execute(update_query, update_values)
            updated_package = cur.fetchone()

            # Log to pricing_history
            for field in updates.dict(exclude_unset=True).keys():
                old_value = old_package[field]
                new_value = updated_package[field]

                if old_value != new_value:
                    cur.execute("""
                        INSERT INTO pricing_history
                        (item_type, item_id, field_changed, old_value, new_value, changed_by)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        'credit_package',
                        updated_package['id'],
                        field,
                        json.dumps(str(old_value)) if old_value is not None else None,
                        json.dumps(str(new_value)) if new_value is not None else None,
                        admin_user_id
                    ))

            conn.commit()

            logger.info(f"✅ Super admin {admin_user_id} updated package {package_key}")

            return {
                "success": True,
                "package": dict(updated_package)
            }

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Error updating package {package_key}: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

        finally:
            cur.close()


# ============================================================================
# PRICING HISTORY
# ============================================================================

@router.get("/admin/pricing/history")
async def get_pricing_history(request: Request, limit: int = 50):
    """Get pricing change history"""
    await require_super_admin(request)

    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT ph.*, u.email as changed_by_email, u.name as changed_by_name
                FROM pricing_history ph
                LEFT JOIN users u ON ph.changed_by = u.id
                ORDER BY ph.changed_at DESC
                LIMIT %s
            """, (limit,))

            history = cur.fetchall()

            return {
                "success": True,
                "history": [dict(h) for h in history]
            }

        finally:
            cur.close()
