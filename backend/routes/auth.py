"""
Authentication Routes
Handles user registration, login, email verification, and password reset
"""

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime, timedelta
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from logger import setup_logger
from utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_verification_token,
    generate_reset_token,
    hash_token,
    validate_password_strength,
    validate_email
)
from utils.email import (
    send_verification_email,
    send_password_reset_email,
    send_welcome_email
)

router = APIRouter()
logger = setup_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    organization_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class VerifyEmailRequest(BaseModel):
    token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


# ============================================================================
# DATABASE HELPERS
# ============================================================================

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def get_user_by_email(email: str):
    """Get user by email address"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT * FROM users WHERE email = %s",
            (email.lower(),)
        )
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()


def get_user_by_id(user_id: str):
    """Get user by ID"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT * FROM users WHERE id = %s",
            (user_id,)
        )
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()


# ============================================================================
# REGISTRATION
# ============================================================================

@router.post("/auth/register")
async def register(request: RegisterRequest, req: Request):
    """
    Register a new user account

    Creates a new user with:
    - Hashed password
    - Email verification token
    - Default 'user' role
    - Free plan
    """
    # Validate email format
    if not validate_email(request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )

    # Validate password strength
    is_valid, error_msg = validate_password_strength(request.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # Check if user already exists
    existing_user = get_user_by_email(request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Generate organization slug from name
    org_slug = None
    if request.organization_name:
        import re
        org_slug = re.sub(r'[^a-z0-9]+', '-', request.organization_name.lower()).strip('-')

    # Hash password
    password_hash = hash_password(request.password)

    # Generate verification token
    verification_token = generate_verification_token()
    verification_expires = datetime.utcnow() + timedelta(days=7)

    # Create user
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO users (
                name, email, password_hash, organization_name, organization_slug,
                role, plan, is_active, email_verified,
                verification_token, verification_token_expires,
                created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING id, name, email, organization_name, role, plan, created_at
        """, (
            request.name,
            request.email.lower(),
            password_hash,
            request.organization_name,
            org_slug,
            'user',  # Default role
            'free',  # Default plan
            True,
            False,  # Email not verified yet
            verification_token,
            verification_expires,
            datetime.utcnow()
        ))

        user = cur.fetchone()
        conn.commit()

        # Log registration event
        ip_address = req.client.host if req.client else None
        user_agent = req.headers.get('user-agent')

        cur.execute("""
            INSERT INTO audit_log (
                user_id, event_type, event_status, ip_address, user_agent
            ) VALUES (%s, %s, %s, %s, %s)
        """, (
            user['id'], 'register', 'success', ip_address, user_agent
        ))
        conn.commit()

        logger.info(f"✅ New user registered: {request.email} (ID: {user['id']})")

        # Send verification email
        send_verification_email(request.email, verification_token)

        return {
            "success": True,
            "message": "Registration successful. Please check your email to verify your account.",
            "user": {
                "id": str(user['id']),
                "name": user['name'],
                "email": user['email'],
                "organization_name": user['organization_name'],
                "role": user['role'],
                "plan": user['plan']
            },
            # For development: include verification token
            "verification_token": verification_token if os.getenv("ENVIRONMENT") == "development" else None
        }

    except psycopg2.IntegrityError as e:
        conn.rollback()
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or organization name already exists"
        )
    except Exception as e:
        conn.rollback()
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )
    finally:
        cur.close()
        conn.close()


# ============================================================================
# LOGIN
# ============================================================================

@router.post("/auth/login")
async def login(request: LoginRequest, req: Request):
    """
    Authenticate user and return JWT tokens

    Returns:
    - Access token (1 hour expiry)
    - Refresh token (30 days expiry)
    """
    # Get user
    user = get_user_by_email(request.email)

    if not user:
        # Log failed attempt (no user_id since user doesn't exist)
        conn = get_db_connection()
        cur = conn.cursor()
        ip_address = req.client.host if req.client else None
        user_agent = req.headers.get('user-agent')

        cur.execute("""
            INSERT INTO audit_log (
                event_type, event_status, ip_address, user_agent, error_message,
                metadata
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            'login', 'failure', ip_address, user_agent,
            'User not found',
            {'email': request.email}
        ))
        conn.commit()
        cur.close()
        conn.close()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if account is locked
    if user['is_locked']:
        if user['locked_until'] and user['locked_until'] > datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account locked due to failed login attempts. Try again after {user['locked_until']}"
            )
        else:
            # Unlock if lock period expired
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "UPDATE users SET is_locked = false, locked_until = NULL, failed_login_attempts = 0 WHERE id = %s",
                (user['id'],)
            )
            conn.commit()
            cur.close()
            conn.close()
            user['is_locked'] = False

    # Check if account is active
    if not user['is_active']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    # Check if email is verified
    if not user['email_verified']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in. Check your inbox for the verification link."
        )

    # Check if user has an active paid subscription
    subscription_status = user.get('subscription_status', 'inactive')
    if user['plan'] == 'free' or subscription_status not in ['active', 'trialing']:
        # Allow access if subscription is active or in trial period
        # Block if: free plan, canceled, past_due, unpaid, or inactive
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Please select and pay for a plan to access the platform."
        )

    # Verify password
    if not verify_password(request.password, user['password_hash']):
        # Record failed login
        conn = get_db_connection()
        cur = conn.cursor()
        ip_address = req.client.host if req.client else None
        user_agent = req.headers.get('user-agent')

        cur.execute(
            "SELECT record_login_attempt(%s, %s, %s, %s, %s)",
            (user['id'], False, ip_address, user_agent, 'Invalid password')
        )
        conn.commit()
        cur.close()
        conn.close()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Create tokens
    access_token = create_access_token(
        user_id=str(user['id']),
        email=user['email'],
        role=user['role']
    )
    refresh_token = create_refresh_token(user_id=str(user['id']))

    # Store refresh token in database
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        ip_address = req.client.host if req.client else None
        user_agent = req.headers.get('user-agent')
        token_hash = hash_token(refresh_token)
        expires_at = datetime.utcnow() + timedelta(days=30)

        cur.execute("""
            INSERT INTO refresh_tokens (
                user_id, token_hash, expires_at, ip_address, user_agent
            ) VALUES (%s, %s, %s, %s, %s)
        """, (
            user['id'], token_hash, expires_at, ip_address, user_agent
        ))

        # Record successful login
        cur.execute(
            "SELECT record_login_attempt(%s, %s, %s, %s, %s)",
            (user['id'], True, ip_address, user_agent, None)
        )

        conn.commit()

        logger.info(f"✅ User logged in: {user['email']} (ID: {user['id']})")

        return {
            "success": True,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": str(user['id']),
                "name": user['name'],
                "email": user['email'],
                "organization_name": user['organization_name'],
                "role": user['role'],
                "plan": user['plan'],
                "email_verified": user['email_verified']
            }
        }

    except Exception as e:
        conn.rollback()
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )
    finally:
        cur.close()
        conn.close()


