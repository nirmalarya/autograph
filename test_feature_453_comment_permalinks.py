#!/usr/bin/env python3
"""
E2E Test for Feature #453: Comment Permalinks

Tests that comments have direct links that can be used to jump directly
to a specific comment. The permalink should be in the format:
{base_url}diagram/{diagram_id}#comment-{comment_id}

Note: Full UI testing (scrolling, highlighting) would require a browser.
This test verifies the backend provides the permalink.
"""

import requests
import uuid
import jwt as jwt_lib
import re

# Configuration
BASE_URL = "http://localhost:8080"
DIAGRAM_SERVICE_URL = "http://localhost:8082"

def test_comment_permalinks():
    """Test that comments have permalinks for direct access."""

    print("=" * 80)
    print("FEATURE #453: Comment Permalinks")
    print("=" * 80)

    # Step 1: Login test user
    print("\n1. Setting up test user...")
    test_email = "test_user_450@example.com"
    test_password = "TestPass123!"

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
        "title": f"Test Diagram 453 {uuid.uuid4().hex[:8]}",
        "diagram_type": "flowchart",
        "content": {"elements": []}
    }

    create_response = requests.post(
        f"{BASE_URL}/api/diagrams",
        headers=headers,
        json=diagram_data
    )
    print(f"   Create diagram status: {create_response.status_code}")
    assert create_response.status_code in [200, 201], f"Failed: {create_response.text}"

    diagram_id = create_response.json()["id"]
    print(f"   ✓ Diagram created: {diagram_id}")

    # Step 3: Create a comment
    print("\n3. Creating a test comment...")
    comment_content = "Test comment for permalink feature"

    comment_response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/comments",
        headers=headers,
        json={
            "content": comment_content,
            "position_x": 100,
            "position_y": 200
        }
    )
    print(f"   Create comment status: {comment_response.status_code}")
    assert comment_response.status_code == 201, f"Failed: {comment_response.text}"

    comment_data = comment_response.json()
    comment_id = comment_data["id"]
    print(f"   ✓ Comment created: {comment_id}")

    # Step 4: Verify permalink is in response (simulates right-click copy link)
    print("\n4. Verifying permalink in comment response...")
    assert "permalink" in comment_data, "Comment should have permalink field"
    permalink = comment_data["permalink"]
    print(f"   ✓ Permalink found: {permalink}")

    # Step 5: Verify permalink format
    print("\n5. Verifying permalink format...")
    # Expected format: {base_url}diagram/{diagram_id}#comment-{comment_id}
    expected_pattern = rf".*diagram/{diagram_id}#comment-{comment_id}"
    assert re.match(expected_pattern, permalink), \
        f"Permalink should match pattern. Got: {permalink}"
    print(f"   ✓ Permalink format correct")

    # Verify it contains the comment ID in the hash
    assert f"#comment-{comment_id}" in permalink, \
        "Permalink should contain #comment-{id} anchor"
    print(f"   ✓ Permalink contains comment anchor: #comment-{comment_id}")

    # Step 6: Retrieve comments list and verify permalinks are included
    print("\n6. Retrieving comments and verifying permalinks...")
    get_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/comments",
        headers=headers
    )
    assert get_response.status_code == 200, f"Failed: {get_response.text}"

    get_data = get_response.json()
    comments = get_data["comments"]
    print(f"   ✓ Retrieved {len(comments)} comments")

    # Find our comment in the list
    our_comment = None
    for comment in comments:
        if comment["id"] == comment_id:
            our_comment = comment
            break

    assert our_comment is not None, "Our comment should be in the list"
    print(f"   ✓ Found our comment in list")

    # Step 7: Verify comment in list also has permalink
    print("\n7. Verifying permalink in comment list...")
    assert "permalink" in our_comment, "Comment in list should have permalink"
    list_permalink = our_comment["permalink"]
    print(f"   ✓ Permalink in list: {list_permalink}")

    # Should be the same as the one from creation
    assert list_permalink == permalink or \
           list_permalink.endswith(f"diagram/{diagram_id}#comment-{comment_id}"), \
        "Permalink in list should match creation permalink"
    print(f"   ✓ Permalink consistency verified")

    # Step 8: Create multiple comments and verify each has unique permalink
    print("\n8. Creating multiple comments to verify unique permalinks...")
    permalinks = {permalink}  # Start with first comment's permalink

    for i in range(3):
        multi_response = requests.post(
            f"{DIAGRAM_SERVICE_URL}/{diagram_id}/comments",
            headers=headers,
            json={
                "content": f"Comment {i+2} for permalinks",
                "position_x": 100 + (i * 50),
                "position_y": 200
            }
        )
        assert multi_response.status_code == 201

        multi_data = multi_response.json()
        assert "permalink" in multi_data
        multi_permalink = multi_data["permalink"]

        # Verify unique
        assert multi_permalink not in permalinks, \
            f"Each comment should have unique permalink"
        permalinks.add(multi_permalink)

        print(f"   ✓ Comment {i+2} has unique permalink")

    print(f"   ✓ All {len(permalinks)} permalinks are unique")

    # Step 9: Simulate opening link by parsing the comment ID from permalink
    print("\n9. Simulating permalink navigation...")
    # Extract comment ID from permalink (simulates opening in new tab)
    match = re.search(r'#comment-([a-f0-9-]+)', permalink)
    assert match, "Should be able to extract comment ID from permalink"
    extracted_comment_id = match.group(1)

    assert extracted_comment_id == comment_id, \
        f"Extracted ID should match. Expected {comment_id}, got {extracted_comment_id}"
    print(f"   ✓ Comment ID successfully extracted from permalink")
    print(f"   ✓ Simulated navigation to comment: {extracted_comment_id[:8]}...")

    # In a real browser, the #comment-{id} anchor would:
    # - Scroll the page to the comment
    # - Highlight the comment
    # This test verifies the permalink is correct; actual UI behavior requires browser testing

    print("\n" + "=" * 80)
    print("✅ FEATURE #453 TEST PASSED")
    print("=" * 80)
    print("\nTest Results:")
    print(f"  • Comment creation includes permalink field")
    print(f"  • Permalink format verified: diagram/{{id}}#comment-{{id}}")
    print(f"  • Permalink contains comment anchor (#comment-{{id}})")
    print(f"  • Permalinks included in comment list responses")
    print(f"  • Permalink consistency verified across endpoints")
    print(f"  • Multiple comments have unique permalinks")
    print(f"  • Comment ID can be extracted from permalink")
    print("\n✅ Comment permalinks work correctly!")
    print("\nNote: Full UI testing (scroll to comment, highlighting) requires browser.")
    print("Backend permalink generation is working as expected.")

    return True


if __name__ == "__main__":
    try:
        test_comment_permalinks()
        print("\n" + "🎉 " * 20)
        print("ALL TESTS PASSED!")
        print("🎉 " * 20)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise
