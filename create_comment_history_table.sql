-- Comment History Table
-- Tracks all edits made to comments for audit and history viewing

CREATE TABLE IF NOT EXISTS comment_history (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    comment_id VARCHAR(36) NOT NULL,
    old_content TEXT NOT NULL,
    old_text_start INTEGER,
    old_text_end INTEGER,
    old_text_content TEXT,
    edited_by VARCHAR(36) NOT NULL,
    edited_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    version_number INTEGER NOT NULL,
    FOREIGN KEY (comment_id) REFERENCES comments(id) ON DELETE CASCADE,
    FOREIGN KEY (edited_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Index for efficient history retrieval
CREATE INDEX IF NOT EXISTS idx_comment_history_comment ON comment_history(comment_id, version_number DESC);
CREATE INDEX IF NOT EXISTS idx_comment_history_edited_at ON comment_history(comment_id, edited_at DESC);

-- Trigger function to record comment history on updates
CREATE OR REPLACE FUNCTION record_comment_history()
RETURNS TRIGGER AS $$
DECLARE
    next_version INTEGER;
BEGIN
    -- Only record if content changed
    IF OLD.content IS DISTINCT FROM NEW.content OR
       OLD.text_start IS DISTINCT FROM NEW.text_start OR
       OLD.text_end IS DISTINCT FROM NEW.text_end OR
       OLD.text_content IS DISTINCT FROM NEW.text_content THEN

        -- Get next version number
        SELECT COALESCE(MAX(version_number), 0) + 1
        INTO next_version
        FROM comment_history
        WHERE comment_id = OLD.id;

        -- Insert history record
        INSERT INTO comment_history (
            comment_id,
            old_content,
            old_text_start,
            old_text_end,
            old_text_content,
            edited_by,
            edited_at,
            version_number
        ) VALUES (
            OLD.id,
            OLD.content,
            OLD.text_start,
            OLD.text_end,
            OLD.text_content,
            NEW.user_id, -- The user making the edit
            NOW(),
            next_version
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop trigger if exists and create new one
DROP TRIGGER IF EXISTS trigger_record_comment_history ON comments;

CREATE TRIGGER trigger_record_comment_history
    BEFORE UPDATE ON comments
    FOR EACH ROW
    EXECUTE FUNCTION record_comment_history();
