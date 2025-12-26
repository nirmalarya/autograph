-- Create free plan test user
DELETE FROM users WHERE email = 'free_test_557@test.com';
INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role, plan, created_at, updated_at)
VALUES (
    'test-free-557',
    'free_test_557@test.com',
    '$2b$12$I5GLSHv9MQ078xuCHqrj/OiT0tVBGnEKhReaHYpBCO/Lh/J8kCVqO',
    'Free Plan Test User',
    true,
    true,
    'user',
    'free',
    NOW(),
    NOW()
);

SELECT 'Free plan test user created' AS status;
