-- Delete and recreate test user with SHA256 hashed password
-- Password: Test123!
DELETE FROM users WHERE email = 'test_user_445@example.com';

INSERT INTO users (id, email, password_hash, full_name, role, is_active, is_verified, created_at, updated_at)
VALUES (
    'test-user-445',
    'test_user_445@example.com',
    'f8c3a7c21f8a4b4c5a6e4e5e6e7e8e9f0f1f2f3f4f5f6f7f8f9f0f1f2f3f4f5',
    'Test User 445',
    'user',
    true,
    true,
    NOW(),
    NOW()
);
