-- Create test user for feature 480
INSERT INTO users (id, email, password_hash, is_verified, is_active, role, created_at, updated_at)
VALUES (
  'compress-test-480-user',
  'compress480@test.com',
  '$2b$12$/F8QEW2CFwyhp4fld9Luk.8zkrBMPr5aUApHcINOLtUS.ksyQ1oMy',
  true,
  true,
  'user',
  NOW(),
  NOW()
) ON CONFLICT (email) DO NOTHING;
