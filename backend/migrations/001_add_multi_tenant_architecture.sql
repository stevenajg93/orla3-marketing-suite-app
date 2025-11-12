-- ============================================================================
-- MIGRATION 001: ADD MULTI-TENANT ARCHITECTURE
-- Description: Add user authentication tables and per-user cloud storage tokens
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- For token encryption

-- ============================================================================
-- USERS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,

    -- Organization details
    organization_name TEXT,
    organization_slug TEXT UNIQUE,

    -- Account status
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin', 'superadmin')),
    plan TEXT NOT NULL DEFAULT 'free' CHECK (plan IN ('free', 'starter', 'pro', 'enterprise')),
    is_active BOOLEAN NOT NULL DEFAULT true,
    email_verified BOOLEAN NOT NULL DEFAULT false,

    -- Security
    failed_login_attempts INTEGER DEFAULT 0,
    is_locked BOOLEAN DEFAULT false,
    locked_until TIMESTAMPTZ,

    -- Verification tokens
    verification_token TEXT,
    verification_token_expires TIMESTAMPTZ,
    reset_token TEXT,
    reset_token_expires TIMESTAMPTZ,

    -- Profile
    profile_image_url TEXT,
    timezone TEXT DEFAULT 'UTC',

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_org_slug ON users(organization_slug) WHERE organization_slug IS NOT NULL;
CREATE INDEX idx_users_created ON users(created_at DESC);

-- ============================================================================
-- REFRESH TOKENS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    is_revoked BOOLEAN DEFAULT false,
    revoked_at TIMESTAMPTZ,
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens(token_hash);
CREATE INDEX idx_refresh_tokens_expires ON refresh_tokens(expires_at);

-- ============================================================================
-- AUDIT LOG TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    event_type TEXT NOT NULL,  -- 'login', 'logout', 'register', 'password_reset', etc.
    event_status TEXT NOT NULL CHECK (event_status IN ('success', 'failure')),
    ip_address INET,
    user_agent TEXT,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_type ON audit_log(event_type);
CREATE INDEX idx_audit_created ON audit_log(created_at DESC);

-- ============================================================================
-- CLOUD STORAGE TOKENS TABLE (Multi-Tenant)
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_cloud_storage_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Provider info
    provider TEXT NOT NULL CHECK (provider IN ('google_drive', 'onedrive', 'dropbox')),
    provider_user_id TEXT,  -- User ID from the cloud provider
    provider_email TEXT,     -- Email associated with cloud account

    -- OAuth tokens (encrypted)
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    token_expires_at TIMESTAMPTZ NOT NULL,

    -- Provider-specific metadata
    metadata JSONB DEFAULT '{}'::jsonb,  -- Store drive IDs, folder paths, etc.

    -- Status
    is_active BOOLEAN DEFAULT true,
    last_refreshed_at TIMESTAMPTZ,

    -- Timestamps
    connected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraint: One active connection per user per provider
    CONSTRAINT unique_user_provider UNIQUE (user_id, provider)
);

CREATE INDEX idx_cloud_tokens_user ON user_cloud_storage_tokens(user_id);
CREATE INDEX idx_cloud_tokens_provider ON user_cloud_storage_tokens(provider);
CREATE INDEX idx_cloud_tokens_active ON user_cloud_storage_tokens(is_active) WHERE is_active = true;
CREATE INDEX idx_cloud_tokens_expires ON user_cloud_storage_tokens(token_expires_at);

COMMENT ON TABLE user_cloud_storage_tokens IS 'Stores per-user OAuth tokens for cloud storage providers (Google Drive, OneDrive, Dropbox)';
COMMENT ON COLUMN user_cloud_storage_tokens.access_token IS 'Encrypted OAuth access token';
COMMENT ON COLUMN user_cloud_storage_tokens.refresh_token IS 'Encrypted OAuth refresh token';

-- ============================================================================
-- ADD user_id TO EXISTING TABLES
-- ============================================================================

-- Add user_id to brand_strategy
ALTER TABLE brand_strategy
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_brand_strategy_user ON brand_strategy(user_id);

-- Add user_id to brand_voice_assets
ALTER TABLE brand_voice_assets
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_brand_voice_assets_user ON brand_voice_assets(user_id);

-- Update category check constraint to include new categories
ALTER TABLE brand_voice_assets
DROP CONSTRAINT IF EXISTS brand_voice_assets_category_check;

ALTER TABLE brand_voice_assets
ADD CONSTRAINT brand_voice_assets_category_check
CHECK (category IN ('guidelines', 'voice_samples', 'logos', 'target_audience_insights'));

-- Add user_id to competitors
ALTER TABLE competitors
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_competitors_user ON competitors(user_id);

-- Add user_id to competitor_analyses (cascade from competitors)
-- Note: competitor_analyses already has FK to competitors, so user isolation is inherited

-- Add user_id to content_library
ALTER TABLE content_library
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_content_library_user ON content_library(user_id);

-- Add user_id to content_calendar
ALTER TABLE content_calendar
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_content_calendar_user ON content_calendar(user_id);

