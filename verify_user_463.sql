-- Verify email for test user
UPDATE users SET email_verified = TRUE WHERE email LIKE 'unlimited_versions_%@test.com' AND email_verified = FALSE;
