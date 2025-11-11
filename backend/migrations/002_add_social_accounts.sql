-- ============================================================================
-- SOCIAL ACCOUNTS TABLE - OAuth Token Storage
-- Migration: 002_add_social_accounts.sql
-- Purpose: Store OAuth credentials for multi-tenant social media posting
-- ============================================================================

-- Create social_accounts table
CREATE TABLE IF NOT EXISTS social_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- User relationship (for future multi-tenant support)
    user_id UUID,  -- Can be NULL for now, will link to users table later

    -- Platform identification
    platform TEXT NOT NULL CHECK (platform IN (
        'instagram', 'facebook', 'linkedin', 'twitter', 'x',
        'tiktok', 'youtube', 'reddit', 'tumblr', 'wordpress'
    )),

    -- OAuth credentials
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_expires_at TIMESTAMPTZ,

    -- Account details
    account_name TEXT NOT NULL,  -- Display name (e.g., "ORLA3 Studio")
    account_id TEXT NOT NULL,    -- Platform's account ID
    account_username TEXT,       -- Handle/username (e.g., @orla3studio)
    account_email TEXT,
    profile_image_url TEXT,

    -- Platform-specific metadata
    account_metadata JSONB DEFAULT '{}'::jsonb,

    -- Status and usage
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,  -- Default account for this platform
    last_token_refresh TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,

    -- Timestamps
    connected_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    UNIQUE(platform, account_id),  -- One record per platform account
    CHECK (access_token != '')     -- Token cannot be empty
);

-- Indexes for performance
CREATE INDEX idx_social_accounts_user ON social_accounts(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_social_accounts_platform ON social_accounts(platform);
CREATE INDEX idx_social_accounts_active ON social_accounts(is_active) WHERE is_active = true;
CREATE INDEX idx_social_accounts_expires ON social_accounts(token_expires_at) WHERE token_expires_at IS NOT NULL;
CREATE INDEX idx_social_accounts_last_used ON social_accounts(last_used_at DESC);

-- Only one default account per platform (per user)
CREATE UNIQUE INDEX idx_social_accounts_default
    ON social_accounts(platform, COALESCE(user_id, '00000000-0000-0000-0000-000000000000'::uuid))
    WHERE is_default = true;

-- Trigger to update updated_at
CREATE TRIGGER update_social_accounts_updated_at
    BEFORE UPDATE ON social_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to get active accounts for a platform
CREATE OR REPLACE FUNCTION get_active_accounts(p_platform TEXT, p_user_id UUID DEFAULT NULL)
RETURNS TABLE(
    id UUID,
    account_name TEXT,
    account_username TEXT,
    profile_image_url TEXT,
    is_default BOOLEAN,
    connected_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        sa.id,
        sa.account_name,
        sa.account_username,
        sa.profile_image_url,
        sa.is_default,
        sa.connected_at
    FROM social_accounts sa
    WHERE sa.platform = p_platform
      AND sa.is_active = true
      AND (p_user_id IS NULL OR sa.user_id = p_user_id)
    ORDER BY sa.is_default DESC, sa.connected_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to check if token is expired
CREATE OR REPLACE FUNCTION is_token_expired(p_account_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    expires_at TIMESTAMPTZ;
BEGIN
    SELECT token_expires_at INTO expires_at
    FROM social_accounts
    WHERE id = p_account_id;

    IF expires_at IS NULL THEN
        -- No expiry set, assume token is valid
        RETURN false;
    END IF;

    -- Add 5-minute buffer to refresh before actual expiry
    RETURN expires_at <= (NOW() + INTERVAL '5 minutes');
END;
$$ LANGUAGE plpgsql;

-- Function to update last_used_at when posting
CREATE OR REPLACE FUNCTION update_account_usage(p_account_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE social_accounts
    SET last_used_at = NOW()
    WHERE id = p_account_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: Connected accounts summary
CREATE OR REPLACE VIEW connected_accounts_summary AS
SELECT
    platform,
    COUNT(*) as total_accounts,
    COUNT(*) FILTER (WHERE is_active = true) as active_accounts,
    COUNT(*) FILTER (WHERE is_default = true) as default_accounts,
    MAX(connected_at) as last_connected
FROM social_accounts
GROUP BY platform
ORDER BY platform;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE social_accounts IS 'Stores OAuth credentials for connected social media accounts';
COMMENT ON COLUMN social_accounts.access_token IS 'OAuth access token (should be encrypted in production)';
COMMENT ON COLUMN social_accounts.refresh_token IS 'OAuth refresh token for token renewal';
COMMENT ON COLUMN social_accounts.token_expires_at IS 'When the access token expires (NULL if never expires)';
COMMENT ON COLUMN social_accounts.account_metadata IS 'Platform-specific data (permissions, page IDs, etc.)';
COMMENT ON COLUMN social_accounts.is_default IS 'Default account to use for this platform';
