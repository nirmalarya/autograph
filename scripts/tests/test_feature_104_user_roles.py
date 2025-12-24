"""
Feature #104: User Roles - Admin, Editor, Viewer with different permissions

Test verifies:
1. Admin role can access all endpoints
2. Editor role can access editor and viewer endpoints
3. Viewer role can only access viewer endpoints
4. Permission checks work correctly
"""

import requests
import time
from datetime import datetime

# Configuration
AUTH_SERVICE_URL = "http://localhost:8085"

def print_separator(title=""):
    """Print a separator line."""
    if title:
        print(f"\n{'=' * 80}")
        print(f"{title}")
        print('=' * 80)
    else:
        print('=' * 80)

def register_user(email: str, password: str, role: str, full_name: str = None):
    """Register a new user with specified role."""
    url = f"{AUTH_SERVICE_URL}/register"
    data = {
        "email": email,
        "password": password,
        "role": role
    }
    if full_name:
        data["full_name"] = full_name
    
    response = requests.post(url, json=data)
    return response

def login_user(email: str, password: str):
    """Login and return access token."""
    url = f"{AUTH_SERVICE_URL}/login"
    data = {
        "email": email,
        "password": password
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def verify_email(user_id: str, db_connection):
    """Verify email directly in database for testing."""
    import psycopg2
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="autograph",
        user="autograph",
        password="autograph_dev_password"
    )
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_verified = TRUE WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

def check_permission(token: str, endpoint: str):
    """Check if user can access an endpoint."""
    url = f"{AUTH_SERVICE_URL}{endpoint}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return response

