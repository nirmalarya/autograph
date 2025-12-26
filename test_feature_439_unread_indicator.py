#!/usr/bin/env python3
"""
E2E Test for Feature #439: Unread Comment Indicator
Tests that comments show unread indicators for users who haven't read them yet.
"""

import requests
import time

# Base URLs
AUTH_URL = "http://localhost:8085"  # Direct to auth service
API_URL = "http://localhost:8080/api/diagram-service"

def test_feature_439():
    """Test unread comment indicator feature."""
    print("\n" + "="*80)
    print("Testing Feature #439: Unread Comment Indicator")
    print("="*80)

    # ========================================
    # STEP 1: Create two test users
    # ========================================
    print("\n[Step 1] Creating two test users...")

    # User A
    user_a_email = f"user_a_{int(time.time())}@test.com"
    user_a_password = "TestPassword123!"

    register_response_a = requests.post(
        f"{AUTH_URL}/register",
        json={
            "email": user_a_email,
            "password": user_a_password,
            "full_name": "User A"
        }
    )
    if register_response_a.status_code not in [200, 201]:
        raise AssertionError(f"User A registration failed: {register_response_a.text}")
    print(f"✅ User A registered: {user_a_email}")

    # User B
    user_b_email = f"user_b_{int(time.time())}@test.com"
    user_b_password = "TestPassword123!"

    register_response_b = requests.post(
        f"{AUTH_URL}/register",
        json={
            "email": user_b_email,
            "password": user_b_password,
            "full_name": "User B"
        }
    )
    if register_response_b.status_code not in [200, 201]:
        raise AssertionError(f"User B registration failed: {register_response_b.text}")
    print(f"✅ User B registered: {user_b_email}")

    # ========================================
    # STEP 2: Login both users
    # ========================================
    print("\n[Step 2] Logging in both users...")

    # Login User A
    login_response_a = requests.post(
        f"{AUTH_URL}/login",
        json={
            "email": user_a_email,
            "password": user_a_password
        }
    )
    assert login_response_a.status_code == 200, f"User A login failed: {login_response_a.text}"
    user_a_token = login_response_a.json()["access_token"]
    user_a_id = login_response_a.json()["user"]["id"]
    print(f"✅ User A logged in")

    # Login User B
    login_response_b = requests.post(
        f"{AUTH_URL}/login",
        json={
            "email": user_b_email,
            "password": user_b_password
        }
    )
    assert login_response_b.status_code == 200, f"User B login failed: {login_response_b.text}"
    user_b_token = login_response_b.json()["access_token"]
    user_b_id = login_response_b.json()["user"]["id"]
    print(f"✅ User B logged in")

    # ========================================
    # STEP 3: User A creates a diagram
    # ========================================
    print("\n[Step 3] User A creates a diagram...")

    diagram_response = requests.post(
        f"{API_URL}/diagrams",
        json={
            "name": "Test Diagram for Unread Comments",
            "type": "canvas"
        },
        headers={"Authorization": f"Bearer {user_a_token}"}
    )
    assert diagram_response.status_code == 200, f"Diagram creation failed: {diagram_response.text}"
    diagram_id = diagram_response.json()["id"]
    print(f"✅ Diagram created: {diagram_id}")

    # ========================================
    # STEP 4: User A adds a comment
    # ========================================
    print("\n[Step 4] User A adds a comment...")

    comment_response = requests.post(
        f"{API_URL}/{diagram_id}/comments",
        json={
            "content": "This is a test comment from User A",
            "position_x": 100,
            "position_y": 100
        },
        headers={"Authorization": f"Bearer {user_a_token}"}
    )
    assert comment_response.status_code == 200, f"Comment creation failed: {comment_response.text}"
    comment_id = comment_response.json()["id"]
    print(f"✅ Comment created: {comment_id}")

    # ========================================
    # STEP 5: User B logs in and views comments
    # ========================================
    print("\n[Step 5] User B views comments (should see unread indicator)...")

    # Wait a moment to ensure timestamp difference
    time.sleep(1)

    get_comments_response = requests.get(
        f"{API_URL}/{diagram_id}/comments",
        headers={"Authorization": f"Bearer {user_b_token}"}
    )
    assert get_comments_response.status_code == 200, f"Get comments failed: {get_comments_response.text}"
    comments = get_comments_response.json()["comments"]

    assert len(comments) == 1, f"Expected 1 comment, got {len(comments)}"
    comment = comments[0]

    # Verify unread indicator is present
    assert "is_unread" in comment, "is_unread field missing from comment"
    assert comment["is_unread"] == True, f"Expected comment to be unread, but is_unread={comment['is_unread']}"
    print(f"✅ Comment shows as unread for User B")

    # ========================================
    # STEP 6: User B marks comment as read
    # ========================================
    print("\n[Step 6] User B marks comment as read...")

    mark_read_response = requests.post(
        f"{API_URL}/{diagram_id}/comments/{comment_id}/mark-read",
        headers={"Authorization": f"Bearer {user_b_token}"}
    )
    assert mark_read_response.status_code == 200, f"Mark as read failed: {mark_read_response.text}"
    print(f"✅ Comment marked as read")

    # ========================================
    # STEP 7: Verify indicator is cleared
    # ========================================
    print("\n[Step 7] User B views comments again (indicator should be cleared)...")

    get_comments_response_2 = requests.get(
        f"{API_URL}/{diagram_id}/comments",
        headers={"Authorization": f"Bearer {user_b_token}"}
    )
    assert get_comments_response_2.status_code == 200, f"Get comments failed: {get_comments_response_2.text}"
    comments_2 = get_comments_response_2.json()["comments"]

    assert len(comments_2) == 1, f"Expected 1 comment, got {len(comments_2)}"
    comment_2 = comments_2[0]

    # Verify unread indicator is cleared
    assert "is_unread" in comment_2, "is_unread field missing from comment"
    assert comment_2["is_unread"] == False, f"Expected comment to be read, but is_unread={comment_2['is_unread']}"
    print(f"✅ Unread indicator cleared for User B")

    # ========================================
    # STEP 8: Verify User A doesn't see their own comments as unread
    # ========================================
    print("\n[Step 8] Verify User A doesn't see their own comment as unread...")

    get_comments_response_a = requests.get(
        f"{API_URL}/{diagram_id}/comments",
        headers={"Authorization": f"Bearer {user_a_token}"}
    )
    assert get_comments_response_a.status_code == 200, f"Get comments failed: {get_comments_response_a.text}"
    comments_a = get_comments_response_a.json()["comments"]

    assert len(comments_a) == 1, f"Expected 1 comment, got {len(comments_a)}"
    comment_a = comments_a[0]

    # User A should never see their own comment as unread
    assert comment_a["is_unread"] == False, f"User A should not see their own comment as unread"
    print(f"✅ User A's own comment shows as read (not unread)")

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
        exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