# ============================================================================
# GET CURRENT USER
# ============================================================================

@router.get("/auth/me")
async def get_current_user(request: Request):
    """
    Get current authenticated user info

    Requires: Bearer token in Authorization header
    """
    # Get token from Authorization header
    auth_header = request.headers.get('authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )

    token = auth_header.replace('Bearer ', '')
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user_id = payload.get('sub')
    user = get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "success": True,
        "user": {
            "id": str(user['id']),
            "name": user['name'],
            "email": user['email'],
            "organization_name": user['organization_name'],
            "organization_slug": user['organization_slug'],
            "role": user['role'],
            "plan": user['plan'],
            "email_verified": user['email_verified'],
            "profile_image_url": user.get('profile_image_url'),
            "timezone": user.get('timezone'),
            "created_at": user['created_at'].isoformat() if user['created_at'] else None,
            "last_login_at": user['last_login_at'].isoformat() if user.get('last_login_at') else None
        }
    }


# ============================================================================
# REFRESH TOKEN
# ============================================================================

@router.post("/auth/refresh")
async def refresh_access_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token

    Returns:
    - New access token
    - Same refresh token (until it expires)
    """
    # Decode refresh token
    payload = decode_token(request.refresh_token)

    if not payload or payload.get('type') != 'refresh':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_id = payload.get('sub')

    # Check if refresh token exists and is not revoked
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        token_hash = hash_token(request.refresh_token)

        cur.execute("""
            SELECT * FROM refresh_tokens
            WHERE token_hash = %s AND user_id = %s
              AND is_revoked = false AND expires_at > NOW()
        """, (token_hash, user_id))

        refresh_token_record = cur.fetchone()

        if not refresh_token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token revoked or expired"
            )

        # Get user
        user = get_user_by_id(user_id)

        if not user or not user['is_active']:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Create new access token
        access_token = create_access_token(
            user_id=str(user['id']),
            email=user['email'],
            role=user['role']
        )

        # Update last_used_at
        cur.execute("""
            UPDATE refresh_tokens
            SET last_used_at = NOW()
            WHERE token_hash = %s
        """, (token_hash,))
        conn.commit()

        return {
            "success": True,
            "access_token": access_token,
            "token_type": "bearer"
        }

    finally:
        cur.close()
        conn.close()


# ============================================================================
# LOGOUT
# ============================================================================

@router.post("/auth/logout")
async def logout(request: RefreshTokenRequest):
    """
    Logout user by revoking refresh token
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        token_hash = hash_token(request.refresh_token)

        cur.execute("""
            UPDATE refresh_tokens
            SET is_revoked = true, revoked_at = NOW()
            WHERE token_hash = %s
        """, (token_hash,))

        conn.commit()

        return {
            "success": True,
            "message": "Logged out successfully"
        }

    finally:
        cur.close()
        conn.close()


