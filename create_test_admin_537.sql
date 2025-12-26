-- Create test admin user for IP allowlist testing
INSERT INTO users (id, email, password_hash, role, is_active, is_verified, created_at, updated_at)
VALUES (
    'admin-ip-537',
    'admin-ip537@test.com',
    '$2b$12$lzeePnlCHsq7vwtSKo8XD.BAMNEMoXcmOrIYYUVJHpVi9Bau/0vwu',
    'admin',
    true,
    true,
    NOW(),
    NOW()
)
ON CONFLICT (id) DO UPDATE SET
    password_hash = EXCLUDED.password_hash,
    role = 'admin',
    is_verified = true;
