-- Enable pgcrypto extension for encryption at rest
-- This extension provides cryptographic functions for PostgreSQL

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Verify extension is installed
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'pgcrypto'
    ) THEN
        RAISE NOTICE 'pgcrypto extension successfully enabled';
    ELSE
        RAISE EXCEPTION 'Failed to enable pgcrypto extension';
    END IF;
END $$;
