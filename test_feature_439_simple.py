#!/usr/bin/env python3
"""
E2E Test for Feature #439: Unread Comment Indicator
Tests that comments show unread indicators for users who haven't read them yet.
"""

import requests
import time
import hashlib

# Base URLs
API_URL = "http://localhost:8080/api/diagram-service"

# Use pre-created test users (create them in DB first)
USER_A_EMAIL = "test_user_a@example.com"
USER_A_PASSWORD = "Password123!"
USER_B_EMAIL = "test_user_b@example.com"
USER_B_PASSWORD = "Password123!"

def hash_password(password: str) -> str:
    """Hash password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

def setup_test_users():
    """Setup test users directly in the database."""
    import subprocess

    user_a_hash = hash_password(USER_A_PASSWORD)
    user_b_hash = hash_password(USER_B_PASSWORD)

    sql_commands = f"""
    -- Create User A
    INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role, created_at, updated_at)
    VALUES ('user-a-439', '{USER_A_EMAIL}', '{user_a_hash}', 'Test User A', true, true, 'user', NOW(), NOW())
    ON CONFLICT (email) DO UPDATE SET is_verified = true, is_active = true;

    -- Create User B
    INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role, created_at, updated_at)
    VALUES ('user-b-439', '{USER_B_EMAIL}', '{user_b_hash}', 'Test User B', true, true, 'user', NOW(), NOW())
    ON CONFLICT (email) DO UPDATE SET is_verified = true, is_active = true;
    """

    result = subprocess.run(
        ['docker', 'exec', '-i', 'autograph-postgres', 'psql', '-U', 'autograph', '-d', 'autograph'],
        input=sql_commands.encode(),
        capture_output=True
    )

    if result.returncode != 0:
        print(f"Warning: Failed to create users in DB: {result.stderr.decode()}")
    else:
        print("✅ Test users created in database")

def login_user(email, password):
    """Login and get JWT token."""
    response = requests.post(
        "http://localhost:8085/login",
        json={"email": email, "password": password}
    )
    if response.status_code != 200:
        raise Exception(f"Login failed for {email}: {response.text}")
    return response.json()["access_token"], response.json()["user"]["id"]

def test_feature_439():
    """Test unread comment indicator feature."""
    print("\n" + "="*80)
    print("Testing Feature #439: Unread Comment Indicator")
    print("="*80)

    # ========================================
    # STEP 1: Setup test users
    # ========================================
    print("\n[Step 1] Setting up test users...")
    setup_test_users()

    # ========================================
    # STEP 2: Login both users
    # ========================================
    print("\n[Step 2] Logging in both users...")

    user_a_token, user_a_id = login_user(USER_A_EMAIL, USER_A_PASSWORD)
    print(f"✅ User A logged in: {user_a_id}")

    user_b_token, user_b_id = login_user(USER_B_EMAIL, USER_B_PASSWORD)
    print(f"✅ User B logged in: {user_b_id}")

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
    # STEP 5: User B views comments (should see unread indicator)
    # ========================================
    print("\n[Step 5] User B views comments (should see unread indicator)...")

    time.sleep(1)  # Wait a moment

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
    print(f"✅ Comment shows as unread for User B (is_unread={comment['is_unread']})")

    # ========================================
    # STEP 6: User B marks comment as read
    # ========================================
    print("\n[Step 6] User B marks comment as read...")

    mark_read_response = requests.post(
        f"{API_URL}/{diagram_id}/comments/{comment_id}/mark-read",
        headers={"Authorization": f"Bearer {user_b_token}"}
    )
    assert mark_read_response.status_code == 200, f"Mark as read failed: {mark_read_response.text}"
    read_data = mark_read_response.json()
    print(f"✅ Comment marked as read at {read_data.get('read_at')}")

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
    print(f"✅ Unread indicator cleared for User B (is_unread={comment_2['is_unread']})")

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
