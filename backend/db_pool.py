"""
Database Connection Pool
Centralized psycopg2 connection pooling for all routes
Replaces individual get_db_connection() functions in each route file
"""

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import os
from contextlib import contextmanager
from logger import setup_logger
import atexit

logger = setup_logger(__name__)

# Global connection pool
_connection_pool = None

def init_connection_pool(minconn=2, maxconn=20):
    """
    Initialize the global connection pool

    Args:
        minconn: Minimum number of connections in pool (default: 2)
        maxconn: Maximum number of connections in pool (default: 20)

    Connection pool configuration:
    - Minimum connections: 2 (always available, reduces cold start latency)
    - Maximum connections: 20 (Railway free tier PostgreSQL limit is 20)
    - Pool type: ThreadedConnectionPool (thread-safe)
    """
    global _connection_pool

    if _connection_pool is not None:
        logger.warning("⚠️  Connection pool already initialized")
        return _connection_pool

    DATABASE_URL = os.getenv("DATABASE_URL")

    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable not set")

    try:
        _connection_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=minconn,
            maxconn=maxconn,
            dsn=DATABASE_URL,
            cursor_factory=RealDictCursor,
            # Connection health check settings
            keepalives=1,              # Enable TCP keepalive
            keepalives_idle=30,        # Start keepalive probes after 30s
            keepalives_interval=10,    # Send probe every 10s
            keepalives_count=5,        # Close connection after 5 failed probes
            # Timeout settings
            connect_timeout=10         # Connection timeout in seconds
        )

        logger.info(f"✅ Database connection pool initialized (min={minconn}, max={maxconn})")

        # Register cleanup on exit
        atexit.register(close_all_connections)

        return _connection_pool

    except Exception as e:
        logger.error(f"❌ Failed to initialize connection pool: {str(e)}")
        raise


def get_connection_pool():
    """
    Get the global connection pool instance

    Raises:
        RuntimeError: If pool not initialized
    """
    global _connection_pool

    if _connection_pool is None:
        raise RuntimeError(
            "Connection pool not initialized. Call init_connection_pool() first."
        )

    return _connection_pool


@contextmanager
def get_db_connection():
    """
    Context manager to get a connection from the pool

    Usage:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users")
            results = cur.fetchall()
            cur.close()

    The connection is automatically returned to the pool when exiting the context.
    """
    pool_instance = get_connection_pool()
    conn = None

    try:
        # Get connection from pool
        conn = pool_instance.getconn()

        if conn is None:
            raise Exception("Failed to get connection from pool")

        yield conn

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"❌ Database error: {str(e)}")
        raise

    finally:
        # Always return connection to pool
        if conn:
            pool_instance.putconn(conn)


def get_db_connection_legacy():
    """
    Legacy non-context-manager connection getter
    For backward compatibility with old code patterns

    ⚠️  WARNING: You MUST manually call putconn() to return the connection!
    ⚠️  Prefer using get_db_connection() context manager instead

    Usage:
        conn = get_db_connection_legacy()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users")
            results = cur.fetchall()
            cur.close()
        finally:
            return_connection(conn)
    """
    pool_instance = get_connection_pool()
    return pool_instance.getconn()


def return_connection(conn):
    """
    Return a connection to the pool

    Only needed if using get_db_connection_legacy()
    Context manager usage automatically returns connections
    """
    if conn:
        pool_instance = get_connection_pool()
        pool_instance.putconn(conn)


def close_all_connections():
    """
    Close all connections in the pool
    Called automatically on application shutdown
    """
    global _connection_pool

    if _connection_pool is not None:
        try:
            _connection_pool.closeall()
            logger.info("✅ All database connections closed")
        except Exception as e:
            logger.error(f"❌ Error closing connections: {str(e)}")
        finally:
            _connection_pool = None


def get_pool_status():
    """
    Get current connection pool statistics

    Returns:
        dict: Pool statistics (available, allocated, total)
    """
    try:
        pool_instance = get_connection_pool()

        # Access internal pool state (psycopg2 doesn't expose this cleanly)
        # This is a workaround - pool stats aren't officially supported
        return {
            "status": "healthy",
            "min_connections": pool_instance.minconn,
            "max_connections": pool_instance.maxconn,
            "note": "psycopg2 pool doesn't expose detailed stats"
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


# Initialize pool on module import if DATABASE_URL is set
if os.getenv("DATABASE_URL"):
    try:
        init_connection_pool()
    except Exception as e:
        logger.warning(f"⚠️  Failed to initialize pool on import: {str(e)}")
