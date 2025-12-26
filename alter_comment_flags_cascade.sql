-- Alter comment_flags table to preserve flags when comments are deleted
-- This maintains an audit trail of moderation actions

-- First, drop the existing foreign key constraint
ALTER TABLE comment_flags
DROP CONSTRAINT comment_flags_comment_id_fkey;

-- Make comment_id nullable to allow flags to exist after comment deletion
ALTER TABLE comment_flags
ALTER COLUMN comment_id DROP NOT NULL;

-- Add the foreign key back with SET NULL on delete
ALTER TABLE comment_flags
ADD CONSTRAINT comment_flags_comment_id_fkey
FOREIGN KEY (comment_id)
REFERENCES comments(id)
ON DELETE SET NULL;

-- Add a comment explaining the design decision
COMMENT ON COLUMN comment_flags.comment_id IS 'Foreign key to comments table. NULL indicates comment was deleted but flag is preserved for audit trail.';
