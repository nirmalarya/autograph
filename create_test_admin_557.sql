-- Create admin user for feature 557 testing
INSERT INTO users (id, email, password_hash, full_name, role, is_active, is_verified)
VALUES (
    'admin-557',
    'admin557@test.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMeshWQG4Y0p9.VPcIr9Qz5.Ky',  -- password: test123
    'Admin 557',
    'admin',
    true,
    true
)
ON CONFLICT (email) DO NOTHING;
