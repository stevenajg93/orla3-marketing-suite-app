-- ============================================================================
-- MULTI-TENANT ARCHITECTURE MIGRATION
-- Migration: 003_add_multi_tenant.sql
-- Purpose: Add user_id to all tables for multi-tenant SaaS architecture
-- ============================================================================

-- ============================================================================
-- USERS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Authentication (for future auth integration)
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,

    -- Organization info
    organization_name TEXT,
    organization_slug TEXT UNIQUE,  -- URL-friendly name

    -- Subscription (for future billing)
    plan TEXT DEFAULT 'free' CHECK (plan IN ('free', 'starter', 'pro', 'enterprise')),
    is_active BOOLEAN DEFAULT true,

    -- Metadata
    profile_image_url TEXT,
    timezone TEXT DEFAULT 'UTC',
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_org_slug ON users(organization_slug) WHERE organization_slug IS NOT NULL;
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = true;

-- Trigger for updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ADD user_id TO EXISTING TABLES
-- ============================================================================

-- Brand Strategy
ALTER TABLE brand_strategy
    ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_brand_strategy_user ON brand_strategy(user_id);

-- Make user_id unique per user (only one active strategy per user)
DROP INDEX IF EXISTS idx_active_strategy;
CREATE UNIQUE INDEX idx_active_strategy_per_user
    ON brand_strategy(COALESCE(user_id, '00000000-0000-0000-0000-000000000000'::uuid));

-- Brand Voice Assets
ALTER TABLE brand_voice_assets
    ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_brand_assets_user ON brand_voice_assets(user_id);

-- Competitors
ALTER TABLE competitors
    ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_competitors_user ON competitors(user_id);

-- Competitor Analyses (inherits from competitors, but add for direct queries)
ALTER TABLE competitor_analyses
    ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_analyses_user ON competitor_analyses(user_id);

-- Content Library
ALTER TABLE content_library
    ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_content_user ON content_library(user_id);

-- Content Calendar
ALTER TABLE content_calendar
    ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_calendar_user ON content_calendar(user_id);

-- Published Posts
ALTER TABLE published_posts
    ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_posts_user ON published_posts(user_id);

-- Social Accounts (already has user_id, but ensure index exists)
CREATE INDEX IF NOT EXISTS idx_social_accounts_user_active ON social_accounts(user_id)
    WHERE user_id IS NOT NULL AND is_active = true;

-- ============================================================================
-- CONNECTED SERVICES TABLE (for Drive, WordPress OAuth)
-- ============================================================================

CREATE TABLE IF NOT EXISTS connected_services (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- User relationship
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- Service identification
    service_type TEXT NOT NULL CHECK (service_type IN ('google_drive', 'wordpress', 'dropbox', 'notion')),

    -- OAuth credentials
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_expires_at TIMESTAMPTZ,

    -- Service details
    service_name TEXT NOT NULL,  -- User-friendly name (e.g., "My Drive", "Company Blog")
    service_id TEXT NOT NULL,    -- Service's identifier (e.g., Drive ID, WordPress site ID)
    service_url TEXT,

    -- Service-specific metadata
    service_metadata JSONB DEFAULT '{}'::jsonb,

    -- Status
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,  -- Default service for this type
    last_token_refresh TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,

    -- Timestamps
    connected_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    UNIQUE(user_id, service_type, service_id),
    CHECK (access_token != '')
);

-- Indexes
CREATE INDEX idx_connected_services_user ON connected_services(user_id);
CREATE INDEX idx_connected_services_type ON connected_services(service_type);
CREATE INDEX idx_connected_services_active ON connected_services(is_active) WHERE is_active = true;
CREATE INDEX idx_connected_services_expires ON connected_services(token_expires_at) WHERE token_expires_at IS NOT NULL;

-- Only one default service per type per user
CREATE UNIQUE INDEX idx_connected_services_default
    ON connected_services(user_id, service_type)
    WHERE is_default = true;

-- Trigger for updated_at
CREATE TRIGGER update_connected_services_updated_at
    BEFORE UPDATE ON connected_services
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- CREATE SYSTEM USER (for existing ORLA data)
-- ============================================================================

