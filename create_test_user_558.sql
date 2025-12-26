-- Create test user for feature #558 (webhook management)
INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role, plan, created_at, updated_at)
VALUES (
    'test-webhook-558',
    'webhook-test@autograph.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MHS', -- password: Test123!
    'Webhook Test User',
    true,
    true,
    'user',
    'enterprise',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
)
ON CONFLICT (email) DO UPDATE SET
    plan = 'enterprise',
    is_active = true,
    is_verified = true;
