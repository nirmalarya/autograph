-- Create test user for Feature #580
-- Password: TestPassword123!
-- Hash generated with bcrypt

INSERT INTO users (id, email, password_hash, full_name, created_at, is_active, is_verified, role)
VALUES (
    'folder-rename-test-user-580',
    'folder_rename_580@example.com',
    '$2b$12$lrea6jv3bIWcVBOTGqq/FeJajL.NH6q6Qil558VoUzet1Zmw/e97u',
    'Folder Rename Test User',
    NOW(),
    true,
    true,
    'user'
)
ON CONFLICT (email) DO NOTHING;
