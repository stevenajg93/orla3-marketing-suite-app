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
from db_pool import get_db_connection  # Use connection pool
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
from utils.cookies import (
    set_access_token_cookie,
    set_refresh_token_cookie,
    clear_auth_cookies
)

router = APIRouter()
logger = setup_logger(__name__)


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


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    timezone: Optional[str] = None
    profile_image_url: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# ============================================================================
# DATABASE HELPERS
# ============================================================================


def get_user_by_email(email: str):
    """Get user by email address"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT * FROM users WHERE email = %s",
                (email.lower(),)
            )
            return cur.fetchone()
        finally:
            cur.close()


def get_user_by_id(user_id: str):
    """Get user by ID"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT * FROM users WHERE id = %s",
                (user_id,)
            )
            return cur.fetchone()
        finally:
            cur.close()


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
    with get_db_connection() as conn:
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


# ============================================================================
# LOGIN
# ============================================================================

@router.post("/auth/login")
async def login(request: LoginRequest, req: Request, response: Response):
    """
    Authenticate user and return JWT tokens

    Returns:
    - Access token (1 hour expiry) - set in HttpOnly cookie
    - Refresh token (30 days expiry) - set in HttpOnly cookie
    - User data in response body
    """
    # Get user
    user = get_user_by_email(request.email)

    if not user:
        # Log failed attempt (no user_id since user doesn't exist)
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
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
            finally:
                cur.close()

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
            with get_db_connection() as conn:
                cur = conn.cursor()
                try:
                    cur.execute(
                        "UPDATE users SET is_locked = false, locked_until = NULL, failed_login_attempts = 0 WHERE id = %s",
                        (user['id'],)
                    )
                    conn.commit()
                finally:
                    cur.close()
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
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                ip_address = req.client.host if req.client else None
                user_agent = req.headers.get('user-agent')

                cur.execute(
                    "SELECT record_login_attempt(%s, %s, %s, %s, %s)",
                    (user['id'], False, ip_address, user_agent, 'Invalid password')
                )
                conn.commit()
            finally:
                cur.close()

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
    with get_db_connection() as conn:
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

            # Set tokens in HttpOnly cookies
            set_access_token_cookie(response, access_token)
            set_refresh_token_cookie(response, refresh_token)

            return {
                "success": True,
                "token_type": "bearer",
                "user": {
                    "id": str(user['id']),
                    "name": user['name'],
                    "email": user['email'],
                    "organization_name": user['organization_name'],
                    "role": user['role'],
                    "plan": user['plan'],
                    "email_verified": user['email_verified'],
                    "is_super_admin": user.get('is_super_admin', False)
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


# ============================================================================
# GET CURRENT USER
# ============================================================================

@router.get("/auth/me")
async def get_current_user(request: Request):
    """
    Get current authenticated user info

    Reads token from:
    1. HttpOnly cookie (preferred, more secure)
    2. Authorization header (fallback for API clients)
    """
    # Try to get token from cookie first (HttpOnly cookie approach)
    token = request.cookies.get('access_token')

    # Fallback to Authorization header for API clients/backward compatibility
    if not token:
        auth_header = request.headers.get('authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization"
        )

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
            "is_super_admin": user.get('is_super_admin', False),
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
async def refresh_access_token(request: Request, response: Response, body: RefreshTokenRequest = None):
    """
    Refresh access token using refresh token

    Reads refresh token from:
    1. HttpOnly cookie (preferred)
    2. Request body (fallback)

    Returns:
    - New access token (set in HttpOnly cookie)
    """
    # Try to get refresh token from cookie first
    refresh_token = request.cookies.get('refresh_token')

    # Fallback to request body for API clients
    if not refresh_token and body:
        refresh_token = body.refresh_token

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token"
        )

    # Decode refresh token
    payload = decode_token(refresh_token)

    if not payload or payload.get('type') != 'refresh':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_id = payload.get('sub')

    # Check if refresh token exists and is not revoked
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            token_hash = hash_token(refresh_token)

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

            # Set new access token in HttpOnly cookie
            set_access_token_cookie(response, access_token)

            return {
                "success": True,
                "token_type": "bearer"
            }

        finally:
            cur.close()


# ============================================================================
# LOGOUT
# ============================================================================

@router.post("/auth/logout")
async def logout(request: Request, response: Response, body: RefreshTokenRequest = None):
    """
    Logout user by revoking refresh token and clearing cookies

    Reads refresh token from:
    1. HttpOnly cookie (preferred)
    2. Request body (fallback)
    """
    # Try to get refresh token from cookie first
    refresh_token = request.cookies.get('refresh_token')

    # Fallback to request body for API clients
    if not refresh_token and body:
        refresh_token = body.refresh_token

    # Revoke token in database if we have one
    if refresh_token:
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                token_hash = hash_token(refresh_token)

                cur.execute("""
                    UPDATE refresh_tokens
                    SET is_revoked = true, revoked_at = NOW()
                    WHERE token_hash = %s
                """, (token_hash,))

                conn.commit()
            finally:
                cur.close()

    # Always clear cookies on logout
    clear_auth_cookies(response)

    return {
        "success": True,
        "message": "Logged out successfully"
    }


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

    with get_db_connection() as conn:
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


@router.post("/auth/verify-email")
async def verify_email(request: VerifyEmailRequest):
    """
    Verify user email with verification token
    """
    with get_db_connection() as conn:
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

    with get_db_connection() as conn:
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

    with get_db_connection() as conn:
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


# ============================================================================
# UPDATE PROFILE
# ============================================================================

@router.put("/auth/profile")
async def update_profile(request: UpdateProfileRequest, req: Request):
    """
    Update user profile information

    Requires: Bearer token in Authorization header
    """
    # Get token from Authorization header
    auth_header = req.headers.get('authorization')
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
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            # Build update query dynamically based on provided fields
            update_fields = []
            update_values = []

            if request.name is not None:
                update_fields.append("name = %s")
                update_values.append(request.name)

            if request.timezone is not None:
                update_fields.append("timezone = %s")
                update_values.append(request.timezone)

            if request.profile_image_url is not None:
                update_fields.append("profile_image_url = %s")
                update_values.append(request.profile_image_url)

            if not update_fields:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No fields to update"
                )

            # Add updated_at timestamp
            update_fields.append("updated_at = NOW()")
            update_values.append(user_id)

            # Execute update
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s RETURNING *"
            cur.execute(query, update_values)
            updated_user = cur.fetchone()

            conn.commit()

            logger.info(f"Profile updated for user: {updated_user['email']}")

            return {
                "success": True,
                "message": "Profile updated successfully",
                "user": {
                    "id": str(updated_user['id']),
                    "name": updated_user['name'],
                    "email": updated_user['email'],
                    "timezone": updated_user.get('timezone'),
                    "profile_image_url": updated_user.get('profile_image_url')
                }
            }

        except Exception as e:
            conn.rollback()
            logger.error(f"Profile update error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile"
            )
        finally:
            cur.close()


