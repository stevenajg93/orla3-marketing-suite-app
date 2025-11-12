"""
Credit Management API Routes
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import setup_logger
from utils.auth import decode_token
from utils.credits import (
    get_user_credits,
    get_credit_history,
    get_credit_cost,
    CREDIT_COSTS,
    InsufficientCreditsError
)

router = APIRouter()
logger = setup_logger(__name__)


def get_user_from_token(request: Request) -> str:
    """Extract user_id from JWT token"""
    auth_header = request.headers.get('authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Missing authorization token")

    token = auth_header.replace('Bearer ', '')
    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload.get('sub')  # user_id


@router.get("/credits/balance")
async def get_credit_balance(request: Request):
    """
    Get user's current credit balance and allocation

    Returns:
        {
            "balance": 1500,
            "monthly_allocation": 2000,
            "total_used": 500,
            "total_purchased": 0,
            "percentage_used": 25,
            "warning_threshold": false
        }
    """
    try:
        user_id = get_user_from_token(request)
        credit_info = get_user_credits(user_id)

        # Calculate percentage used this month
        allocation = credit_info['monthly_allocation']
        used_this_month = allocation - credit_info['balance'] + credit_info['total_purchased']
        percentage_used = (used_this_month / allocation * 100) if allocation > 0 else 0

        # Warning threshold (when below 20% remaining)
        warning_threshold = credit_info['balance'] < (allocation * 0.2)

        return {
            "success": True,
            "credits": {
                **credit_info,
                "percentage_used": round(percentage_used, 1),
                "warning_threshold": warning_threshold
            }
        }

    except ValueError as e:
        logger.error(f"❌ Error getting credit balance: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error getting credit balance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/credits/history")
async def get_transaction_history(request: Request, limit: int = 50):
    """
    Get user's credit transaction history

    Query params:
        limit: Number of transactions to return (default: 50, max: 200)
    """
    try:
        user_id = get_user_from_token(request)

        # Limit the limit
        limit = min(limit, 200)

        transactions = get_credit_history(user_id, limit)

        return {
            "success": True,
            "transactions": transactions,
            "count": len(transactions)
        }

    except Exception as e:
        logger.error(f"❌ Error getting credit history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/credits/costs")
async def get_operation_costs():
    """
    Get credit costs for all operations

    Returns a map of operation_type -> credit_cost
    """
    return {
        "success": True,
        "costs": CREDIT_COSTS
    }


@router.get("/credits/check/{operation_type}")
async def check_credit_availability(request: Request, operation_type: str):
    """
    Check if user has enough credits for a specific operation

    Path params:
        operation_type: Type of operation (e.g., 'social_caption', 'blog_post')

    Returns:
        {
            "has_credits": true,
            "required": 5,
            "available": 1500,
            "operation_type": "blog_post"
        }
    """
    try:
        user_id = get_user_from_token(request)

        # Get required credits
        required_credits = get_credit_cost(operation_type)
        if required_credits == 0:
            raise HTTPException(status_code=400, detail=f"Invalid operation type: {operation_type}")

        # Get user's balance
        credit_info = get_user_credits(user_id)

        return {
            "success": True,
            "has_credits": credit_info['balance'] >= required_credits,
            "required": required_credits,
            "available": credit_info['balance'],
            "operation_type": operation_type
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error checking credit availability: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
