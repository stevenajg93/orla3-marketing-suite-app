-- Add folder selection to cloud storage connections
-- Allows users to limit which folders the app can access

ALTER TABLE user_cloud_storage_tokens
ADD COLUMN IF NOT EXISTS selected_folders JSONB DEFAULT '[]'::jsonb;

COMMENT ON COLUMN user_cloud_storage_tokens.selected_folders IS
'Array of folder IDs/paths that user has granted access to. Empty array means all folders accessible.';
