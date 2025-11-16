-- Migration 011: Add Organizations and Team Multi-Tenancy
-- Date: 2025-11-16
-- Description: Implement organization/team structure with role-based access control

BEGIN;

-- ============================================================================
-- ORGANIZATIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL, -- URL-friendly identifier

    -- Subscription details
    subscription_tier TEXT NOT NULL CHECK (subscription_tier IN ('starter', 'professional', 'business', 'enterprise')),
    subscription_status TEXT DEFAULT 'active' CHECK (subscription_status IN ('active', 'suspended', 'cancelled', 'trial')),

    -- User limits based on tier
    max_users INTEGER NOT NULL DEFAULT 1,
    current_user_count INTEGER DEFAULT 1,

    -- Billing
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    billing_email TEXT,

    -- Organization storage (replaces personal cloud storage)
    storage_provider TEXT CHECK (storage_provider IN ('google_shared_drive', 'onedrive_sharepoint', 'dropbox_team', 'orla3_native', NULL)),
    storage_drive_id TEXT, -- Provider-specific ID (Shared Drive, SharePoint site, Team Folder, GCS bucket)
    storage_drive_name TEXT,
    storage_quota_gb INTEGER DEFAULT 5, -- Storage quota for orla3_native (in GB)
    storage_used_gb DECIMAL DEFAULT 0, -- Current usage for orla3_native

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT user_limit_not_exceeded CHECK (current_user_count <= max_users)
);

CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_tier ON organizations(subscription_tier);
CREATE INDEX idx_organizations_stripe ON organizations(stripe_customer_id);

-- ============================================================================
-- USER ROLES ENUM
-- ============================================================================
CREATE TYPE user_role AS ENUM ('owner', 'admin', 'member', 'viewer');

-- ============================================================================
-- ORGANIZATION MEMBERSHIPS (Junction Table)
-- ============================================================================
CREATE TABLE IF NOT EXISTS organization_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Role & permissions
    role user_role NOT NULL DEFAULT 'member',

    -- Status
    is_active BOOLEAN DEFAULT true,
    invited_at TIMESTAMPTZ DEFAULT NOW(),
    joined_at TIMESTAMPTZ,

    -- Metadata
    invited_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    UNIQUE(organization_id, user_id) -- User can only be in org once
);

CREATE INDEX idx_org_members_org ON organization_members(organization_id);
CREATE INDEX idx_org_members_user ON organization_members(user_id);
CREATE INDEX idx_org_members_role ON organization_members(role);

-- ============================================================================
-- UPDATE USERS TABLE
-- ============================================================================
-- Add personal vs organization account flag
ALTER TABLE users
ADD COLUMN IF NOT EXISTS account_type TEXT DEFAULT 'personal' CHECK (account_type IN ('personal', 'organization'));

-- Add current active organization (for users in multiple orgs)
ALTER TABLE users
ADD COLUMN IF NOT EXISTS current_organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_users_current_org ON users(current_organization_id);

-- ============================================================================
-- MIGRATE EXISTING USERS TO ORGANIZATIONS
-- ============================================================================
-- Create personal organization for each existing user
-- Map existing 'plan' column values to new 'subscription_tier' structure
INSERT INTO organizations (id, name, slug, subscription_tier, max_users, stripe_customer_id, stripe_subscription_id)
SELECT
    uuid_generate_v4(),
    COALESCE(email, 'Personal Workspace'),
    LOWER(REGEXP_REPLACE(COALESCE(email, id::text), '[^a-z0-9]', '-', 'g')),
    -- Map plan values to subscription_tier
    CASE COALESCE(plan, 'starter')
        WHEN 'free' THEN 'starter'
        WHEN 'starter' THEN 'starter'
        WHEN 'pro' THEN 'professional'
        WHEN 'business' THEN 'business'
        WHEN 'enterprise' THEN 'enterprise'
        ELSE 'starter'
    END,
    -- Set max_users based on plan
    CASE COALESCE(plan, 'starter')
        WHEN 'free' THEN 1
        WHEN 'starter' THEN 1
        WHEN 'pro' THEN 3
        WHEN 'business' THEN 10
        WHEN 'enterprise' THEN 25
        ELSE 1
    END,
    stripe_customer_id,
    stripe_subscription_id
FROM users
ON CONFLICT (slug) DO NOTHING;

