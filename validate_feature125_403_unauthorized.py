#!/usr/bin/env python3
"""
Feature #125: Get diagram by ID returns 403 for unauthorized access

Test Steps:
1. User A creates private diagram
2. User B attempts GET /api/diagrams/<id>
3. Verify 403 Forbidden response
4. Verify error: 'You do not have permission to access this diagram'
5. User A shares diagram with User B
6. User B attempts GET again
7. Verify 200 OK response
"""

import requests
import json
import sys
import subprocess
import time
from datetime import datetime
from typing import Dict, Any, Tuple

# Configuration
BASE_URL = "http://localhost:8080"
API_GATEWAY = f"{BASE_URL}/api"

def verify_email(email: str) -> None:
    """Verify user email in database."""
    verify_cmd = ["docker", "exec", "autograph-postgres", "psql", "-U", "autograph", "-d", "autograph", "-c", f"UPDATE users SET is_verified = true WHERE email = '{email}';"]
    result = subprocess.run(verify_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Warning: Email verification may have failed: {result.stderr}")

def register_and_login(username_base: str) -> Tuple[str, str]:
    """Register a new user and return their JWT token and email"""
    # Use timestamp to create unique email
    email = f"{username_base.lower()}_{int(datetime.now().timestamp())}@test.com"
    password = "SecurePass123!"
    username = f"{username_base}_{int(datetime.now().timestamp())}"

    # Register
    register_response = requests.post(
        f"{API_GATEWAY}/auth/register",
        json={
            "email": email,
            "password": password,
            "username": username
        }
    )

    if register_response.status_code != 201:
        raise Exception(f"Registration failed: {register_response.text}")

    # Verify email in database
    verify_email(email)

    # Small delay to ensure DB update is committed
    time.sleep(1.0)

    # Login to get token
    login_response = requests.post(
        f"{API_GATEWAY}/auth/login",
        json={
            "email": email,
            "password": password
        }
    )
    if login_response.status_code != 200:
        raise Exception(f"Failed to login after registration: {login_response.text}")

    return login_response.json()["access_token"], email

def create_diagram(token: str, title: str = "Private Test Diagram") -> str:
    """Create a new diagram and return its ID"""
    response = requests.post(
        f"{API_GATEWAY}/diagrams",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": title,
            "diagram_type": "canvas",
            "canvas_data": {
                "shapes": [
                    {
                        "id": "shape1",
                        "type": "rectangle",
                        "x": 100,
                        "y": 100,
                        "width": 200,
                        "height": 100,
                        "text": "Private Shape"
                    }
                ]
            }
        }
    )

    # Accept both 200 and 201 status codes
    if response.status_code not in [200, 201]:
        raise Exception(f"Failed to create diagram: {response.status_code} - {response.text}")

    return response.json()["id"]

def share_diagram(token: str, diagram_id: str, recipient_email: str, permission: str = "view") -> bool:
    """Share a diagram with another user"""
    response = requests.post(
        f"{API_GATEWAY}/diagrams/{diagram_id}/share",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "shared_with_email": recipient_email,
            "permission": permission,
            "is_public": False  # This is a private share with a specific user
        }
    )

    return response.status_code in [200, 201]

def get_diagram(token: str, diagram_id: str) -> requests.Response:
    """Attempt to get a diagram by ID"""
    response = requests.get(
        f"{API_GATEWAY}/diagrams/{diagram_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response

def run_test() -> bool:
    """Run the complete test"""
    print("=" * 80)
    print("Feature #125: Get diagram by ID returns 403 for unauthorized access")
    print("=" * 80)

    try:
        # Step 1: User A creates private diagram
        print("\n[Step 1] User A creates private diagram...")
        user_a_token, user_a_email = register_and_login("user_a_feature125")
        print(f"✓ User A registered/logged in: {user_a_email}")

        diagram_id = create_diagram(user_a_token, "Private Diagram for Feature 125")
        print(f"✓ User A created diagram: {diagram_id}")

        # Step 2: User B attempts GET /api/diagrams/<id>
        print("\n[Step 2] User B attempts GET /api/diagrams/{id}...")
        user_b_token, user_b_email = register_and_login("user_b_feature125")
        print(f"✓ User B registered/logged in: {user_b_email}")

        response = get_diagram(user_b_token, diagram_id)
        print(f"✓ User B sent GET request")

        # Step 3: Verify 403 Forbidden response
        print("\n[Step 3] Verify 403 Forbidden response...")
        if response.status_code != 403:
            print(f"✗ Expected 403 Forbidden, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        print(f"✓ Received 403 Forbidden as expected")

        # Step 4: Verify error message
        print("\n[Step 4] Verify error: 'You do not have permission to access this diagram'...")
        try:
            error_data = response.json()
            error_detail = error_data.get("detail", "")

            # Check for permission-related error message
            if "permission" not in error_detail.lower() and "access" not in error_detail.lower():
                print(f"✗ Error message doesn't mention permissions: {error_detail}")
                return False

            print(f"✓ Error message confirmed: {error_detail}")
        except json.JSONDecodeError:
            print(f"✗ Response is not valid JSON: {response.text}")
            return False

        # Step 5: User A shares diagram with User B
        print("\n[Step 5] User A shares diagram with User B...")
        if not share_diagram(user_a_token, diagram_id, user_b_email, "view"):
            print("✗ Failed to share diagram")
            return False
        print(f"✓ Diagram shared with User B (view permission)")

        # Step 6: User B attempts GET again
        print("\n[Step 6] User B attempts GET again...")
        response = get_diagram(user_b_token, diagram_id)
        print(f"✓ User B sent GET request after sharing")

        # Step 7: Verify 200 OK response
        print("\n[Step 7] Verify 200 OK response...")
        if response.status_code != 200:
            print(f"✗ Expected 200 OK, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        print(f"✓ Received 200 OK as expected")

        # Verify we got the diagram data
        diagram_data = response.json()
        if diagram_data.get("id") != diagram_id:
            print(f"✗ Diagram ID mismatch: expected {diagram_id}, got {diagram_data.get('id')}")
            return False
        print(f"✓ Diagram data returned successfully")

        # Verify canvas data is present
        if "canvas_data" not in diagram_data:
            print(f"✗ canvas_data not in response")
            return False
        print(f"✓ canvas_data present in response")

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED - Feature #125 working correctly!")
        print("=" * 80)
        print("\nSummary:")
        print("• Unauthorized access returns 403 Forbidden ✓")
        print("• Error message includes permission denial ✓")
        print("• After sharing, access is granted with 200 OK ✓")
        print("• Diagram data is returned after authorization ✓")

        return True

    except Exception as e:
        print(f"\n✗ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
