"""
Authentication Utilities
- Password hashing with bcrypt
- JWT token generation and validation
- Token generation for email verification and password reset
"""

import bcrypt
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
import os
from logger import setup_logger

logger = setup_logger(__name__)

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30 days

# ============================================================================
# PASSWORD HASHING
# ============================================================================

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash

    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hash to check against

    Returns:
        True if password matches, False otherwise
    """
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


# ============================================================================
# JWT TOKEN GENERATION
# ============================================================================

def create_access_token(user_id: str, email: str, role: str) -> str:
    """
    Create a JWT access token

    Args:
        user_id: User UUID
        email: User email
        role: User role (system_admin, org_admin, user)

    Returns:
        JWT token string
    """
    expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": user_id,  # Subject (user ID)
        "email": email,
        "role": role,
        "type": "access",
        "exp": expires_at,
        "iat": datetime.utcnow()
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def create_refresh_token(user_id: str) -> str:
    """
    Create a JWT refresh token

    Args:
        user_id: User UUID

    Returns:
        JWT refresh token string
    """
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": expires_at,
        "iat": datetime.utcnow()
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def decode_token(token: str) -> Optional[Dict]:
    """
    Decode and validate a JWT token

    Args:
        token: JWT token string

    Returns:
        Decoded payload dict if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None


def get_user_id_from_token(token: str) -> Optional[str]:
    """
    Extract user ID from JWT token

    Args:
        token: JWT token string

    Returns:
        User ID if valid, None otherwise
    """
    payload = decode_token(token)
    if payload:
        return payload.get("sub")
    return None


# ============================================================================
# VERIFICATION & RESET TOKENS
# ============================================================================

def generate_verification_token() -> str:
    """
    Generate a secure random token for email verification

    Returns:
        URL-safe token string
    """
    return secrets.token_urlsafe(32)


def generate_reset_token() -> str:
    """
    Generate a secure random token for password reset

    Returns:
        URL-safe token string
    """
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """
    Hash a token for storage in database (for refresh tokens)

    Args:
        token: Token to hash

    Returns:
        SHA256 hash of token
    """
    import hashlib
    return hashlib.sha256(token.encode()).hexdigest()


# ============================================================================
# PASSWORD VALIDATION
# ============================================================================

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets security requirements

    Args:
        password: Password to validate

    Returns:
        (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"

    return True, ""


# ============================================================================
# EMAIL VALIDATION
# ============================================================================

def validate_email(email: str) -> bool:
    """
    Basic email validation

    Args:
        email: Email address to validate

    Returns:
        True if email format is valid
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
