-- Create test user for optimistic UI testing (Feature #620)
INSERT INTO users (id, email, password_hash, is_active, is_verified, role, created_at)
VALUES (
    'test-optimistic-620',
    'test_optimistic@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5koiyL3Qa4Whm', -- password: TestPass123!
    true,
    true,
    'user',
    NOW()
)
ON CONFLICT (id) DO UPDATE SET
    password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5koiyL3Qa4Whm',
    is_active = true,
    is_verified = true;

SELECT id, email, is_active, is_verified FROM users WHERE id = 'test-optimistic-620';
