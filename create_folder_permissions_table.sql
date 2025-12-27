-- Create folder_permissions table for controlling access to folders
CREATE TABLE IF NOT EXISTS folder_permissions (
    id VARCHAR(36) PRIMARY KEY,
    folder_id VARCHAR(36) NOT NULL REFERENCES folders(id) ON DELETE CASCADE,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permission VARCHAR(20) NOT NULL DEFAULT 'view', -- 'view' or 'edit'
    granted_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(folder_id, user_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_folder_permissions_folder ON folder_permissions(folder_id);
CREATE INDEX IF NOT EXISTS idx_folder_permissions_user ON folder_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_folder_permissions_granted_by ON folder_permissions(granted_by);

-- Add comment
COMMENT ON TABLE folder_permissions IS 'Access control permissions for folders';
COMMENT ON COLUMN folder_permissions.permission IS 'Permission level: view (read-only) or edit (full access)';
