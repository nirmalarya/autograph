-- Create test user for feature 459: Version snapshots with full note_content
-- Password: SecurePass123!
INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role)
VALUES (
    'test-user-459',
    'test459@example.com',
    '$2b$12$aE8OacYJVz1NV/hfNjeZUeUfWbQbu/rRltvFF1IVt7IeZ/MAQQaS.',
    'Test User 459',
    true,
    true,
    'user'
) ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash;
