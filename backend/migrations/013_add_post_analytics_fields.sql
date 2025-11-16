-- Migration 013: Add analytics fields to published_posts
-- Date: 2025-11-16
-- Description: Add user_id, title, and content_type for analytics display

-- Add user_id to track which user published the post
ALTER TABLE published_posts
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

-- Add title for display in analytics
ALTER TABLE published_posts
ADD COLUMN IF NOT EXISTS title TEXT;

-- Add content_type for better categorization
ALTER TABLE published_posts
ADD COLUMN IF NOT EXISTS content_type TEXT;

-- Create index on user_id for faster queries
CREATE INDEX IF NOT EXISTS idx_posts_user ON published_posts(user_id);

-- Update engagement_data structure to store metrics:
-- {
--   "views": 0,
--   "likes": 0,
--   "comments": 0,
--   "shares": 0,
--   "engagement": 0,
--   "last_updated": "2025-11-16T00:00:00Z"
-- }

COMMENT ON COLUMN published_posts.user_id IS 'User who published the post';
COMMENT ON COLUMN published_posts.title IS 'Post title for display';
COMMENT ON COLUMN published_posts.content_type IS 'Type: blog, text, image, video, carousel';
COMMENT ON COLUMN published_posts.engagement_data IS 'JSONB: views, likes, comments, shares, engagement, last_updated';
