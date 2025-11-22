"""
Pytest Configuration and Fixtures
Provides test client, mock database, and utility fixtures for all tests
"""

import pytest
import os
import sys
from typing import Generator, Dict, Any
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from contextlib import contextmanager

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test environment variables BEFORE importing app modules
os.environ["JWT_SECRET"] = "test-secret-key-that-is-at-least-32-characters-long"
os.environ["OPENAI_API_KEY"] = "test-openai-key"
os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test_db"
os.environ["FRONTEND_URL"] = "http://localhost:3000"
os.environ["ENVIRONMENT"] = "test"

from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport


# ============================================================================
# MOCK DATABASE CONNECTION MANAGER
# ============================================================================

class MockCursor:
    """Mock database cursor for testing"""
    def __init__(self):
        self.fetchone_value = None
        self.fetchall_value = []
        self._execute_calls = []

    def execute(self, query, params=None):
        self._execute_calls.append((query, params))

    def fetchone(self):
        return self.fetchone_value

    def fetchall(self):
        return self.fetchall_value

    def close(self):
        pass


class MockConnection:
    """Mock database connection for testing"""
    def __init__(self):
        self._cursor = MockCursor()

    def cursor(self):
        return self._cursor

    def commit(self):
        pass

    def rollback(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


# Global mock connection for tests to configure
_mock_connection = MockConnection()


def _mock_get_db_connection():
    """Mock get_db_connection that returns our mock connection"""
    @contextmanager
    def _inner():
        yield _mock_connection
    return _inner()


# ============================================================================
# APP FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def app():
    """
    Create FastAPI app instance for testing.
    Uses session scope for efficiency - app created once per test session.
    """
    # Patch db_pool.get_db_connection BEFORE importing main
    with patch('db_pool.get_db_connection', _mock_get_db_connection), \
         patch('db_pool.init_connection_pool'), \
         patch('db_pool.close_all_connections'), \
         patch('scheduler.start_scheduler'), \
         patch('scheduler.stop_scheduler'):
        from main import app as fastapi_app
        yield fastapi_app


@pytest.fixture
def client(app) -> Generator[TestClient, None, None]:
    """
    Synchronous test client for simple API tests.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client(app) -> Generator[AsyncClient, None, None]:
    """
    Async test client for async endpoint tests.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
def mock_db_cursor():
    """
    Get access to the mock cursor for configuring test responses.
    Reset cursor state before each test.
    """
    _mock_connection._cursor = MockCursor()
    return _mock_connection._cursor


# ============================================================================
# AUTH FIXTURES
# ============================================================================

@pytest.fixture
def mock_user() -> Dict[str, Any]:
    """
    Standard test user data.
    """
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "test@example.com",
        "name": "Test User",
        "organization_name": "Test Org",
        "organization_slug": "test-org",
        "role": "user",
        "plan": "professional",
        "is_active": True,
        "email_verified": True,
        "is_super_admin": False,
        "is_locked": False,
        "locked_until": None,
        "failed_login_attempts": 0,
        "subscription_status": "active",
        "password_hash": "$2b$12$test_hash",
        "created_at": datetime.utcnow(),
        "last_login_at": None,
        "timezone": "UTC",
        "profile_image_url": None,
        "current_organization_id": "660e8400-e29b-41d4-a716-446655440001",
        "stripe_subscription_id": "sub_test123",
        "credit_balance": 100,
    }


@pytest.fixture
def mock_super_admin() -> Dict[str, Any]:
    """
    Super admin test user data.
    """
    return {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "email": "admin@example.com",
        "name": "Super Admin",
        "organization_name": "Admin Org",
        "organization_slug": "admin-org",
        "role": "admin",
        "plan": "enterprise",
        "is_active": True,
        "email_verified": True,
        "is_super_admin": True,
        "is_locked": False,
        "locked_until": None,
        "failed_login_attempts": 0,
        "subscription_status": "active",
        "password_hash": "$2b$12$admin_hash",
        "created_at": datetime.utcnow(),
        "last_login_at": None,
        "stripe_subscription_id": "sub_admin123",
        "credit_balance": 1000,
    }


