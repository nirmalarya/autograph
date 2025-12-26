-- Create verified test user for feature 472
INSERT INTO users (id, email, password_hash, full_name, role, is_verified, is_active, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    'test_user_472@example.com',
    '$2b$12$1v7D4UY7G7UlMtxcm79V3ezWXzadW0.3x9K5G6VFRwj7YPBu7C6f2',
    'Test User 472',
    'user',
    true,
    true,
    NOW(),
    NOW()
)
ON CONFLICT (email) DO UPDATE
SET is_verified = true,
    is_active = true,
    role = 'user',
    password_hash = EXCLUDED.password_hash,
    updated_at = NOW();