-- Add user_id to published_posts
ALTER TABLE published_posts
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_published_posts_user ON published_posts(user_id);

-- ============================================================================
-- ADD BRAND ASSET COLUMNS TO brand_strategy
-- ============================================================================
ALTER TABLE brand_strategy
ADD COLUMN IF NOT EXISTS brand_colors TEXT[] DEFAULT ARRAY[]::TEXT[],
ADD COLUMN IF NOT EXISTS brand_fonts TEXT[] DEFAULT ARRAY[]::TEXT[],
ADD COLUMN IF NOT EXISTS logo_url TEXT,
ADD COLUMN IF NOT EXISTS primary_color TEXT,
ADD COLUMN IF NOT EXISTS secondary_color TEXT;

COMMENT ON COLUMN brand_strategy.brand_colors IS 'Array of hex color codes extracted from brand guidelines';
COMMENT ON COLUMN brand_strategy.brand_fonts IS 'Array of font family names used in brand';
COMMENT ON COLUMN brand_strategy.logo_url IS 'URL or file path to primary brand logo (GCS or local)';
COMMENT ON COLUMN brand_strategy.primary_color IS 'Primary brand color hex code';
COMMENT ON COLUMN brand_strategy.secondary_color IS 'Secondary brand color hex code';

-- ============================================================================
-- UPDATE UNIQUE CONSTRAINTS FOR MULTI-TENANCY
-- ============================================================================

-- Drop old unique constraint on brand_strategy (one per tenant, not global)
DROP INDEX IF EXISTS idx_active_strategy;

-- Create unique constraint: one active strategy per user
CREATE UNIQUE INDEX IF NOT EXISTS idx_active_strategy_per_user
ON brand_strategy (user_id)
WHERE user_id IS NOT NULL;

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to record login attempts (security)
CREATE OR REPLACE FUNCTION record_login_attempt(
    p_user_id UUID,
    p_success BOOLEAN,
    p_ip_address INET,
    p_user_agent TEXT,
    p_error_message TEXT DEFAULT NULL
)
RETURNS void AS $$
DECLARE
    v_failed_attempts INTEGER;
BEGIN
    -- Insert audit log
    INSERT INTO audit_log (
        user_id, event_type, event_status, ip_address, user_agent, error_message
    ) VALUES (
        p_user_id, 'login',
        CASE WHEN p_success THEN 'success' ELSE 'failure' END,
        p_ip_address, p_user_agent, p_error_message
    );

    IF p_success THEN
        -- Reset failed attempts on successful login
        UPDATE users
        SET failed_login_attempts = 0,
            is_locked = false,
            locked_until = NULL,
            last_login_at = NOW()
        WHERE id = p_user_id;
    ELSE
        -- Increment failed attempts
        UPDATE users
        SET failed_login_attempts = failed_login_attempts + 1
        WHERE id = p_user_id
        RETURNING failed_login_attempts INTO v_failed_attempts;

        -- Lock account after 5 failed attempts
        IF v_failed_attempts >= 5 THEN
            UPDATE users
            SET is_locked = true,
                locked_until = NOW() + INTERVAL '30 minutes'
            WHERE id = p_user_id;
        END IF;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to clean expired refresh tokens (scheduled job)
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM refresh_tokens
    WHERE expires_at < NOW() OR (is_revoked = true AND revoked_at < NOW() - INTERVAL '30 days');

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to refresh cloud storage token
CREATE OR REPLACE FUNCTION refresh_cloud_storage_token(
    p_token_id UUID,
    p_new_access_token TEXT,
    p_new_expires_at TIMESTAMPTZ
)
RETURNS void AS $$
BEGIN
    UPDATE user_cloud_storage_tokens
    SET access_token = p_new_access_token,
        token_expires_at = p_new_expires_at,
        last_refreshed_at = NOW(),
        updated_at = NOW()
    WHERE id = p_token_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- UPDATE TRIGGERS
-- ============================================================================

-- Trigger for users.updated_at
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Trigger for user_cloud_storage_tokens.updated_at
DROP TRIGGER IF EXISTS update_cloud_tokens_updated_at ON user_cloud_storage_tokens;
CREATE TRIGGER update_cloud_tokens_updated_at
BEFORE UPDATE ON user_cloud_storage_tokens
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE users IS 'User accounts for the Orla³ Marketing Suite';
COMMENT ON TABLE refresh_tokens IS 'JWT refresh tokens for authentication';
COMMENT ON TABLE audit_log IS 'Security audit log for user actions';
COMMENT ON TABLE user_cloud_storage_tokens IS 'Per-user OAuth tokens for cloud storage providers';

COMMENT ON FUNCTION record_login_attempt IS 'Records login attempts and handles account locking after failed attempts';
COMMENT ON FUNCTION cleanup_expired_tokens IS 'Removes expired and old revoked refresh tokens (run as scheduled job)';
COMMENT ON FUNCTION refresh_cloud_storage_token IS 'Updates cloud storage access token after refresh';
