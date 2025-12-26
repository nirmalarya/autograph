#!/usr/bin/env python3
"""Test Feature #433: Comment Reactions (Emoji Reactions)

Tests:
1. View comment
2. Click reaction button (add 👍)
3. Verify thumbs up added
4. Test ❤️ and 😄 emojis
5. Verify all reactions work
6. Toggle reactions (remove/re-add)
"""

import requests
import json
import sys
import jwt

# Configuration
API_BASE_URL = "http://localhost:8080/api"
DIAGRAM_SERVICE_URL = "http://localhost:8082"

# Test credentials
TEST_USER_EMAIL = "testreactions@test.com"
TEST_USER_PASSWORD = "Test123!"

def register_and_login():
    """Register test user and get auth token."""
    print("\n1. Logging in...")

    # Try to login directly (user may already exist)
    # Login
    login_response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
    )

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)
        return None

    token = login_response.json().get("access_token")

    # Decode JWT to get user_id
    decoded = jwt.decode(token, options={'verify_signature': False})
    user_id = decoded.get("sub")

    print(f"✅ Logged in successfully (user_id: {user_id})")
    return token, user_id


def create_diagram(token, user_id):
    """Create a test diagram."""
    print("\n2. Creating test diagram...")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{API_BASE_URL}/diagrams",
        headers=headers,
        json={
            "title": "Test Diagram for Reactions",
            "type": "canvas",
            "content": {"elements": []}
        }
    )

    if response.status_code not in [200, 201]:
        print(f"❌ Failed to create diagram: {response.status_code}")
        print(response.text)
        return None

    diagram_id = response.json().get("id")
    print(f"✅ Created diagram: {diagram_id}")
    return diagram_id


def create_comment(token, user_id, diagram_id):
    """Create a comment on the diagram."""
    print("\n3. Creating comment...")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-User-ID": user_id
    }

    response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/comments",
        headers=headers,
        json={
            "content": "This is a test comment for reactions!"
        }
    )

    if response.status_code not in [200, 201]:
        print(f"❌ Failed to create comment: {response.status_code}")
        print(response.text)
        return None

    comment_id = response.json().get("id")
    print(f"✅ Created comment: {comment_id}")
    return comment_id


def add_reaction(token, user_id, diagram_id, comment_id, emoji):
    """Add an emoji reaction to a comment."""
    print(f"\n4. Adding reaction: {emoji}...")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-User-ID": user_id
    }

    response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/comments/{comment_id}/reactions",
        headers=headers,
        json={"emoji": emoji}
    )

    if response.status_code not in [200, 201]:
        print(f"❌ Failed to add reaction {emoji}: {response.status_code}")
        print(response.text)
        return False

    result = response.json()
    action = result.get("action", "unknown")
    print(f"✅ Reaction {emoji} {action}")
    return action == "added"


def get_comment_reactions(token, user_id, diagram_id, comment_id):
    """Get reactions for a comment."""
    print(f"\n5. Getting comment reactions...")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-User-ID": user_id
    }

    response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/comments",
        headers=headers
    )

    if response.status_code != 200:
        print(f"❌ Failed to get comments: {response.status_code}")
        print(response.text)
        return None

    comments = response.json().get("comments", [])
    for comment in comments:
        if comment["id"] == comment_id:
            reactions = comment.get("reactions", {})
            total_reactions = comment.get("total_reactions", 0)
            print(f"✅ Found comment with reactions: {reactions}")
            print(f"   Total reactions: {total_reactions}")
            return reactions

    print(f"❌ Comment not found in response")
    return None


def remove_reaction(token, user_id, diagram_id, comment_id, emoji):
    """Remove an emoji reaction (toggle)."""
    print(f"\n6. Removing reaction: {emoji}...")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-User-ID": user_id
    }

    # POST with same emoji toggles it off
    response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/comments/{comment_id}/reactions",
        headers=headers,
        json={"emoji": emoji}
    )

    if response.status_code not in [200, 201]:
        print(f"❌ Failed to remove reaction {emoji}: {response.status_code}")
        print(response.text)
        return False

    result = response.json()
    action = result.get("action", "unknown")
    print(f"✅ Reaction {emoji} {action}")
    return action == "removed"


