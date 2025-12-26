-- Create test user for feature 473
INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role, created_at, updated_at)
VALUES (
    'test-user-473-id',
    'versioncomment473@test.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5rvJ8M.6YvGYC',
    'Version Comment Test',
    true,
    true,
    'user',
    NOW(),
    NOW()
)
ON CONFLICT (email) DO UPDATE SET
    password_hash = EXCLUDED.password_hash,
    is_verified = true,
    is_active = true;
