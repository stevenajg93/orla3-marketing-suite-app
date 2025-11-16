-- ============================================================================
-- ORLA³ MARKETING SUITE - DATABASE SCHEMA
-- PostgreSQL Schema for Supabase/Neon/Railway
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- BRAND STRATEGY
-- ============================================================================
CREATE TABLE brand_strategy (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand_voice JSONB NOT NULL,
    messaging_pillars TEXT[] NOT NULL,
    language_patterns JSONB NOT NULL,
    dos_and_donts JSONB NOT NULL,
    target_audience JSONB NOT NULL,
    content_themes TEXT[],
    competitive_positioning JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Only one active strategy at a time
CREATE UNIQUE INDEX idx_active_strategy ON brand_strategy ((1));

-- ============================================================================
-- BRAND VOICE ASSETS
-- ============================================================================
CREATE TABLE brand_voice_assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('guidelines', 'voice_samples', 'community_videographer', 'community_client')),
    file_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    content_preview TEXT,
    file_size_bytes INTEGER,
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_brand_assets_category ON brand_voice_assets(category);
CREATE INDEX idx_brand_assets_uploaded ON brand_voice_assets(uploaded_at DESC);

-- ============================================================================
-- COMPETITORS
-- ============================================================================
CREATE TABLE competitors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    industry TEXT,
    location TEXT,
    social_handles JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_competitors_name ON competitors(name);

-- ============================================================================
-- COMPETITOR ANALYSES
-- ============================================================================
CREATE TABLE competitor_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    competitor_id UUID NOT NULL REFERENCES competitors(id) ON DELETE CASCADE,
    analysis_type TEXT DEFAULT 'marketing',
    summary TEXT,
    strengths TEXT[],
    weaknesses TEXT[],
    content_strategy JSONB,
    messaging_themes TEXT[],
    gaps_they_miss TEXT[],
    opportunities_for_us TEXT[],
    what_to_avoid TEXT[],
    threat_level TEXT CHECK (threat_level IN ('low', 'medium', 'high')),
    raw_analysis JSONB,
    analyzed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_analyses_competitor ON competitor_analyses(competitor_id);
CREATE INDEX idx_analyses_date ON competitor_analyses(analyzed_at DESC);

-- ============================================================================
-- CONTENT LIBRARY
-- ============================================================================
CREATE TABLE content_library (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    content_type TEXT NOT NULL CHECK (content_type IN ('blog', 'carousel', 'social', 'video')),
    content TEXT NOT NULL,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'scheduled', 'archived')),
    platform TEXT,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    media_url TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    published_at TIMESTAMPTZ,
    scheduled_for TIMESTAMPTZ
);

CREATE INDEX idx_content_type ON content_library(content_type);
CREATE INDEX idx_content_status ON content_library(status);
CREATE INDEX idx_content_created ON content_library(created_at DESC);
CREATE INDEX idx_content_tags ON content_library USING GIN(tags);
CREATE INDEX idx_content_platform ON content_library(platform) WHERE platform IS NOT NULL;

-- ============================================================================
-- CONTENT CALENDAR
-- ============================================================================
CREATE TABLE content_calendar (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_id UUID REFERENCES content_library(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    content_type TEXT NOT NULL,
    scheduled_date TIMESTAMPTZ NOT NULL,
    status TEXT DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'published', 'cancelled', 'failed')),
    platform TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_calendar_date ON content_calendar(scheduled_date);
CREATE INDEX idx_calendar_status ON content_calendar(status);
CREATE INDEX idx_calendar_content ON content_calendar(content_id) WHERE content_id IS NOT NULL;

-- ============================================================================
-- PUBLISHED POSTS (Track social media posts)
-- ============================================================================
CREATE TABLE published_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_id UUID REFERENCES content_library(id) ON DELETE SET NULL,
    platform TEXT NOT NULL,
    post_id TEXT,
    post_url TEXT,
    caption TEXT,
    media_urls TEXT[],
    published_at TIMESTAMPTZ DEFAULT NOW(),
    engagement_data JSONB DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_posts_platform ON published_posts(platform);
CREATE INDEX idx_posts_published ON published_posts(published_at DESC);
CREATE INDEX idx_posts_content ON published_posts(content_id) WHERE content_id IS NOT NULL;

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_brand_strategy_updated_at BEFORE UPDATE ON brand_strategy
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_competitors_updated_at BEFORE UPDATE ON competitors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_content_library_updated_at BEFORE UPDATE ON content_library
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_calendar_updated_at BEFORE UPDATE ON content_calendar
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: Recent content with all metadata
CREATE VIEW recent_content AS
SELECT 
    cl.*,
    COALESCE(
        (SELECT json_agg(json_build_object('platform', platform, 'post_url', post_url, 'published_at', published_at))
         FROM published_posts pp WHERE pp.content_id = cl.id),
        '[]'::json
    ) as published_posts
FROM content_library cl
ORDER BY cl.created_at DESC;

-- View: Competitor summary with latest analysis
CREATE VIEW competitor_summary AS
SELECT 
    c.*,
    ca.summary as latest_analysis_summary,
    ca.threat_level,
    ca.analyzed_at as last_analyzed
FROM competitors c
LEFT JOIN LATERAL (
    SELECT * FROM competitor_analyses 
    WHERE competitor_id = c.id 
    ORDER BY analyzed_at DESC 
    LIMIT 1
) ca ON true
ORDER BY c.created_at DESC;

-- ============================================================================
-- SAMPLE DATA FUNCTIONS
-- ============================================================================

-- Function to get content statistics
CREATE OR REPLACE FUNCTION get_content_stats()
RETURNS TABLE(
    content_type TEXT,
    status TEXT,
    count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cl.content_type,
        cl.status,
        COUNT(*) as count
    FROM content_library cl
    GROUP BY cl.content_type, cl.status
    ORDER BY cl.content_type, cl.status;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PERMISSIONS (for Supabase RLS - optional)
-- ============================================================================
-- Enable Row Level Security on tables
-- ALTER TABLE brand_strategy ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE brand_voice_assets ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE competitors ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE competitor_analyses ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE content_library ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE content_calendar ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE published_posts ENABLE ROW LEVEL SECURITY;

-- Create policies (uncomment when adding auth)
-- CREATE POLICY "Enable read access for all users" ON content_library FOR SELECT USING (true);
-- CREATE POLICY "Enable insert for authenticated users only" ON content_library FOR INSERT WITH CHECK (auth.role() = 'authenticated');

