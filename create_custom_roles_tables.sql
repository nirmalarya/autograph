-- Custom Roles System for Enterprise Feature #530
-- This enables teams to define granular permissions beyond the default admin/editor/viewer roles

-- Custom roles table
CREATE TABLE IF NOT EXISTS custom_roles (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    team_id VARCHAR(36) NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,

    -- Permissions (granular)
    can_invite_members BOOLEAN DEFAULT FALSE NOT NULL,
    can_remove_members BOOLEAN DEFAULT FALSE NOT NULL,
    can_manage_roles BOOLEAN DEFAULT FALSE NOT NULL,
    can_create_diagrams BOOLEAN DEFAULT TRUE NOT NULL,
    can_edit_own_diagrams BOOLEAN DEFAULT TRUE NOT NULL,
    can_edit_all_diagrams BOOLEAN DEFAULT FALSE NOT NULL,
    can_delete_own_diagrams BOOLEAN DEFAULT TRUE NOT NULL,
    can_delete_all_diagrams BOOLEAN DEFAULT FALSE NOT NULL,
    can_share_diagrams BOOLEAN DEFAULT TRUE NOT NULL,
    can_comment BOOLEAN DEFAULT TRUE NOT NULL,
    can_export BOOLEAN DEFAULT TRUE NOT NULL,
    can_view_analytics BOOLEAN DEFAULT FALSE NOT NULL,
    can_manage_team_settings BOOLEAN DEFAULT FALSE NOT NULL,

    -- Built-in role flag
    is_system_role BOOLEAN DEFAULT FALSE NOT NULL,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,

    -- Constraints
    CONSTRAINT unique_role_per_team UNIQUE(team_id, name)
);

-- Indexes for custom_roles
CREATE INDEX idx_custom_roles_team ON custom_roles(team_id);
CREATE INDEX idx_custom_roles_system ON custom_roles(is_system_role);

-- Update team_members to support custom roles
ALTER TABLE team_members ADD COLUMN IF NOT EXISTS custom_role_id VARCHAR(36) REFERENCES custom_roles(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_team_members_custom_role ON team_members(custom_role_id);

-- Insert system roles for each team (backwards compatibility)
-- Note: This will be done programmatically when teams are created or migrated
