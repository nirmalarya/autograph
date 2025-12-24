-- Migration: Add version retention policy fields to files table
-- Created: 2025-12-24
-- Purpose: Enable configurable version retention policies

-- Add retention policy fields to files table
ALTER TABLE files
ADD COLUMN IF NOT EXISTS retention_policy VARCHAR(20) DEFAULT 'keep_all' NOT NULL,
ADD COLUMN IF NOT EXISTS retention_count INTEGER,
ADD COLUMN IF NOT EXISTS retention_days INTEGER;

-- Add index for efficient policy queries
CREATE INDEX IF NOT EXISTS idx_files_retention_policy ON files(retention_policy);

-- Add comments for documentation
COMMENT ON COLUMN files.retention_policy IS 'Version retention policy: keep_all, keep_last_n, keep_duration';
COMMENT ON COLUMN files.retention_count IS 'For keep_last_n policy: number of versions to keep';
COMMENT ON COLUMN files.retention_days IS 'For keep_duration policy: number of days to keep versions';

-- Example values:
-- retention_policy = 'keep_all': Keep all versions (default)
-- retention_policy = 'keep_last_n' with retention_count = 100: Keep only last 100 versions
-- retention_policy = 'keep_duration' with retention_days = 365: Keep versions for 1 year
