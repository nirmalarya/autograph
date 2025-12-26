#!/usr/bin/env python3
"""
Test Feature #531: Permission Templates
Tests the ability to list role templates and apply them to create custom roles.
"""

import requests
import json
from passlib.context import CryptContext

BASE_URL = "http://localhost:8080"
AUTH_URL = "http://localhost:8085"

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def test_permission_templates():
    """Test permission templates feature."""

    print("=" * 80)
    print("FEATURE #531: PERMISSION TEMPLATES TEST")
    print("=" * 80)

    # Step 1: Create admin user for testing
    print("\n1. Creating admin user...")
    password_hash = pwd_context.hash("admin123")

    import psycopg2
    conn = psycopg2.connect(
        host="localhost",
        database="autograph",
        user="autograph",
        password="autograph_password",
        port=5432
    )
    cur = conn.cursor()

    # Create admin user
    cur.execute("""
        INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role)
        VALUES ('admin531', 'admin531@test.com', %s, 'Admin User 531', true, true, 'admin')
        ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash
        RETURNING id
    """, (password_hash,))
    admin_id = cur.fetchone()[0]

    # Create test team
    cur.execute("""
        INSERT INTO teams (id, name, slug, owner_id)
        VALUES ('team531', 'Test Team 531', 'test-team-531', %s)
        ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name
        RETURNING id
    """, (admin_id,))
    team_id = cur.fetchone()[0]

    conn.commit()
    print(f"✅ Created admin user: {admin_id}")
    print(f"✅ Created team: {team_id}")

    # Step 2: Login to get token
    print("\n2. Logging in...")
    login_response = requests.post(
        f"{AUTH_URL}/login",
        json={
            "email": "admin531@test.com",
            "password": "admin123"
        }
    )

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)
        return False

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")

    # Step 3: List permission templates
    print("\n3. Listing permission templates...")
    templates_response = requests.get(
        f"{AUTH_URL}/admin/roles/templates",
        headers=headers
    )

    if templates_response.status_code != 200:
        print(f"❌ Failed to list templates: {templates_response.status_code}")
        print(templates_response.text)
        return False

    templates_data = templates_response.json()
    print(f"✅ Retrieved {templates_data['count']} templates")
    print("\nAvailable templates:")
    for template in templates_data['templates']:
        print(f"  - {template['name']}: {template['description']}")

    # Step 4: Apply a template to create a custom role
    print("\n4. Applying 'Team Admin' template...")

    # Find Team Admin template
    team_admin_template = None
    for template in templates_data['templates']:
        if template['name'] == 'Team Admin':
            team_admin_template = template
            break

    if not team_admin_template:
        print("❌ Team Admin template not found")
        return False

    apply_response = requests.post(
        f"{AUTH_URL}/admin/roles/templates/{team_admin_template['id']}/apply",
        headers=headers,
        json={
            "team_id": team_id,
            "role_name": "Project Administrator",
            "custom_description": "Custom admin role for project management"
        }
    )

    if apply_response.status_code != 200:
        print(f"❌ Failed to apply template: {apply_response.status_code}")
        print(apply_response.text)
        return False

    role_data = apply_response.json()
    print(f"✅ Created custom role: {role_data['name']}")
    print(f"   Template used: {role_data['template_used']}")
    print(f"   Role ID: {role_data['id']}")

    # Step 5: Verify the role was created in database
    print("\n5. Verifying role in database...")
    cur.execute("""
        SELECT name, description, can_invite_members, can_manage_roles,
               can_create_diagrams, can_manage_team_settings
        FROM custom_roles
        WHERE id = %s
    """, (role_data['id'],))

    db_role = cur.fetchone()
    if not db_role:
        print("❌ Role not found in database")
        return False

    print(f"✅ Role verified in database:")
    print(f"   Name: {db_role[0]}")
    print(f"   Description: {db_role[1]}")
    print(f"   Can invite members: {db_role[2]}")
    print(f"   Can manage roles: {db_role[3]}")
    print(f"   Can create diagrams: {db_role[4]}")
    print(f"   Can manage team settings: {db_role[5]}")

    # Step 6: Test applying another template (Viewer)
    print("\n6. Applying 'Viewer' template...")

    viewer_template = None
    for template in templates_data['templates']:
        if template['name'] == 'Viewer':
            viewer_template = template
            break

    if viewer_template:
        apply_response2 = requests.post(
            f"{AUTH_URL}/admin/roles/templates/{viewer_template['id']}/apply",
            headers=headers,
            json={
                "team_id": team_id,
                "role_name": "External Reviewer"
            }
        )

        if apply_response2.status_code == 200:
            role_data2 = apply_response2.json()
            print(f"✅ Created second custom role: {role_data2['name']}")
            print(f"   Template used: {role_data2['template_used']}")
        else:
            print(f"⚠️  Warning: Failed to apply second template: {apply_response2.status_code}")

    # Cleanup
    cur.close()
    conn.close()

    print("\n" + "=" * 80)
    print("✅ FEATURE #531 TEST PASSED")
    print("=" * 80)
    return True


if __name__ == "__main__":
    try:
        success = test_permission_templates()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
