-- ============================================================================
-- Migration: Add 'generating' status and 'image' content type
-- Date: 2025-11-11
-- Purpose: Allow AI-generated content to save while being generated
-- ============================================================================

-- Add 'generating' to the allowed status values
ALTER TABLE content_library
DROP CONSTRAINT IF EXISTS content_library_status_check;

ALTER TABLE content_library
ADD CONSTRAINT content_library_status_check
CHECK (status IN ('draft', 'published', 'scheduled', 'archived', 'generating'));

-- Add 'image' to the allowed content_type values
ALTER TABLE content_library
DROP CONSTRAINT IF EXISTS content_library_content_type_check;

ALTER TABLE content_library
ADD CONSTRAINT content_library_content_type_check
CHECK (content_type IN ('blog', 'carousel', 'social', 'video', 'image'));

-- Done!
-- Now AI images and videos can save with status='generating'
-- When complete, status will be updated to 'draft'
