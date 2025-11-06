-- Add sample_content column to competitors table
ALTER TABLE competitors 
ADD COLUMN IF NOT EXISTS sample_content TEXT;

-- Add comment
COMMENT ON COLUMN competitors.sample_content IS 'Manual paste of competitor website copy, social posts, or marketing content for analysis';
