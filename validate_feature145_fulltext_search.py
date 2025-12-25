#!/usr/bin/env python3
"""
Feature #145 Validation: Full-text search across diagram titles and content

Test Steps:
1. Create diagram with title 'AWS Architecture'
2. Add text element: 'EC2 instances'
3. Create another diagram with title 'Database Schema'
4. Add text: 'PostgreSQL tables'
5. Navigate to /dashboard
6. Enter search: 'AWS'
7. Verify first diagram found
8. Enter search: 'PostgreSQL'
9. Verify second diagram found
10. Enter search: 'instances'
11. Verify first diagram found (content search)
"""
import requests
import json
import sys
from datetime import datetime


API_URL = "http://localhost:8080/api"
DIAGRAM_SERVICE_URL = "http://localhost:8082"


def register_and_verify_user(email: str, password: str, full_name: str) -> dict:
    """Register a new user and verify their email."""
    print(f"📝 Registering user: {email}")

    # Register
    response = requests.post(f"{API_URL}/auth/register", json={
        "email": email,
        "password": password,
        "full_name": full_name
    })

    if response.status_code not in [200, 201]:
        print(f"❌ Registration failed: {response.text}")
        return None

    user_data = response.json()
    user_id = user_data['id']
    print(f"✅ User registered: {user_id}")

    # Auto-verify email (for testing) - use Docker exec
    import subprocess
    result = subprocess.run([
        "docker", "exec", "autograph-postgres",
        "psql", "-U", "autograph", "-d", "autograph",
        "-c", f"UPDATE users SET is_verified = true WHERE id = '{user_id}';"
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Failed to verify email: {result.stderr}")
        return None

    print(f"✅ Email verified (auto)")

    return user_data


def login_user(email: str, password: str) -> tuple:
    """Login and get access token."""
    import jwt

    print(f"🔑 Logging in: {email}")

    response = requests.post(f"{API_URL}/auth/login", json={
        "email": email,
        "password": password
    })

    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return None, None

    data = response.json()
    access_token = data.get('access_token')

    # Decode JWT to get user_id (sub claim)
    try:
        decoded = jwt.decode(access_token, options={"verify_signature": False})
        user_id = decoded.get("sub")
    except Exception as e:
        print(f"❌ Failed to decode JWT: {e}")
        return None, None

    print(f"✅ Logged in successfully")
    print(f"   User ID: {user_id}")

    return access_token, user_id


def create_diagram_with_text(access_token: str, user_id: str, title: str, text_content: str) -> dict:
    """Create a diagram with canvas data containing text."""
    print(f"📊 Creating diagram: {title}")

    # Create canvas data with text element
    canvas_data = {
        "type": "canvas",
        "shapes": [
            {
                "id": "text1",
                "type": "text",
                "x": 100,
                "y": 100,
                "text": text_content,
                "width": 200,
                "height": 50
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-User-ID": user_id
    }

    response = requests.post(
        f"{API_URL}/diagrams",
        headers=headers,
        json={
            "title": title,
            "file_type": "canvas",
            "canvas_data": canvas_data
        }
    )

    if response.status_code != 200:
        print(f"❌ Failed to create diagram: {response.text}")
        return None

    diagram = response.json()
    print(f"✅ Diagram created: {diagram['id']}")
    return diagram


def search_diagrams(access_token: str, user_id: str, search_term: str) -> list:
    """Search diagrams by keyword."""
    print(f"🔍 Searching for: '{search_term}'")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-User-ID": user_id
    }

    response = requests.get(
        f"{API_URL}/diagrams",
        headers=headers,
        params={"search": search_term}
    )

    if response.status_code != 200:
        print(f"❌ Search failed: {response.text}")
        return None

    data = response.json()
    diagrams = data['diagrams']
    print(f"✅ Found {len(diagrams)} diagram(s)")
    return diagrams


def cleanup_user(user_id: str):
    """Clean up test user from database."""
    import subprocess

    print(f"🧹 Cleaning up user: {user_id}")

    # Delete user using Docker exec (cascades to diagrams, sessions, etc.)
    result = subprocess.run([
        "docker", "exec", "autograph-postgres",
        "psql", "-U", "autograph", "-d", "autograph",
        "-c", f"DELETE FROM users WHERE id = '{user_id}';"
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ Cleanup complete")
    else:
        print(f"⚠️  Cleanup may have failed: {result.stderr}")


def main():
    """Run validation for Feature #145."""
    print("=" * 80)
    print("Feature #145: Full-text search across diagram titles and content")
    print("=" * 80)

    # Generate unique email for test
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    email = f"search_test_{timestamp}@example.com"
    password = "SecurePass123!"
    full_name = "Search Test User"

    user_id = None

    try:
        # Step 1: Register and verify user
        print("\n📋 STEP 1: Register and verify user")
        user_data = register_and_verify_user(email, password, full_name)
        if not user_data:
            print("❌ FAILED: User registration")
            return False
        user_id = user_data['id']

        # Step 2: Login
        print("\n📋 STEP 2: Login")
        access_token, user_id = login_user(email, password)
        if not access_token:
            print("❌ FAILED: Login")
            return False

        # Step 3: Create diagram with title 'AWS Architecture' and text 'EC2 instances'
        print("\n📋 STEP 3: Create diagram with title 'AWS Architecture'")
        diagram1 = create_diagram_with_text(
            access_token, user_id,
            "AWS Architecture",
            "EC2 instances"
        )
        if not diagram1:
            print("❌ FAILED: Create diagram 1")
            return False

        # Step 4: Create diagram with title 'Database Schema' and text 'PostgreSQL tables'
        print("\n📋 STEP 4: Create diagram with title 'Database Schema'")
        diagram2 = create_diagram_with_text(
            access_token, user_id,
            "Database Schema",
            "PostgreSQL tables"
        )
        if not diagram2:
            print("❌ FAILED: Create diagram 2")
            return False

        # Step 5: Search for 'AWS' (should find diagram 1 by title)
        print("\n📋 STEP 5: Search for 'AWS'")
        results = search_diagrams(access_token, user_id, "AWS")
        if results is None:
            print("❌ FAILED: Search for 'AWS'")
            return False

        if len(results) == 0:
            print("❌ FAILED: Expected to find diagram with 'AWS' in title")
            return False

        # Verify diagram1 is in results
        found_diagram1 = any(d['id'] == diagram1['id'] for d in results)
        if not found_diagram1:
            print(f"❌ FAILED: Diagram 1 not found in search results")
            return False

        print(f"✅ PASSED: Found diagram with 'AWS' in title")

        # Step 6: Search for 'PostgreSQL' (should find diagram 2 by content)
        print("\n📋 STEP 6: Search for 'PostgreSQL'")
        results = search_diagrams(access_token, user_id, "PostgreSQL")
        if results is None:
            print("❌ FAILED: Search for 'PostgreSQL'")
            return False

        if len(results) == 0:
            print("❌ FAILED: Expected to find diagram with 'PostgreSQL' in content")
            return False

        # Verify diagram2 is in results
        found_diagram2 = any(d['id'] == diagram2['id'] for d in results)
        if not found_diagram2:
            print(f"❌ FAILED: Diagram 2 not found in search results")
            return False

        print(f"✅ PASSED: Found diagram with 'PostgreSQL' in content")

        # Step 7: Search for 'instances' (should find diagram 1 by content search)
        print("\n📋 STEP 7: Search for 'instances' (content search)")
        results = search_diagrams(access_token, user_id, "instances")
        if results is None:
            print("❌ FAILED: Search for 'instances'")
            return False

        if len(results) == 0:
            print("❌ FAILED: Expected to find diagram with 'instances' in canvas content")
            return False

        # Verify diagram1 is in results (content search)
        found_diagram1 = any(d['id'] == diagram1['id'] for d in results)
        if not found_diagram1:
            print(f"❌ FAILED: Diagram 1 not found in content search results")
            return False

        print(f"✅ PASSED: Found diagram with 'instances' in canvas content")

        # Step 8: Search for 'Database' (should find diagram 2 by title)
        print("\n📋 STEP 8: Search for 'Database' (title search)")
        results = search_diagrams(access_token, user_id, "Database")
        if results is None:
            print("❌ FAILED: Search for 'Database'")
            return False

        if len(results) == 0:
            print("❌ FAILED: Expected to find diagram with 'Database' in title")
            return False

        # Verify diagram2 is in results
        found_diagram2 = any(d['id'] == diagram2['id'] for d in results)
        if not found_diagram2:
            print(f"❌ FAILED: Diagram 2 not found in title search results")
            return False

        print(f"✅ PASSED: Found diagram with 'Database' in title")

        # Step 9: Search for 'tables' (should find diagram 2 by content)
        print("\n📋 STEP 9: Search for 'tables' (content search)")
        results = search_diagrams(access_token, user_id, "tables")
        if results is None:
            print("❌ FAILED: Search for 'tables'")
            return False

        if len(results) == 0:
            print("❌ FAILED: Expected to find diagram with 'tables' in content")
            return False

        # Verify diagram2 is in results
        found_diagram2 = any(d['id'] == diagram2['id'] for d in results)
        if not found_diagram2:
            print(f"❌ FAILED: Diagram 2 not found in content search results")
            return False

        print(f"✅ PASSED: Found diagram with 'tables' in content")

        # Step 10: Search for non-existent term (should return empty)
        print("\n📋 STEP 10: Search for non-existent term")
        results = search_diagrams(access_token, user_id, "nonexistent_term_12345")
        if results is None:
            print("❌ FAILED: Search for non-existent term")
            return False

        if len(results) != 0:
            print(f"❌ FAILED: Expected empty results for non-existent term, got {len(results)}")
            return False

        print(f"✅ PASSED: Search for non-existent term returns empty results")

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED - Feature #145 is working correctly!")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n❌ EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        if user_id:
            cleanup_user(user_id)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
