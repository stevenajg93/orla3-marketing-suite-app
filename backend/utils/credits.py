"""
Credit Management Utility
Handles credit deduction, checking, and tracking
"""

from typing import Dict, Optional
import json
import sys
import os

# Add parent directory to path for db_pool import
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from db_pool import get_db_connection

# Credit costs for different operations
CREDIT_COSTS = {
    "social_caption": 2,
    "blog_post": 5,
    "ai_image_standard": 10,
    "ai_image_ultra": 20,
    "ai_video_8sec": 200,
    "strategy_generation": 10,
    "competitor_analysis": 5,
    "brand_voice_analysis": 3,
}


class InsufficientCreditsError(Exception):
    """Raised when user doesn't have enough credits"""
    def __init__(self, required: int, available: int):
        self.required = required
        self.available = available
        super().__init__(f"Insufficient credits. Required: {required}, Available: {available}")


def get_credit_cost(operation_type: str) -> int:
    """Get the credit cost for an operation"""
    return CREDIT_COSTS.get(operation_type, 0)


def get_user_credits(user_id: str) -> Dict:
    """
    Get user's current credit balance and allocation

    Returns:
        {
            "balance": 1500,
            "monthly_allocation": 2000,
            "total_used": 500,
            "total_purchased": 0,
            "last_reset": "2024-01-15T10:00:00"
        }
    """
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT
                    credit_balance as balance,
                    monthly_credit_allocation as monthly_allocation,
                    total_credits_used as total_used,
                    total_credits_purchased as total_purchased,
                    last_credit_reset_at as last_reset
                FROM users
                WHERE id = %s
            """, (user_id,))

            result = cur.fetchone()

            if not result:
                raise ValueError(f"User not found: {user_id}")

            return dict(result)
        finally:
            cur.close()


def check_sufficient_credits(user_id: str, required_credits: int) -> bool:
    """Check if user has enough credits"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("SELECT has_sufficient_credits(%s, %s) as has_credits", (user_id, required_credits))
            result = cur.fetchone()
            return result['has_credits'] if result else False
        finally:
            cur.close()


def deduct_credits(
    user_id: str,
    operation_type: str,
    credits: Optional[int] = None,
    operation_details: Optional[Dict] = None,
    description: Optional[str] = None
) -> Dict:
    """
    Deduct credits from user's balance

    Args:
        user_id: User's UUID
        operation_type: Type of operation (e.g., 'social_caption', 'blog_post')
        credits: Number of credits to deduct (if None, uses CREDIT_COSTS)
        operation_details: Additional context about the operation
        description: Human-readable description

    Returns:
        {
            "transaction_id": "uuid",
            "credits_deducted": 5,
            "balance_after": 1495,
            "operation_type": "blog_post"
        }

    Raises:
        InsufficientCreditsError: If user doesn't have enough credits
    """
    if credits is None:
        credits = get_credit_cost(operation_type)

    if credits == 0:
        raise ValueError(f"Invalid operation type: {operation_type}")

    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            # Check if user has enough credits
            if not check_sufficient_credits(user_id, credits):
                credit_info = get_user_credits(user_id)
                raise InsufficientCreditsError(credits, credit_info['balance'])

            # Deduct credits using database function
            cur.execute("""
                SELECT record_credit_transaction(
                    %s::uuid,
                    'spent'::varchar,
                    %s::integer,
                    %s::varchar,
                    %s::jsonb,
                    %s::text
                ) as transaction_id
            """, (
                user_id,
                -credits,  # Negative for deduction
                operation_type,
                json.dumps(operation_details) if operation_details else None,
                description or f"Used {credits} credits for {operation_type}"
            ))

            transaction_id = cur.fetchone()['transaction_id']
            conn.commit()

            # Get updated balance
            credit_info = get_user_credits(user_id)

            return {
                "transaction_id": str(transaction_id),
                "credits_deducted": credits,
                "balance_after": credit_info['balance'],
                "operation_type": operation_type
            }

        except Exception as e:
            conn.rollback()
            # Check if it's an insufficient credits error from the database
            if "Insufficient credits" in str(e):
                credit_info = get_user_credits(user_id)
                raise InsufficientCreditsError(credits, credit_info['balance'])
            raise
        finally:
            cur.close()


def add_credits(
    user_id: str,
    credits: int,
    transaction_type: str = "purchased",
    description: Optional[str] = None,
    stripe_payment_intent_id: Optional[str] = None
) -> Dict:
    """
    Add credits to user's balance

    Used for:
    - Credit purchases
    - Refunds
    - Manual adjustments
    """
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT record_credit_transaction(
                    %s::uuid,
                    %s::varchar,
                    %s::integer,
                    NULL,
                    %s::jsonb,
                    %s::text
                ) as transaction_id
            """, (
                user_id,
                transaction_type,
                credits,
                json.dumps({"stripe_payment_intent_id": stripe_payment_intent_id}) if stripe_payment_intent_id else None,
                description or f"Added {credits} credits"
            ))

            transaction_id = cur.fetchone()['transaction_id']
            conn.commit()

            credit_info = get_user_credits(user_id)

            return {
                "transaction_id": str(transaction_id),
                "credits_added": credits,
                "balance_after": credit_info['balance'],
                "transaction_type": transaction_type
            }
        finally:
            cur.close()


def get_credit_history(user_id: str, limit: int = 50) -> list:
    """Get user's credit transaction history"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT
                    id,
                    transaction_type,
                    amount,
                    balance_after,
                    operation_type,
                    operation_details,
                    description,
                    created_at
                FROM credit_transactions
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (user_id, limit))

            transactions = cur.fetchall()
            return [dict(tx) for tx in transactions]
        finally:
            cur.close()
