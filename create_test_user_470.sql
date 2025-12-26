-- Create test user for feature 470
INSERT INTO users (id, email, password_hash, full_name, is_verified, is_active, role, created_at, updated_at)
VALUES (
    'test-user-470',
    'test_restore_470@example.com',
    '$2b$12$eZHG6GHmOwis.55ojmCzD.ow/KrLUqa.1A1JNauzDsNM1byCPgsoC', -- password: TestPass123!
    'Test Restore User',
    TRUE,
    TRUE,
    'user',
    NOW(),
    NOW()
)
ON CONFLICT (email) DO UPDATE
SET
    password_hash = EXCLUDED.password_hash,
    is_verified = TRUE,
    is_active = TRUE,
    updated_at = NOW();
