-- Create test admin user and team for Feature #531
-- Password: admin123
-- Hash generated: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ND4J6BcrS7.K

INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role)
VALUES ('admin531', 'admin531@test.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ND4J6BcrS7.K', 'Admin User 531', true, true, 'admin')
ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash, role = 'admin';

-- Create test team
INSERT INTO teams (id, name, slug, owner_id, plan)
VALUES ('team531', 'Test Team 531', 'test-team-531', 'admin531', 'enterprise')
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name, owner_id = 'admin531';
