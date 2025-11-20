"""
User Context Middleware for Multi-Tenant Architecture

This middleware handles user identification for all requests:
- Validates JWT token from Authorization header
- Extracts user_id from valid JWT
- PUBLIC ROUTES: Falls back to System User if no valid token
- PROTECTED ROUTES: Rejects requests with invalid/missing tokens (HTTP 401)
- Adds user_id to request state for routes to access

SECURITY: This middleware fails CLOSED - invalid tokens are rejected, not ignored.
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import setup_logger
from utils.auth import decode_token

logger = setup_logger(__name__)

# System User ID (ORLA's internal account)
SYSTEM_USER_ID = uuid.UUID('00000000-0000-0000-0000-000000000000')

# Routes that don't require authentication (public endpoints)
PUBLIC_ROUTES = [
    '/auth/register',
    '/auth/login',
    '/auth/verify-email',
    '/auth/forgot-password',
    '/auth/reset-password',
    '/auth/refresh',
    '/health',
    '/',
    '/docs',
    '/openapi.json'
]


class UserContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add user context to all requests

    Authentication Flow:
    1. PUBLIC ROUTES: Allow without token, fallback to System User
    2. PROTECTED ROUTES with valid JWT: Extract user_id and role
    3. PROTECTED ROUTES with invalid/missing JWT: Return HTTP 401 (fail-closed)

    Security: This middleware fails CLOSED to prevent unauthorized access.
    """

    async def dispatch(self, request: Request, call_next):
        user_id = SYSTEM_USER_ID
        user_role = 'system_admin'

        # Check if route is public
        is_public_route = any(
            request.url.path.startswith(route) for route in PUBLIC_ROUTES
        )

        # Try to get JWT token from Authorization header
        auth_header = request.headers.get('authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')
            payload = decode_token(token)

            if payload and payload.get('type') == 'access':
                try:
                    user_id = uuid.UUID(payload.get('sub'))
                    user_role = payload.get('role', 'user')
                    logger.debug(f"Authenticated request from user: {user_id} (role: {user_role})")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid user ID in JWT: {payload.get('sub')}")
                    if not is_public_route:
                        # Reject invalid user ID on protected routes
                        raise HTTPException(
                            status_code=401,
                            detail="Invalid authentication credentials"
                        )
                    # Public routes can continue with System User
                    user_id = SYSTEM_USER_ID
                    user_role = 'system_admin'
            elif not is_public_route:
                # CRITICAL FIX: Invalid or expired token on protected route - REJECT
                logger.warning(f"Invalid or expired token on protected route: {request.url.path}")
                raise HTTPException(
                    status_code=401,
                    detail="Invalid or expired authentication token"
                )
        elif not is_public_route:
            # CRITICAL FIX: No auth header on protected route - REJECT
            logger.warning(f"Missing authentication on protected route: {request.url.path}")
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )

        # Add user_id and role to request state
        request.state.user_id = user_id
        request.state.user_role = user_role

        # Continue with request
        response = await call_next(request)
        return response


def get_user_id(request: Request) -> uuid.UUID:
    """
    Helper function to get user_id from request state

    Usage in routes:
        from middleware.user_context import get_user_id

        @router.get("/my-data")
        async def get_my_data(request: Request):
            user_id = get_user_id(request)
            # Use user_id to filter data
    """
    return request.state.user_id
