-- Add missing columns to shares table for user-specific sharing
ALTER TABLE shares
ADD COLUMN IF NOT EXISTS shared_with_user_id VARCHAR(36);

ALTER TABLE shares
ADD COLUMN IF NOT EXISTS version_id VARCHAR(36);

-- Add foreign key constraints
ALTER TABLE shares
DROP CONSTRAINT IF EXISTS shares_shared_with_user_id_fkey;

ALTER TABLE shares
ADD CONSTRAINT shares_shared_with_user_id_fkey
FOREIGN KEY (shared_with_user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE shares
DROP CONSTRAINT IF EXISTS shares_version_id_fkey;

ALTER TABLE shares
ADD CONSTRAINT shares_version_id_fkey
FOREIGN KEY (version_id) REFERENCES versions(id) ON DELETE CASCADE;

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_shares_shared_with_user ON shares(shared_with_user_id);
