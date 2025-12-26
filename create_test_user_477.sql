-- Create test users for Feature #477: Version author search
-- User 1: John
INSERT INTO users (id, email, full_name, password_hash, is_verified, is_active, role, created_at, updated_at)
VALUES (
    'test-477-john',
    'test477john@example.com',
    'John Doe',
    '$2b$12$tuzO2vJRHUOzdCmWriFOuOesOCym6sBhFbqpC/84tcMD7YC9iX7Cm', -- TestPass123!
    true,
    true,
    'user',
    NOW(),
    NOW()
)
ON CONFLICT (email) DO UPDATE
SET full_name = EXCLUDED.full_name,
    password_hash = EXCLUDED.password_hash,
    is_verified = EXCLUDED.is_verified,
    is_active = EXCLUDED.is_active;

-- User 2: Jane
INSERT INTO users (id, email, full_name, password_hash, is_verified, is_active, role, created_at, updated_at)
VALUES (
    'test-477-jane',
    'test477jane@example.com',
    'Jane Smith',
    '$2b$12$tuzO2vJRHUOzdCmWriFOuOesOCym6sBhFbqpC/84tcMD7YC9iX7Cm', -- TestPass123!
    true,
    true,
    'user',
    NOW(),
    NOW()
)
ON CONFLICT (email) DO UPDATE
SET full_name = EXCLUDED.full_name,
    password_hash = EXCLUDED.password_hash,
    is_verified = EXCLUDED.is_verified,
    is_active = EXCLUDED.is_active;