-- Link users to their personal organizations
INSERT INTO organization_members (organization_id, user_id, role, joined_at)
SELECT
    o.id,
    u.id,
    'owner',
    NOW()
FROM users u
JOIN organizations o ON o.slug = LOWER(REGEXP_REPLACE(COALESCE(u.email, u.id::text), '[^a-z0-9]', '-', 'g'))
ON CONFLICT (organization_id, user_id) DO NOTHING;

-- Set current_organization_id for all users
UPDATE users u
SET current_organization_id = o.id
FROM organizations o
WHERE o.slug = LOWER(REGEXP_REPLACE(COALESCE(u.email, u.id::text), '[^a-z0-9]', '-', 'g'));

-- ============================================================================
-- UPDATE EXISTING TABLES TO USE ORGANIZATION_ID
-- ============================================================================

-- content_library: Add organization_id
ALTER TABLE content_library
ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE;

UPDATE content_library cl
SET organization_id = u.current_organization_id
FROM users u
WHERE cl.user_id = u.id;

CREATE INDEX IF NOT EXISTS idx_content_library_org ON content_library(organization_id);

-- content_calendar: Add organization_id
ALTER TABLE content_calendar
ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE;

UPDATE content_calendar cc
SET organization_id = u.current_organization_id
FROM users u
WHERE cc.user_id = u.id;

CREATE INDEX IF NOT EXISTS idx_content_calendar_org ON content_calendar(organization_id);

-- connected_services: Make organization-level
ALTER TABLE connected_services
ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE;

UPDATE connected_services cs
SET organization_id = u.current_organization_id
FROM users u
WHERE cs.user_id = u.id;

CREATE INDEX IF NOT EXISTS idx_connected_services_org ON connected_services(organization_id);

-- user_cloud_storage_tokens: Make organization-level (shared/team drives only)
ALTER TABLE user_cloud_storage_tokens
ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
ADD COLUMN IF NOT EXISTS storage_type TEXT CHECK (storage_type IN ('google_shared_drive', 'onedrive_sharepoint', 'dropbox_team', 'personal')) DEFAULT 'personal',
ADD COLUMN IF NOT EXISTS drive_id TEXT; -- Shared Drive ID, SharePoint Site ID, Team Folder ID

UPDATE user_cloud_storage_tokens ucst
SET organization_id = u.current_organization_id,
    storage_type = 'personal' -- Mark existing connections as personal (to be migrated)
FROM users u
WHERE ucst.user_id = u.id;

CREATE INDEX IF NOT EXISTS idx_cloud_storage_org ON user_cloud_storage_tokens(organization_id);

COMMENT ON COLUMN user_cloud_storage_tokens.storage_type IS 'Type of storage: google_shared_drive, onedrive_sharepoint, dropbox_team, or personal (deprecated)';

-- ============================================================================
-- ORLA³ NATIVE STORAGE TABLE (for organizations without shared drives)
-- ============================================================================
CREATE TABLE IF NOT EXISTS organization_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- File metadata
    filename TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    mime_type TEXT NOT NULL,
    file_extension TEXT,

    -- GCS storage
    gcs_bucket TEXT NOT NULL, -- e.g., 'orla3-org-storage'
    gcs_path TEXT NOT NULL, -- e.g., 'org-{uuid}/brand-assets/logo.png'
    gcs_public_url TEXT, -- Public URL if needed

    -- Organization/categorization
    folder TEXT DEFAULT 'uncategorized', -- e.g., 'brand-assets', 'content', 'logos'
    tags TEXT[], -- For searchability

    -- Audit
    uploaded_by UUID REFERENCES users(id),
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed_at TIMESTAMPTZ,
    access_count INTEGER DEFAULT 0,

    -- Soft delete
    is_deleted BOOLEAN DEFAULT false,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID REFERENCES users(id)
);

CREATE INDEX idx_org_files_org ON organization_files(organization_id);
CREATE INDEX idx_org_files_folder ON organization_files(folder);
CREATE INDEX idx_org_files_deleted ON organization_files(is_deleted);
CREATE INDEX idx_org_files_mime ON organization_files(mime_type);

