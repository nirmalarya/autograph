-- Create test user for feature 517 (SVG optimization)
INSERT INTO users (id, email, password_hash, is_verified, is_active, role, created_at, updated_at)
VALUES (
  'svg-opt-517-user',
  'svgopt517@test.com',
  '$2b$12$AWaJCpPLbgee98LBxZMEP.cScv/lk2l4R40SidVJwO.xgqSAP5Re2',
  true,
  true,
  'user',
  NOW(),
  NOW()
) ON CONFLICT (email) DO UPDATE SET
  is_verified = true,
  is_active = true;
