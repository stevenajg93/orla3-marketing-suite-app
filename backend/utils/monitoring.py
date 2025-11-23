"""
Monitoring and Error Tracking for ORLA³ Marketing Suite

Integrates with Sentry for:
- Error tracking and alerting
- Performance monitoring
- User context for debugging

Configuration via environment variables:
- SENTRY_DSN: Your Sentry project DSN
- SENTRY_ENVIRONMENT: Environment name (production, staging, development)
- SENTRY_TRACES_SAMPLE_RATE: Performance monitoring sample rate (0.0 to 1.0)
"""

import os
from typing import Optional, Dict, Any
from functools import wraps

# Sentry Configuration
SENTRY_DSN = os.getenv("SENTRY_DSN")
SENTRY_ENVIRONMENT = os.getenv("SENTRY_ENVIRONMENT", "development")
SENTRY_TRACES_SAMPLE_RATE = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))

# Track initialization status
_sentry_initialized = False


def init_sentry() -> bool:
    """
    Initialize Sentry SDK for error tracking.

    Call this during application startup.
    Returns True if Sentry was initialized, False otherwise.
    """
    global _sentry_initialized

    if not SENTRY_DSN:
        print("⚠️  Sentry not configured - SENTRY_DSN environment variable not set")
        return False

    if _sentry_initialized:
        return True

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment=SENTRY_ENVIRONMENT,
            # Performance monitoring
            traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
            # Send PII data (email, username) for user context
            send_default_pii=True,
            # Integrations
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                StarletteIntegration(transaction_style="endpoint"),
            ],
            # Release tracking (if version is available)
            release=os.getenv("APP_VERSION", "1.0.0"),
            # Filter out health checks and other noise
            before_send=_filter_events,
        )

        _sentry_initialized = True
        print(f"✅ Sentry initialized (Environment: {SENTRY_ENVIRONMENT})")
        return True

    except ImportError:
        print("⚠️  Sentry SDK not installed - run: pip install sentry-sdk[fastapi]")
        return False
    except Exception as e:
        print(f"❌ Failed to initialize Sentry: {e}")
        return False


def _filter_events(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Filter out events we don't want to send to Sentry.

    - Health check requests
    - Expected 4xx errors (not bugs)
    """
    # Filter by URL path
    if "request" in event:
        url = event.get("request", {}).get("url", "")
        # Skip health checks
        if "/health" in url or url.endswith("/"):
            return None

    # Filter by exception type
    if "exception" in event:
        exc_type = event.get("exception", {}).get("values", [{}])[0].get("type", "")
        # Skip expected HTTP errors
        if exc_type in ["HTTPException", "ValidationError"]:
            # Only filter 4xx errors
            status_code = hint.get("exc_info", [None, None, None])[1]
            if hasattr(status_code, "status_code") and 400 <= status_code.status_code < 500:
                return None

    return event


def set_user_context(user_id: str, email: Optional[str] = None, extra: Optional[Dict] = None):
    """
    Set user context for Sentry events.

    Call this after authenticating a user to associate errors with the user.

    Args:
        user_id: User's unique identifier
        email: User's email address
        extra: Additional user data
    """
    if not _sentry_initialized:
        return

    try:
        import sentry_sdk

        user_data = {"id": user_id}
        if email:
            user_data["email"] = email
        if extra:
            user_data.update(extra)

        sentry_sdk.set_user(user_data)

    except Exception:
        pass  # Silently fail - monitoring shouldn't break the app


def capture_exception(exception: Exception, extra: Optional[Dict] = None):
    """
    Manually capture an exception and send to Sentry.

    Use this for exceptions that are caught but should still be tracked.

    Args:
        exception: The exception to capture
        extra: Additional context data
    """
    if not _sentry_initialized:
        return

    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            if extra:
                for key, value in extra.items():
                    scope.set_extra(key, value)
            sentry_sdk.capture_exception(exception)

    except Exception:
        pass


def capture_message(message: str, level: str = "info", extra: Optional[Dict] = None):
    """
    Capture a message (not an exception) and send to Sentry.

    Useful for tracking important events that aren't errors.

    Args:
        message: Message to send
        level: Severity level (debug, info, warning, error, fatal)
        extra: Additional context data
    """
    if not _sentry_initialized:
        return

    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            if extra:
                for key, value in extra.items():
                    scope.set_extra(key, value)
            sentry_sdk.capture_message(message, level=level)

    except Exception:
        pass


def add_breadcrumb(
    message: str,
    category: str = "custom",
    level: str = "info",
    data: Optional[Dict] = None
):
    """
    Add a breadcrumb for debugging context.

    Breadcrumbs appear in the event timeline to help understand
    what happened before an error.

    Args:
        message: Breadcrumb message
        category: Category (e.g., "auth", "api", "database")
        level: Severity level
        data: Additional data
    """
    if not _sentry_initialized:
        return

    try:
        import sentry_sdk

        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data or {}
        )

    except Exception:
        pass


def monitor_performance(operation_name: str):
    """
    Decorator to monitor function performance.

    Creates a Sentry transaction span for the decorated function.

    Usage:
        @monitor_performance("process_payment")
        async def process_payment(user_id: str, amount: float):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not _sentry_initialized:
                return await func(*args, **kwargs)

            try:
                import sentry_sdk

                with sentry_sdk.start_span(op=operation_name, description=func.__name__):
                    return await func(*args, **kwargs)
            except ImportError:
                return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not _sentry_initialized:
                return func(*args, **kwargs)

            try:
                import sentry_sdk

                with sentry_sdk.start_span(op=operation_name, description=func.__name__):
                    return func(*args, **kwargs)
            except ImportError:
                return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
