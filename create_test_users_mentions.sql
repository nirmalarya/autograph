-- Create test users for mentions feature testing
-- Password for both: password123
-- Hash generated with bcrypt cost=12

INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role, created_at, updated_at)
VALUES
  ('alice-mention-test', 'alice@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS7sFPD2u', 'Alice Test', true, true, 'user', NOW(), NOW()),
  ('bob-mention-test', 'bob@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS7sFPD2u', 'Bob Test', true, true, 'user', NOW(), NOW())
ON CONFLICT (email) DO NOTHING;
