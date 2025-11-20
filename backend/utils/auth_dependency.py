"""
FastAPI Authentication Dependency
Provides a standard way to extract and validate user_id from JWT tokens
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict
import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.auth import decode_token

security = HTTPBearer()
DATABASE_URL = os.getenv("DATABASE_URL")


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Extract and validate user_id from JWT token

    Usage in routes:
    ```python
    from utils.auth_dependency import get_current_user_id

    @router.get("/my-route")
    async def my_route(user_id: str = Depends(get_current_user_id)):
        # user_id is automatically extracted and validated
        pass
    ```

    Returns:
        str: The user_id (UUID) from the JWT token

    Raises:
        HTTPException: If token is missing, invalid, or expired
    """
    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user_id",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


def get_user_from_request(request: Request) -> Optional[str]:
    """
    Alternative method: Extract user_id from Request object

    Usage:
    ```python
    @router.get("/my-route")
    async def my_route(request: Request):
        user_id = get_user_from_request(request)
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")
    ```

    Returns:
        Optional[str]: The user_id if valid token exists, None otherwise
    """
    auth_header = request.headers.get('authorization')

    if not auth_header or not auth_header.startswith('Bearer '):
        return None

    token = auth_header.replace('Bearer ', '')
    payload = decode_token(token)

    if not payload:
        return None

    return payload.get('sub')


async def get_optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """
    Get user_id from JWT token if present, but don't require authentication

    Useful for endpoints that behave differently for authenticated vs unauthenticated users

    Usage:
    ```python
    @router.get("/public-route")
    async def public_route(user_id: Optional[str] = Depends(get_optional_user_id)):
        if user_id:
            # Return personalized content
        else:
            # Return public content
    ```

    Returns:
        Optional[str]: The user_id if valid token exists, None otherwise
    """
    if not credentials:
        return None

    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        return None

    return payload.get("sub")


async def get_user_context(
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, str]:
    """
    Get full user context including organization_id and role

    Usage in routes:
    ```python
    from utils.auth_dependency import get_user_context

    @router.get("/my-route")
    async def my_route(context: Dict = Depends(get_user_context)):
        user_id = context['user_id']
        org_id = context['organization_id']
        role = context['role']
    ```

    Returns:
        Dict containing:
        - user_id: str (UUID)
        - organization_id: str (UUID)
        - role: str (owner|admin|member|viewer)

    Raises:
        HTTPException: If user has no organization or invalid state
    """
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()

    try:
        # Get user's current organization and role
        cursor.execute("""
            SELECT
                u.current_organization_id,
                om.role
            FROM users u
            LEFT JOIN organization_members om ON om.user_id = u.id
                AND om.organization_id = u.current_organization_id
            WHERE u.id = %s
        """, (user_id,))

        result = cursor.fetchone()

        # Allow legacy users without organizations (for backwards compatibility)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User not found in database",
            )

        organization_id = result['current_organization_id']
        role = result['role']

        # For users without organization (legacy/free users), use NULL organization_id
        return {
            "user_id": user_id,
            "organization_id": str(organization_id) if organization_id else None,
            "role": role or "member"  # Default to member if no role found
        }

    finally:
        cursor.close()
