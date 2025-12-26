-- Create test users for Feature #444 (Real-time comments test)
-- Password for both: SecurePassword123!
-- Hash generated with: python3 -c "from passlib.hash import bcrypt; print(bcrypt.hash('SecurePassword123!'))"

-- Delete if exists
DELETE FROM users WHERE email IN ('realtime_user1@example.com', 'realtime_user2@example.com');

-- User 1
INSERT INTO users (id, email, password_hash, full_name, role, is_active, is_verified, created_at, updated_at)
VALUES (
    'rt-user-1-444',
    'realtime_user1@example.com',
    '$2b$12$KIXqFz7eHdBvE6F8oX0T4OqN7xVqxB4zQGKZv8y3Jx3mH6FQnH2Ky',
    'Realtime Test User 1',
    'user',
    true,
    true,
    NOW(),
    NOW()
);

-- User 2
INSERT INTO users (id, email, password_hash, full_name, role, is_active, is_verified, created_at, updated_at)
VALUES (
    'rt-user-2-444',
    'realtime_user2@example.com',
    '$2b$12$KIXqFz7eHdBvE6F8oX0T4OqN7xVqxB4zQGKZv8y3Jx3mH6FQnH2Ky',
    'Realtime Test User 2',
    'user',
    true,
    true,
    NOW(),
    NOW()
);
