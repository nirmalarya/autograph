-- Migration: Add comment_count trigger to automatically update file comment counts
-- Feature #159: Diagram comment count badge

-- Step 1: Create trigger function to update comment count
CREATE OR REPLACE FUNCTION update_comment_count()
RETURNS TRIGGER AS $$
DECLARE
    target_file_id VARCHAR;
BEGIN
    -- Get the file_id from either NEW or OLD record
    target_file_id := COALESCE(NEW.file_id, OLD.file_id);

    -- Update the comment count for the file
    -- Only count comments that are not deleted (no is_deleted column in comments table currently)
    UPDATE files
    SET comment_count = (
        SELECT COUNT(*)
        FROM comments
        WHERE file_id = target_file_id
    )
    WHERE id = target_file_id;

    -- Return appropriate record based on operation
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Step 2: Create trigger for INSERT operations
DROP TRIGGER IF EXISTS trigger_update_comment_count_insert ON comments;
CREATE TRIGGER trigger_update_comment_count_insert
AFTER INSERT ON comments
FOR EACH ROW
EXECUTE FUNCTION update_comment_count();

-- Step 3: Create trigger for DELETE operations
DROP TRIGGER IF EXISTS trigger_update_comment_count_delete ON comments;
CREATE TRIGGER trigger_update_comment_count_delete
AFTER DELETE ON comments
FOR EACH ROW
EXECUTE FUNCTION update_comment_count();

-- Step 4: Create trigger for UPDATE operations (in case file_id changes)
DROP TRIGGER IF EXISTS trigger_update_comment_count_update ON comments;
CREATE TRIGGER trigger_update_comment_count_update
AFTER UPDATE ON comments
FOR EACH ROW
WHEN (OLD.file_id IS DISTINCT FROM NEW.file_id)
EXECUTE FUNCTION update_comment_count();

-- Step 5: Initialize comment_count for all existing files
UPDATE files
SET comment_count = (
    SELECT COUNT(*)
    FROM comments
    WHERE comments.file_id = files.id
);

-- Verify the trigger setup
SELECT
    'Comment count triggers installed successfully!' as status,
    COUNT(*) as total_files,
    SUM(comment_count) as total_comments
FROM files;
