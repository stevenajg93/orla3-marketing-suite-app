-- Migration: Add auto-reply settings table for real-time comment monitoring
-- Date: 2025-01-14
-- Purpose: Store user preferences for automated comment replies

CREATE TABLE IF NOT EXISTS auto_reply_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Enable/disable auto-reply per platform
    enabled BOOLEAN DEFAULT false,
    platforms JSONB DEFAULT '[]'::jsonb, -- Array of platforms to monitor: ["instagram", "facebook", "twitter"]

    -- Reply behavior
    reply_to_questions BOOLEAN DEFAULT true,
    reply_to_mentions BOOLEAN DEFAULT true,
    reply_to_all_comments BOOLEAN DEFAULT false,

    -- Sentiment filters
    reply_to_positive BOOLEAN DEFAULT true,
    reply_to_neutral BOOLEAN DEFAULT true,
    reply_to_negative BOOLEAN DEFAULT false, -- Safer to not auto-reply to negative

    -- AI reply configuration
    reply_tone VARCHAR(50) DEFAULT 'friendly', -- friendly, professional, casual, enthusiastic
    reply_length VARCHAR(50) DEFAULT 'short', -- short, medium, long
    custom_instructions TEXT, -- Additional instructions for AI (e.g., "Always include a call to action")

    -- Rate limiting
    max_replies_per_hour INTEGER DEFAULT 10,
    min_reply_interval_minutes INTEGER DEFAULT 15, -- Don't reply more than once per 15 minutes

    -- Timestamps
    last_check_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Ensure one settings record per user
    UNIQUE(user_id)
);

-- Index for faster lookups
CREATE INDEX idx_auto_reply_settings_user_id ON auto_reply_settings(user_id);
CREATE INDEX idx_auto_reply_settings_enabled ON auto_reply_settings(enabled) WHERE enabled = true;

-- Comment on table
COMMENT ON TABLE auto_reply_settings IS 'User preferences for automated social media comment replies';
