"""
User Context Middleware for Multi-Tenant Architecture

This middleware handles user identification for all requests:
- Checks for X-User-ID header (for authenticated users)
- Falls back to System User (00000000-0000-0000-0000-000000000000) if not provided
- Adds user_id to request state for routes to access

Future: Replace with proper authentication (JWT, OAuth, session, etc.)
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
from logger import setup_logger

logger = setup_logger(__name__)

# System User ID (ORLA's internal account)
SYSTEM_USER_ID = uuid.UUID('00000000-0000-0000-0000-000000000000')


class UserContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add user context to all requests
    """

    async def dispatch(self, request: Request, call_next):
        # Get user ID from header (for future authentication)
        user_id_header = request.headers.get('X-User-ID')

        if user_id_header:
            try:
                user_id = uuid.UUID(user_id_header)
                logger.debug(f"Request from user: {user_id}")
            except ValueError:
                logger.warning(f"Invalid user ID in header: {user_id_header}, using System User")
                user_id = SYSTEM_USER_ID
        else:
            # Default to System User (preserves existing ORLA functionality)
            user_id = SYSTEM_USER_ID

        # Add user_id to request state
        request.state.user_id = user_id

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
