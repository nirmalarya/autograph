-- Verify all test users for team testing (bypassing email verification)
UPDATE users
SET is_verified = TRUE
WHERE email LIKE '%team_admin_%@test.com'
   OR email LIKE '%team_member%@test.com';

-- Show updated users
SELECT id, email, is_verified, role
FROM users
WHERE email LIKE '%team_admin_%@test.com'
   OR email LIKE '%team_member%@test.com'
ORDER BY created_at DESC
LIMIT 10;