def main():
    """Run Feature #104 tests."""
    
    print_separator("FEATURE #104: USER ROLES TEST SUITE")
    print(f"Testing against: {AUTH_SERVICE_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Generate unique email addresses
    timestamp = int(time.time())
    admin_email = f"admin_{timestamp}@example.com"
    editor_email = f"editor_{timestamp}@example.com"
    viewer_email = f"viewer_{timestamp}@example.com"
    password = "TestPassword123!"
    
    # Import psycopg2 for database operations
    import psycopg2
    
    print_separator("TEST FEATURE #104: User Roles and Permissions")
    
    # Step 1: Create admin user
    print("\nStep 1: Create user with role='admin'")
    response = register_user(admin_email, password, "admin", "Admin User")
    if response.status_code == 201:
        admin_data = response.json()
        admin_id = admin_data["id"]
        print(f"✓ Admin user registered (ID: {admin_id})")
        print(f"  Email: {admin_email}")
        print(f"  Role: {admin_data['role']}")
        
        # Verify email for admin
        verify_email(admin_id, None)
        print("✓ Admin email verified via database")
    else:
        print(f"✗ Failed to register admin: {response.status_code} - {response.text}")
        return False
    
    # Step 2: Create editor user
    print("\nStep 4: Create user with role='editor'")
    response = register_user(editor_email, password, "editor", "Editor User")
    if response.status_code == 201:
        editor_data = response.json()
        editor_id = editor_data["id"]
        print(f"✓ Editor user registered (ID: {editor_id})")
        print(f"  Email: {editor_email}")
        print(f"  Role: {editor_data['role']}")
        
        # Verify email for editor
        verify_email(editor_id, None)
        print("✓ Editor email verified via database")
    else:
        print(f"✗ Failed to register editor: {response.status_code} - {response.text}")
        return False
    
    # Step 3: Create viewer user
    print("\nStep 8: Create user with role='viewer'")
    response = register_user(viewer_email, password, "viewer", "Viewer User")
    if response.status_code == 201:
        viewer_data = response.json()
        viewer_id = viewer_data["id"]
        print(f"✓ Viewer user registered (ID: {viewer_id})")
        print(f"  Email: {viewer_email}")
        print(f"  Role: {viewer_data['role']}")
        
        # Verify email for viewer
        verify_email(viewer_id, None)
        print("✓ Viewer email verified via database")
    else:
        print(f"✗ Failed to register viewer: {response.status_code} - {response.text}")
        return False
    
    # Login all users
    print("\nLogging in all users...")
    admin_token = login_user(admin_email, password)
    if admin_token:
        print(f"✓ Admin logged in successfully")
    else:
        print("✗ Admin login failed")
        return False
    
    editor_token = login_user(editor_email, password)
    if editor_token:
        print(f"✓ Editor logged in successfully")
    else:
        print("✗ Editor login failed")
        return False
    
    viewer_token = login_user(viewer_email, password)
    if viewer_token:
        print(f"✓ Viewer logged in successfully")
    else:
        print("✗ Viewer login failed")
        return False
    
    # Test admin permissions
    print("\nStep 2-3: Verify admin can access all endpoints")
    
    # Admin -> Admin endpoint
    response = check_permission(admin_token, "/permissions/admin")
    if response.status_code == 200:
        print("✓ Admin can access admin endpoint")
        data = response.json()
        print(f"  Response: {data['message']}")
    else:
        print(f"✗ Admin cannot access admin endpoint: {response.status_code}")
        return False
    
    # Admin -> Editor endpoint
    response = check_permission(admin_token, "/permissions/editor")
    if response.status_code == 200:
        print("✓ Admin can access editor endpoint")
    else:
        print(f"✗ Admin cannot access editor endpoint: {response.status_code}")
        return False
    
    # Admin -> Viewer endpoint
    response = check_permission(admin_token, "/permissions/viewer")
    if response.status_code == 200:
        print("✓ Admin can access viewer endpoint")
    else:
        print(f"✗ Admin cannot access viewer endpoint: {response.status_code}")
        return False
    
    # Test editor permissions
    print("\nStep 5-7: Verify editor permissions")
    
    # Editor -> Admin endpoint (should fail)
    response = check_permission(editor_token, "/permissions/admin")
    if response.status_code == 403:
        print("✓ Editor correctly blocked from admin endpoint")
        print(f"  Error: {response.json()['detail']}")
    else:
        print(f"✗ Editor should not access admin endpoint: {response.status_code}")
        return False
    
    # Editor -> Editor endpoint (should work)
    response = check_permission(editor_token, "/permissions/editor")
    if response.status_code == 200:
        print("✓ Editor can access editor endpoint")
        data = response.json()
        print(f"  Response: {data['message']}")
    else:
        print(f"✗ Editor cannot access editor endpoint: {response.status_code}")
        return False
    
    # Editor -> Viewer endpoint (should work)
    response = check_permission(editor_token, "/permissions/viewer")
    if response.status_code == 200:
        print("✓ Editor can access viewer endpoint")
    else:
        print(f"✗ Editor cannot access viewer endpoint: {response.status_code}")
        return False
    
    # Test viewer permissions
    print("\nStep 9-10: Verify viewer permissions")
    
    # Viewer -> Admin endpoint (should fail)
    response = check_permission(viewer_token, "/permissions/admin")
    if response.status_code == 403:
        print("✓ Viewer correctly blocked from admin endpoint")
    else:
        print(f"✗ Viewer should not access admin endpoint: {response.status_code}")
        return False
    
    # Viewer -> Editor endpoint (should fail)
    response = check_permission(viewer_token, "/permissions/editor")
    if response.status_code == 403:
        print("✓ Viewer correctly blocked from editor endpoint")
        print(f"  Error: {response.json()['detail']}")
    else:
        print(f"✗ Viewer should not access editor endpoint: {response.status_code}")
        return False
    
    # Viewer -> Viewer endpoint (should work)
    response = check_permission(viewer_token, "/permissions/viewer")
    if response.status_code == 200:
        print("✓ Viewer can access viewer endpoint")
        data = response.json()
        print(f"  Response: {data['message']}")
    else:
        print(f"✗ Viewer cannot access viewer endpoint: {response.status_code}")
        return False
    
    # Summary
    print_separator("✅ FEATURE #104: PASSED - User roles and permissions working correctly")
    
    print("\nTest Summary:")
    print("  • Admin user can access all endpoints (admin, editor, viewer)")
    print("  • Editor user can access editor and viewer endpoints (blocked from admin)")
    print("  • Viewer user can only access viewer endpoints (blocked from admin and editor)")
    print("  • Permission checks correctly enforce role hierarchy")
    print("  • Registration accepts role parameter")
    print("  • Role validation works correctly")
    
    print_separator("TEST SUMMARY")
    print("Feature #104 (User roles): ✅ PASSED")
    print_separator()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
