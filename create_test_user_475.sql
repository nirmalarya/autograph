-- Create test user for feature 475
INSERT INTO users (id, email, full_name, password_hash, role, is_active, email_verified, created_at, updated_at)
VALUES (
  '475-test-user-id',
  'test475@example.com',
  'Feature 475 Test User',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TT6WRQkH3WhQzk3f.k1YaBqK.W.i', -- hash for 'password123'
  'admin',
  true,
  true,
  NOW(),
  NOW()
)
ON CONFLICT (email) DO UPDATE
SET email_verified = true, is_active = true, role = 'admin';
