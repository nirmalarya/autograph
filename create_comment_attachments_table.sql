-- Create comment_attachments table for feature #448
CREATE TABLE IF NOT EXISTS comment_attachments (
    id VARCHAR(36) PRIMARY KEY,
    comment_id VARCHAR(36) NOT NULL REFERENCES comments(id) ON DELETE CASCADE,

    -- File info
    filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    file_size INTEGER NOT NULL,

    -- Storage paths (MinIO)
    storage_path VARCHAR(512) NOT NULL,
    thumbnail_path VARCHAR(512),

    -- Image dimensions
    width INTEGER,
    height INTEGER,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_comment_attachments_comment ON comment_attachments(comment_id);

COMMENT ON TABLE comment_attachments IS 'Comment attachments (images attached to comments)';
COMMENT ON COLUMN comment_attachments.storage_path IS 'Full-size image path in MinIO';
COMMENT ON COLUMN comment_attachments.thumbnail_path IS 'Thumbnail image path in MinIO';
