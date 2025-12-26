#!/usr/bin/env python3
"""
Test Feature #439: Unread Comment Indicator

Tests that comments show unread indicators for users who haven't read them yet.

Test Steps:
1. User A adds comment
2. User B logs in
3. Verify unread indicator on comment
4. User B reads comment (marks as read)
5. Verify indicator cleared
"""

import requests
import json
from datetime import datetime
import psycopg2
import time

BASE_URL = "http://localhost:8080/api"

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
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        # Email is stored as lowercase in the database
        cur.execute(
            "UPDATE users SET is_verified = true WHERE LOWER(email) = LOWER(%s)",
            (email,)
        )
        rows_affected = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        print(f"  → Email verified for {email} (rows affected: {rows_affected})")
    except Exception as e:
        print(f"  → Failed to verify email: {e}")


def create_user(username_suffix):
    """Create a test user and return tokens."""
    email = f"unread_test_user_{username_suffix}_{int(time.time())}@example.com"
    password = "SecurePass123!"

    # Register
    register_response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": f"Unread Test User {username_suffix}"
        }
    )

    if register_response.status_code not in [200, 201]:
        print(f"Registration failed: {register_response.status_code} - {register_response.text}")
        return None

    # Wait a moment for registration to complete
    time.sleep(0.5)

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
    # Handle different response formats
    if "user" in data:
        user_id = data["user"]["id"]
    elif "user_id" in data:
        user_id = data["user_id"]
    else:
        user_id = data.get("id")

    return {
        "email": email,
        "user_id": user_id,
        "access_token": data["access_token"]
    }


def test_feature_439():
    """Test unread comment indicator feature."""
    print("\n" + "="*80)
    print("Testing Feature #439: Unread Comment Indicator")
    print("="*80)

    # ========================================
    # STEP 1: Create two test users
    # ========================================
    print("\n[Step 1] Creating two test users...")

    user_a = create_user("A")
    if not user_a:
        raise Exception("Failed to create User A")
    print(f"✅ User A created: {user_a['email']}")

    user_b = create_user("B")
    if not user_b:
        raise Exception("Failed to create User B")
    print(f"✅ User B created: {user_b['email']}")

    # ========================================
    # STEP 2: User A creates a diagram
    # ========================================
    print("\n[Step 2] User A creates a diagram...")

    diagram_response = requests.post(
        f"{BASE_URL}/diagrams",
        json={
            "title": "Test Diagram for Unread Comments",
            "type": "canvas"
        },
        headers={"Authorization": f"Bearer {user_a['access_token']}"}
    )
    assert diagram_response.status_code == 200, f"Diagram creation failed: {diagram_response.text}"
    diagram_id = diagram_response.json()["id"]
    print(f"✅ Diagram created: {diagram_id}")

    # ========================================
    # STEP 3: User A adds a comment
    # ========================================
    print("\n[Step 3] User A adds a comment...")

    comment_response = requests.post(
        f"{BASE_URL}/diagrams/{diagram_id}/comments",
        json={
            "content": "This is a test comment from User A",
            "position_x": 100,
            "position_y": 100
        },
        headers={"Authorization": f"Bearer {user_a['access_token']}"}
    )
    assert comment_response.status_code in [200, 201], f"Comment creation failed: status={comment_response.status_code}, response={comment_response.text}"
    comment_id = comment_response.json()["id"]
    print(f"✅ Comment created: {comment_id}")

    # ========================================
    # STEP 4: User B views comments (should see unread indicator)
    # ========================================
    print("\n[Step 4] User B views comments (should see unread indicator)...")

    time.sleep(1)  # Wait a moment

    get_comments_response = requests.get(
        f"{BASE_URL}/diagrams/{diagram_id}/comments",
        headers={"Authorization": f"Bearer {user_b['access_token']}"}
    )
    assert get_comments_response.status_code == 200, f"Get comments failed: {get_comments_response.text}"
    comments = get_comments_response.json()["comments"]

    assert len(comments) == 1, f"Expected 1 comment, got {len(comments)}"
    comment = comments[0]

    # Debug: Print comment fields
    print(f"  → Comment fields: {list(comment.keys())}")

    # Verify unread indicator is present
    assert "is_unread" in comment, f"is_unread field missing from comment. Fields: {list(comment.keys())}"
    assert comment["is_unread"] == True, f"Expected comment to be unread, but is_unread={comment['is_unread']}"
    print(f"✅ Comment shows as unread for User B (is_unread={comment['is_unread']})")

    # ========================================
    # STEP 5: User B marks comment as read
    # ========================================
    print("\n[Step 5] User B marks comment as read...")

    mark_read_response = requests.post(
        f"{BASE_URL}/diagrams/{diagram_id}/comments/{comment_id}/mark-read",
        headers={"Authorization": f"Bearer {user_b['access_token']}"}
    )
    assert mark_read_response.status_code == 200, f"Mark as read failed: {mark_read_response.text}"
    read_data = mark_read_response.json()
    print(f"✅ Comment marked as read at {read_data.get('read_at')}")

    # ========================================
    # STEP 6: Verify indicator is cleared
    # ========================================
    print("\n[Step 6] User B views comments again (indicator should be cleared)...")

    get_comments_response_2 = requests.get(
        f"{BASE_URL}/diagrams/{diagram_id}/comments",
        headers={"Authorization": f"Bearer {user_b['access_token']}"}
    )
    assert get_comments_response_2.status_code == 200, f"Get comments failed: {get_comments_response_2.text}"
    comments_2 = get_comments_response_2.json()["comments"]

    assert len(comments_2) == 1, f"Expected 1 comment, got {len(comments_2)}"
    comment_2 = comments_2[0]

    # Verify unread indicator is cleared
    assert "is_unread" in comment_2, "is_unread field missing from comment"
    assert comment_2["is_unread"] == False, f"Expected comment to be read, but is_unread={comment_2['is_unread']}"
    print(f"✅ Unread indicator cleared for User B (is_unread={comment_2['is_unread']})")

    # ========================================
    # STEP 7: Verify User A doesn't see their own comments as unread
    # ========================================
    print("\n[Step 7] Verify User A doesn't see their own comment as unread...")

    get_comments_response_a = requests.get(
        f"{BASE_URL}/diagrams/{diagram_id}/comments",
        headers={"Authorization": f"Bearer {user_a['access_token']}"}
    )
    assert get_comments_response_a.status_code == 200, f"Get comments failed: {get_comments_response_a.text}"
    comments_a = get_comments_response_a.json()["comments"]

    assert len(comments_a) == 1, f"Expected 1 comment, got {len(comments_a)}"
    comment_a = comments_a[0]

    # User A should never see their own comment as unread
    assert comment_a["is_unread"] == False, f"User A should not see their own comment as unread"
    print(f"✅ User A's own comment shows as read (is_unread={comment_a['is_unread']})")

    # ========================================
    # Final Summary
    # ========================================
    print("\n" + "="*80)
    print("✅ Feature #439 TEST PASSED!")
    print("="*80)
    print("\nTest Summary:")
    print("1. ✅ User A created comment")
    print("2. ✅ User B saw unread indicator on comment")
    print("3. ✅ User B marked comment as read")
    print("4. ✅ Unread indicator cleared for User B")
    print("5. ✅ User A never saw their own comment as unread")
    print("\nAll tests passed successfully!")

    return True


if __name__ == "__main__":
    try:
        test_feature_439()
        exit(0)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
