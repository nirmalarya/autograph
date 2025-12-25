-- Function to update collaborator count for a file
-- Collaborators = owner (1) + number of unique shared_with_user_id entries
CREATE OR REPLACE FUNCTION update_file_collaborator_count()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the collaborator count for the affected file
    -- Count unique users the file is shared with (excluding NULL and public shares)
    UPDATE files
    SET collaborator_count = 1 + (
        SELECT COUNT(DISTINCT shared_with_user_id)
        FROM shares
        WHERE file_id = COALESCE(NEW.file_id, OLD.file_id)
          AND shared_with_user_id IS NOT NULL
          AND is_active = true
    )
    WHERE id = COALESCE(NEW.file_id, OLD.file_id);

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger to update count when a share is inserted
DROP TRIGGER IF EXISTS trigger_share_insert_update_collaborator_count ON shares;
CREATE TRIGGER trigger_share_insert_update_collaborator_count
    AFTER INSERT ON shares
    FOR EACH ROW
    EXECUTE FUNCTION update_file_collaborator_count();

-- Trigger to update count when a share is updated
DROP TRIGGER IF EXISTS trigger_share_update_update_collaborator_count ON shares;
CREATE TRIGGER trigger_share_update_update_collaborator_count
    AFTER UPDATE ON shares
    FOR EACH ROW
    EXECUTE FUNCTION update_file_collaborator_count();

-- Trigger to update count when a share is deleted
DROP TRIGGER IF EXISTS trigger_share_delete_update_collaborator_count ON shares;
CREATE TRIGGER trigger_share_delete_update_collaborator_count
    AFTER DELETE ON shares
    FOR EACH ROW
    EXECUTE FUNCTION update_file_collaborator_count();

-- Initialize collaborator_count for all existing files
UPDATE files
SET collaborator_count = 1 + (
    SELECT COUNT(DISTINCT shared_with_user_id)
    FROM shares
    WHERE file_id = files.id
      AND shared_with_user_id IS NOT NULL
      AND is_active = true
);
