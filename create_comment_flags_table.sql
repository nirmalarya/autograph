-- Comment Flags Table for Moderation
-- Stores flags/reports of inappropriate comments

CREATE TABLE IF NOT EXISTS comment_flags (
    id VARCHAR(36) PRIMARY KEY DEFAULT replace(gen_random_uuid()::text, '-', ''),
    comment_id VARCHAR(36) NOT NULL REFERENCES comments(id) ON DELETE CASCADE,
    flagger_user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reason VARCHAR(50) NOT NULL,  -- spam, harassment, offensive, inappropriate, other
    details TEXT,  -- Optional additional details
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, reviewed, dismissed, actioned
    reviewed_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMP,
    admin_notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Prevent duplicate flags from same user on same comment
    UNIQUE(comment_id, flagger_user_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_comment_flags_comment_id ON comment_flags(comment_id);
CREATE INDEX IF NOT EXISTS idx_comment_flags_flagger ON comment_flags(flagger_user_id);
CREATE INDEX IF NOT EXISTS idx_comment_flags_status ON comment_flags(status);
CREATE INDEX IF NOT EXISTS idx_comment_flags_created ON comment_flags(created_at DESC);

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_comment_flags_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_comment_flags_updated_at
    BEFORE UPDATE ON comment_flags
    FOR EACH ROW
    EXECUTE FUNCTION update_comment_flags_updated_at();

-- Trigger to increment/decrement flag count on comments
CREATE OR REPLACE FUNCTION update_comment_flag_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE comments
        SET flag_count = flag_count + 1
        WHERE id = NEW.comment_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE comments
        SET flag_count = GREATEST(0, flag_count - 1)
        WHERE id = OLD.comment_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_comment_flag_count
    AFTER INSERT OR DELETE ON comment_flags
    FOR EACH ROW
    EXECUTE FUNCTION update_comment_flag_count();
