-- Create test user for feature 441 with email already verified
INSERT INTO users (id, email, password_hash, full_name, is_verified, is_active, role, created_at, updated_at)
VALUES (
    'test-user-441-search',
    'test441_search@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYfLw3j2tJm', -- "TestPassword123!"
    'Test User 441',
    true,
    true,
    'user',
    NOW(),
    NOW()
)
ON CONFLICT (id) DO UPDATE
SET is_verified = true, is_active = true;
