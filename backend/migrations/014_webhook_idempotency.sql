-- Migration 014: Webhook Idempotency
-- Prevent duplicate processing of Stripe webhook events
-- Date: November 20, 2025

-- Webhook events tracking table
CREATE TABLE IF NOT EXISTS webhook_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id VARCHAR(255) UNIQUE NOT NULL,     -- Stripe event ID (evt_...)
    event_type VARCHAR(100) NOT NULL,           -- e.g., 'checkout.session.completed'
    processed_at TIMESTAMP DEFAULT NOW(),       -- When we processed it
    payload JSONB,                               -- Full event data (for debugging)
    processing_result VARCHAR(50),              -- 'success', 'error', 'skipped'
    error_message TEXT,                         -- If processing failed
    user_id UUID,                               -- Associated user (if applicable)
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_webhook_events_event_id ON webhook_events(event_id);
CREATE INDEX IF NOT EXISTS idx_webhook_events_type ON webhook_events(event_type, processed_at DESC);
CREATE INDEX IF NOT EXISTS idx_webhook_events_user ON webhook_events(user_id, processed_at DESC);
CREATE INDEX IF NOT EXISTS idx_webhook_events_created ON webhook_events(created_at DESC);

-- Add constraint to prevent duplicate event processing
COMMENT ON TABLE webhook_events IS 'Idempotency tracking for Stripe webhooks - prevents zombie subscriptions';
COMMENT ON COLUMN webhook_events.event_id IS 'Stripe event ID - unique constraint prevents duplicate processing';
COMMENT ON COLUMN webhook_events.processing_result IS 'Outcome: success (processed), error (failed), skipped (already processed)';

-- Function to check if event was already processed
CREATE OR REPLACE FUNCTION is_webhook_event_processed(p_event_id VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM webhook_events
        WHERE event_id = p_event_id
        AND processing_result = 'success'
    );
END;
$$ LANGUAGE plpgsql;

-- Function to record webhook event
CREATE OR REPLACE FUNCTION record_webhook_event(
    p_event_id VARCHAR,
    p_event_type VARCHAR,
    p_payload JSONB,
    p_result VARCHAR DEFAULT 'success',
    p_error_message TEXT DEFAULT NULL,
    p_user_id UUID DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_id UUID;
BEGIN
    INSERT INTO webhook_events (
        event_id,
        event_type,
        payload,
        processing_result,
        error_message,
        user_id
    ) VALUES (
        p_event_id,
        p_event_type,
        p_payload,
        p_result,
        p_error_message,
        p_user_id
    )
    ON CONFLICT (event_id) DO UPDATE SET
        processed_at = NOW(),
        processing_result = EXCLUDED.processing_result,
        error_message = EXCLUDED.error_message
    RETURNING id INTO v_id;

    RETURN v_id;
END;
$$ LANGUAGE plpgsql;

-- Cleanup old webhook events (optional - run via cron)
-- Keep last 90 days of webhook events for debugging
CREATE OR REPLACE FUNCTION cleanup_old_webhook_events()
RETURNS INTEGER AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    DELETE FROM webhook_events
    WHERE created_at < NOW() - INTERVAL '90 days'
    AND processing_result = 'success';

    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    RETURN v_deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
COMMENT ON FUNCTION is_webhook_event_processed IS 'Check if Stripe webhook event was already processed (prevents duplicates)';
COMMENT ON FUNCTION record_webhook_event IS 'Record webhook event processing for idempotency';
COMMENT ON FUNCTION cleanup_old_webhook_events IS 'Delete webhook events older than 90 days (keeps only errors/recent for debugging)';
