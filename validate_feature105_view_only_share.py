#!/usr/bin/env python3
"""
Feature #105 Validation: Shared diagram with view-only access

This test validates that:
1. User A can create a diagram
2. User A can share the diagram with User B (view-only)
3. User B can access and view the diagram
4. User B receives 403 Forbidden when attempting to edit
5. Error message is: "You have view-only access to this diagram"
"""

import requests
import json
import sys
import time
import uuid
import psycopg2

# Configuration
API_GATEWAY = "http://localhost:8080"
AUTH_SERVICE = "http://localhost:8085"  # Direct to auth service
DIAGRAM_SERVICE = "http://localhost:8082"  # Direct to diagram service

def generate_test_email():
    """Generate unique test email."""
    return f"test_feature105_{uuid.uuid4().hex[:8]}@example.com"

def verify_email_in_db(user_id):
    """Mark user as verified in database."""
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="autograph",
        user="autograph",
        password="autograph_dev_password"
    )
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_verified = true WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

def register_and_login(email, password="Password123!"):
    """Register a new user and get auth token."""
    print(f"\n📝 Registering user: {email}")

    # Register
    register_data = {
        "email": email,
        "password": password,
        "role": "viewer"
    }

    response = requests.post(f"{AUTH_SERVICE}/register", json=register_data)
    if response.status_code != 201:
        print(f"❌ Registration failed: {response.status_code} - {response.text}")
        return None

    reg_data = response.json()
    user_id = reg_data.get("id")

    print(f"✅ User registered successfully. User ID: {user_id}")

    # Verify email in database
    print(f"📧 Verifying email in database...")
    verify_email_in_db(user_id)
    print(f"✅ Email verified")

    # Login
    print(f"🔐 Logging in...")
    login_data = {
        "email": email,
        "password": password
    }

    response = requests.post(f"{AUTH_SERVICE}/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None

    data = response.json()
    token = data.get("access_token")
    # User ID might be in different fields
    login_user_id = data.get("user_id") or data.get("id") or user_id

    print(f"✅ Login successful. User ID: {login_user_id}")

    return {
        "email": email,
        "user_id": login_user_id,
        "token": token
    }

def create_diagram(user_data):
    """Create a new diagram."""
    print(f"\n📊 Creating diagram for {user_data['email']}")

    diagram_data = {
        "title": f"Test Diagram - Feature 105",
        "canvas_data": {
            "elements": [
                {"type": "rectangle", "x": 100, "y": 100, "width": 200, "height": 100}
            ]
        }
    }

    headers = {
        "Authorization": f"Bearer {user_data['token']}",
        "X-User-ID": user_data['user_id']
    }

    response = requests.post(f"{DIAGRAM_SERVICE}/", json=diagram_data, headers=headers)
    if response.status_code not in [200, 201]:
        print(f"❌ Diagram creation failed: {response.status_code} - {response.text}")
        return None

    data = response.json()
    diagram_id = data.get("id")

    print(f"✅ Diagram created: {diagram_id}")

    return diagram_id

def share_diagram(user_data, diagram_id, share_with_email, permission="view"):
    """Share a diagram with another user."""
    print(f"\n🔗 Sharing diagram {diagram_id} with {share_with_email} ({permission} permission)")

    share_data = {
        "permission": permission,
        "shared_with_email": share_with_email
    }

    headers = {
        "Authorization": f"Bearer {user_data['token']}",
        "X-User-ID": user_data['user_id']
    }

    response = requests.post(f"{DIAGRAM_SERVICE}/{diagram_id}/share", json=share_data, headers=headers)
    if response.status_code not in [200, 201]:
        print(f"❌ Share creation failed: {response.status_code} - {response.text}")
        return None

    data = response.json()
    print(f"✅ Diagram shared successfully")

    return data

def get_diagram(user_data, diagram_id):
    """Get a diagram (test view access)."""
    print(f"\n👁️  Getting diagram {diagram_id} as {user_data['email']}")

    headers = {
        "Authorization": f"Bearer {user_data['token']}",
        "X-User-ID": user_data['user_id']
    }

    response = requests.get(f"{DIAGRAM_SERVICE}/{diagram_id}", headers=headers)

    if response.status_code != 200:
        print(f"❌ Get diagram failed: {response.status_code} - {response.text}")
        return None

    print(f"✅ Successfully viewed diagram")
    return response.json()

def update_diagram(user_data, diagram_id):
    """Attempt to update a diagram (test edit access)."""
    print(f"\n✏️  Attempting to update diagram {diagram_id} as {user_data['email']}")

    update_data = {
        "canvas_data": {
            "elements": [
                {"type": "rectangle", "x": 150, "y": 150, "width": 250, "height": 150}
            ]
        }
    }

    headers = {
        "Authorization": f"Bearer {user_data['token']}",
        "X-User-ID": user_data['user_id']
    }

    response = requests.put(f"{DIAGRAM_SERVICE}/{diagram_id}", json=update_data, headers=headers)

    return response

def main():
    """Run Feature #105 validation test."""
    print("=" * 80)
    print("FEATURE #105 VALIDATION: Shared diagram with view-only access")
    print("=" * 80)

    # Step 1: Register User A
    user_a_email = generate_test_email()
    user_a = register_and_login(user_a_email)
    if not user_a:
        print("\n❌ FAILED: Could not register User A")
        return 1

    # Step 2: Register User B
    user_b_email = generate_test_email()
    user_b = register_and_login(user_b_email)
    if not user_b:
        print("\n❌ FAILED: Could not register User B")
        return 1

    # Step 3: User A creates diagram
    diagram_id = create_diagram(user_a)
    if not diagram_id:
        print("\n❌ FAILED: Could not create diagram")
        return 1

    # Step 4: User A shares diagram with User B (view-only)
    share = share_diagram(user_a, diagram_id, user_b_email, permission="view")
    if not share:
        print("\n❌ FAILED: Could not share diagram")
        return 1

    # Give the system a moment to process
    time.sleep(1)

    # Step 5: User B accesses diagram
    diagram_data = get_diagram(user_b, diagram_id)
    if not diagram_data:
        print("\n❌ FAILED: User B cannot view shared diagram")
        return 1

    print(f"✅ Step 5 passed: User B can view diagram")

    # Step 6: User B attempts to edit diagram
    response = update_diagram(user_b, diagram_id)

    if response.status_code != 403:
        print(f"\n❌ FAILED: Expected 403 Forbidden, got {response.status_code}")
        print(f"Response: {response.text}")
        return 1

    print(f"✅ Step 6 passed: User B received 403 Forbidden")

    # Step 7: Verify error message
    error_data = response.json()
    error_message = error_data.get("detail", "")

    expected_message = "You have view-only access to this diagram"
    if expected_message not in error_message:
        print(f"\n❌ FAILED: Expected error message '{expected_message}', got '{error_message}'")
        return 1

    print(f"✅ Step 7 passed: Correct error message: '{error_message}'")

    # Bonus: Verify User A can still edit
    print(f"\n🔧 Bonus: Verifying User A can still edit their own diagram")
    response = update_diagram(user_a, diagram_id)

    if response.status_code != 200:
        print(f"⚠️  Warning: User A cannot edit their own diagram: {response.status_code}")
    else:
        print(f"✅ User A can still edit their own diagram")

    # All tests passed
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED - FEATURE #105 VALIDATED")
    print("=" * 80)

    return 0

if __name__ == "__main__":
    sys.exit(main())
