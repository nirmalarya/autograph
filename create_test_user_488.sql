-- Create test user for feature 488
-- Password: SecurePass123!

INSERT INTO users (id, email, password_hash, full_name, is_active, role, is_verified, created_at, updated_at)
VALUES (
    'test-user-488',
    'feature488@test.com',
    '$2b$12$umgFraqhvriiwmVETO5kDuc4sx3LqbiM7Skox3NqiQP3SbAH5jqAG',
    'Feature 488 Test User',
    true,
    'viewer',
    true,
    NOW(),
    NOW()
)
ON CONFLICT (email) DO UPDATE
SET password_hash = EXCLUDED.password_hash,
    is_verified = true,
    is_active = true;
