-- Create test user for Feature #479
-- Password: TestPassword123!
-- Hash generated with: python3 -c "import bcrypt; print(bcrypt.hashpw(b'TestPassword123!', bcrypt.gensalt()).decode())"

DO $$
DECLARE
    test_user_id UUID := gen_random_uuid();
    test_email TEXT := 'feature479test@example.com';
BEGIN
    -- Delete existing test user if exists
    DELETE FROM users WHERE email = test_email;

    -- Create test user
    INSERT INTO users (
        id, email, password_hash, full_name,
        is_active, is_verified, role,
        created_at, updated_at
    ) VALUES (
        test_user_id,
        test_email,
        '$2b$12$ymrBsr56tDIgkWBjJaj/KeROABWxCVUWy5G4kcGJkCM7MXOWH0AY6',
        'Test User Feature 479',
        true,
        true,
        'user',
        NOW(),
        NOW()
    );

    RAISE NOTICE 'Created test user: % with ID: %', test_email, test_user_id;
END $$;
