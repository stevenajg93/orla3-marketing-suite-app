-- Migration: Add oauth_states table for OAuth CSRF protection
-- This table stores temporary state tokens during OAuth flows

CREATE TABLE IF NOT EXISTS oauth_states (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    state VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_user_platform UNIQUE (user_id, platform)
);

-- Index for fast state lookup during OAuth callback
CREATE INDEX IF NOT EXISTS idx_oauth_states_state ON oauth_states(state);

-- Index for user + platform lookup
CREATE INDEX IF NOT EXISTS idx_oauth_states_user_platform ON oauth_states(user_id, platform);

-- Index for cleanup of expired states
CREATE INDEX IF NOT EXISTS idx_oauth_states_expires_at ON oauth_states(expires_at);

-- Add comments
COMMENT ON TABLE oauth_states IS 'Temporary OAuth state tokens for CSRF protection during social media OAuth flows';
COMMENT ON COLUMN oauth_states.state IS 'Random token to prevent CSRF attacks during OAuth';
COMMENT ON COLUMN oauth_states.expires_at IS 'State tokens expire after 10 minutes';
