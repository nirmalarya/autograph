DELETE FROM users WHERE email = 'pdftest448@example.com';

INSERT INTO users (id, email, full_name, password_hash, is_active, is_verified, role, created_at, updated_at)
VALUES (
    '448-pdf-test-user',
    'pdftest448@example.com',
    'PDF Test User 448',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5PW8l9nGkFcXe',
    true,
    true,
    'user',
    NOW(),
    NOW()
)
ON CONFLICT (id) DO UPDATE SET
    email = EXCLUDED.email,
    password_hash = EXCLUDED.password_hash,
    is_active = true,
    is_verified = true,
    role = 'user',
    updated_at = NOW();
