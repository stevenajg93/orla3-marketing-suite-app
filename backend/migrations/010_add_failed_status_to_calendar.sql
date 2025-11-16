-- Migration: Add 'failed' status to content_calendar
-- Date: 2025-11-16
-- Description: Allow 'failed' status for posts that encounter publishing errors

-- Drop existing constraint
ALTER TABLE content_calendar
DROP CONSTRAINT IF EXISTS content_calendar_status_check;

-- Add new constraint with 'failed' status
ALTER TABLE content_calendar
ADD CONSTRAINT content_calendar_status_check
CHECK (status IN ('scheduled', 'published', 'cancelled', 'failed'));

-- Update schema.sql documentation:
-- Line 118 should be updated to:
-- status TEXT DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'published', 'cancelled', 'failed')),
