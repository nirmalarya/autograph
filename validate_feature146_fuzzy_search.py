#!/usr/bin/env python3
"""
Feature #146 Validation: Full-text search with fuzzy matching (typo tolerance)

Test Steps:
1. Create diagram with title 'Architecture'
2. Navigate to /dashboard (simulated)
3. Enter search: 'Architecure' (typo: missing 't')
4. Verify diagram still found (fuzzy match)
5. Enter search: 'Archtecture' (typo: transposed letters)
6. Verify diagram still found (fuzzy match)
7. Test similarity threshold with severe typo
8. Verify reasonable typo tolerance
"""
import requests
import json
import sys
from datetime import datetime


API_URL = "http://localhost:8080/api"


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


def create_diagram(access_token: str, user_id: str, title: str) -> dict:
    """Create a simple diagram with a title."""
    print(f"📊 Creating diagram: {title}")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-User-ID": user_id,
        "Content-Type": "application/json"
    }

    # Create simple canvas diagram
    response = requests.post(
        f"{API_URL}/diagrams",
        headers=headers,
        json={
            "title": title,
            "file_type": "canvas",
            "canvas_data": {
                "elements": [
                    {
                        "type": "text",
                        "content": "Sample text content"
                    }
                ]
            }
        }
    )

    if response.status_code not in [200, 201]:
        print(f"❌ Failed to create diagram: {response.text}")
        return None

    diagram = response.json()
    print(f"✅ Diagram created: {diagram['id']}")
    return diagram


def search_diagrams(access_token: str, user_id: str, search_term: str) -> list:
    """Search for diagrams."""
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
    if diagrams:
        for diagram in diagrams:
            print(f"   - {diagram['title']}")
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
    """Run validation for Feature #146."""
    print("=" * 80)
    print("Feature #146: Full-text search with fuzzy matching (typo tolerance)")
    print("=" * 80)

    # Generate unique email for test
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    email = f"fuzzy_search_{timestamp}@example.com"
    password = "SecurePass123!"
    full_name = "Fuzzy Search Test User"

    user_id = None
    test_passed = True

    try:
        # Step 1: Register and verify user
        print("\n" + "=" * 80)
        print("STEP 1: Register and verify user")
        print("=" * 80)
        user_data = register_and_verify_user(email, password, full_name)
        if not user_data:
            print("❌ TEST FAILED: User registration/verification failed")
            return 1
        user_id = user_data['id']

        # Step 2: Login
        print("\n" + "=" * 80)
        print("STEP 2: Login user")
        print("=" * 80)
        access_token, user_id_from_token = login_user(email, password)
        if not access_token:
            print("❌ TEST FAILED: Login failed")
            return 1

        # Step 3: Create diagram with title 'Architecture'
        print("\n" + "=" * 80)
        print("STEP 3: Create diagram with title 'Architecture'")
        print("=" * 80)
        diagram1 = create_diagram(access_token, user_id, "Architecture")
        if not diagram1:
            print("❌ TEST FAILED: Failed to create first diagram")
            test_passed = False

        # Step 4: Create another diagram with different title for contrast
        print("\n" + "=" * 80)
        print("STEP 4: Create diagram with title 'Database Design'")
        print("=" * 80)
        diagram2 = create_diagram(access_token, user_id, "Database Design")
        if not diagram2:
            print("❌ TEST FAILED: Failed to create second diagram")
            test_passed = False

        # Step 5: Test exact search (should work)
        print("\n" + "=" * 80)
        print("STEP 5: Search with exact term 'Architecture'")
        print("=" * 80)
        results = search_diagrams(access_token, user_id, "Architecture")
        if results is None or len(results) == 0:
            print("❌ TEST FAILED: Exact search didn't find the diagram")
            test_passed = False
        elif not any(d['title'] == 'Architecture' for d in results):
            print("❌ TEST FAILED: Architecture diagram not in results")
            test_passed = False
        else:
            print("✅ Exact search works correctly")

        # Step 6: Test fuzzy search - missing 't' (Architecure)
        print("\n" + "=" * 80)
        print("STEP 6: Search with typo 'Architecure' (missing 't')")
        print("=" * 80)
        results = search_diagrams(access_token, user_id, "Architecure")
        if results is None or len(results) == 0:
            print("❌ TEST FAILED: Fuzzy search didn't find diagram with missing letter")
            test_passed = False
        elif not any(d['title'] == 'Architecture' for d in results):
            print("❌ TEST FAILED: Architecture diagram not found with typo")
            test_passed = False
        else:
            print("✅ Fuzzy search works with missing letter typo")

        # Step 7: Test fuzzy search - transposed letters (Archtecture)
        print("\n" + "=" * 80)
        print("STEP 7: Search with typo 'Archtecture' (transposed 'ch')")
        print("=" * 80)
        results = search_diagrams(access_token, user_id, "Archtecture")
        if results is None or len(results) == 0:
            print("❌ TEST FAILED: Fuzzy search didn't find diagram with transposed letters")
            test_passed = False
        elif not any(d['title'] == 'Architecture' for d in results):
            print("❌ TEST FAILED: Architecture diagram not found with transposition")
            test_passed = False
        else:
            print("✅ Fuzzy search works with transposed letters")

        # Step 8: Test similarity threshold - severe typo should not match
        print("\n" + "=" * 80)
        print("STEP 8: Test threshold with severe typo 'Xyz' (should not match)")
        print("=" * 80)
        results = search_diagrams(access_token, user_id, "Xyz")
        if results and any(d['title'] == 'Architecture' for d in results):
            print("❌ TEST FAILED: Fuzzy search matched completely different term")
            test_passed = False
        else:
            print("✅ Fuzzy search correctly rejects severe typos")

        # Step 9: Test case-insensitive fuzzy matching
        print("\n" + "=" * 80)
        print("STEP 9: Search with lowercase typo 'architecure'")
        print("=" * 80)
        results = search_diagrams(access_token, user_id, "architecure")
        if results is None or len(results) == 0:
            print("❌ TEST FAILED: Case-insensitive fuzzy search failed")
            test_passed = False
        elif not any(d['title'] == 'Architecture' for d in results):
            print("❌ TEST FAILED: Architecture diagram not found with lowercase typo")
            test_passed = False
        else:
            print("✅ Case-insensitive fuzzy search works")

        # Step 10: Test moderate typo - multiple errors
        print("\n" + "=" * 80)
        print("STEP 10: Search with multiple typos 'Archtecure' (ch transposed + missing t)")
        print("=" * 80)
        results = search_diagrams(access_token, user_id, "Archtecure")
        if results is None or len(results) == 0:
            print("❌ TEST FAILED: Fuzzy search didn't find diagram with multiple typos")
            test_passed = False
        elif not any(d['title'] == 'Architecture' for d in results):
            print("❌ TEST FAILED: Architecture diagram not found with multiple typos")
            test_passed = False
        else:
            print("✅ Fuzzy search handles multiple typos")

        # Final result
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        if test_passed:
            print("✅ ALL TESTS PASSED")
            print("Feature #146 (Fuzzy Search with Typo Tolerance) is working correctly!")
            return 0
        else:
            print("❌ SOME TESTS FAILED")
            print("Feature #146 needs fixes")
            return 1

    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        # Cleanup
        if user_id:
            print("\n" + "=" * 80)
            print("CLEANUP")
            print("=" * 80)
            cleanup_user(user_id)


if __name__ == "__main__":
    sys.exit(main())
