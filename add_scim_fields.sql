-- Add SCIM fields to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS scim_external_id VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS scim_active BOOLEAN DEFAULT TRUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS scim_meta JSONB DEFAULT '{}'::jsonb;

-- Create index for SCIM external ID lookups
CREATE INDEX IF NOT EXISTS idx_users_scim_external_id ON users(scim_external_id);

-- Create SCIM tokens table for API authentication
CREATE TABLE IF NOT EXISTS scim_tokens (
    id VARCHAR(36) PRIMARY KEY,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    scopes TEXT[] DEFAULT ARRAY['read', 'write'],
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_scim_tokens_hash ON scim_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_scim_tokens_active ON scim_tokens(is_active);
