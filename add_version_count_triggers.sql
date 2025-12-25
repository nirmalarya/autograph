-- Migration: Add version_count trigger to automatically update file version counts
-- Feature #160: Diagram version count display

-- Step 1: Create trigger function to update version count
CREATE OR REPLACE FUNCTION update_version_count()
RETURNS TRIGGER AS $$
DECLARE
    target_file_id VARCHAR;
BEGIN
    -- Get the file_id from either NEW or OLD record
    target_file_id := COALESCE(NEW.file_id, OLD.file_id);

    -- Update the version count for the file
    -- Count all versions for this file
    UPDATE files
    SET version_count = (
        SELECT COUNT(*)
        FROM versions
        WHERE file_id = target_file_id
    )
    WHERE id = target_file_id;

    -- Return appropriate record based on operation
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Step 2: Create trigger for INSERT operations
DROP TRIGGER IF EXISTS trigger_update_version_count_insert ON versions;
CREATE TRIGGER trigger_update_version_count_insert
AFTER INSERT ON versions
FOR EACH ROW
EXECUTE FUNCTION update_version_count();

-- Step 3: Create trigger for DELETE operations
DROP TRIGGER IF EXISTS trigger_update_version_count_delete ON versions;
CREATE TRIGGER trigger_update_version_count_delete
AFTER DELETE ON versions
FOR EACH ROW
EXECUTE FUNCTION update_version_count();

-- Step 4: Create trigger for UPDATE operations (in case file_id changes - unlikely but safe)
DROP TRIGGER IF EXISTS trigger_update_version_count_update ON versions;
CREATE TRIGGER trigger_update_version_count_update
AFTER UPDATE ON versions
FOR EACH ROW
WHEN (OLD.file_id IS DISTINCT FROM NEW.file_id)
EXECUTE FUNCTION update_version_count();

-- Step 5: Initialize version_count for all existing files
UPDATE files
SET version_count = (
    SELECT COUNT(*)
    FROM versions
    WHERE versions.file_id = files.id
);

-- Verify the trigger setup
SELECT
    'Version count triggers installed successfully!' as status,
    COUNT(*) as total_files,
    SUM(version_count) as total_versions
FROM files;
