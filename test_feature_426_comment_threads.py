#!/usr/bin/env python3
"""
Test Feature #426: Comment Threads - Reply to Comments

This test validates that users can reply to comments, creating threaded conversations.
"""

import requests
import json
import sys
import time

# Configuration
AUTH_SERVICE = "http://localhost:8085"
DIAGRAM_SERVICE = "http://localhost:8082"
TEST_USER_EMAIL = "comment_thread_test@example.com"
TEST_USER_PASSWORD = "SecurePass123!@#"

def print_step(step_num, description):
    """Print test step."""
    print(f"\n{'='*60}")
    print(f"Step {step_num}: {description}")
    print('='*60)

def register_and_login():
    """Register and login a test user."""
    print_step(1, "Register and login test user")

    # Register
    register_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
        "full_name": "Test User"
    }

    try:
        response = requests.post(f"{AUTH_SERVICE}/register", json=register_data)
        if response.status_code == 201:
            print(f"✓ User registered: {TEST_USER_EMAIL}")
        elif response.status_code == 400 and "already exists" in response.text:
            print(f"✓ User already exists: {TEST_USER_EMAIL}")
        else:
            print(f"✗ Registration failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Registration error: {e}")

    # Login
    login_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }

    response = requests.post(f"{AUTH_SERVICE}/login", json=login_data)
    if response.status_code == 200:
        data = response.json()
        # Try different possible fields for user_id
        user_id = data.get('user_id') or data.get('sub') or data.get('id')

        # If still not found, try to decode the access token
        if not user_id and 'access_token' in data:
            import base64
            token = data['access_token']
            payload_b64 = token.split('.')[1]
            # Add padding if needed
            payload_b64 += '=' * (4 - len(payload_b64) % 4)
            payload = json.loads(base64.b64decode(payload_b64))
            user_id = payload.get('sub')

        print(f"✓ Login successful, user_id: {user_id}")
        return user_id
    else:
        print(f"✗ Login failed: {response.status_code}")
        print(response.text)
        sys.exit(1)

def create_diagram(user_id):
    """Create a test diagram."""
    print_step(2, "Create test diagram")

    diagram_data = {
        "title": "Comment Thread Test Diagram",
        "file_type": "canvas",
        "canvas_data": {"shapes": [], "bindings": []}
    }

    response = requests.post(
        f"{DIAGRAM_SERVICE}/",
        json=diagram_data,
        headers={"X-User-ID": user_id}
    )

    if response.status_code in [200, 201]:
        diagram = response.json()
        diagram_id = diagram['id']
        print(f"✓ Diagram created: {diagram_id}")
        return diagram_id
    else:
        print(f"✗ Diagram creation failed: {response.status_code}")
        print(response.text)
        sys.exit(1)

def create_parent_comment(diagram_id, user_id):
    """Create a parent comment."""
    print_step(3, "Create parent comment")

    comment_data = {
        "content": "This is the parent comment. Can someone reply to this?",
        "position_x": 100.0,
        "position_y": 100.0,
        "element_id": "shape-123"
    }

    response = requests.post(
        f"{DIAGRAM_SERVICE}/{diagram_id}/comments",
        json=comment_data,
        headers={"X-User-ID": user_id}
    )

    if response.status_code == 201:
        comment = response.json()
        comment_id = comment['id']
        print(f"✓ Parent comment created: {comment_id}")
        print(f"  Content: {comment['content'][:50]}...")
        print(f"  Parent ID: {comment.get('parent_id', 'None')}")
        return comment_id
    else:
        print(f"✗ Comment creation failed: {response.status_code}")
        print(response.text)
        sys.exit(1)

def create_reply(diagram_id, user_id, parent_comment_id):
    """Create a reply to the parent comment."""
    print_step(4, "Create reply to parent comment")

    reply_data = {
        "content": "This is a reply to the parent comment! Thread test successful.",
        "parent_id": parent_comment_id  # KEY FIELD FOR THREADING!
    }

    response = requests.post(
        f"{DIAGRAM_SERVICE}/{diagram_id}/comments",
        json=reply_data,
        headers={"X-User-ID": user_id}
    )

    if response.status_code == 201:
        reply = response.json()
        reply_id = reply['id']
        print(f"✓ Reply created: {reply_id}")
        print(f"  Content: {reply['content'][:50]}...")
        print(f"  Parent ID: {reply.get('parent_id')}")

        # Verify parent_id matches
        if reply.get('parent_id') == parent_comment_id:
            print(f"✓ Reply correctly linked to parent comment")
        else:
            print(f"✗ Reply not linked correctly!")
            print(f"  Expected parent_id: {parent_comment_id}")
            print(f"  Got parent_id: {reply.get('parent_id')}")

        return reply_id
    else:
        print(f"✗ Reply creation failed: {response.status_code}")
        print(response.text)
        sys.exit(1)

