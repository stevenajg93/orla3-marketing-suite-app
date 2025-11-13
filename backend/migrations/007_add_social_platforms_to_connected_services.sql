-- Migration: Add social media platforms to connected_services constraint
-- The connected_services table was originally for cloud storage (Drive, Dropbox, etc.)
-- Now it also supports 9 social media platforms for OAuth connections

-- Drop old constraint that only allowed cloud storage
ALTER TABLE connected_services DROP CONSTRAINT IF EXISTS connected_services_service_type_check;

-- Add new constraint with both cloud storage AND social media platforms
ALTER TABLE connected_services ADD CONSTRAINT connected_services_service_type_check
CHECK (service_type = ANY (ARRAY[
    -- Cloud Storage (original)
    'google_drive'::text,
    'wordpress'::text,
    'dropbox'::text,
    'notion'::text,
    -- Social Media Platforms (new)
    'instagram'::text,
    'linkedin'::text,
    'twitter'::text,
    'facebook'::text,
    'tiktok'::text,
    'youtube'::text,
    'reddit'::text,
    'tumblr'::text
]));

-- Add comment
COMMENT ON CONSTRAINT connected_services_service_type_check ON connected_services
IS 'Allowed service types: cloud storage (google_drive, wordpress, dropbox, notion) and social media (instagram, linkedin, twitter, facebook, tiktok, youtube, reddit, tumblr)';