-- Insert System User (represents ORLA's internal account)
INSERT INTO users (
    id,
    email,
    name,
    organization_name,
    organization_slug,
    plan,
    created_at
) VALUES (
    '00000000-0000-0000-0000-000000000000'::uuid,
    'system@orla3.com',
    'ORLA³ Studio',
    'ORLA³ Studio',
    'orla3-studio',
    'enterprise',
    NOW()
) ON CONFLICT (id) DO NOTHING;

-- Assign all existing data to System User
UPDATE brand_strategy SET user_id = '00000000-0000-0000-0000-000000000000'::uuid WHERE user_id IS NULL;
UPDATE brand_voice_assets SET user_id = '00000000-0000-0000-0000-000000000000'::uuid WHERE user_id IS NULL;
UPDATE competitors SET user_id = '00000000-0000-0000-0000-000000000000'::uuid WHERE user_id IS NULL;
UPDATE competitor_analyses SET user_id = '00000000-0000-0000-0000-000000000000'::uuid WHERE user_id IS NULL;
UPDATE content_library SET user_id = '00000000-0000-0000-0000-000000000000'::uuid WHERE user_id IS NULL;
UPDATE content_calendar SET user_id = '00000000-0000-0000-0000-000000000000'::uuid WHERE user_id IS NULL;
UPDATE published_posts SET user_id = '00000000-0000-0000-0000-000000000000'::uuid WHERE user_id IS NULL;
UPDATE social_accounts SET user_id = '00000000-0000-0000-0000-000000000000'::uuid WHERE user_id IS NULL;

-- Create System User's Google Drive service connection (from existing env vars)
-- Note: This will be replaced by OAuth later, but preserves current functionality
INSERT INTO connected_services (
    user_id,
    service_type,
    service_name,
    service_id,
    service_url,
    access_token,
    refresh_token,
    is_default,
    service_metadata
)
SELECT
    '00000000-0000-0000-0000-000000000000'::uuid,
    'google_drive',
    'GECS Labs Drive',
    '0AM2nUL9uMdpsUk9PVA',  -- SHARED_DRIVE_ID
    'https://drive.google.com/drive/folders/0AM2nUL9uMdpsUk9PVA',
    'system_credentials',  -- Placeholder - actual credentials from env
    'system_credentials',  -- Placeholder - actual credentials from env
    true,
    jsonb_build_object(
        'drive_name', 'GECS Labs',
        'marketing_folder', 'Marketing',
        'legacy', true,
        'note', 'Migrated from environment variables'
    )
WHERE NOT EXISTS (
    SELECT 1 FROM connected_services
    WHERE user_id = '00000000-0000-0000-0000-000000000000'::uuid
    AND service_type = 'google_drive'
);

-- Create System User's WordPress service connection (from existing env vars)
INSERT INTO connected_services (
    user_id,
    service_type,
    service_name,
    service_id,
    service_url,
    access_token,
    is_default,
    service_metadata
)
SELECT
    '00000000-0000-0000-0000-000000000000'::uuid,
    'wordpress',
    'ORLA WordPress',
    'sgillespiea7d7336966-wgdcj.wordpress.com',  -- WORDPRESS_SITE_ID
    'https://sgillespiea7d7336966-wgdcj.wordpress.com',
    'system_credentials',  -- Placeholder - actual credentials from env
    true,
    jsonb_build_object(
        'site_id', 'sgillespiea7d7336966-wgdcj.wordpress.com',
        'username', 'admin',
        'legacy', true,
        'note', 'Migrated from environment variables'
    )
WHERE NOT EXISTS (
    SELECT 1 FROM connected_services
    WHERE user_id = '00000000-0000-0000-0000-000000000000'::uuid
    AND service_type = 'wordpress'
);

-- ============================================================================
-- UPDATE VIEWS FOR MULTI-TENANT
-- ============================================================================

-- Drop and recreate views with user_id
DROP VIEW IF EXISTS recent_content;
CREATE VIEW recent_content AS
SELECT
    cl.*,
    COALESCE(
        (SELECT json_agg(json_build_object('platform', platform, 'post_url', post_url, 'published_at', published_at))
         FROM published_posts pp WHERE pp.content_id = cl.id AND pp.user_id = cl.user_id),
        '[]'::json
    ) as published_posts
FROM content_library cl
ORDER BY cl.created_at DESC;

DROP VIEW IF EXISTS competitor_summary;
CREATE VIEW competitor_summary AS
SELECT
    c.*,
    ca.summary as latest_analysis_summary,
    ca.threat_level
FROM competitors c
LEFT JOIN LATERAL (
    SELECT * FROM competitor_analyses
    WHERE competitor_id = c.id
    AND user_id = c.user_id
    ORDER BY analyzed_at DESC
    LIMIT 1
) ca ON true
ORDER BY c.created_at DESC;

DROP VIEW IF EXISTS connected_accounts_summary;
CREATE OR REPLACE VIEW connected_accounts_summary AS
SELECT
    user_id,
    platform,
    COUNT(*) as total_accounts,
    COUNT(*) FILTER (WHERE is_active = true) as active_accounts,
    COUNT(*) FILTER (WHERE is_default = true) as default_accounts,
    MAX(connected_at) as last_connected
FROM social_accounts
GROUP BY user_id, platform
ORDER BY user_id, platform;

-- ============================================================================
-- HELPER FUNCTIONS FOR MULTI-TENANT
-- ============================================================================

-- Function to get user's content stats
CREATE OR REPLACE FUNCTION get_content_stats(p_user_id UUID)
RETURNS TABLE(
    content_type TEXT,
    status TEXT,
    count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        cl.content_type,
        cl.status,
        COUNT(*) as count
    FROM content_library cl
    WHERE cl.user_id = p_user_id
    GROUP BY cl.content_type, cl.status
    ORDER BY cl.content_type, cl.status;
END;
$$ LANGUAGE plpgsql;

-- Function to check if user has access to resource
CREATE OR REPLACE FUNCTION user_owns_resource(p_user_id UUID, p_table_name TEXT, p_resource_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    owner_id UUID;
BEGIN
    EXECUTE format('SELECT user_id FROM %I WHERE id = $1', p_table_name)
    INTO owner_id
    USING p_resource_id;

    RETURN owner_id = p_user_id OR owner_id IS NULL;
END;
$$ LANGUAGE plpgsql;

-- Function to get user's connected services
CREATE OR REPLACE FUNCTION get_user_services(p_user_id UUID, p_service_type TEXT DEFAULT NULL)
RETURNS TABLE(
    id UUID,
    service_type TEXT,
    service_name TEXT,
    service_url TEXT,
    is_default BOOLEAN,
    connected_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        cs.id,
        cs.service_type,
        cs.service_name,
        cs.service_url,
        cs.is_default,
        cs.connected_at
    FROM connected_services cs
    WHERE cs.user_id = p_user_id
      AND cs.is_active = true
      AND (p_service_type IS NULL OR cs.service_type = p_service_type)
    ORDER BY cs.is_default DESC, cs.connected_at DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE users IS 'Multi-tenant user accounts';
COMMENT ON TABLE connected_services IS 'OAuth credentials for Google Drive, WordPress, etc.';
COMMENT ON COLUMN users.organization_slug IS 'URL-friendly organization identifier';
COMMENT ON COLUMN connected_services.service_metadata IS 'Service-specific configuration (Drive IDs, WordPress site IDs, etc.)';

-- ============================================================================
-- SUMMARY
-- ============================================================================

-- Output migration summary
DO $$
BEGIN
    RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
    RAISE NOTICE '✅ MULTI-TENANT MIGRATION COMPLETE';
    RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
    RAISE NOTICE '';
    RAISE NOTICE '📊 Tables Updated:';
    RAISE NOTICE '   ✓ users (created)';
    RAISE NOTICE '   ✓ connected_services (created)';
    RAISE NOTICE '   ✓ brand_strategy (added user_id)';
    RAISE NOTICE '   ✓ brand_voice_assets (added user_id)';
    RAISE NOTICE '   ✓ competitors (added user_id)';
    RAISE NOTICE '   ✓ competitor_analyses (added user_id)';
    RAISE NOTICE '   ✓ content_library (added user_id)';
    RAISE NOTICE '   ✓ content_calendar (added user_id)';
    RAISE NOTICE '   ✓ published_posts (added user_id)';
    RAISE NOTICE '   ✓ social_accounts (already had user_id)';
    RAISE NOTICE '';
    RAISE NOTICE '👤 System User Created:';
    RAISE NOTICE '   ID: 00000000-0000-0000-0000-000000000000';
    RAISE NOTICE '   Email: system@orla3.com';
    RAISE NOTICE '   Org: ORLA³ Studio';
    RAISE NOTICE '';
    RAISE NOTICE '🔗 All existing data assigned to System User';
    RAISE NOTICE '✅ ORLA data preserved and functional';
    RAISE NOTICE '';
    RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
END $$;
