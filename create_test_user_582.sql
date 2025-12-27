-- Create test user for feature 582
INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role, created_at, updated_at)
VALUES (
    '582-test-user-colors-icons',
    'feature582@test.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU.BaHjRNlnW', -- password: TestPass123!
    'Feature 582 Test User',
    true,
    true,
    'user',
    NOW(),
    NOW()
)
ON CONFLICT (id) DO NOTHING;
