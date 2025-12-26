-- Create test user for feature #446
INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role)
VALUES (
    'test-user-446',
    'test_user_446@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ztP.dBQEm3ay',  -- Hash for 'Test123!'
    'Test User 446',
    true,
    true,
    'user'
)
ON CONFLICT (email) DO UPDATE SET
    password_hash = EXCLUDED.password_hash,
    is_active = true,
    is_verified = true;
