-- Create comment_reads table for tracking which users have read which comments
-- This enables the "unread indicator" feature for comments

CREATE TABLE IF NOT EXISTS comment_reads (
    id VARCHAR(36) PRIMARY KEY,
    comment_id VARCHAR(36) NOT NULL REFERENCES comments(id) ON DELETE CASCADE,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    read_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    -- Ensure one read record per user per comment
    UNIQUE(comment_id, user_id)
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_comment_reads_comment ON comment_reads(comment_id);
CREATE INDEX IF NOT EXISTS idx_comment_reads_user ON comment_reads(user_id);
CREATE INDEX IF NOT EXISTS idx_comment_reads_lookup ON comment_reads(comment_id, user_id);

-- Grant permissions
GRANT ALL PRIVILEGES ON comment_reads TO autograph_user;
