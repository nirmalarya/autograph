-- Create test user for Feature #577
INSERT INTO users (id, email, password_hash, is_active, is_verified, role, plan)
VALUES (
  gen_random_uuid()::text,
  'bulkselect577@test.com',
  '$2b$12$LHqXa7Uq.XOaZ1rfN0aXQe7rY8pP8RrG/WvX9dIm8.vQq6sF/9E4S',
  true,
  true,
  'user',
  'free'
)
ON CONFLICT (email) DO NOTHING;
