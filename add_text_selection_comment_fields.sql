-- Add fields for note text selection comments
-- Feature #425: Comments: Add comment to note text selection

ALTER TABLE comments
ADD COLUMN IF NOT EXISTS text_start INTEGER,
ADD COLUMN IF NOT EXISTS text_end INTEGER,
ADD COLUMN IF NOT EXISTS text_content TEXT;

-- Add index for querying comments by text position
CREATE INDEX IF NOT EXISTS idx_comments_text_selection
ON comments(file_id, element_id, text_start, text_end)
WHERE text_start IS NOT NULL;

-- Comment on columns for documentation
COMMENT ON COLUMN comments.text_start IS 'Starting character position for text selection comments in notes';
COMMENT ON COLUMN comments.text_end IS 'Ending character position for text selection comments in notes';
COMMENT ON COLUMN comments.text_content IS 'The selected text content for reference';
