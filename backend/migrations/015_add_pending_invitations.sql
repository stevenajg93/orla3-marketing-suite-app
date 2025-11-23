-- Migration 015: Add pending_invitations table for team email invitations
-- Date: 2025-11-23
-- Description: Allow inviting non-existing users to organizations via email

-- Table to store pending invitations
CREATE TABLE IF NOT EXISTS pending_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('viewer', 'member', 'admin')),
    invitation_token VARCHAR(255) NOT NULL UNIQUE,
    invited_by UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    accepted_at TIMESTAMPTZ,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'expired', 'cancelled'))
);

-- Index for looking up invitations by email
CREATE INDEX IF NOT EXISTS idx_pending_invitations_email ON pending_invitations(email);

-- Index for looking up invitations by token
CREATE INDEX IF NOT EXISTS idx_pending_invitations_token ON pending_invitations(invitation_token);

-- Index for organization lookups
CREATE INDEX IF NOT EXISTS idx_pending_invitations_org ON pending_invitations(organization_id);

-- Prevent duplicate pending invitations to same org/email
CREATE UNIQUE INDEX IF NOT EXISTS idx_pending_invitations_unique
ON pending_invitations(organization_id, email)
WHERE status = 'pending';

-- Comments
COMMENT ON TABLE pending_invitations IS 'Stores email invitations for non-existing users to join organizations';
COMMENT ON COLUMN pending_invitations.invitation_token IS 'Unique token sent in invitation email link';
COMMENT ON COLUMN pending_invitations.expires_at IS 'Invitation expires after 7 days by default';
COMMENT ON COLUMN pending_invitations.status IS 'pending=awaiting acceptance, accepted=user joined, expired=past expiry, cancelled=revoked by admin';