# ============================================================================
# CHANGE PASSWORD
# ============================================================================

@router.post("/auth/change-password")
async def change_password(request: ChangePasswordRequest, req: Request):
    """
    Change user password

    Requires: Bearer token in Authorization header
    Validates current password before updating
    """
    # Get token from Authorization header
    auth_header = req.headers.get('authorization')
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

    # Verify current password
    if not verify_password(request.current_password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Validate new password strength
    is_valid, error_msg = validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # Hash new password
    new_password_hash = hash_password(request.new_password)

    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            # Update password
            cur.execute("""
                UPDATE users
                SET password_hash = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (new_password_hash, user_id))

            # Revoke all refresh tokens (force re-login on all devices)
            cur.execute("""
                UPDATE refresh_tokens
                SET is_revoked = true, revoked_at = NOW()
                WHERE user_id = %s AND is_revoked = false
            """, (user_id,))

            conn.commit()

            logger.info(f"Password changed for user: {user['email']}")

            return {
                "success": True,
                "message": "Password changed successfully. Please log in again on all devices."
            }

        except Exception as e:
            conn.rollback()
            logger.error(f"Password change error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to change password"
            )
        finally:
            cur.close()


# ============================================================================
# DELETE ACCOUNT
# ============================================================================

@router.delete("/auth/account")
async def delete_account(req: Request):
    """
    Delete user account and all associated data

    WARNING: This is a destructive action that cannot be undone
    Deletes:
    - User account
    - All content library items
    - All credit transactions
    - All social connections
    - All cloud storage tokens
    - Organization membership

    Requires: Bearer token in Authorization header
    """
    # Get token from Authorization header
    auth_header = req.headers.get('authorization')
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

    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            # Check if user is organization owner
            cur.execute("""
                SELECT o.id, o.name, o.current_user_count
                FROM organizations o
                JOIN organization_members om ON o.id = om.organization_id
                WHERE om.user_id = %s AND om.role = 'owner'
            """, (user_id,))

            owned_orgs = cur.fetchall()

            # If user owns organizations with other members, prevent deletion
            for org in owned_orgs:
                if org['current_user_count'] > 1:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cannot delete account. You own organization '{org['name']}' with {org['current_user_count']} members. Please transfer ownership or remove other members first."
                    )

            # Delete user (CASCADE will handle related records)
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))

            conn.commit()

            logger.info(f"Account deleted: {user['email']} (ID: {user_id})")

            return {
                "success": True,
                "message": "Account permanently deleted"
            }

        except HTTPException:
            raise
        except Exception as e:
            conn.rollback()
            logger.error(f"Account deletion error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete account"
            )
        finally:
            cur.close()
