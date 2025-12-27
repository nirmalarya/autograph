-- Test user for Feature 581: Delete folder with contents
INSERT INTO users (id, email, password_hash, full_name, role, is_active, is_verified, created_at, updated_at)
VALUES (
    '581-test-user-id',
    'feature581@test.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYBYtkDCvye',  -- "password"
    'Feature 581 Test User',
    'user',
    true,
    true,
    NOW(),
    NOW()
) ON CONFLICT (id) DO NOTHING;
