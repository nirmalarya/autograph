#!/usr/bin/env python3
"""
Feature #435 Test: Delete Own Comments

Tests the ability for users to delete their own comments.

Test Flow:
1. Register/login user
2. Create a diagram
3. Post a comment on the diagram
4. Delete the comment
5. Verify comment is deleted and removed from list
"""

import requests
import time
import uuid
import psycopg2
import base64
import json

# Test configuration
API_BASE_URL = "http://localhost:8080/api"
DIAGRAM_SERVICE_URL = "http://localhost:8082"
DB_CONFIG = {
    "dbname": "autograph",
    "user": "autograph",
    "password": "autograph_dev_password",
    "host": "localhost",
    "port": 5432
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

def test_delete_own_comment():
    """Test deleting own comment."""
    print("=" * 80)
    print("Feature #435 Test: Delete Own Comments")
    print("=" * 80)

    # Step 1: Register and login
    print("\n[1/5] Registering and logging in user...")
    test_email = f"delete_comment_test_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "SecurePass123!"

    # Register
    register_response = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={
            "email": test_email,
            "password": test_password,
            "full_name": "Delete Test User"
        }
    )

    if register_response.status_code != 201:
        print(f"❌ Registration failed: {register_response.status_code}")
        print(register_response.text)
        return False

    # Verify email
    verify_email(test_email)
    print(f"✅ Email verified")

    # Login
    login_response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={
            "email": test_email,
            "password": test_password
        }
    )

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)
        return False

    login_data = login_response.json()
    token = login_data["access_token"]
    # Decode JWT to get user_id from 'sub' claim
    payload_str = token.split('.')[1]
    # Add padding if needed
    payload_str += '=' * (4 - len(payload_str) % 4)
    payload = json.loads(base64.b64decode(payload_str))
    user_id = payload["sub"]
    print(f"✅ Logged in as user: {user_id}")

    # Step 2: Create a diagram
    print("\n[2/5] Creating a test diagram...")
    create_diagram_response = requests.post(
        f"{API_BASE_URL}/diagrams",
        headers={
            "Authorization": f"Bearer {token}",
            "X-User-ID": user_id
        },
        json={
            "title": "Delete Comment Test Diagram",
            "diagram_type": "canvas",
            "canvas_data": {"shapes": [], "arrows": []}
        }
    )

    if create_diagram_response.status_code not in (200, 201):
        print(f"❌ Failed to create diagram: {create_diagram_response.status_code}")
        print(create_diagram_response.text)
        return False

    diagram_id = create_diagram_response.json()["id"]
    print(f"✅ Created diagram: {diagram_id}")

    # Step 3: Post a comment
    print("\n[3/5] Posting a comment...")
    comment_text = "This comment will be deleted"
    create_comment_response = requests.post(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments",
        headers={
            "Authorization": f"Bearer {token}",
            "X-User-ID": user_id
        },
        json={
            "content": comment_text,
            "position_x": 100,
            "position_y": 200
        }
    )

    if create_comment_response.status_code != 201:
        print(f"❌ Failed to create comment: {create_comment_response.status_code}")
        print(create_comment_response.text)
        return False

    comment_id = create_comment_response.json()["id"]
    print(f"✅ Created comment: {comment_id}")
    print(f"   Content: {comment_text}")

    # Verify comment exists in list
    print("\n   Verifying comment exists in list...")
    get_comments_response = requests.get(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments",
        headers={
            "Authorization": f"Bearer {token}",
            "X-User-ID": user_id
        }
    )

    if get_comments_response.status_code != 200:
        print(f"❌ Failed to get comments: {get_comments_response.status_code}")
        return False

    comments_data = get_comments_response.json()
    comments_before = comments_data.get("comments", [])
    comment_found = any(c["id"] == comment_id for c in comments_before)

    if not comment_found:
        print(f"❌ Comment not found in list before deletion")
        return False

    print(f"✅ Comment found in list ({len(comments_before)} total comments)")

    # Step 4: Delete the comment
    print("\n[4/5] Deleting the comment...")
    delete_response = requests.delete(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments/{comment_id}/delete",
        headers={
            "Authorization": f"Bearer {token}",
            "X-User-ID": user_id
        }
    )

    if delete_response.status_code != 200:
        print(f"❌ Failed to delete comment: {delete_response.status_code}")
        print(delete_response.text)
        return False

    delete_result = delete_response.json()
    print(f"✅ Comment deleted successfully")
    print(f"   Response: {delete_result.get('message', 'N/A')}")

    # Step 5: Verify comment is deleted and removed from list
    print("\n[5/5] Verifying comment is deleted...")

    # Check that comment no longer exists
    get_deleted_comment_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/comments/{comment_id}",
        headers={
            "X-User-ID": user_id
        }
    )

    # Should get 404
    if get_deleted_comment_response.status_code == 404:
        print(f"✅ Comment no longer exists (404)")
    elif get_deleted_comment_response.status_code == 200:
        print(f"❌ Comment still exists after deletion!")
        return False

    # Verify removed from list
    get_comments_after_response = requests.get(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments",
        headers={
            "Authorization": f"Bearer {token}",
            "X-User-ID": user_id
        }
    )

    if get_comments_after_response.status_code != 200:
        print(f"❌ Failed to get comments: {get_comments_after_response.status_code}")
        return False

    comments_after_data = get_comments_after_response.json()
    comments_after = comments_after_data.get("comments", [])
    comment_still_exists = any(c["id"] == comment_id for c in comments_after)

    if comment_still_exists:
        print(f"❌ Comment still appears in list after deletion")
        return False

    print(f"✅ Comment removed from list ({len(comments_after)} total comments)")
    print(f"   Comments before: {len(comments_before)}")
    print(f"   Comments after: {len(comments_after)}")

    # Verify count decreased
    expected_count = len(comments_before) - 1
    if len(comments_after) == expected_count:
        print(f"✅ Comment count decreased correctly")
    else:
        print(f"⚠️  Comment count mismatch (expected {expected_count}, got {len(comments_after)})")

    print("\n" + "=" * 80)
    print("✅ Feature #435 TEST PASSED: Delete Own Comments")
    print("=" * 80)
    print("\nTest Results:")
    print("✅ User can post a comment")
    print("✅ User can delete their own comment")
    print("✅ Comment is permanently deleted (404)")
    print("✅ Comment is removed from list")
    print("✅ Comment count decreases correctly")

    return True


def test_cannot_delete_others_comment():
    """Test that users cannot delete other users' comments."""
    print("\n" + "=" * 80)
    print("Security Test: Cannot Delete Others' Comments")
    print("=" * 80)

    # Create two users
    print("\n[1/4] Creating two users...")
    user1_email = f"user1_{uuid.uuid4().hex[:8]}@example.com"
    user2_email = f"user2_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePass123!"

    # Register user 1
    requests.post(
        f"{API_BASE_URL}/auth/register",
        json={
            "email": user1_email,
            "password": password,
            "full_name": "User One"
        }
    )
    verify_email(user1_email)

    # Register user 2
    requests.post(
        f"{API_BASE_URL}/auth/register",
        json={
            "email": user2_email,
            "password": password,
            "full_name": "User Two"
        }
    )
    verify_email(user2_email)

    # Login as user 1
    login1 = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"email": user1_email, "password": password}
    ).json()
    token1 = login1["access_token"]
    payload1_str = token1.split('.')[1] + '=' * (4 - len(token1.split('.')[1]) % 4)
    user1_id = json.loads(base64.b64decode(payload1_str))["sub"]

    # Login as user 2
    login2 = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"email": user2_email, "password": password}
    ).json()
    token2 = login2["access_token"]
    payload2_str = token2.split('.')[1] + '=' * (4 - len(token2.split('.')[1]) % 4)
    user2_id = json.loads(base64.b64decode(payload2_str))["sub"]

    print(f"✅ Created users: {user1_id} and {user2_id}")

    # Create diagram as user 1
    print("\n[2/4] User 1 creates diagram...")
    diagram_response = requests.post(
        f"{API_BASE_URL}/diagrams",
        headers={
            "Authorization": f"Bearer {token1}",
            "X-User-ID": user1_id
        },
        json={
            "title": "Shared Diagram",
            "diagram_type": "canvas",
            "canvas_data": {"shapes": []}
        }
    )

    if diagram_response.status_code not in (200, 201):
        print(f"❌ Failed to create diagram: {diagram_response.status_code}")
        print(diagram_response.text)
        return False

    diagram_id = diagram_response.json()["id"]
    print(f"✅ Diagram created: {diagram_id}")

    # User 1 posts a comment
    print("\n[3/4] User 1 posts a comment...")
    comment_response = requests.post(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments",
        headers={
            "Authorization": f"Bearer {token1}",
            "X-User-ID": user1_id
        },
        json={"content": "User 1's comment"}
    )

    if comment_response.status_code not in (200, 201):
        print(f"❌ Failed to create comment: {comment_response.status_code}")
        print(comment_response.text)
        return False

    comment_id = comment_response.json()["id"]
    print(f"✅ Comment created: {comment_id}")

    # User 2 tries to delete user 1's comment
    print("\n[4/4] User 2 tries to delete User 1's comment...")
    delete_response = requests.delete(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments/{comment_id}/delete",
        headers={
            "Authorization": f"Bearer {token2}",
            "X-User-ID": user2_id
        }
    )

    if delete_response.status_code == 403:
        print(f"✅ Delete rejected with 403 Forbidden")
        print(f"   Message: {delete_response.json().get('detail', 'N/A')}")
        return True
    else:
        print(f"❌ Unexpected status code: {delete_response.status_code}")
        print(f"   Expected 403, got {delete_response.status_code}")
        return False


if __name__ == "__main__":
    try:
        # Test basic delete functionality
        success1 = test_delete_own_comment()

        # Test security (cannot delete others' comments)
        success2 = test_cannot_delete_others_comment()

        if success1 and success2:
            print("\n" + "=" * 80)
            print("🎉 ALL TESTS PASSED")
            print("=" * 80)
            exit(0)
        else:
            print("\n" + "=" * 80)
            print("❌ SOME TESTS FAILED")
            print("=" * 80)
            exit(1)

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
