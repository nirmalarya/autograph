#!/usr/bin/env python3
"""
Test Feature #438: Comment Count Badge

Tests that diagrams display a comment count badge that updates in real-time.

Test Steps:
1. Create a diagram
2. Add 3 comments to the diagram
3. Get diagram details and verify comment_count = 3
4. Add another comment
5. Verify comment_count updates to 4
6. Delete a comment
7. Verify comment_count updates to 3
"""

import requests
import json
from datetime import datetime
import psycopg2
import base64

BASE_URL = "http://localhost:8080/api"
API_KEY = "test-api-key-123"

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "autograph",
    "user": "autograph",
    "password": "autograph_dev_password"
}


def verify_email(email):
    """Mark user email as verified in database."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET is_verified = true WHERE email = %s",
        (email,)
    )
    conn.commit()
    cur.close()
    conn.close()

def create_user(username_suffix):
    """Create a test user and return tokens."""
    email = f"comment_count_user_{username_suffix}@example.com"
    password = "SecurePass123!"

    # Register
    register_response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": f"Comment Count User {username_suffix}"
        }
    )

    if register_response.status_code != 201:
        print(f"Registration failed: {register_response.status_code} - {register_response.text}")
        return None

    # Verify email
    verify_email(email)

    # Login
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password}
    )

    if login_response.status_code != 200:
        print(f"Login failed: {login_response.status_code} - {login_response.text}")
        return None

    data = login_response.json()

    # Extract user_id from JWT token
    token = data["access_token"]
    # Decode JWT payload (middle part)
    payload_b64 = token.split('.')[1]
    # Add padding if needed
    payload_b64 += '=' * (4 - len(payload_b64) % 4)
    payload = json.loads(base64.b64decode(payload_b64))
    user_id = payload["sub"]

    return {
        "user_id": user_id,
        "email": email,
        "token": token
    }


def create_diagram(user_token, user_id):
    """Create a test diagram."""
    response = requests.post(
        f"{BASE_URL}/diagrams",
        headers={
            "Authorization": f"Bearer {user_token}",
            "X-User-ID": user_id
        },
        json={
            "title": "Comment Count Test Diagram",
            "type": "canvas",
            "content": {"shapes": []}
        }
    )

    if response.status_code not in [200, 201]:
        print(f"Failed to create diagram: {response.status_code} - {response.text}")
        return None

    return response.json()


def add_comment(user_token, user_id, diagram_id, content):
    """Add a comment to a diagram."""
    response = requests.post(
        f"{BASE_URL}/diagrams/{diagram_id}/comments",
        headers={
            "Authorization": f"Bearer {user_token}",
            "X-User-ID": user_id
        },
        json={
            "content": content,
            "position_x": 100.0,
            "position_y": 100.0
        }
    )

    if response.status_code != 201:
        print(f"Failed to add comment: {response.status_code} - {response.text}")
        return None

    return response.json()


def get_diagram(user_token, user_id, diagram_id):
    """Get diagram details including comment count."""
    response = requests.get(
        f"{BASE_URL}/diagrams/{diagram_id}",
        headers={
            "Authorization": f"Bearer {user_token}",
            "X-User-ID": user_id
        }
    )

    if response.status_code != 200:
        print(f"Failed to get diagram: {response.status_code} - {response.text}")
        return None

    return response.json()


def delete_comment(user_token, user_id, diagram_id, comment_id):
    """Delete a comment."""
    response = requests.delete(
        f"{BASE_URL}/diagrams/{diagram_id}/comments/{comment_id}/delete",
        headers={
            "Authorization": f"Bearer {user_token}",
            "X-User-ID": user_id
        }
    )

    if response.status_code not in [200, 204]:
        print(f"Delete failed: {response.status_code} - {response.text}")

    return response.status_code in [200, 204]


def test_comment_count_badge():
    """Test comment count badge functionality."""
    print("=" * 80)
    print("Feature #438 Test: Comment Count Badge")
    print("=" * 80)

    # Create user
    print("\n[1/7] Creating user...")
    user = create_user(datetime.now().strftime("%H%M%S%f"))
    if not user:
        return False
    print(f"✅ Created user: {user['email']}")

    # Create diagram
    print("\n[2/7] Creating diagram...")
    diagram = create_diagram(user["token"], user["user_id"])
    if not diagram:
        return False
    diagram_id = diagram["id"]
    print(f"✅ Created diagram: {diagram_id}")

    # Verify initial count is 0
    print("\n[3/7] Verifying initial comment count...")
    diagram_data = get_diagram(user["token"], user["user_id"], diagram_id)
    if not diagram_data:
        return False

    initial_count = diagram_data.get("comment_count", 0)
    if initial_count != 0:
        print(f"❌ Initial comment count should be 0, got {initial_count}")
        return False
    print(f"✅ Initial comment count: {initial_count}")

    # Add 3 comments
    print("\n[4/7] Adding 3 comments...")
    comment_ids = []
    for i in range(3):
        comment = add_comment(
            user["token"],
            user["user_id"],
            diagram_id,
            f"Test comment #{i+1}"
        )
        if not comment:
            return False
        comment_ids.append(comment["id"])
    print(f"✅ Added 3 comments")

    # Verify count is 3
    print("\n[5/7] Verifying comment count = 3...")
    diagram_data = get_diagram(user["token"], user["user_id"], diagram_id)
    if not diagram_data:
        return False

    count = diagram_data.get("comment_count", 0)
    if count != 3:
        print(f"❌ Comment count should be 3, got {count}")
        return False
    print(f"✅ Comment count badge shows: {count}")

    # Add one more comment
    print("\n[6/7] Adding another comment...")
    comment = add_comment(
        user["token"],
        user["user_id"],
        diagram_id,
        "Test comment #4"
    )
    if not comment:
        return False
    comment_ids.append(comment["id"])
    print(f"✅ Added 4th comment")

    # Verify count is 4
    diagram_data = get_diagram(user["token"], user["user_id"], diagram_id)
    if not diagram_data:
        return False

    count = diagram_data.get("comment_count", 0)
    if count != 4:
        print(f"❌ Comment count should be 4, got {count}")
        return False
    print(f"✅ Comment count badge updated to: {count}")

    # Delete a comment
    print("\n[7/7] Deleting a comment and verifying count...")
    if not delete_comment(user["token"], user["user_id"], diagram_id, comment_ids[0]):
        print("❌ Failed to delete comment")
        return False
    print(f"✅ Deleted comment")

    # Verify count is 3
    diagram_data = get_diagram(user["token"], user["user_id"], diagram_id)
    if not diagram_data:
        return False

    count = diagram_data.get("comment_count", 0)
    if count != 3:
        print(f"❌ Comment count should be 3 after deletion, got {count}")
        return False
    print(f"✅ Comment count badge updated to: {count}")

    print("\n" + "=" * 80)
    print("✅ Feature #438 TEST PASSED: Comment Count Badge")
    print("=" * 80)
    print("\nTest Results:")
    print("✅ Initial comment count is 0")
    print("✅ Comment count updates when comments added")
    print("✅ Comment count badge shows correct value")
    print("✅ Comment count decrements when comment deleted")
    print("✅ Real-time updates working")

    return True


if __name__ == "__main__":
    try:
        success = test_comment_count_badge()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
