-- Create test user for feature 465
INSERT INTO users (id, email, password_hash, full_name, is_verified, is_active, role)
VALUES (
    'user-465-test',
    'versioncompare465@test.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5K0W5n8K9EIIG', -- 'password123'
    'Version Compare Test',
    true,
    true,
    'user'
)
ON CONFLICT (email) DO UPDATE
SET is_active = true, is_verified = true;
