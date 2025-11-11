-- ============================================================================
-- AUTHENTICATION SYSTEM MIGRATION
-- Migration: 004_add_authentication.sql
-- Purpose: Add authentication fields and user roles to users table
-- ============================================================================

-- ============================================================================
-- ADD AUTHENTICATION FIELDS TO USERS TABLE
-- ============================================================================

ALTER TABLE users
    -- Password authentication
    ADD COLUMN IF NOT EXISTS password_hash TEXT,

    -- Email verification
    ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT false,
    ADD COLUMN IF NOT EXISTS verification_token TEXT,
    ADD COLUMN IF NOT EXISTS verification_token_expires TIMESTAMPTZ,

    -- Password reset
    ADD COLUMN IF NOT EXISTS reset_token TEXT,
    ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMPTZ,

    -- User role (system_admin, org_admin, user)
    ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'user',

    -- Account status
    ADD COLUMN IF NOT EXISTS is_locked BOOLEAN DEFAULT false,
    ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS locked_until TIMESTAMPTZ;

-- Add role check constraint
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'users_role_check'
    ) THEN
        ALTER TABLE users
            ADD CONSTRAINT users_role_check
            CHECK (role IN ('system_admin', 'org_admin', 'user'));
    END IF;
END $$;

-- ============================================================================
-- CREATE INDEXES FOR AUTHENTICATION
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_users_verification_token
    ON users(verification_token)
    WHERE verification_token IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_users_reset_token
    ON users(reset_token)
    WHERE reset_token IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_users_email_verified
    ON users(email_verified)
    WHERE email_verified = true;

CREATE INDEX IF NOT EXISTS idx_users_role
    ON users(role);

-- ============================================================================
-- UPDATE SYSTEM USER WITH ADMIN ROLE
-- ============================================================================

UPDATE users
SET
    role = 'system_admin',
    email_verified = true
WHERE id = '00000000-0000-0000-0000-000000000000'::uuid;

-- ============================================================================
-- CREATE REFRESH TOKENS TABLE (for JWT token refresh)
-- ============================================================================

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- User relationship
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Token data
    token_hash TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,

    -- Device/session info
    user_agent TEXT,
    ip_address TEXT,

    -- Status
    is_revoked BOOLEAN DEFAULT false,
    revoked_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for refresh tokens
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user
    ON refresh_tokens(user_id);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_hash
    ON refresh_tokens(token_hash)
    WHERE is_revoked = false;

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires
    ON refresh_tokens(expires_at)
    WHERE is_revoked = false;

-- ============================================================================
-- CREATE AUDIT LOG TABLE (for security tracking)
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- User relationship (nullable for failed login attempts)
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Event details
    event_type TEXT NOT NULL,  -- login, logout, register, password_reset, etc.
    event_status TEXT NOT NULL CHECK (event_status IN ('success', 'failure', 'pending')),

    -- Request metadata
    ip_address TEXT,
    user_agent TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Error details (for failures)
    error_message TEXT,

    -- Timestamp
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for audit log
CREATE INDEX IF NOT EXISTS idx_audit_log_user
    ON audit_log(user_id);

CREATE INDEX IF NOT EXISTS idx_audit_log_event_type
    ON audit_log(event_type);

CREATE INDEX IF NOT EXISTS idx_audit_log_created
    ON audit_log(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_log_status
    ON audit_log(event_status)
    WHERE event_status = 'failure';

-- ============================================================================
-- HELPER FUNCTIONS FOR AUTHENTICATION
-- ============================================================================

-- Function to clean up expired tokens
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS void AS $$
BEGIN
    -- Clean up expired verification tokens
    UPDATE users
    SET verification_token = NULL,
        verification_token_expires = NULL
    WHERE verification_token IS NOT NULL
      AND verification_token_expires < NOW();

    -- Clean up expired reset tokens
    UPDATE users
    SET reset_token = NULL,
        reset_token_expires = NULL
    WHERE reset_token IS NOT NULL
      AND reset_token_expires < NOW();

    -- Mark expired refresh tokens as revoked
    UPDATE refresh_tokens
    SET is_revoked = true,
        revoked_at = NOW()
    WHERE expires_at < NOW()
      AND is_revoked = false;
END;
$$ LANGUAGE plpgsql;

-- Function to record login attempt
CREATE OR REPLACE FUNCTION record_login_attempt(
    p_user_id UUID,
    p_success BOOLEAN,
    p_ip_address TEXT DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL
)
RETURNS void AS $$
BEGIN
    -- Insert audit log
    INSERT INTO audit_log (
        user_id,
        event_type,
        event_status,
        ip_address,
        user_agent,
        error_message
    ) VALUES (
        p_user_id,
        'login',
        CASE WHEN p_success THEN 'success' ELSE 'failure' END,
        p_ip_address,
        p_user_agent,
        p_error_message
    );

    IF NOT p_success THEN
        -- Increment failed login attempts
        UPDATE users
        SET failed_login_attempts = failed_login_attempts + 1,
            is_locked = CASE
                WHEN failed_login_attempts + 1 >= 5 THEN true
                ELSE false
            END,
            locked_until = CASE
                WHEN failed_login_attempts + 1 >= 5 THEN NOW() + INTERVAL '30 minutes'
                ELSE NULL
            END
        WHERE id = p_user_id;
    ELSE
        -- Reset failed login attempts on success
        UPDATE users
        SET failed_login_attempts = 0,
            is_locked = false,
            locked_until = NULL,
            last_login_at = NOW()
        WHERE id = p_user_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to unlock expired account locks
CREATE OR REPLACE FUNCTION unlock_expired_locks()
RETURNS void AS $$
BEGIN
    UPDATE users
    SET is_locked = false,
        locked_until = NULL,
        failed_login_attempts = 0
    WHERE is_locked = true
      AND locked_until IS NOT NULL
      AND locked_until < NOW();
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE refresh_tokens IS 'JWT refresh tokens for maintaining user sessions';
COMMENT ON TABLE audit_log IS 'Security audit log for tracking authentication events';
COMMENT ON COLUMN users.password_hash IS 'Bcrypt hashed password';
COMMENT ON COLUMN users.role IS 'User role: system_admin (ORLA internal), org_admin (customer admin), user (team member)';
COMMENT ON COLUMN users.is_locked IS 'Account locked due to failed login attempts';

-- ============================================================================
-- SUMMARY
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
    RAISE NOTICE '✅ AUTHENTICATION SYSTEM MIGRATION COMPLETE';
    RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
    RAISE NOTICE '';
    RAISE NOTICE '📊 Tables Updated:';
    RAISE NOTICE '   ✓ users (added auth fields)';
    RAISE NOTICE '   ✓ refresh_tokens (created)';
    RAISE NOTICE '   ✓ audit_log (created)';
    RAISE NOTICE '';
    RAISE NOTICE '🔐 Authentication Features:';
    RAISE NOTICE '   ✓ Password hashing support';
    RAISE NOTICE '   ✓ Email verification';
    RAISE NOTICE '   ✓ Password reset tokens';
    RAISE NOTICE '   ✓ User roles (system_admin, org_admin, user)';
    RAISE NOTICE '   ✓ Account locking after 5 failed attempts';
    RAISE NOTICE '   ✓ JWT refresh token storage';
    RAISE NOTICE '   ✓ Security audit logging';
    RAISE NOTICE '';
    RAISE NOTICE '👤 System User upgraded to system_admin role';
    RAISE NOTICE '';
    RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
END $$;
