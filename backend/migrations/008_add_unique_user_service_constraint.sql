-- Migration: Add unique constraint on (user_id, service_type)
-- This ensures users can only connect ONE account per platform
-- Required for ON CONFLICT clause in OAuth token storage

CREATE UNIQUE INDEX IF NOT EXISTS idx_connected_services_user_service
ON connected_services(user_id, service_type);

-- Add comment
COMMENT ON INDEX idx_connected_services_user_service
IS 'Ensures one connection per user per service type (e.g., one Twitter account per user)';
