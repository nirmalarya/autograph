-- Create admin user for Feature #532 testing
INSERT INTO users (id, email, password_hash, full_name, role, is_active, is_verified, created_at, updated_at)
VALUES (
    'admin-532-test',
    'admin532@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIvAprzZ0i', -- password: testpass123
    'Admin 532',
    'admin',
    true,
    true,
    NOW(),
    NOW()
)
ON CONFLICT (email) DO UPDATE SET
    role = 'admin',
    is_active = true,
    is_verified = true;
