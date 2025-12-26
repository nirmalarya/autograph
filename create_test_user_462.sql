-- Create test user for feature 462 with email verified
INSERT INTO users (id, email, password_hash, full_name, is_verified, is_active, role, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    'test_feature_462@example.com',
    '$2b$12$j0YCILlHyCoGzTvquUe0MeF0KVx9Mj4KEcdRxV6GOWpeR7239paLq', -- hash of "SecurePassword123!@#"
    'Test User Feature 462',
    true,
    true,
    'user',
    NOW(),
    NOW()
)
ON CONFLICT (email) DO UPDATE
SET password_hash = '$2b$12$j0YCILlHyCoGzTvquUe0MeF0KVx9Mj4KEcdRxV6GOWpeR7239paLq',
    is_verified = true,
    is_active = true;
