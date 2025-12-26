-- Permission Templates for Enterprise Feature #531
-- Pre-configured role templates that teams can use as starting points

CREATE TABLE IF NOT EXISTS role_templates (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    category VARCHAR(50) DEFAULT 'standard', -- standard, industry-specific, etc.

    -- Permissions (same as custom_roles for easy copying)
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

    -- Metadata
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes
CREATE INDEX idx_role_templates_category ON role_templates(category);
CREATE INDEX idx_role_templates_active ON role_templates(is_active);

-- Insert standard permission templates
INSERT INTO role_templates (name, description, category,
    can_invite_members, can_remove_members, can_manage_roles,
    can_create_diagrams, can_edit_own_diagrams, can_edit_all_diagrams,
    can_delete_own_diagrams, can_delete_all_diagrams, can_share_diagrams,
    can_comment, can_export, can_view_analytics, can_manage_team_settings)
VALUES
    -- Admin template - full permissions
    ('Team Admin',
     'Full administrative access to all team features and settings',
     'standard',
     true, true, true,
     true, true, true,
     true, true, true,
     true, true, true, true),

    -- Editor template - can create and edit all content
    ('Content Editor',
     'Can create, edit, and delete all diagrams but cannot manage team members or settings',
     'standard',
     false, false, false,
     true, true, true,
     true, true, true,
     true, true, false, false),

    -- Contributor template - can create own content
    ('Contributor',
     'Can create and manage own diagrams, collaborate with others',
     'standard',
     false, false, false,
     true, true, false,
     true, false, true,
     true, true, false, false),

    -- Viewer template - read-only with comments
    ('Viewer',
     'Can view diagrams, add comments, and export content',
     'standard',
     false, false, false,
     false, false, false,
     false, false, false,
     true, true, false, false),

    -- Guest template - minimal access
    ('Guest',
     'Minimal access - can only view diagrams without commenting or exporting',
     'standard',
     false, false, false,
     false, false, false,
     false, false, false,
     false, false, false, false),

    -- Manager template - oversight role
    ('Team Manager',
     'Can manage members and view analytics but limited content editing',
     'standard',
     true, true, true,
     true, true, false,
     true, false, true,
     true, true, true, true),

    -- Analyst template - data-focused
    ('Analyst',
     'Can view all content, access analytics, and export data',
     'standard',
     false, false, false,
     false, false, false,
     false, false, false,
     true, true, true, false),

    -- Designer template - content creation focused
    ('Designer',
     'Focused on diagram creation and editing with export capabilities',
     'standard',
     false, false, false,
     true, true, true,
     true, true, true,
     true, true, false, false);

-- Add comment explaining usage
COMMENT ON TABLE role_templates IS 'Pre-configured permission templates that teams can use to quickly create custom roles';
