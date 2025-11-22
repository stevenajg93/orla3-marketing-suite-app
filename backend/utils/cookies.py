"""
Cookie utilities for secure JWT storage
HttpOnly cookies prevent XSS attacks by making tokens inaccessible to JavaScript
"""

from fastapi import Response
from datetime import timedelta
import os


# Cookie configuration
COOKIE_DOMAIN = None  # Set to domain for cross-subdomain sharing if needed
COOKIE_PATH = "/"
ACCESS_TOKEN_MAX_AGE = 60 * 60  # 1 hour in seconds
REFRESH_TOKEN_MAX_AGE = 60 * 60 * 24 * 30  # 30 days in seconds


def is_production() -> bool:
    """Check if running in production environment"""
    return os.getenv("ENVIRONMENT", "development") == "production"


def set_access_token_cookie(response: Response, token: str) -> None:
    """
    Set the access token in an HttpOnly cookie

    Security settings:
    - httponly: True - Prevents JavaScript access (XSS protection)
    - secure: True in production - Only sent over HTTPS
    - samesite: 'lax' - Protects against CSRF while allowing navigation
    - max_age: 1 hour - Matches JWT expiration
    """
    response.set_cookie(
        key="access_token",
        value=token,
        max_age=ACCESS_TOKEN_MAX_AGE,
        httponly=True,
        secure=is_production(),  # True in production (HTTPS only)
        samesite="lax",
        path=COOKIE_PATH,
        domain=COOKIE_DOMAIN,
    )


def set_refresh_token_cookie(response: Response, token: str) -> None:
    """
    Set the refresh token in an HttpOnly cookie

    Security settings:
    - httponly: True - Prevents JavaScript access (XSS protection)
    - secure: True in production - Only sent over HTTPS
    - samesite: 'strict' - More restrictive for refresh tokens
    - max_age: 30 days - Matches JWT expiration
    """
    response.set_cookie(
        key="refresh_token",
        value=token,
        max_age=REFRESH_TOKEN_MAX_AGE,
        httponly=True,
        secure=is_production(),
        samesite="strict",  # Stricter for refresh tokens
        path=COOKIE_PATH,
        domain=COOKIE_DOMAIN,
    )


def clear_auth_cookies(response: Response) -> None:
    """
    Clear both access and refresh token cookies
    Used for logout and token invalidation
    """
    response.delete_cookie(
        key="access_token",
        path=COOKIE_PATH,
        domain=COOKIE_DOMAIN,
    )
    response.delete_cookie(
        key="refresh_token",
        path=COOKIE_PATH,
        domain=COOKIE_DOMAIN,
    )
