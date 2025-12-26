-- Create verified test user for feature #450
DO $$
DECLARE
    v_user_id VARCHAR(36) := 'test-user-450-' || substring(md5(random()::text) from 1 for 8);
    v_email VARCHAR(255) := 'test_user_450@example.com';
    v_password_hash VARCHAR(255) := '$2b$12$bdHUqIfewAyegMJx70wIs.kY3.9ejmoZO4ruFp52AwNXBaBgaxIkG';  -- Password: TestPass123!
BEGIN
    -- Delete if exists
    DELETE FROM users WHERE email = v_email;

    -- Insert new user
    INSERT INTO users (
        id, email, password_hash, full_name, is_active, is_verified, role, created_at, updated_at
    ) VALUES (
        v_user_id,
        v_email,
        v_password_hash,
        'Test User 450',
        true,
        true,  -- Email verified
        'user',
        NOW(),
        NOW()
    );

    RAISE NOTICE 'Created test user: % with ID: %', v_email, v_user_id;
END $$;

-- Show the created user
SELECT id, email, full_name, is_verified FROM users WHERE email = 'test_user_450@example.com';
