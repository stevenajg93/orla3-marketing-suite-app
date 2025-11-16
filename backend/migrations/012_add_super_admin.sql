-- Migration 012: Add Super Admin System
-- Date: 2025-11-16
-- Description: Add super admin capabilities for platform management

BEGIN;

-- ============================================================================
-- ADD SUPER ADMIN COLUMNS TO USERS TABLE
-- ============================================================================

-- Add super admin flag
ALTER TABLE users
ADD COLUMN IF NOT EXISTS is_super_admin BOOLEAN DEFAULT false;

-- Add credits exempt flag (for super admins and special accounts)
ALTER TABLE users
ADD COLUMN IF NOT EXISTS credits_exempt BOOLEAN DEFAULT false;

-- Add last login tracking
ALTER TABLE users
ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ;

-- Add account status
ALTER TABLE users
ADD COLUMN IF NOT EXISTS account_status TEXT DEFAULT 'active'
    CHECK (account_status IN ('active', 'suspended', 'banned', 'trial'));

-- Add admin notes field
ALTER TABLE users
ADD COLUMN IF NOT EXISTS admin_notes TEXT;

CREATE INDEX IF NOT EXISTS idx_users_is_super_admin ON users(is_super_admin) WHERE is_super_admin = true;
CREATE INDEX IF NOT EXISTS idx_users_account_status ON users(account_status);

-- ============================================================================
-- SET INITIAL SUPER ADMIN
-- ============================================================================

-- Set s.gillespie@gecslabs.com as super admin with unlimited credits
UPDATE users
SET
    is_super_admin = true,
    credits_exempt = true,
    account_status = 'active',
    admin_notes = 'Platform founder - Super admin with unlimited credits'
WHERE email = 's.gillespie@gecslabs.com';

-- ============================================================================
-- ADMIN AUDIT LOG TABLE
-- ============================================================================

-- Track all admin actions for accountability
CREATE TABLE IF NOT EXISTS admin_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    admin_user_id UUID NOT NULL REFERENCES users(id),
    action_type TEXT NOT NULL, -- 'grant_credits', 'suspend_user', 'change_plan', 'delete_content', etc.
    target_user_id UUID REFERENCES users(id),
    target_organization_id UUID REFERENCES organizations(id),
    details JSONB, -- Structured data about what changed
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_admin_audit_admin ON admin_audit_log(admin_user_id);
CREATE INDEX idx_admin_audit_target_user ON admin_audit_log(target_user_id);
CREATE INDEX idx_admin_audit_created ON admin_audit_log(created_at DESC);

-- ============================================================================
-- ADMIN FUNCTIONS
-- ============================================================================

-- Function to check if user is super admin
CREATE OR REPLACE FUNCTION is_user_super_admin(p_user_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    is_admin BOOLEAN;
BEGIN
    SELECT is_super_admin INTO is_admin
    FROM users
    WHERE id = p_user_id;

    RETURN COALESCE(is_admin, false);
END;
$$ LANGUAGE plpgsql;

-- Function to grant credits to a user (admin only)
CREATE OR REPLACE FUNCTION admin_grant_credits(
    p_admin_user_id UUID,
    p_target_user_id UUID,
    p_credits INTEGER,
    p_reason TEXT
)
RETURNS BOOLEAN AS $$
BEGIN
    -- Verify admin
    IF NOT is_user_super_admin(p_admin_user_id) THEN
        RAISE EXCEPTION 'Unauthorized: User is not a super admin';
    END IF;

    -- Add credits
    UPDATE users
    SET credit_balance = credit_balance + p_credits
    WHERE id = p_target_user_id;

    -- Log transaction
    INSERT INTO credit_transactions (
        user_id,
        amount,
        transaction_type,
        description
    ) VALUES (
        p_target_user_id,
        p_credits,
        'admin_grant',
        p_reason
    );

    -- Log admin action
    INSERT INTO admin_audit_log (
        admin_user_id,
        action_type,
        target_user_id,
        details
    ) VALUES (
        p_admin_user_id,
        'grant_credits',
        p_target_user_id,
        jsonb_build_object(
            'credits', p_credits,
            'reason', p_reason
        )
    );

    RETURN true;
END;
$$ LANGUAGE plpgsql;

-- Function to suspend/unsuspend user account
CREATE OR REPLACE FUNCTION admin_set_account_status(
    p_admin_user_id UUID,
    p_target_user_id UUID,
    p_status TEXT,
    p_reason TEXT
)
RETURNS BOOLEAN AS $$
BEGIN
    -- Verify admin
    IF NOT is_user_super_admin(p_admin_user_id) THEN
        RAISE EXCEPTION 'Unauthorized: User is not a super admin';
    END IF;

    -- Update status
    UPDATE users
    SET account_status = p_status
    WHERE id = p_target_user_id;

    -- Log admin action
    INSERT INTO admin_audit_log (
        admin_user_id,
        action_type,
        target_user_id,
        details
    ) VALUES (
        p_admin_user_id,
        'change_account_status',
        p_target_user_id,
        jsonb_build_object(
            'new_status', p_status,
            'reason', p_reason
        )
    );

    RETURN true;
END;
$$ LANGUAGE plpgsql;

COMMIT;

-- ============================================================================
-- VERIFY MIGRATION
-- ============================================================================

SELECT
    'Super admins' AS category,
    COUNT(*) AS count
FROM users
WHERE is_super_admin = true;

SELECT
    email,
    is_super_admin,
    credits_exempt,
    account_status,
    credit_balance
FROM users
WHERE is_super_admin = true;
