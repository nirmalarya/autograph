-- Create test user for feature #584: Drag-drop move files to folders
INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role, created_at, updated_at)
VALUES (
    '584-test-user-id',
    'feature584@test.com',
    '$2b$12$rTby.Ew3eQ9/25lcPo9oze44hMLbSrjCQLUPkayxBPEXyD8cpbaaq',
    'Feature 584 Test User',
    true,
    true,
    'user',
    NOW(),
    NOW()
)
ON CONFLICT (email) DO UPDATE
SET password_hash = EXCLUDED.password_hash,
    is_active = EXCLUDED.is_active,
    is_verified = EXCLUDED.is_verified;
