"""
Authentication Tests
Tests for registration, login, token refresh, and security features
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import jwt
import os


class TestHealthCheck:
    """Test basic API health endpoints"""

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "version" in data

    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestJWTSecurity:
    """Test JWT token generation and validation"""

    def test_access_token_creation(self, mock_user):
        """Test that access tokens are created with correct claims"""
        from utils.auth import create_access_token, decode_token

        token = create_access_token(
            user_id=mock_user["id"],
            email=mock_user["email"],
            role=mock_user["role"]
        )

        # Verify token can be decoded
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == mock_user["id"]
        assert payload["email"] == mock_user["email"]
        assert payload["role"] == mock_user["role"]
        assert payload["type"] == "access"

    def test_refresh_token_creation(self, mock_user):
        """Test that refresh tokens are created correctly"""
        from utils.auth import create_refresh_token, decode_token

        token = create_refresh_token(user_id=mock_user["id"])

        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == mock_user["id"]
        assert payload["type"] == "refresh"

    def test_expired_token_rejected(self, expired_token):
        """Test that expired tokens are rejected"""
        from utils.auth import decode_token

        payload = decode_token(expired_token)
        assert payload is None  # Should return None for expired tokens

    def test_invalid_token_rejected(self):
        """Test that invalid tokens are rejected"""
        from utils.auth import decode_token

        payload = decode_token("invalid.token.here")
        assert payload is None

    def test_wrong_secret_rejected(self, mock_user):
        """Test that tokens signed with wrong secret are rejected"""
        from utils.auth import decode_token

        # Create token with different secret
        payload = {
            "sub": mock_user["id"],
            "email": mock_user["email"],
            "role": mock_user["role"],
            "type": "access",
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
        }
        wrong_token = jwt.encode(payload, "wrong-secret", algorithm="HS256")

        result = decode_token(wrong_token)
        assert result is None


class TestPasswordSecurity:
    """Test password hashing and validation"""

    def test_password_hashing(self):
        """Test that passwords are properly hashed"""
        from utils.auth import hash_password, verify_password

        password = "SecurePass123!"
        hashed = hash_password(password)

        # Hash should be different from original
        assert hashed != password
        # Hash should be bcrypt format
        assert hashed.startswith("$2b$")
        # Verification should work
        assert verify_password(password, hashed) is True

    def test_wrong_password_rejected(self):
        """Test that wrong passwords are rejected"""
        from utils.auth import hash_password, verify_password

        hashed = hash_password("CorrectPassword123!")
        assert verify_password("WrongPassword123!", hashed) is False

    def test_weak_password_validation(self, weak_passwords):
        """Test that weak passwords are rejected"""
        from utils.auth import validate_password_strength

        for weak_password in weak_passwords:
            is_valid, error_msg = validate_password_strength(weak_password)
            assert is_valid is False, f"Password '{weak_password}' should be rejected"
            assert error_msg is not None

    def test_strong_password_accepted(self):
        """Test that strong passwords are accepted"""
        from utils.auth import validate_password_strength

        strong_passwords = [
            "SecurePass123!",
            "MyP@ssw0rd!2024",
            "C0mplex!Password",
        ]

        for password in strong_passwords:
            is_valid, error_msg = validate_password_strength(password)
            assert is_valid is True, f"Password '{password}' should be accepted: {error_msg}"


class TestEmailValidation:
    """Test email validation"""

    def test_valid_emails_accepted(self):
        """Test that valid emails are accepted"""
        from utils.auth import validate_email

        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "user@subdomain.example.com",
        ]

        for email in valid_emails:
            assert validate_email(email) is True, f"Email '{email}' should be valid"

    def test_invalid_emails_rejected(self):
        """Test that invalid emails are rejected"""
        from utils.auth import validate_email

        invalid_emails = [
            "not-an-email",
            "@no-local-part.com",
            "no-domain@",
            "spaces in@email.com",
            "",
        ]

        for email in invalid_emails:
            assert validate_email(email) is False, f"Email '{email}' should be invalid"


class TestAuthEndpointSecurity:
    """Test authentication endpoint security"""

    def test_me_endpoint_requires_auth(self, client):
        """Test that /auth/me requires authentication"""
        response = client.get("/auth/me")
        assert response.status_code in [401, 403]  # HTTPBearer may return 401 or 403

    def test_me_endpoint_rejects_invalid_token(self, client):
        """Test that /auth/me rejects invalid tokens"""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401

    def test_me_endpoint_rejects_expired_token(self, client, expired_token):
        """Test that /auth/me rejects expired tokens"""
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401

    def test_me_endpoint_with_valid_token(self, client, valid_access_token, mock_db_cursor, mock_user):
        """Test that /auth/me works with valid token"""
        # Configure mock to return user data
        mock_db_cursor.fetchone_value = mock_user

        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {valid_access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["user"]["email"] == mock_user["email"]


class TestRegistrationValidation:
    """Test registration input validation"""

    def test_registration_validates_email(self, client, mock_db_cursor):
        """Test that registration validates email format"""
        response = client.post(
            "/auth/register",
            json={
                "name": "Test User",
                "email": "invalid-email",
                "password": "SecurePass123!",
            }
        )
        # Pydantic validation returns 422, route validation returns 400
        assert response.status_code in [400, 422]

    def test_registration_validates_password_strength(self, client, mock_db_cursor):
        """Test that registration validates password strength"""
        response = client.post(
            "/auth/register",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "password": "weak",
            }
        )
        assert response.status_code == 400

    def test_registration_prevents_duplicate_email(self, client, mock_db_cursor):
        """Test that registration prevents duplicate emails"""
        # Configure mock to return existing user
        mock_db_cursor.fetchone_value = {"id": "existing-user-id"}

        response = client.post(
            "/auth/register",
            json={
                "name": "Test User",
                "email": "existing@example.com",
                "password": "SecurePass123!",
            }
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()


class TestLoginSecurity:
    """Test login security features"""

    def test_login_validates_credentials(self, client, mock_db_cursor):
        """Test that login validates email and password"""
        # Configure mock for user not found
        mock_db_cursor.fetchone_value = None

        response = client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SomePass123!",
            }
        )

        # Should return 401 without revealing if email exists
        assert response.status_code == 401

    def test_login_checks_email_verification(self, client, mock_db_cursor, mock_user):
        """Test that login requires email verification"""
        # Return user with unverified email
        unverified_user = {**mock_user, "email_verified": False}
        mock_db_cursor.fetchone_value = unverified_user

        response = client.post(
            "/auth/login",
            json={
                "email": mock_user["email"],
                "password": "TestPass123!",
            }
        )

        assert response.status_code == 403
        assert "verify" in response.json()["detail"].lower()

    def test_login_checks_account_locked(self, client, mock_db_cursor, mock_user):
        """Test that login blocks locked accounts"""
        # Return locked user
        locked_user = {
            **mock_user,
            "is_locked": True,
            "locked_until": datetime.utcnow() + timedelta(hours=1)
        }
        mock_db_cursor.fetchone_value = locked_user

        response = client.post(
            "/auth/login",
            json={
                "email": mock_user["email"],
                "password": "TestPass123!",
            }
        )

        assert response.status_code == 403
        assert "locked" in response.json()["detail"].lower()

    def test_login_checks_subscription_status(self, client, mock_db_cursor, mock_user):
        """Test that login requires active subscription"""
        # Return user with free plan and no subscription
        free_user = {
            **mock_user,
            "plan": "free",
            "subscription_status": "inactive"
        }
        mock_db_cursor.fetchone_value = free_user

        response = client.post(
            "/auth/login",
            json={
                "email": mock_user["email"],
                "password": "TestPass123!",
            }
        )

        assert response.status_code == 402  # Payment required


class TestTokenRefresh:
    """Test token refresh functionality"""

    def test_refresh_validates_token_type(self, client, valid_access_token, mock_db_cursor):
        """Test that refresh endpoint rejects access tokens"""
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": valid_access_token}  # Using access token instead
        )

        assert response.status_code == 401

    def test_refresh_checks_revocation(self, client, valid_refresh_token, mock_db_cursor, mock_user):
        """Test that refresh endpoint checks if token is revoked"""
        # Return None indicating token not found or revoked
        mock_db_cursor.fetchone_value = None

        response = client.post(
            "/auth/refresh",
            json={"refresh_token": valid_refresh_token}
        )

        assert response.status_code == 401
        assert "revoked" in response.json()["detail"].lower() or "expired" in response.json()["detail"].lower()


class TestJWTSecretValidation:
    """Test that JWT_SECRET validation works correctly"""

    def test_jwt_secret_required(self):
        """Test that JWT_SECRET is set and used for tokens"""
        import os
        # JWT_SECRET must be set in environment
        jwt_secret = os.environ.get("JWT_SECRET")
        assert jwt_secret is not None
        assert len(jwt_secret) >= 32

    def test_jwt_secret_minimum_length(self):
        """Test that JWT_SECRET must be at least 32 characters"""
        # The config validation already checks this
        from config import Config
        assert Config.JWT_SECRET is not None
        assert len(Config.JWT_SECRET) >= 32


class TestAuthDependency:
    """Test the auth dependency injection"""

    def test_get_current_user_id_extracts_user(self, valid_access_token):
        """Test that get_current_user_id correctly extracts user_id"""
        from utils.auth import decode_token

        payload = decode_token(valid_access_token)
        assert payload is not None
        assert "sub" in payload
        # The sub claim should be a valid UUID string
        assert len(payload["sub"]) == 36  # UUID format

    def test_auth_dependency_fails_closed(self, client):
        """Test that auth dependency fails CLOSED (rejects missing/invalid auth)"""
        # Routes using get_current_user_id should fail without token
        # This tests the fail-closed security requirement

        # Test without any auth
        response = client.get("/auth/me")
        assert response.status_code in [401, 403]  # Must reject

        # Test with malformed auth
        response = client.get(
            "/auth/me",
            headers={"Authorization": "NotBearer token"}
        )
        assert response.status_code in [401, 403]  # Must reject
