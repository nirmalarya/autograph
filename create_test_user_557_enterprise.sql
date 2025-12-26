-- Create enterprise plan test user
DELETE FROM users WHERE email = 'enterprise_test_557@test.com';
INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role, plan, created_at, updated_at)
VALUES (
    'test-enterprise-557',
    'enterprise_test_557@test.com',
    '$2b$12$I5GLSHv9MQ078xuCHqrj/OiT0tVBGnEKhReaHYpBCO/Lh/J8kCVqO',
    'Enterprise Plan Test User',
    true,
    true,
    'user',
    'enterprise',
    NOW(),
    NOW()
);

SELECT 'Enterprise plan test user created' AS status;
