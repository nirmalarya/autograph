-- Create test user for feature 476
INSERT INTO users (id, email, full_name, password_hash, role, is_active, is_verified, created_at, updated_at)
VALUES (
  '476-test-user-id',
  'test476@example.com',
  'Feature 476 Test User',
  '$2b$12$V8dm5erzwNIAGWMJvjZ8.OehlmwQjcaKmy7wQogF0pslDwdqsf10y', -- hash for 'TestPass123!'
  'admin',
  true,
  true,
  NOW(),
  NOW()
)
ON CONFLICT (email) DO UPDATE
SET is_verified = true, is_active = true, role = 'admin', password_hash = '$2b$12$V8dm5erzwNIAGWMJvjZ8.OehlmwQjcaKmy7wQogF0pslDwdqsf10y';
