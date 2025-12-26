-- Update realtime_user1 password to: SecurePassword123!
-- This is the original hash from the create script
UPDATE users
SET password_hash = '$2b$12$KIXqFz7eHdBvE6F8oX0T4OqN7xVqxB4zQGKZv8y3Jx3mH6FQnH2Ky'
WHERE email = 'realtime_user1@example.com';
