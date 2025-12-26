-- Create pro plan test user
DELETE FROM users WHERE email = 'pro_test_557@test.com';
INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role, plan, created_at, updated_at)
VALUES (
    'test-pro-557',
    'pro_test_557@test.com',
    '$2b$12$I5GLSHv9MQ078xuCHqrj/OiT0tVBGnEKhReaHYpBCO/Lh/J8kCVqO',
    'Pro Plan Test User',
    true,
    true,
    'user',
    'pro',
    NOW(),
    NOW()
);

SELECT 'Pro plan test user created' AS status;