@pytest.fixture
def valid_access_token(mock_user) -> str:
    """
    Generate a valid JWT access token for testing authenticated routes.
    """
    from utils.auth import create_access_token
    return create_access_token(
        user_id=mock_user["id"],
        email=mock_user["email"],
        role=mock_user["role"]
    )


@pytest.fixture
def valid_refresh_token(mock_user) -> str:
    """
    Generate a valid JWT refresh token for testing token refresh.
    """
    from utils.auth import create_refresh_token
    return create_refresh_token(user_id=mock_user["id"])


@pytest.fixture
def admin_access_token(mock_super_admin) -> str:
    """
    Generate a valid JWT access token for super admin testing.
    """
    from utils.auth import create_access_token
    return create_access_token(
        user_id=mock_super_admin["id"],
        email=mock_super_admin["email"],
        role=mock_super_admin["role"]
    )


@pytest.fixture
def expired_token() -> str:
    """
    Generate an expired JWT token for testing token validation.
    """
    import jwt
    payload = {
        "sub": "550e8400-e29b-41d4-a716-446655440000",
        "email": "test@example.com",
        "role": "user",
        "type": "access",
        "exp": datetime.utcnow() - timedelta(hours=1),
        "iat": datetime.utcnow() - timedelta(hours=2),
    }
    return jwt.encode(payload, os.environ["JWT_SECRET"], algorithm="HS256")


@pytest.fixture
def auth_headers(valid_access_token) -> Dict[str, str]:
    """
    Authorization headers with valid access token.
    """
    return {"Authorization": f"Bearer {valid_access_token}"}


@pytest.fixture
def admin_auth_headers(admin_access_token) -> Dict[str, str]:
    """
    Authorization headers with super admin access token.
    """
    return {"Authorization": f"Bearer {admin_access_token}"}


# ============================================================================
# DATABASE MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_db_connection():
    """
    Mock database connection for unit tests.
    Returns a MagicMock that simulates psycopg2 connection behavior.
    """
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    return mock_conn, mock_cursor


@pytest.fixture
def mock_get_db_connection(mock_db_connection):
    """
    Patch get_db_connection to return mock connection.
    """
    mock_conn, mock_cursor = mock_db_connection
    with patch('db_pool.get_db_connection') as mock:
        mock.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock.return_value.__exit__ = MagicMock(return_value=False)
        yield mock_conn, mock_cursor


# ============================================================================
# STRIPE MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_stripe():
    """
    Mock Stripe API for payment tests.
    """
    with patch('stripe.Subscription') as mock_subscription, \
         patch('stripe.Customer') as mock_customer, \
         patch('stripe.checkout.Session') as mock_session:

        # Mock subscription object
        mock_sub = MagicMock()
        mock_sub.id = "sub_test123"
        mock_sub.status = "active"
        mock_subscription.retrieve.return_value = mock_sub
        mock_subscription.cancel.return_value = mock_sub

        # Mock customer object
        mock_cust = MagicMock()
        mock_cust.id = "cus_test123"
        mock_customer.create.return_value = mock_cust

        # Mock checkout session
        mock_sess = MagicMock()
        mock_sess.id = "cs_test123"
        mock_sess.url = "https://checkout.stripe.com/test"
        mock_session.create.return_value = mock_sess

        yield {
            "Subscription": mock_subscription,
            "Customer": mock_customer,
            "Session": mock_session,
        }


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def sample_registration_data() -> Dict[str, str]:
    """
    Valid registration request data.
    """
    return {
        "name": "New User",
        "email": "newuser@example.com",
        "password": "SecurePass123!",
        "organization_name": "New Org"
    }


@pytest.fixture
def sample_login_data() -> Dict[str, str]:
    """
    Valid login request data.
    """
    return {
        "email": "test@example.com",
        "password": "TestPass123!"
    }


@pytest.fixture
def weak_passwords() -> list:
    """
    List of weak passwords that should fail validation.
    Based on actual implementation requirements:
    - Minimum 8 characters
    - At least one uppercase
    - At least one lowercase
    - At least one number
    """
    return [
        "short",           # Too short (< 8 chars)
        "nouppercase1",    # No uppercase
        "NOLOWERCASE1",    # No lowercase
        "NoNumbers",       # No numbers
        "12345678",        # Only numbers (no letters)
    ]
