-- Create test user for Feature 456 (Version Numbering)
-- Password: TestPassword123!
-- Hash generated with bcrypt

INSERT INTO users (id, email, password_hash, is_verified, is_active, role, created_at, updated_at)
VALUES (
    'test-user-456',
    'test456@example.com',
    '$2b$12$kMMPDoDUTFUGiLNzQbLbfuD47GOuOGFviIwkwbIcHJfj6CrUzcPcq',
    true,
    true,
    'user',
    NOW(),
    NOW()
)
ON CONFLICT (email) DO UPDATE
SET password_hash = '$2b$12$kMMPDoDUTFUGiLNzQbLbfuD47GOuOGFviIwkwbIcHJfj6CrUzcPcq',
    is_verified = true,
    is_active = true;
