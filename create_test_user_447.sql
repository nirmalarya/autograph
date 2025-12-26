-- Create test user for Feature #447 (Comment History)
INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role, created_at, updated_at)
VALUES (
    gen_random_uuid()::text,
    'historyuser447@test.com',
    'fc82b5c6c0c2ed7c2e8ee47f2a85ac7f0dbf7f8fd5e0f1f8e8e8e8e8e8e8e8e8',  -- SHA256('Test123!@#')
    'History User 447',
    true,
    true,
    'user',
    NOW(),
    NOW()
)
ON CONFLICT (email) DO UPDATE
SET password_hash = 'fc82b5c6c0c2ed7c2e8ee47f2a85ac7f0dbf7f8fd5e0f1f8e8e8e8e8e8e8e8e8',
    is_active = true,
    is_verified = true;