# ============================================================================
# EMAIL VERIFICATION
# ============================================================================

@router.post("/auth/resend-verification")
async def resend_verification_email(request: ForgotPasswordRequest):
    """
    Resend email verification link to user

    Args:
        request: Email address of user

    Returns:
        Success message
    """
    user = get_user_by_email(request.email)

    # Don't reveal if email exists (security best practice)
    if not user:
        return {
            "success": True,
            "message": "If the email exists and is unverified, a verification link has been sent"
        }

    # Check if already verified
    if user['email_verified']:
        return {
            "success": True,
            "message": "Email is already verified"
        }

    # Generate new verification token
    verification_token = generate_verification_token()
    verification_expires = datetime.utcnow() + timedelta(days=7)

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            UPDATE users
            SET verification_token = %s, verification_token_expires = %s
            WHERE id = %s
        """, (verification_token, verification_expires, user['id']))

        conn.commit()

        logger.info(f"📧 Verification email resent to: {request.email}")

        # Send verification email
        send_verification_email(request.email, verification_token)

        return {
            "success": True,
            "message": "If the email exists and is unverified, a verification link has been sent",
            # For development: include verification token
            "verification_token": verification_token if os.getenv("ENVIRONMENT") == "development" else None
        }

    finally:
        cur.close()
        conn.close()


@router.post("/auth/verify-email")
async def verify_email(request: VerifyEmailRequest):
    """
    Verify user email with verification token
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT * FROM users
            WHERE verification_token = %s
              AND verification_token_expires > NOW()
        """, (request.token,))

        user = cur.fetchone()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )

        # Mark email as verified
        cur.execute("""
            UPDATE users
            SET email_verified = true,
                verification_token = NULL,
                verification_token_expires = NULL
            WHERE id = %s
        """, (user['id'],))

        conn.commit()

        logger.info(f"✅ Email verified: {user['email']}")

        # Send welcome email
        send_welcome_email(user['email'], user['name'])

        return {
            "success": True,
            "message": "Email verified successfully"
        }

    finally:
        cur.close()
        conn.close()


# ============================================================================
# PASSWORD RESET REQUEST
# ============================================================================

@router.post("/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """
    Request password reset token

    Sends reset token to user's email
    """
    user = get_user_by_email(request.email)

    # Don't reveal if email exists (security best practice)
    if not user:
        return {
            "success": True,
            "message": "If the email exists, a password reset link has been sent"
        }

    # Generate reset token
    reset_token = generate_reset_token()
    reset_expires = datetime.utcnow() + timedelta(hours=1)

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            UPDATE users
            SET reset_token = %s, reset_token_expires = %s
            WHERE id = %s
        """, (reset_token, reset_expires, user['id']))

        conn.commit()

        logger.info(f"🔑 Password reset requested: {request.email}")

        # Send reset email
        send_password_reset_email(request.email, reset_token)

        return {
            "success": True,
            "message": "If the email exists, a password reset link has been sent",
            # For development: include reset token
            "reset_token": reset_token if os.getenv("ENVIRONMENT") == "development" else None
        }

    finally:
        cur.close()
        conn.close()


# ============================================================================
# RESET PASSWORD
# ============================================================================

@router.post("/auth/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """
    Reset password using reset token
    """
    # Validate password strength
    is_valid, error_msg = validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT * FROM users
            WHERE reset_token = %s
              AND reset_token_expires > NOW()
        """, (request.token,))

        user = cur.fetchone()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )

        # Hash new password
        password_hash = hash_password(request.new_password)

        # Update password and clear reset token
        cur.execute("""
            UPDATE users
            SET password_hash = %s,
                reset_token = NULL,
                reset_token_expires = NULL,
                failed_login_attempts = 0,
                is_locked = false,
                locked_until = NULL
            WHERE id = %s
        """, (password_hash, user['id']))

        # Revoke all refresh tokens (force re-login)
        cur.execute("""
            UPDATE refresh_tokens
            SET is_revoked = true, revoked_at = NOW()
            WHERE user_id = %s AND is_revoked = false
        """, (user['id'],))

        conn.commit()

        logger.info(f"🔑 Password reset successful: {user['email']}")

        return {
            "success": True,
            "message": "Password reset successfully. Please log in with your new password."
        }

    finally:
        cur.close()
        conn.close()
