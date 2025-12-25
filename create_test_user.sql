INSERT INTO users (id, email, password_hash, is_active, is_verified, role, created_at)
VALUES ('test-user-123', 'test@icons.com', 'dummy', true, true, 'user', NOW())
ON CONFLICT (id) DO NOTHING;

SELECT id, email FROM users WHERE id = 'test-user-123';
