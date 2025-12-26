-- Create test user for feature 458: Version snapshots with full canvas_data
INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role)
VALUES (
    'test-user-458',
    'test458@example.com',
    '$2b$12$6pA8DInjT3gRG1A3mSYEaO/LYmQ7rON803s9fyaTK88WT/1GY4Z1e',
    'Test User 458',
    true,
    true,
    'user'
) ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash;
