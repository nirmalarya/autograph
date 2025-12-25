#!/usr/bin/env python3
"""
Feature #123 Validation: Get diagram by ID returns 404 for non-existent diagram
Tests that GET /api/diagrams/{id} returns 404 when diagram doesn't exist.
"""

import requests
import json
import sys
from datetime import datetime
import uuid

# Configuration
BASE_URL = "http://localhost:8080"
API_GATEWAY = f"{BASE_URL}/api"

def test_get_diagram_404():
    """Test getting non-existent diagram returns 404."""
    print("=" * 80)
    print("Feature #123: Get diagram by ID returns 404 for non-existent diagram")
    print("=" * 80)

    try:
        # Step 1: Register test user
        print("\n1. Registering test user...")
        register_response = requests.post(
            f"{API_GATEWAY}/auth/register",
            json={
                "email": f"test_404_{datetime.now().timestamp()}@example.com",
                "password": "SecurePass123!@#",
                "username": "testuser_404"
            }
        )

        if register_response.status_code != 201:
            print(f"❌ Registration failed: {register_response.status_code}")
            print(register_response.text)
            return False

        user_data = register_response.json()
        user_id = user_data.get("user_id")
        print(f"✅ User registered: {user_id}")

        # Verify email in database
        import subprocess
        email = user_data["email"]
        verify_cmd = f"""docker exec autograph-postgres psql -U autograph -d autograph -c "UPDATE users SET is_verified = true WHERE email = '{email}';" """
        subprocess.run(verify_cmd, shell=True, capture_output=True)
        print(f"✅ Email verified in database")

        # Step 2: Login
        print("\n2. Logging in...")
        login_response = requests.post(
            f"{API_GATEWAY}/auth/login",
            json={
                "email": user_data["email"],
                "password": "SecurePass123!@#"
            }
        )

        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(login_response.text)
            return False

        tokens = login_response.json()
        access_token = tokens.get("access_token")
        print(f"✅ Login successful")

        # Step 3: Send GET /api/diagrams/nonexistent-id
        print("\n3. Sending GET /api/diagrams/nonexistent-id...")

        # Use a valid UUID format but non-existent ID
        nonexistent_id = str(uuid.uuid4())

        get_response = requests.get(
            f"{API_GATEWAY}/diagrams/{nonexistent_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-User-ID": user_id
            }
        )

        # Step 4: Verify 404 Not Found response
        print("\n4. Verifying 404 Not Found response...")
        if get_response.status_code != 404:
            print(f"❌ Expected 404, got {get_response.status_code}")
            print(get_response.text)
            return False

        print(f"✅ Received 404 Not Found response")

        # Step 5: Verify error message
        print("\n5. Verifying error message: 'Diagram not found'...")
        response_data = get_response.json()

        if "detail" not in response_data:
            print("❌ Response missing 'detail' field")
            print(json.dumps(response_data, indent=2))
            return False

        error_message = response_data["detail"]
        if "not found" not in error_message.lower():
            print(f"❌ Error message doesn't contain 'not found': {error_message}")
            return False

        print(f"✅ Error message correct: '{error_message}'")

        # Step 6: Verify response body contains error details
        print("\n6. Verifying response body contains error details...")

        # Should have detail field at minimum
        if not isinstance(response_data, dict):
            print(f"❌ Response is not a JSON object: {type(response_data)}")
            return False

        print(f"✅ Response body contains error details")
        print(f"   Detail: {response_data.get('detail')}")

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED - Feature #123 is working!")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_get_diagram_404()
    sys.exit(0 if success else 1)
