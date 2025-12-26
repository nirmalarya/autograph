#!/usr/bin/env python3
"""
Test Feature #439: Comment Filters (all, open, resolved, mine, mentions)

Tests the comment filtering functionality to filter by:
- all: show all comments (default)
- open: show only unresolved comments
- resolved: show only resolved comments
- mine: show only comments by the current user
- mentions: show only comments that mention the current user
"""

import requests
import os
import sys
import uuid
import psycopg2
import time

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080/api")
DIAGRAM_SERVICE_URL = os.getenv("DIAGRAM_SERVICE_URL", "http://localhost:8082")

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


def test_comment_filters():
    """Test comment filters: all, open, resolved, mine, mentions."""
    print("\n" + "="*60)
    print("TEST: Comment Filters")
    print("="*60)

    # Step 1: Create two test users
    print("\n[1] Creating test users...")

    # User A (use timestamp for simpler username without hyphens)
    import time
    timestamp = int(time.time() * 1000)
    user_a_email = f"usera{timestamp}@example.com"
    user_a_password = "SecurePass123!"

    response = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={
            "email": user_a_email,
            "password": user_a_password,
            "full_name": "User A"
        }
    )

    if response.status_code != 201:
        print(f"❌ Failed to register User A: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    user_a_id = response.json()["id"]
    print(f"✅ User A registered: {user_a_email}, ID: {user_a_id}")

    # Wait and verify email
    time.sleep(0.5)
    verify_email(user_a_email)

    # Login User A
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={
            "email": user_a_email,
            "password": user_a_password
        }
    )

    if response.status_code != 200:
        print(f"❌ Failed to login User A: {response.status_code}")
        return False

    user_a_token = response.json()["access_token"]
    print(f"✅ User A logged in")

    # User B
    user_b_email = f"userb{timestamp + 1}@example.com"
    user_b_password = "SecurePass123!"

    response = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={
            "email": user_b_email,
            "password": user_b_password,
            "full_name": "User B"
        }
    )

    if response.status_code != 201:
        print(f"❌ Failed to register User B: {response.status_code}")
        return False

    user_b_id = response.json()["id"]
    print(f"✅ User B registered: {user_b_email}, ID: {user_b_id}")

    # Wait and verify email
    time.sleep(0.5)
    verify_email(user_b_email)

    # Login User B
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={
            "email": user_b_email,
            "password": user_b_password
        }
    )

    if response.status_code != 200:
        print(f"❌ Failed to login User B: {response.status_code}")
        return False

    user_b_token = response.json()["access_token"]
    print(f"✅ User B logged in")

    # Step 2: Create a diagram (User A)
    print("\n[2] Creating diagram (User A)...")

    response = requests.post(
        f"{API_BASE_URL}/diagrams",
        headers={"Authorization": f"Bearer {user_a_token}"},
        json={
            "title": f"Test Diagram {uuid.uuid4()}",
            "type": "flowchart",
            "content": {"nodes": [], "edges": []}
        }
    )

    if response.status_code not in [200, 201]:
        print(f"❌ Failed to create diagram: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    diagram_id = response.json()["id"]
    print(f"✅ Diagram created: {diagram_id}")

    # Step 3: Share diagram with User B (edit permission)
    print("\n[3] Sharing diagram with User B...")

    response = requests.post(
        f"{API_BASE_URL}/diagrams/{diagram_id}/share",
        headers={"Authorization": f"Bearer {user_a_token}"},
        json={
            "shared_with_user_id": user_b_id,
            "permission": "edit"
        }
    )

    if response.status_code not in [200, 201]:
        print(f"❌ Failed to share diagram: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    print(f"✅ Diagram shared with User B")

    # Step 4: Create test comments with different states
    print("\n[4] Creating test comments...")

    # User A creates comment 1 (will be open)
    response = requests.post(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments",
        headers={"Authorization": f"Bearer {user_a_token}"},
        json={
            "content": "User A comment 1 - open"
        }
    )

    if response.status_code != 201:
        print(f"❌ Failed to create comment 1: {response.status_code}")
        return False

    comment_1_id = response.json()["id"]
    print(f"✅ Comment 1 created by User A: {comment_1_id}")

    # User A creates comment 2 (will be resolved)
    response = requests.post(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments",
        headers={"Authorization": f"Bearer {user_a_token}"},
        json={
            "content": "User A comment 2 - will resolve"
        }
    )

    if response.status_code != 201:
        print(f"❌ Failed to create comment 2: {response.status_code}")
        return False

    comment_2_id = response.json()["id"]
    print(f"✅ Comment 2 created by User A: {comment_2_id}")

    # User B creates comment 3 (will be open)
    response = requests.post(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments",
        headers={"Authorization": f"Bearer {user_b_token}"},
        json={
            "content": "User B comment 3 - open"
        }
    )

    if response.status_code != 201:
        print(f"❌ Failed to create comment 3: {response.status_code}")
        return False

    comment_3_id = response.json()["id"]
    print(f"✅ Comment 3 created by User B: {comment_3_id}")

    # User B creates comment 4 with mention of User A
    # Extract username from email (part before @)
    user_a_username = user_a_email.split('@')[0]
    response = requests.post(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments",
        headers={"Authorization": f"Bearer {user_b_token}"},
        json={
            "content": f"User B comment 4 - mentioning User A @{user_a_username}"
        }
    )

    if response.status_code != 201:
        print(f"❌ Failed to create comment 4: {response.status_code}")
        return False

    comment_4_id = response.json()["id"]
    print(f"✅ Comment 4 created by User B with mention: {comment_4_id}")

    # Resolve comment 2
    print("\n[5] Resolving comment 2...")

    response = requests.post(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments/{comment_2_id}/resolve",
        headers={"Authorization": f"Bearer {user_a_token}"}
    )

    if response.status_code != 200:
        print(f"❌ Failed to resolve comment: {response.status_code}")
        return False

    print(f"✅ Comment 2 resolved")

    # Step 6: Test filter: all
    print("\n[6] Testing filter: all")

    response = requests.get(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments?filter=all",
        headers={"Authorization": f"Bearer {user_a_token}"}
    )

    if response.status_code != 200:
        print(f"❌ Failed to get comments with filter=all: {response.status_code}")
        return False

    comments = response.json()["comments"]
    if len(comments) != 4:
        print(f"❌ Expected 4 comments with filter=all, got {len(comments)}")
        return False

    print(f"✅ Filter 'all' returned {len(comments)} comments")

    # Step 7: Test filter: open
    print("\n[7] Testing filter: open")

    response = requests.get(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments?filter=open",
        headers={"Authorization": f"Bearer {user_a_token}"}
    )

    if response.status_code != 200:
        print(f"❌ Failed to get comments with filter=open: {response.status_code}")
        return False

    comments = response.json()["comments"]
    # Should get 3 comments (1, 3, 4) - all except comment 2 which is resolved
    if len(comments) != 3:
        print(f"❌ Expected 3 open comments, got {len(comments)}")
        for c in comments:
            print(f"   Comment {c['id']}: is_resolved={c['is_resolved']}, content={c['content'][:30]}")
        return False

    # Verify all are unresolved
    for comment in comments:
        if comment["is_resolved"]:
            print(f"❌ Filter 'open' returned a resolved comment: {comment['id']}")
            return False

    print(f"✅ Filter 'open' returned {len(comments)} unresolved comments")

    # Step 8: Test filter: resolved
    print("\n[8] Testing filter: resolved")

    response = requests.get(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments?filter=resolved",
        headers={"Authorization": f"Bearer {user_a_token}"}
    )

    if response.status_code != 200:
        print(f"❌ Failed to get comments with filter=resolved: {response.status_code}")
        return False

    comments = response.json()["comments"]
    # Should get 1 comment (comment 2)
    if len(comments) != 1:
        print(f"❌ Expected 1 resolved comment, got {len(comments)}")
        return False

    if comments[0]["id"] != comment_2_id:
        print(f"❌ Expected comment {comment_2_id}, got {comments[0]['id']}")
        return False

    if not comments[0]["is_resolved"]:
        print(f"❌ Comment should be resolved but is_resolved=false")
        return False

    print(f"✅ Filter 'resolved' returned {len(comments)} resolved comment(s)")

    # Step 9: Test filter: mine (User A)
    print("\n[9] Testing filter: mine (User A)")

    response = requests.get(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments?filter=mine",
        headers={"Authorization": f"Bearer {user_a_token}"}
    )

    if response.status_code != 200:
        print(f"❌ Failed to get comments with filter=mine: {response.status_code}")
        return False

    comments = response.json()["comments"]
    # Should get 2 comments (comment 1 and 2 by User A)
    if len(comments) != 2:
        print(f"❌ Expected 2 comments by User A, got {len(comments)}")
        return False

    # Verify all are by User A
    for comment in comments:
        if comment["user_id"] != user_a_id:
            print(f"❌ Filter 'mine' returned comment not by User A: {comment['id']}")
            return False

    print(f"✅ Filter 'mine' returned {len(comments)} comment(s) by User A")

    # Step 10: Test filter: mine (User B)
    print("\n[10] Testing filter: mine (User B)")

    response = requests.get(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments?filter=mine",
        headers={"Authorization": f"Bearer {user_b_token}"}
    )

    if response.status_code != 200:
        print(f"❌ Failed to get comments with filter=mine: {response.status_code}")
        return False

    comments = response.json()["comments"]
    # Should get 2 comments (comment 3 and 4 by User B)
    if len(comments) != 2:
        print(f"❌ Expected 2 comments by User B, got {len(comments)}")
        return False

    # Verify all are by User B
    for comment in comments:
        if comment["user_id"] != user_b_id:
            print(f"❌ Filter 'mine' returned comment not by User B: {comment['id']}")
            return False

    print(f"✅ Filter 'mine' returned {len(comments)} comment(s) by User B")

    # Step 11: Test filter: mentions (User A)
    print("\n[11] Testing filter: mentions (User A)")

    response = requests.get(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments?filter=mentions",
        headers={"Authorization": f"Bearer {user_a_token}"}
    )

    if response.status_code != 200:
        print(f"❌ Failed to get comments with filter=mentions: {response.status_code}")
        return False

    comments = response.json()["comments"]
    # Should get 1 comment (comment 4 which mentions User A)
    if len(comments) != 1:
        print(f"❌ Expected 1 comment mentioning User A, got {len(comments)}")
        return False

    if comments[0]["id"] != comment_4_id:
        print(f"❌ Expected comment {comment_4_id}, got {comments[0]['id']}")
        return False

    # Verify mention is in the mentions array
    if user_a_id not in comments[0].get("mentions", []):
        print(f"❌ Comment should mention User A but doesn't")
        return False

    print(f"✅ Filter 'mentions' returned {len(comments)} comment(s) mentioning User A")

    # Step 12: Test filter: mentions (User B - should be empty)
    print("\n[12] Testing filter: mentions (User B - should be empty)")

    response = requests.get(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments?filter=mentions",
        headers={"Authorization": f"Bearer {user_b_token}"}
    )

    if response.status_code != 200:
        print(f"❌ Failed to get comments with filter=mentions: {response.status_code}")
        return False

    comments = response.json()["comments"]
    # Should get 0 comments (no one mentioned User B)
    if len(comments) != 0:
        print(f"❌ Expected 0 comments mentioning User B, got {len(comments)}")
        return False

    print(f"✅ Filter 'mentions' returned {len(comments)} comment(s) for User B (as expected)")

    print("\n" + "="*60)
    print("✅ ALL FILTER TESTS PASSED!")
    print("="*60)
    return True


if __name__ == "__main__":
    try:
        success = test_comment_filters()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
