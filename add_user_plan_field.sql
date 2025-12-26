-- Add plan field to users table for API rate limiting
-- Feature #557: API rate limiting configurable per plan

-- Add plan column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='users' AND column_name='plan'
    ) THEN
        ALTER TABLE users
        ADD COLUMN plan VARCHAR(50) DEFAULT 'free' NOT NULL;

        COMMENT ON COLUMN users.plan IS 'User subscription plan: free, pro, enterprise';
    END IF;
END $$;

-- Update existing users to have 'free' plan
UPDATE users SET plan = 'free' WHERE plan IS NULL;

-- Create index for efficient plan-based queries
CREATE INDEX IF NOT EXISTS idx_users_plan ON users(plan);

-- Display confirmation
SELECT 'User plan field added successfully' AS status;