def cleanup(token, diagram_id):
    """Clean up test data."""
    print(f"\n7. Cleaning up...")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Delete diagram (cascades to comments and reactions)
    response = requests.delete(
        f"{API_BASE_URL}/diagrams/{diagram_id}",
        headers=headers
    )

    if response.status_code in [200, 204]:
        print(f"✅ Cleaned up diagram")
    else:
        print(f"⚠️  Failed to delete diagram: {response.status_code}")


def main():
    """Run all tests for Feature #433."""
    print("=" * 60)
    print("Testing Feature #433: Comment Reactions (Emoji Reactions)")
    print("=" * 60)

    # Step 1: Register and login
    auth_result = register_and_login()
    if not auth_result:
        print("\n❌ FAILED: Could not authenticate")
        return False

    token, user_id = auth_result

    # Step 2: Create diagram
    diagram_id = create_diagram(token, user_id)
    if not diagram_id:
        print("\n❌ FAILED: Could not create diagram")
        return False

    # Step 3: Create comment
    comment_id = create_comment(token, user_id, diagram_id)
    if not comment_id:
        print("\n❌ FAILED: Could not create comment")
        cleanup(token, diagram_id)
        return False

    # Step 4: Add 👍 reaction
    if not add_reaction(token, user_id, diagram_id, comment_id, "👍"):
        print("\n❌ FAILED: Could not add 👍 reaction")
        cleanup(token, diagram_id)
        return False

    # Step 5: Verify 👍 added
    reactions = get_comment_reactions(token, user_id, diagram_id, comment_id)
    if reactions is None or "👍" not in reactions:
        print("\n❌ FAILED: 👍 reaction not found")
        cleanup(token, diagram_id)
        return False

    if reactions["👍"] != 1:
        print(f"\n❌ FAILED: Expected 1 👍 reaction, got {reactions['👍']}")
        cleanup(token, diagram_id)
        return False

    print("✅ Verified 👍 reaction added")

    # Step 6: Add ❤️ reaction
    if not add_reaction(token, user_id, diagram_id, comment_id, "❤️"):
        print("\n❌ FAILED: Could not add ❤️ reaction")
        cleanup(token, diagram_id)
        return False

    # Step 7: Add 😄 reaction
    if not add_reaction(token, user_id, diagram_id, comment_id, "😄"):
        print("\n❌ FAILED: Could not add 😄 reaction")
        cleanup(token, diagram_id)
        return False

    # Step 8: Verify all reactions
    reactions = get_comment_reactions(token, user_id, diagram_id, comment_id)
    if reactions is None:
        print("\n❌ FAILED: Could not get reactions")
        cleanup(token, diagram_id)
        return False

    expected_emojis = ["👍", "❤️", "😄"]
    for emoji in expected_emojis:
        if emoji not in reactions:
            print(f"\n❌ FAILED: {emoji} reaction not found")
            cleanup(token, diagram_id)
            return False
        if reactions[emoji] != 1:
            print(f"\n❌ FAILED: Expected 1 {emoji} reaction, got {reactions[emoji]}")
            cleanup(token, diagram_id)
            return False

    print("✅ Verified all reactions (👍, ❤️, 😄)")

    # Step 9: Test toggle (remove 👍)
    if not remove_reaction(token, user_id, diagram_id, comment_id, "👍"):
        print("\n❌ FAILED: Could not remove 👍 reaction")
        cleanup(token, diagram_id)
        return False

    # Step 10: Verify 👍 removed
    reactions = get_comment_reactions(token, user_id, diagram_id, comment_id)
    if reactions is None:
        print("\n❌ FAILED: Could not get reactions")
        cleanup(token, diagram_id)
        return False

    if "👍" in reactions:
        print(f"\n❌ FAILED: 👍 reaction should be removed but still present")
        cleanup(token, diagram_id)
        return False

    print("✅ Verified 👍 reaction removed")

    # Step 11: Re-add 👍
    if not add_reaction(token, user_id, diagram_id, comment_id, "👍"):
        print("\n❌ FAILED: Could not re-add 👍 reaction")
        cleanup(token, diagram_id)
        return False

    # Step 12: Verify 👍 re-added
    reactions = get_comment_reactions(token, user_id, diagram_id, comment_id)
    if reactions is None or "👍" not in reactions:
        print("\n❌ FAILED: 👍 reaction not re-added")
        cleanup(token, diagram_id)
        return False

    print("✅ Verified 👍 reaction re-added (toggle works)")

    # Cleanup
    cleanup(token, diagram_id)

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED for Feature #433")
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
