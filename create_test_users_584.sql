-- Create test users for Feature 584 (Folder Permissions)
-- Owner user
INSERT INTO users (id, email, password_hash, is_active, is_verified, role, created_at, updated_at)
VALUES (
    '584-folder-owner',
    'folder-owner-584@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyWFiRWXvb0a', -- password: testpass123
    true,
    true,
    'user',
    NOW(),
    NOW()
)
ON CONFLICT (id) DO NOTHING;

-- Viewer user (will get view-only permission)
INSERT INTO users (id, email, password_hash, is_active, is_verified, role, created_at, updated_at)
VALUES (
    '584-folder-viewer',
    'folder-viewer-584@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyWFiRWXvb0a', -- password: testpass123
    true,
    true,
    'user',
    NOW(),
    NOW()
)
ON CONFLICT (id) DO NOTHING;

-- Editor user (will get edit permission, then be removed)
INSERT INTO users (id, email, password_hash, is_active, is_verified, role, created_at, updated_at)
VALUES (
    '584-folder-editor',
    'folder-editor-584@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyWFiRWXvb0a', -- password: testpass123
    true,
    true,
    'user',
    NOW(),
    NOW()
)
ON CONFLICT (id) DO NOTHING;
