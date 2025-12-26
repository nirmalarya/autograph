#!/usr/bin/env python3
"""
E2E Test for Feature #452: Comment Sorting - Most Reactions

Tests that comments can be sorted by number of reactions, with comments
that have the most reactions appearing at the top.
"""

import requests
import time
import uuid
import jwt as jwt_lib

# Configuration
BASE_URL = "http://localhost:8080"
DIAGRAM_SERVICE_URL = "http://localhost:8082"

def test_comment_sorting_most_reactions():
    """Test that comments can be sorted by most reactions."""

    print("=" * 80)
    print("FEATURE #452: Comment Sorting - Most Reactions")
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
        "title": f"Test Diagram 452 {uuid.uuid4().hex[:8]}",
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

    # Step 3: Create multiple comments
    print("\n3. Creating comments...")
    comment_ids = []
    comment_contents = []

    for i in range(4):
        comment_content = f"Comment #{i+1} - For reactions test"
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
        assert comment_response.status_code == 201, f"Failed: {comment_response.text}"

        comment_data = comment_response.json()
        comment_ids.append(comment_data["id"])
        print(f"   ✓ Comment {i+1} created: {comment_data['id'][:8]}...")

        time.sleep(0.2)

    print(f"   ✓ Created {len(comment_ids)} comments")

    # Step 4: Add different numbers of reactions to each comment
    print("\n4. Adding reactions to comments...")
    # Comment 0: 1 reaction
    # Comment 1: 5 reactions
    # Comment 2: 3 reactions
    # Comment 3: 0 reactions (no reactions)

    reaction_counts = [1, 5, 3, 0]
    emojis = ["👍", "❤️", "😀", "🎉", "🔥"]

    for i, count in enumerate(reaction_counts):
        for j in range(count):
            emoji = emojis[j % len(emojis)]
            reaction_response = requests.post(
                f"{DIAGRAM_SERVICE_URL}/{diagram_id}/comments/{comment_ids[i]}/reactions",
                headers=headers,
                json={"emoji": emoji}
            )
            # Reactions might return 200 or 201
            assert reaction_response.status_code in [200, 201], \
                f"Failed to add reaction: {reaction_response.text}"

        if count > 0:
            print(f"   ✓ Added {count} reactions to Comment #{i+1}")
        else:
            print(f"   ✓ No reactions for Comment #{i+1}")

    print(f"   ✓ Reactions added")

    # Step 5: Select sort: Most Reactions
    print("\n5. Selecting sort: Most Reactions...")
    sort_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/comments",
        headers=headers,
        params={"sort_by": "most_reactions"}
    )
    print(f"   Get comments (most_reactions) status: {sort_response.status_code}")
    assert sort_response.status_code == 200, f"Failed: {sort_response.text}"

    sorted_data = sort_response.json()
    sorted_comments = sorted_data["comments"]
    print(f"   ✓ Retrieved {len(sorted_comments)} comments sorted by reactions")

    # Step 6: Verify comments with most reactions at top
    print("\n6. Verifying comments with most reactions at top...")
    assert len(sorted_comments) >= 4, f"Should have at least 4 comments"

    # Expected order based on reaction counts:
    # 1st: Comment #2 (5 reactions)
    # 2nd: Comment #3 (3 reactions)
    # 3rd: Comment #1 (1 reaction)
    # 4th: Comment #4 (0 reactions)

    # Verify the comment with most reactions (5) is first
    assert sorted_comments[0]["id"] == comment_ids[1], \
        f"First comment should be the one with 5 reactions (Comment #2)"
    assert sorted_comments[0]["total_reactions"] == 5, \
        f"First comment should have 5 reactions, got {sorted_comments[0]['total_reactions']}"
    print(f"   ✓ Comment with most reactions (5) is at top: {sorted_comments[0]['id'][:8]}...")

    # Verify second place (3 reactions)
    assert sorted_comments[1]["id"] == comment_ids[2], \
        f"Second comment should be the one with 3 reactions (Comment #3)"
    assert sorted_comments[1]["total_reactions"] == 3, \
        f"Second comment should have 3 reactions"
    print(f"   ✓ Comment with 3 reactions is second: {sorted_comments[1]['id'][:8]}...")

    # Verify third place (1 reaction)
    assert sorted_comments[2]["id"] == comment_ids[0], \
        f"Third comment should be the one with 1 reaction (Comment #1)"
    assert sorted_comments[2]["total_reactions"] == 1, \
        f"Third comment should have 1 reaction"
    print(f"   ✓ Comment with 1 reaction is third: {sorted_comments[2]['id'][:8]}...")

    # Verify last place (0 reactions)
    assert sorted_comments[3]["id"] == comment_ids[3], \
        f"Last comment should be the one with 0 reactions (Comment #4)"
    assert sorted_comments[3]["total_reactions"] == 0, \
        f"Last comment should have 0 reactions"
    print(f"   ✓ Comment with 0 reactions is last: {sorted_comments[3]['id'][:8]}...")

    # Step 7: Verify reaction counts are in descending order
    print("\n7. Verifying reaction counts are in descending order...")
    for i in range(len(sorted_comments) - 1):
        current_reactions = sorted_comments[i]["total_reactions"]
        next_reactions = sorted_comments[i + 1]["total_reactions"]
        assert current_reactions >= next_reactions, \
            f"Reaction counts should be descending at index {i}. " \
            f"Current: {current_reactions}, Next: {next_reactions}"

    print(f"   ✓ All reaction counts in descending order")

    # Step 8: Verify total_reactions field is present
    print("\n8. Verifying total_reactions field...")
    for i, comment in enumerate(sorted_comments):
        assert "total_reactions" in comment, \
            f"Comment {i} should have total_reactions field"
        assert isinstance(comment["total_reactions"], int), \
            f"total_reactions should be an integer"
        print(f"   ✓ Comment {i+1}: {comment['total_reactions']} reactions")

    print("\n" + "=" * 80)
    print("✅ FEATURE #452 TEST PASSED")
    print("=" * 80)
    print("\nTest Results:")
    print(f"  • Created {len(comment_ids)} test comments")
    print(f"  • Added varying numbers of reactions (5, 3, 1, 0)")
    print(f"  • Sort: Most Reactions parameter accepted")
    print(f"  • Comments sorted correctly by reaction count")
    print(f"  • Comment with most reactions (5) verified at top")
    print(f"  • Reaction counts in descending order verified")
    print(f"  • All comments include total_reactions field")
    print("\n✅ Comment sorting (most reactions) works correctly!")

    return True


if __name__ == "__main__":
    try:
        test_comment_sorting_most_reactions()
        print("\n" + "🎉 " * 20)
        print("ALL TESTS PASSED!")
        print("🎉 " * 20)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise
