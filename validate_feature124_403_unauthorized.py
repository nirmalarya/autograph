#!/usr/bin/env python3
"""
Feature #124 Validation: Get diagram by ID returns 403 for unauthorized access
Tests that GET /api/diagrams/{id} returns 403 when user doesn't have permission.
"""

import requests
import json
import sys
from datetime import datetime
import subprocess

# Configuration
BASE_URL = "http://localhost:8080"
API_GATEWAY = f"{BASE_URL}/api"

def verify_email(email):
    """Verify user email in database."""
    verify_cmd = ["docker", "exec", "autograph-postgres", "psql", "-U", "autograph", "-d", "autograph", "-c", f"UPDATE users SET is_verified = true WHERE email = '{email}';"]
    result = subprocess.run(verify_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Warning: Email verification may have failed: {result.stderr}")

def register_and_login(username_suffix):
    """Register and login a user."""
    try:
        email = f"test_403_{username_suffix.lower()}_{datetime.now().timestamp()}@example.com"
        print(f"   → Registering: {email}")

        # Register
        register_response = requests.post(
            f"{API_GATEWAY}/auth/register",
            json={
                "email": email,
                "password": "SecurePass123!@#",
                "username": f"testuser_403_{username_suffix}"
            },
            timeout=10
        )
    except Exception as e:
        print(f"   ❌ Registration request failed: {e}")
        return None, None, None

    print(f"   → Registration response: {register_response.status_code}")
    if register_response.status_code != 201:
        print(f"❌ Registration failed for {username_suffix}: {register_response.status_code}")
        print(f"   {register_response.text}")
        return None, None, None

    user_data = register_response.json()
    print(f"   → Registration data keys: {list(user_data.keys())}")
    user_id = user_data.get("user_id") or user_data.get("id")

    # Verify email
    print(f"   → Verifying email...")
    verify_email(email)

    # Small delay to ensure DB update is committed
    import time
    time.sleep(1.0)

    # Login
    print(f"   → Logging in...")
    try:
        login_response = requests.post(
            f"{API_GATEWAY}/auth/login",
            json={
                "email": email,
                "password": "SecurePass123!@#"
            },
            timeout=10
        )
    except Exception as e:
        print(f"   ❌ Login request failed: {e}")
        return None, None, None

    print(f"   → Login response: {login_response.status_code}")
    if login_response.status_code != 200:
        print(f"❌ Login failed for {username_suffix}: {login_response.status_code}")
        print(f"   Email: {email}")
        print(f"   Response: {login_response.text}")

        # Check if verification worked
        check_cmd = ["docker", "exec", "autograph-postgres", "psql", "-U", "autograph", "-d", "autograph", "-c", f"SELECT email, is_verified FROM users WHERE email = '{email}';"]
        check_result = subprocess.run(check_cmd, capture_output=True, text=True)
        print(f"   DB status: {check_result.stdout}")

        return None, None, None

    tokens = login_response.json()
    access_token = tokens.get("access_token")

    print(f"   → User ID: {user_id}, Token: {'present' if access_token else 'missing'}")
    return user_id, access_token, email

def test_get_diagram_403():
    """Test unauthorized access to diagram returns 403."""
    print("=" * 80)
    print("Feature #124: Get diagram by ID returns 403 for unauthorized access")
    print("=" * 80)

    try:
        # Step 1: User A creates private diagram
        print("\n1. User A creates private diagram...")
        print("   Registering User A...")

        user_a_id, user_a_token, user_a_email = register_and_login("userA")
        if not user_a_id:
            print("   ❌ User A registration/login failed")
            return False

        print(f"✅ User A registered and logged in: {user_a_id}")
        print(f"   Creating diagram...")

        # Create diagram
        create_response = requests.post(
            f"{API_GATEWAY}/diagrams",
            headers={
                "Authorization": f"Bearer {user_a_token}",
                "X-User-ID": user_a_id
            },
            json={
                "title": "User A's Private Diagram",
                "file_type": "canvas",
                "canvas_data": {
                    "shapes": [{"id": "s1", "type": "rect", "x": 0, "y": 0}]
                }
            },
            timeout=10
        )

        if create_response.status_code not in [200, 201]:
            print(f"❌ Diagram creation failed: {create_response.status_code}")
            print(create_response.text)
            return False

        diagram = create_response.json()
        diagram_id = diagram.get("id")
        print(f"✅ Diagram created: {diagram_id}")

        # Step 2: User B attempts GET /api/diagrams/<id>
        print("\n2. User B attempts GET /api/diagrams/<id>...")

        user_b_id, user_b_token, user_b_email = register_and_login("userB")
        if not user_b_id:
            return False

        print(f"✅ User B registered and logged in: {user_b_id}")

        get_response = requests.get(
            f"{API_GATEWAY}/diagrams/{diagram_id}",
            headers={
                "Authorization": f"Bearer {user_b_token}",
                "X-User-ID": user_b_id
            },
            timeout=10
        )

        # Step 3: Verify 403 Forbidden response
        print("\n3. Verifying 403 Forbidden response...")
        if get_response.status_code != 403:
            print(f"❌ Expected 403, got {get_response.status_code}")
            print(get_response.text)
            return False

        print(f"✅ Received 403 Forbidden response")

        # Step 4: Verify error message
        print("\n4. Verifying error: 'You do not have permission to access this diagram'...")
        response_data = get_response.json()

        if "detail" not in response_data:
            print("❌ Response missing 'detail' field")
            return False

        error_message = response_data["detail"]
        if "permission" not in error_message.lower():
            print(f"❌ Error message doesn't mention permission: {error_message}")
            return False

        print(f"✅ Error message correct: '{error_message}'")

        # Step 5: User A shares diagram with User B
        print("\n5. User A shares diagram with User B...")

        share_response = requests.post(
            f"{API_GATEWAY}/diagrams/{diagram_id}/share",
            headers={
                "Authorization": f"Bearer {user_a_token}",
                "X-User-ID": user_a_id
            },
            json={
                "shared_with_user_id": user_b_id,
                "permission": "view"
            },
            timeout=10
        )

        if share_response.status_code not in [200, 201]:
            print(f"❌ Share failed: {share_response.status_code}")
            print(share_response.text)
            return False

        print(f"✅ Diagram shared with User B (view permission)")

        # Step 6: User B attempts GET again
        print("\n6. User B attempts GET again...")

        get_response_2 = requests.get(
            f"{API_GATEWAY}/diagrams/{diagram_id}",
            headers={
                "Authorization": f"Bearer {user_b_token}",
                "X-User-ID": user_b_id
            },
            timeout=10
        )

        # Step 7: Verify 200 OK response
        print("\n7. Verifying 200 OK response...")
        if get_response_2.status_code != 200:
            print(f"❌ Expected 200, got {get_response_2.status_code}")
            print(get_response_2.text)
            return False

        print(f"✅ User B can now access shared diagram")

        # Verify it's the correct diagram
        diagram_data = get_response_2.json()
        if diagram_data.get("id") != diagram_id:
            print(f"❌ Diagram ID mismatch")
            return False

        if diagram_data.get("title") != "User A's Private Diagram":
            print(f"❌ Diagram title mismatch")
            return False

        print(f"✅ Correct diagram returned after sharing")

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED - Feature #124 is working!")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_get_diagram_403()
    sys.exit(0 if success else 1)
