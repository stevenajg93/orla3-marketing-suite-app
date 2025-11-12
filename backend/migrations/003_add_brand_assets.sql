-- ============================================================================
-- Migration: Add Brand Visual Assets to brand_strategy
-- Date: 2025-11-12
-- Description: Add columns for brand colors, fonts, and logo URL
-- ============================================================================

-- Add brand visual asset columns
ALTER TABLE brand_strategy
ADD COLUMN IF NOT EXISTS brand_colors TEXT[] DEFAULT ARRAY[]::TEXT[],
ADD COLUMN IF NOT EXISTS brand_fonts TEXT[] DEFAULT ARRAY[]::TEXT[],
ADD COLUMN IF NOT EXISTS logo_url TEXT,
ADD COLUMN IF NOT EXISTS primary_color TEXT,
ADD COLUMN IF NOT EXISTS secondary_color TEXT;

-- Add comment for documentation
COMMENT ON COLUMN brand_strategy.brand_colors IS 'Array of hex color codes extracted from brand guidelines (e.g., #FF5733)';
COMMENT ON COLUMN brand_strategy.brand_fonts IS 'Array of font family names used in brand (e.g., Helvetica, Montserrat)';
COMMENT ON COLUMN brand_strategy.logo_url IS 'URL or file path to primary brand logo';
COMMENT ON COLUMN brand_strategy.primary_color IS 'Primary brand color hex code';
COMMENT ON COLUMN brand_strategy.secondary_color IS 'Secondary brand color hex code';
