-- Create test admin for feature 556
-- Password: SecureAdminPass123!
-- Hash generated with: python3 -c "from passlib.hash import bcrypt; print(bcrypt.hash('SecureAdminPass123!'))"

DELETE FROM users WHERE email = 'admin@test.com';

INSERT INTO users (
    id,
    email,
    password_hash,
    role,
    is_active,
    is_verified,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid()::text,
    'admin@test.com',
    '$2b$12$/nZf815vABDTdxC88D4DKe6x9FY5MlpDfN/Inxg4urxTdJsY9xQca',
    'admin',
    true,
    true,
    NOW(),
    NOW()
);
