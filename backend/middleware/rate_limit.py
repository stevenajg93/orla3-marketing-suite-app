"""
Rate Limiting Middleware for ORLA³ Marketing Suite

Provides configurable rate limiting per endpoint category:
- General API: 100 requests/minute per IP
- AI Generation: 10 requests/minute per user (expensive operations)
- Auth endpoints: 5 requests/minute per IP (prevent brute force)
- Public endpoints: 30 requests/minute per IP

Uses in-memory storage (suitable for single instance).
For multi-instance deployments, consider Redis-based storage.
"""

import time
from collections import defaultdict
from typing import Dict, Tuple, Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import os

from logger import setup_logger

logger = setup_logger(__name__)


# Rate limit configurations (requests, window_seconds)
RATE_LIMITS = {
    # AI generation endpoints - expensive operations
    "ai": (10, 60),  # 10 requests per minute
    # Auth endpoints - prevent brute force
    "auth": (5, 60),  # 5 requests per minute
    # Public/health endpoints - moderate limits
    "public": (30, 60),  # 30 requests per minute
    # Default for all other endpoints
    "default": (100, 60),  # 100 requests per minute
}

# Endpoint category mapping
ENDPOINT_CATEGORIES = {
    "/ai/": "ai",
    "/auth/login": "auth",
    "/auth/register": "auth",
    "/auth/forgot-password": "auth",
    "/auth/reset-password": "auth",
    "/health": "public",
    "/": "public",
}


class RateLimitStore:
    """
    In-memory rate limit storage with automatic cleanup.
    Thread-safe for async operations.
    """

    def __init__(self, cleanup_interval: int = 300):
        # Structure: {key: [(timestamp, count), ...]}
        self._store: Dict[str, list] = defaultdict(list)
        self._cleanup_interval = cleanup_interval
        self._last_cleanup = time.time()

    def _cleanup_old_entries(self, window_seconds: int):
        """Remove entries older than the window"""
        current_time = time.time()

        # Only run cleanup periodically
        if current_time - self._last_cleanup < self._cleanup_interval:
            return

        cutoff = current_time - (window_seconds * 2)  # Keep 2x window for safety
        for key in list(self._store.keys()):
            self._store[key] = [
                (ts, count) for ts, count in self._store[key]
                if ts > cutoff
            ]
            # Remove empty keys
            if not self._store[key]:
                del self._store[key]

        self._last_cleanup = current_time

    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int, int]:
        """
        Check if request is within rate limit.

        Returns:
            (allowed, remaining_requests, retry_after_seconds)
        """
        current_time = time.time()
        window_start = current_time - window_seconds

        # Clean old entries periodically
        self._cleanup_old_entries(window_seconds)

        # Count requests in current window
        requests_in_window = sum(
            count for ts, count in self._store[key]
            if ts > window_start
        )

        if requests_in_window >= max_requests:
            # Find when the oldest request in window will expire
            oldest_in_window = min(
                (ts for ts, _ in self._store[key] if ts > window_start),
                default=current_time
            )
            retry_after = int(oldest_in_window + window_seconds - current_time) + 1
            return False, 0, max(retry_after, 1)

        # Add current request
        self._store[key].append((current_time, 1))

        remaining = max_requests - requests_in_window - 1
        return True, remaining, 0


# Global rate limit store
_rate_limit_store = RateLimitStore()


def get_client_identifier(request: Request) -> str:
    """
    Get client identifier for rate limiting.
    Uses user_id if authenticated, otherwise IP address.
    """
    # Try to get user_id from request state (set by UserContextMiddleware)
    user_id = getattr(request.state, 'user_id', None)
    if user_id:
        return f"user:{user_id}"

    # Fall back to IP address
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # Get the first IP in the chain (client IP)
        return f"ip:{forwarded.split(',')[0].strip()}"

    client_host = request.client.host if request.client else "unknown"
    return f"ip:{client_host}"


def get_endpoint_category(path: str) -> str:
    """Determine rate limit category for an endpoint"""
    for prefix, category in ENDPOINT_CATEGORIES.items():
        if path.startswith(prefix):
            return category
    return "default"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware for FastAPI.

    Applies different rate limits based on endpoint category:
    - AI endpoints: Stricter limits (expensive operations)
    - Auth endpoints: Stricter limits (security)
    - General endpoints: Standard limits
    """

    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled
        # Allow disabling via environment variable
        if os.getenv("DISABLE_RATE_LIMITING", "").lower() == "true":
            self.enabled = False
            logger.warning("Rate limiting is disabled via environment variable")

    async def dispatch(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)

        # Skip rate limiting for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        category = get_endpoint_category(path)
        max_requests, window_seconds = RATE_LIMITS.get(category, RATE_LIMITS["default"])

        # Get client identifier
        client_id = get_client_identifier(request)

        # Create rate limit key (category + client)
        rate_key = f"{category}:{client_id}"

        # Check rate limit
        allowed, remaining, retry_after = _rate_limit_store.check_rate_limit(
            rate_key, max_requests, window_seconds
        )

        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {client_id} on {path} "
                f"(category: {category}, limit: {max_requests}/{window_seconds}s)"
            )

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Too many requests. Please try again later.",
                    "retry_after": retry_after
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after)
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + window_seconds)

        return response


# Utility function for route-level rate limiting (optional)
def rate_limit(max_requests: int = 10, window_seconds: int = 60):
    """
    Decorator for route-level rate limiting.

    Usage:
        @router.post("/expensive-operation")
        @rate_limit(max_requests=5, window_seconds=60)
        async def expensive_operation(request: Request):
            ...
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            client_id = get_client_identifier(request)
            rate_key = f"route:{func.__name__}:{client_id}"

            allowed, remaining, retry_after = _rate_limit_store.check_rate_limit(
                rate_key, max_requests, window_seconds
            )

            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "message": "Too many requests. Please try again later.",
                        "retry_after": retry_after
                    },
                    headers={"Retry-After": str(retry_after)}
                )

            return await func(request, *args, **kwargs)

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    return decorator
