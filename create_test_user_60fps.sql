-- Create test user for 60 FPS test
INSERT INTO users (id, email, password_hash, is_verified, is_active, role, plan)
VALUES (gen_random_uuid()::varchar, 'test60fps@example.com', '$2b$12$jhW9AV5VXfndPg3tjLJ2eO6hytLkYoY5IHkN2U6x.wjQP.DShy6wa', true, true, 'user', 'pro')
ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash, is_verified = EXCLUDED.is_verified, is_active = EXCLUDED.is_active, plan = EXCLUDED.plan;

SELECT id, email, plan, is_verified FROM users WHERE email = 'test60fps@example.com';
