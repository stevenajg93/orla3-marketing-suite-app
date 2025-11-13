-- Migration: Add metadata column to oauth_states for PKCE support
-- This column stores the code_verifier for Twitter OAuth 2.0 PKCE flow

ALTER TABLE oauth_states ADD COLUMN IF NOT EXISTS metadata JSONB;

-- Add comment
COMMENT ON COLUMN oauth_states.metadata IS 'JSON metadata for OAuth flow (e.g., PKCE code_verifier for Twitter)';
