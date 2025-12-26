#!/usr/bin/env python3
"""
E2E Test for Feature #451: Comment Sorting - Oldest First

Tests that comments can be sorted with oldest comments appearing first.
This is the default sorting behavior.
"""

import requests
import time
import uuid
import jwt as jwt_lib

# Configuration
BASE_URL = "http://localhost:8080"
DIAGRAM_SERVICE_URL = "http://localhost:8082"

def test_comment_sorting_oldest_first():
    """Test that comments can be sorted by oldest first (default)."""

    print("=" * 80)
    print("FEATURE #451: Comment Sorting - Oldest First")
    print("=" * 80)

    # Step 1: Login test user (using existing test user)
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
        "title": f"Test Diagram 451 {uuid.uuid4().hex[:8]}",
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
    comment_timestamps = []

    for i in range(4):
        comment_content = f"Comment #{i+1} - Timestamp: {time.time()}"

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
        comment_timestamps.append(comment_data["created_at"])
        print(f"   ✓ Comment {i+1} created: {comment_data['id'][:8]}... at {comment_data['created_at']}")

        # Add a delay to ensure timestamps are different
        time.sleep(0.3)

    print(f"   ✓ Created {len(comment_ids)} comments")

    # Step 4: Select sort: Oldest (explicit parameter)
    print("\n4. Selecting sort: Oldest...")
    oldest_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/comments",
        headers=headers,
        params={"sort_by": "oldest"}
    )
    print(f"   Get comments (oldest) status: {oldest_response.status_code}")
    assert oldest_response.status_code == 200, f"Failed to get comments: {oldest_response.text}"

    oldest_data = oldest_response.json()
    oldest_comments = oldest_data["comments"]
    print(f"   ✓ Retrieved {len(oldest_comments)} comments with sort_by=oldest")

    # Step 5: Verify earliest comment at top
    print("\n5. Verifying earliest comment at top...")
    assert len(oldest_comments) >= 4, f"Should have at least 4 comments, got {len(oldest_comments)}"

    # First comment should be the earliest (first created)
    first_comment = oldest_comments[0]
    assert first_comment["id"] == comment_ids[0], \
        f"First comment should be earliest. Expected {comment_ids[0]}, got {first_comment['id']}"
    print(f"   ✓ Earliest comment is at top: {first_comment['id'][:8]}...")

    # Last comment should be the latest (last created)
    last_comment = oldest_comments[-1]
    assert last_comment["id"] == comment_ids[-1], \
        f"Last comment should be latest. Expected {comment_ids[-1]}, got {last_comment['id']}"
    print(f"   ✓ Latest comment is at bottom: {last_comment['id'][:8]}...")

    # Verify timestamps are in ascending order
    print("\n6. Verifying timestamp order (ascending)...")
    for i in range(len(oldest_comments) - 1):
        current_time = oldest_comments[i]["created_at"]
        next_time = oldest_comments[i + 1]["created_at"]
        assert current_time <= next_time, \
            f"Comments should be in ascending timestamp order at index {i}. " \
            f"Current: {current_time}, Next: {next_time}"

    print(f"   ✓ All comments in correct ascending timestamp order")

    # Step 7: Verify default behavior (no sort_by) also gives oldest first
    print("\n7. Verifying default sorting (no sort_by parameter)...")
    default_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/comments",
        headers=headers
    )
    assert default_response.status_code == 200, f"Failed to get comments: {default_response.text}"

    default_data = default_response.json()
    default_comments = default_data["comments"]

    # Should match oldest first behavior
    assert default_comments[0]["id"] == comment_ids[0], \
        "Default should show oldest first"
    assert default_comments[-1]["id"] == comment_ids[-1], \
        "Default should show newest last"
    print(f"   ✓ Default sorting matches oldest first")

    # Verify all comment IDs match in order
    for i in range(len(default_comments)):
        assert default_comments[i]["id"] == oldest_comments[i]["id"], \
            f"Default and oldest sorting should match at index {i}"

    print(f"   ✓ Default and oldest sorting produce identical results")

    print("\n" + "=" * 80)
    print("✅ FEATURE #451 TEST PASSED")
    print("=" * 80)
    print("\nTest Results:")
    print(f"  • Created {len(comment_ids)} test comments with different timestamps")
    print(f"  • Sort: Oldest parameter accepted and working")
    print(f"  • Earliest comment verified at top position")
    print(f"  • Latest comment verified at bottom position")
    print(f"  • Timestamps verified in ascending order")
    print(f"  • Default behavior confirmed as oldest first")
    print("\n✅ Comment sorting (oldest first) works correctly!")

    return True


if __name__ == "__main__":
    try:
        test_comment_sorting_oldest_first()
        print("\n" + "🎉 " * 20)
        print("ALL TESTS PASSED!")
        print("🎉 " * 20)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise
