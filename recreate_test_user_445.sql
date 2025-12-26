-- Delete and recreate test user with known password
-- Password: Test123!
-- This hash was generated with: python3 -c "from passlib.hash import bcrypt; print(bcrypt.hash('Test123!'))"
DELETE FROM users WHERE email = 'test_user_445@example.com';

INSERT INTO users (id, email, password_hash, full_name, role, is_active, is_verified, created_at, updated_at)
VALUES (
    'test-user-445',
    'test_user_445@example.com',
    '$2b$12$jZlqZkSL5Gg0E5A.HQ8V2OEhjT7oqD6WV2F.L7z6H7jD6Q4ZqQ4ZS',
    'Test User 445',
    'user',
    true,
    true,
    NOW(),
    NOW()
);
