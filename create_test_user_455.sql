-- Create test user for feature 455 testing
-- Password hash for: SecurePass123!
DELETE FROM users WHERE email = 'test_feature_455@example.com';

INSERT INTO users (id, email, password_hash, is_active, is_verified, role)
VALUES (
  'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaa455',
  'test_feature_455@example.com',
  '$2b$12$aE8OacYJVz1NV/hfNjeZUeUfWbQbu/rRltvFF1IVt7IeZ/MAQQaS.',
  true,
  true,  -- Email verified
  'editor'
);
