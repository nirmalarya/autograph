#!/usr/bin/env python3
"""
E2E Test for Feature #450: Comment Sorting (Newest First)

Tests that comments can be sorted with newest comments appearing first.
"""

import requests
import time
import uuid
import jwt as jwt_lib

# Configuration
BASE_URL = "http://localhost:8080"
DIAGRAM_SERVICE_URL = "http://localhost:8082"

def test_comment_sorting_newest_first():
    """Test that comments can be sorted by newest first."""

    print("=" * 80)
    print("FEATURE #450: Comment Sorting - Newest First")
    print("=" * 80)

    # Step 1: Login test user (pre-created via SQL)
    print("\n1. Setting up test user...")
    test_email = "test_user_450@example.com"
    test_password = "TestPass123!"

    # Login
    login_response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "email": test_email,
            "password": test_password
        }
    )
    print(f"   Login status: {login_response.status_code}")
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"

    auth_data = login_response.json()
    access_token = auth_data["access_token"]

    # Decode JWT to get user_id
    decoded = jwt_lib.decode(access_token, options={"verify_signature": False})
    user_id = decoded.get("sub")
    print(f"   ✓ User authenticated: {user_id}")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-User-ID": user_id
    }

    # Step 2: Create a test diagram
    print("\n2. Creating test diagram...")
    diagram_data = {
        "title": f"Test Diagram 450 {uuid.uuid4().hex[:8]}",
        "diagram_type": "flowchart",
        "content": {"elements": []}
    }

    create_response = requests.post(
        f"{BASE_URL}/api/diagrams",
        headers=headers,
        json=diagram_data
    )
    print(f"   Create diagram status: {create_response.status_code}")
    assert create_response.status_code in [200, 201], f"Failed to create diagram: {create_response.text}"

    diagram_id = create_response.json()["id"]
    print(f"   ✓ Diagram created: {diagram_id}")

    # Step 3: Create multiple comments with delays to ensure different timestamps
    print("\n3. Creating comments with different timestamps...")
    comment_ids = []
    comment_contents = []

    for i in range(3):
        comment_content = f"Comment #{i+1} created at {time.time()}"
        comment_contents.append(comment_content)

        comment_response = requests.post(
            f"{DIAGRAM_SERVICE_URL}/{diagram_id}/comments",
            headers=headers,
            json={
                "content": comment_content,
                "position_x": 100,
                "position_y": 100 + (i * 50)
            }
        )
        print(f"   Comment {i+1} status: {comment_response.status_code}")
        assert comment_response.status_code == 201, f"Failed to create comment: {comment_response.text}"

        comment_data = comment_response.json()
        comment_ids.append(comment_data["id"])
        print(f"   ✓ Comment {i+1} created: {comment_data['id'][:8]}...")

        # Add a small delay to ensure timestamps are different
        time.sleep(0.5)

    print(f"   ✓ Created {len(comment_ids)} comments")

    # Step 4: Retrieve comments with default sorting (oldest first)
    print("\n4. Testing default sorting (oldest first)...")
    oldest_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/comments",
        headers=headers,
        params={"sort_by": "oldest"}
    )
    print(f"   Get comments (oldest) status: {oldest_response.status_code}")
    assert oldest_response.status_code == 200, f"Failed to get comments: {oldest_response.text}"

    oldest_data = oldest_response.json()
    oldest_comments = oldest_data["comments"]
    print(f"   ✓ Retrieved {len(oldest_comments)} comments")

    # Verify oldest first order
    assert len(oldest_comments) >= 3, "Should have at least 3 comments"
    assert oldest_comments[0]["content"] == comment_contents[0], "First comment should be oldest"
    assert oldest_comments[-1]["content"] == comment_contents[-1], "Last comment should be newest"
    print(f"   ✓ Oldest first verified: '{oldest_comments[0]['content'][:30]}...'")

    # Step 5: Retrieve comments sorted by newest first
    print("\n5. Testing newest first sorting...")
    newest_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/comments",
        headers=headers,
        params={"sort_by": "newest"}
    )
    print(f"   Get comments (newest) status: {newest_response.status_code}")
    assert newest_response.status_code == 200, f"Failed to get comments: {newest_response.text}"

    newest_data = newest_response.json()
    newest_comments = newest_data["comments"]
    print(f"   ✓ Retrieved {len(newest_comments)} comments")

    # Step 6: Verify newest first order
    print("\n6. Verifying newest first order...")
    assert len(newest_comments) >= 3, "Should have at least 3 comments"

    # The newest comment (last created) should be first in the list
    assert newest_comments[0]["content"] == comment_contents[-1], \
        f"First comment should be newest. Expected '{comment_contents[-1]}', got '{newest_comments[0]['content']}'"

    # The oldest comment (first created) should be last in the list
    assert newest_comments[-1]["content"] == comment_contents[0], \
        f"Last comment should be oldest. Expected '{comment_contents[0]}', got '{newest_comments[-1]['content']}'"

    # Verify the order is reversed from oldest
    assert newest_comments[0]["id"] == oldest_comments[-1]["id"], \
        "First comment in newest should be last in oldest"
    assert newest_comments[-1]["id"] == oldest_comments[0]["id"], \
        "Last comment in newest should be first in oldest"

    print(f"   ✓ Most recent comment appears first: '{newest_comments[0]['content'][:30]}...'")
    print(f"   ✓ Oldest comment appears last: '{newest_comments[-1]['content'][:30]}...'")

    # Step 7: Verify timestamps are in descending order
    print("\n7. Verifying timestamp order...")
    for i in range(len(newest_comments) - 1):
        current_time = newest_comments[i]["created_at"]
        next_time = newest_comments[i + 1]["created_at"]
        assert current_time >= next_time, \
            f"Comments should be in descending timestamp order at index {i}"

    print(f"   ✓ All comments in correct descending timestamp order")

    # Step 8: Test without sort_by parameter (should default to oldest)
    print("\n8. Testing default behavior (no sort_by parameter)...")
    default_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/comments",
        headers=headers
    )
    assert default_response.status_code == 200, f"Failed to get comments: {default_response.text}"

    default_data = default_response.json()
    default_comments = default_data["comments"]

    # Should match oldest first behavior
    assert default_comments[0]["id"] == oldest_comments[0]["id"], \
        "Default should be oldest first"
    print(f"   ✓ Default sorting is oldest first")

    print("\n" + "=" * 80)
    print("✅ FEATURE #450 TEST PASSED")
    print("=" * 80)
    print("\nTest Results:")
    print(f"  • Created {len(comment_ids)} test comments")
    print(f"  • Verified oldest first sorting (default)")
    print(f"  • Verified newest first sorting")
    print(f"  • Confirmed most recent comment appears first")
    print(f"  • Confirmed timestamps in descending order")
    print(f"  • Verified default behavior")
    print("\n✅ Comment sorting (newest first) works correctly!")

    return True


if __name__ == "__main__":
    try:
        test_comment_sorting_newest_first()
        print("\n" + "🎉 " * 20)
        print("ALL TESTS PASSED!")
        print("🎉 " * 20)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise
