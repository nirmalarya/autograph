-- Create test user for Feature #519 PDF optimization test
-- Password: TestPass123!
INSERT INTO users (id, email, password_hash, is_verified, is_active, role, created_at, updated_at)
VALUES (
  'pdf-opt-519-user',
  'pdfopt519@test.com',
  '$2b$12$AWaJCpPLbgee98LBxZMEP.cScv/lk2l4R40SidVJwO.xgqSAP5Re2',
  true,
  true,
  'user',
  NOW(),
  NOW()
) ON CONFLICT (email) DO UPDATE SET
  is_verified = true,
  is_active = true;
