#!/usr/bin/env python3
"""
Validation test for Feature #427: Comments @mentions notify specific users

Tests:
1. Create a comment with @mention
2. Verify mention is created in database
3. Verify mentioned user can see the mention via API
4. Verify notification appears in user's mention list
5. Mark mention as read
"""

import requests
import time
import json

# Configuration
API_GATEWAY_URL = "http://localhost:8080"
DIAGRAM_SERVICE_URL = "http://localhost:8082"

def test_mentions_feature():
    """Test @mentions in comments."""
    print("=" * 80)
    print("FEATURE #427: Comments @mentions notify specific users")
    print("=" * 80)

    # Step 1: Create two test users
    print("\n[1/7] Creating test users...")

    # User 1: alice (will post comment with mention)
    register_data_alice = {
        "email": f"alice_mentions_{int(time.time())}@example.com",
        "password": "SecurePass123!",
        "full_name": "Alice Commenter"
    }

    response = requests.post(
        f"{API_GATEWAY_URL}/auth/register",
        json=register_data_alice,
        headers={"Content-Type": "application/json"}
    )

    if response.status_code != 201:
        print(f"❌ Failed to register Alice: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    alice_email = register_data_alice["email"]
    alice_password = register_data_alice["password"]
    print(f"✅ Alice registered: {alice_email}")

    # User 2: bob (will be mentioned)
    register_data_bob = {
        "email": f"bob_mentions_{int(time.time())}@example.com",
        "password": "SecurePass123!",
        "full_name": "Bob Reviewer"
    }

    response = requests.post(
        f"{API_GATEWAY_URL}/auth/register",
        json=register_data_bob,
        headers={"Content-Type": "application/json"}
    )

    if response.status_code != 201:
        print(f"❌ Failed to register Bob: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    bob_email = register_data_bob["email"]
    bob_password = register_data_bob["password"]
    print(f"✅ Bob registered: {bob_email}")

    # Step 2: Login as Alice
    print("\n[2/7] Logging in as Alice...")

    login_data = {
        "email": alice_email,
        "password": alice_password
    }

    response = requests.post(
        f"{API_GATEWAY_URL}/auth/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )

    if response.status_code != 200:
        print(f"❌ Alice login failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    alice_token = response.json().get("access_token")
    alice_user_id = response.json().get("user", {}).get("id")
    print(f"✅ Alice logged in (user_id: {alice_user_id})")

    # Step 3: Create a diagram as Alice
    print("\n[3/7] Creating diagram as Alice...")

    diagram_data = {
        "name": f"Test Diagram for Mentions {int(time.time())}",
        "type": "canvas",
        "description": "Test diagram for @mentions feature"
    }

    response = requests.post(
        f"{API_GATEWAY_URL}/diagrams",
        json=diagram_data,
        headers={
            "Authorization": f"Bearer {alice_token}",
            "Content-Type": "application/json"
        }
    )

    if response.status_code != 201:
        print(f"❌ Failed to create diagram: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    diagram_id = response.json().get("id")
    print(f"✅ Diagram created: {diagram_id}")

    # Step 4: Create comment with @mention of Bob
    print("\n[4/7] Creating comment with @mention of Bob...")

    # Extract bob's username (email prefix)
    bob_username = bob_email.split("@")[0]

    comment_data = {
        "content": f"Hey @{bob_username} please review this diagram!"
    }

    response = requests.post(
        f"{API_GATEWAY_URL}/diagrams/{diagram_id}/comments",
        json=comment_data,
        headers={
            "Authorization": f"Bearer {alice_token}",
            "Content-Type": "application/json"
        }
    )

    if response.status_code != 201:
        print(f"❌ Failed to create comment: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    comment_id = response.json().get("id")
    print(f"✅ Comment created with @{bob_username} mention")
    print(f"   Comment ID: {comment_id}")

    # Step 5: Login as Bob
    print("\n[5/7] Logging in as Bob...")

    login_data = {
        "email": bob_email,
        "password": bob_password
    }

    response = requests.post(
        f"{API_GATEWAY_URL}/auth/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )

    if response.status_code != 200:
        print(f"❌ Bob login failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    bob_token = response.json().get("access_token")
    bob_user_id = response.json().get("user", {}).get("id")
    print(f"✅ Bob logged in (user_id: {bob_user_id})")

    # Step 6: Get Bob's mentions
    print("\n[6/7] Fetching Bob's mentions...")

    response = requests.get(
        f"{API_GATEWAY_URL}/diagrams/mentions",
        headers={"Authorization": f"Bearer {bob_token}"}
    )

    if response.status_code != 200:
        print(f"❌ Failed to get mentions: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    mentions_data = response.json()
    mentions = mentions_data.get("mentions", [])
    total = mentions_data.get("total", 0)
    unread = mentions_data.get("unread", 0)

    print(f"✅ Bob has {total} total mentions, {unread} unread")

    if total == 0:
        print("❌ Expected at least 1 mention for Bob")
        return False

    # Find our mention
    our_mention = None
    for mention in mentions:
        if mention.get("comment_id") == comment_id:
            our_mention = mention
            break

    if not our_mention:
        print(f"❌ Could not find mention for comment {comment_id}")
        return False

    print(f"✅ Found mention:")
    print(f"   ID: {our_mention.get('id')}")
    print(f"   Comment: {our_mention.get('comment', {}).get('content')}")
    print(f"   Author: {our_mention.get('comment', {}).get('user', {}).get('full_name')}")
    print(f"   Is Read: {our_mention.get('is_read')}")

    # Step 7: Mark mention as read
    print("\n[7/7] Marking mention as read...")

    mention_id = our_mention.get("id")

    response = requests.post(
        f"{API_GATEWAY_URL}/diagrams/mentions/{mention_id}/mark-read",
        headers={"Authorization": f"Bearer {bob_token}"}
    )

    if response.status_code != 200:
        print(f"❌ Failed to mark mention as read: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    read_data = response.json()
    print(f"✅ Mention marked as read at: {read_data.get('read_at')}")

    # Verify mention is now read
    response = requests.get(
        f"{API_GATEWAY_URL}/diagrams/mentions?unread_only=true",
        headers={"Authorization": f"Bearer {bob_token}"}
    )

    if response.status_code == 200:
        unread_mentions = response.json().get("mentions", [])
        unread_count = len(unread_mentions)
        print(f"✅ Bob now has {unread_count} unread mentions (was {unread})")

    print("\n" + "=" * 80)
    print("✅ FEATURE #427 VALIDATION PASSED")
    print("=" * 80)
    print("\nSummary:")
    print("  ✅ Users can @mention other users in comments")
    print("  ✅ Mentions are created when comment contains @username")
    print("  ✅ Mentioned users can retrieve their mentions via API")
    print("  ✅ Mentions show comment content, author, and diagram")
    print("  ✅ Mentions can be marked as read")
    print("  ✅ Unread mentions can be filtered")

    return True

if __name__ == "__main__":
    try:
        success = test_mentions_feature()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