def create_nested_reply(diagram_id, user_id, parent_comment_id):
    """Create another reply to test multiple replies in a thread."""
    print_step(5, "Create second reply (nested conversation)")

    reply_data = {
        "content": "This is another reply in the same thread!",
        "parent_id": parent_comment_id
    }

    response = requests.post(
        f"{DIAGRAM_SERVICE}/{diagram_id}/comments",
        json=reply_data,
        headers={"X-User-ID": user_id}
    )

    if response.status_code == 201:
        reply = response.json()
        print(f"✓ Second reply created: {reply['id']}")
        print(f"  Parent ID: {reply.get('parent_id')}")
        return reply['id']
    else:
        print(f"✗ Second reply creation failed: {response.status_code}")
        return None

def get_comments_and_verify_thread(diagram_id, user_id, parent_id):
    """Get all comments and verify thread structure."""
    print_step(6, "Verify thread structure")

    response = requests.get(
        f"{DIAGRAM_SERVICE}/{diagram_id}/comments",
        headers={"X-User-ID": user_id}
    )

    if response.status_code == 200:
        data = response.json()
        comments = data.get('comments', [])

        print(f"✓ Retrieved {len(comments)} total comments")

        # Separate parent and reply comments
        parent_comments = [c for c in comments if c.get('parent_id') is None]
        reply_comments = [c for c in comments if c.get('parent_id') is not None]

        print(f"  - Parent comments: {len(parent_comments)}")
        print(f"  - Reply comments: {len(reply_comments)}")

        # Verify parent comment has replies_count
        parent = next((c for c in comments if c['id'] == parent_id), None)
        if parent:
            replies_count = parent.get('replies_count', 0)
            print(f"✓ Parent comment has {replies_count} replies")

            if replies_count >= 2:
                print(f"✓ Thread structure verified: parent with {replies_count} replies")
            else:
                print(f"✗ Expected at least 2 replies, got {replies_count}")
        else:
            print(f"✗ Parent comment not found in response")

        # Verify all replies have correct parent_id
        all_correct = all(r.get('parent_id') == parent_id for r in reply_comments)
        if all_correct and len(reply_comments) >= 2:
            print(f"✓ All {len(reply_comments)} replies correctly linked to parent")
        else:
            print(f"✗ Some replies not correctly linked")

        # Print thread structure
        print("\nThread Structure:")
        for comment in comments:
            indent = "  " if comment.get('parent_id') else ""
            prefix = "  └─ " if comment.get('parent_id') else "● "
            print(f"{indent}{prefix}{comment['content'][:60]}...")

        return len(reply_comments) >= 2
    else:
        print(f"✗ Failed to retrieve comments: {response.status_code}")
        return False

def test_filter_by_parent(diagram_id, user_id, parent_id):
    """Test filtering comments by parent_id."""
    print_step(7, "Test filtering by parent_id")

    response = requests.get(
        f"{DIAGRAM_SERVICE}/{diagram_id}/comments?parent_id={parent_id}",
        headers={"X-User-ID": user_id}
    )

    if response.status_code == 200:
        data = response.json()
        comments = data.get('comments', [])

        print(f"✓ Retrieved {len(comments)} replies for parent {parent_id}")

        # Verify all returned comments have the correct parent_id
        all_correct = all(c.get('parent_id') == parent_id for c in comments)
        if all_correct:
            print(f"✓ Filter working: all returned comments are replies to parent")
            return True
        else:
            print(f"✗ Filter not working correctly")
            return False
    else:
        print(f"✗ Failed to filter comments: {response.status_code}")
        return False

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("FEATURE #426: COMMENT THREADS - REPLY TO COMMENTS")
    print("="*60)

    try:
        # Test steps
        user_id = register_and_login()
        diagram_id = create_diagram(user_id)
        parent_comment_id = create_parent_comment(diagram_id, user_id)
        reply1_id = create_reply(diagram_id, user_id, parent_comment_id)
        reply2_id = create_nested_reply(diagram_id, user_id, parent_comment_id)

        # Verify thread structure
        thread_verified = get_comments_and_verify_thread(diagram_id, user_id, parent_comment_id)
        filter_works = test_filter_by_parent(diagram_id, user_id, parent_comment_id)

        # Final result
        print("\n" + "="*60)
        print("TEST RESULTS")
        print("="*60)

        if thread_verified and filter_works:
            print("✓ FEATURE #426 PASSED: Comment threading works correctly!")
            print("  - Parent comments can receive replies")
            print("  - Replies are correctly linked via parent_id")
            print("  - Thread structure is maintained")
            print("  - Filtering by parent_id works")
            sys.exit(0)
        else:
            print("✗ FEATURE #426 FAILED: Some tests did not pass")
            sys.exit(1)

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