-- Trigger to update storage_used_gb when files are added/deleted
CREATE OR REPLACE FUNCTION update_organization_storage_usage()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE organizations
        SET storage_used_gb = storage_used_gb + (NEW.file_size_bytes::DECIMAL / 1073741824) -- bytes to GB
        WHERE id = NEW.organization_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE organizations
        SET storage_used_gb = GREATEST(0, storage_used_gb - (OLD.file_size_bytes::DECIMAL / 1073741824))
        WHERE id = OLD.organization_id;
    ELSIF TG_OP = 'UPDATE' AND OLD.is_deleted = false AND NEW.is_deleted = true THEN
        -- Soft delete: reduce storage usage
        UPDATE organizations
        SET storage_used_gb = GREATEST(0, storage_used_gb - (OLD.file_size_bytes::DECIMAL / 1073741824))
        WHERE id = OLD.organization_id;
    ELSIF TG_OP = 'UPDATE' AND OLD.is_deleted = true AND NEW.is_deleted = false THEN
        -- Restore: increase storage usage
        UPDATE organizations
        SET storage_used_gb = storage_used_gb + (NEW.file_size_bytes::DECIMAL / 1073741824)
        WHERE id = NEW.organization_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_org_storage
AFTER INSERT OR UPDATE OR DELETE ON organization_files
FOR EACH ROW
EXECUTE FUNCTION update_organization_storage_usage();

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to check if user can add more team members
CREATE OR REPLACE FUNCTION can_add_user_to_organization(org_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    org_record RECORD;
BEGIN
    SELECT current_user_count, max_users INTO org_record
    FROM organizations
    WHERE id = org_id;

    RETURN org_record.current_user_count < org_record.max_users;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update current_user_count
CREATE OR REPLACE FUNCTION update_organization_user_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE organizations
        SET current_user_count = (
            SELECT COUNT(*)
            FROM organization_members
            WHERE organization_id = NEW.organization_id AND is_active = true
        )
        WHERE id = NEW.organization_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE organizations
        SET current_user_count = (
            SELECT COUNT(*)
            FROM organization_members
            WHERE organization_id = OLD.organization_id AND is_active = true
        )
        WHERE id = OLD.organization_id;
    ELSIF TG_OP = 'UPDATE' AND OLD.is_active != NEW.is_active THEN
        UPDATE organizations
        SET current_user_count = (
            SELECT COUNT(*)
            FROM organization_members
            WHERE organization_id = NEW.organization_id AND is_active = true
        )
        WHERE id = NEW.organization_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_org_user_count
AFTER INSERT OR UPDATE OR DELETE ON organization_members
FOR EACH ROW
EXECUTE FUNCTION update_organization_user_count();

-- ============================================================================
-- ROLE-BASED ACCESS CONTROL HELPERS
-- ============================================================================

-- Check if user has permission in organization
CREATE OR REPLACE FUNCTION user_has_org_permission(
    p_user_id UUID,
    p_organization_id UUID,
    p_required_role user_role
)
RETURNS BOOLEAN AS $$
DECLARE
    user_role_val user_role;
    role_hierarchy INTEGER;
    required_hierarchy INTEGER;
BEGIN
    -- Get user's role in the organization
    SELECT role INTO user_role_val
    FROM organization_members
    WHERE user_id = p_user_id
      AND organization_id = p_organization_id
      AND is_active = true;

    IF user_role_val IS NULL THEN
        RETURN FALSE;
    END IF;

    -- Role hierarchy: owner > admin > member > viewer
    role_hierarchy := CASE user_role_val
        WHEN 'owner' THEN 4
        WHEN 'admin' THEN 3
        WHEN 'member' THEN 2
        WHEN 'viewer' THEN 1
    END;

    required_hierarchy := CASE p_required_role
        WHEN 'owner' THEN 4
        WHEN 'admin' THEN 3
        WHEN 'member' THEN 2
        WHEN 'viewer' THEN 1
    END;

    RETURN role_hierarchy >= required_hierarchy;
END;
$$ LANGUAGE plpgsql;

COMMIT;

-- ============================================================================
-- VERIFY MIGRATION
-- ============================================================================
SELECT
    'Organizations created' AS status,
    COUNT(*) AS count
FROM organizations;

SELECT
    'Organization members' AS status,
    COUNT(*) AS count
FROM organization_members;

SELECT
    o.name AS organization,
    o.subscription_tier AS tier,
    o.current_user_count || '/' || o.max_users AS "users",
    COUNT(om.id) AS members
FROM organizations o
LEFT JOIN organization_members om ON o.id = om.organization_id
GROUP BY o.id, o.name, o.subscription_tier, o.current_user_count, o.max_users;
