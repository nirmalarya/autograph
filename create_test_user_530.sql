-- Test user and team for Feature #530 (Custom Roles)

-- Create test user (admin of team)
INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role)
VALUES (
    'test-user-530-admin',
    'admin530@test.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TT/iN.CwRpZTXjVTZ8VhZPZsw0pC', -- "password123"
    'Test Admin 530',
    true,
    true,
    'admin'
);

-- Create test team
INSERT INTO teams (id, name, slug, owner_id, plan, max_members)
VALUES (
    'test-team-530',
    'Custom Roles Test Team',
    'custom-roles-test-530',
    'test-user-530-admin',
    'enterprise',
    50
);

-- Add admin as team member
INSERT INTO team_members (id, team_id, user_id, role, invitation_status)
VALUES (
    'test-member-530-admin',
    'test-team-530',
    'test-user-530-admin',
    'admin',
    'active'
);

-- Create another test user (regular member)
INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role)
VALUES (
    'test-user-530-member',
    'member530@test.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TT/iN.CwRpZTXjVTZ8VhZPZsw0pC', -- "password123"
    'Test Member 530',
    true,
    true,
    'user'
);

-- Add as viewer
INSERT INTO team_members (id, team_id, user_id, role, invitation_status)
VALUES (
    'test-member-530-viewer',
    'test-team-530',
    'test-user-530-member',
    'viewer',
    'active'
);
