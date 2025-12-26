#!/usr/bin/env python3
"""
Feature #447: Comment History - View Edit History
Tests viewing the complete edit history of comments
"""

import httpx
import hashlib
import time
import sys

BASE_URL = "http://localhost:8080"
SERVICE_URL = "http://localhost:8082"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def test_comment_history():
    """Test comment edit history feature."""
    print("\n" + "="*60)
    print("FEATURE #447: COMMENT HISTORY - VIEW EDIT HISTORY")
    print("="*60)

    # Step 1: Login with pre-created user
    print("\n1. Logging in with test user...")
    email = "historyuser447@test.com"
    password = "Test123!@#"

    # Login
    login_data = {"email": email, "password": password}
    try:
        response = httpx.post(f"{BASE_URL}/api/auth/login", json=login_data, timeout=10.0)
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False

        token_data = response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            print("❌ No access token received")
            return False

        # Decode JWT to get user_id
        import jwt as jwt_lib
        decoded = jwt_lib.decode(access_token, options={"verify_signature": False})
        user_id = decoded.get("sub")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-User-ID": user_id
        }
        print(f"✅ User logged in successfully (user_id: {user_id})")
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False

    # Step 2: Create a diagram
    print("\n2. Creating test diagram...")
    diagram_data = {
        "title": "History Test Diagram",
        "diagram_type": "note",
        "content": {"elements": []}
    }

    try:
        response = httpx.post(
            f"{BASE_URL}/api/diagrams/",
            json=diagram_data,
            headers=headers,
            timeout=10.0
        )
        if response.status_code not in [200, 201]:
            print(f"❌ Diagram creation failed: {response.status_code}")
            return False

        diagram_id = response.json().get("id")
        print(f"✅ Diagram created: {diagram_id}")
    except Exception as e:
        print(f"❌ Diagram creation error: {e}")
        return False

    # Step 3: Create a comment
    print("\n3. Creating initial comment...")
    comment_data = {
        "content": "Initial comment content - version 1",
        "position_x": 100.0,
        "position_y": 200.0
    }

    try:
        response = httpx.post(
            f"{BASE_URL}/api/diagrams/{diagram_id}/comments",
            json=comment_data,
            headers=headers,
            timeout=10.0
        )
        if response.status_code not in [200, 201]:
            print(f"❌ Comment creation failed: {response.status_code} - {response.text}")
            return False

        comment_id = response.json().get("id")
        print(f"✅ Comment created: {comment_id}")
    except Exception as e:
        print(f"❌ Comment creation error: {e}")
        return False

    # Step 4: Get initial history (should be empty)
    print("\n4. Checking initial history (should have no edits)...")
    try:
        response = httpx.get(
            f"{BASE_URL}/api/diagrams/{diagram_id}/comments/{comment_id}/history",
            headers=headers,
            timeout=10.0
        )
        if response.status_code != 200:
            print(f"❌ History retrieval failed: {response.status_code} - {response.text}")
            return False

        history_data = response.json()
        print(f"   Current version: {history_data['current_version']['content']}")
        print(f"   History count: {len(history_data['history'])}")
        print(f"   Total versions: {history_data['total_versions']}")

        if len(history_data['history']) != 0:
            print(f"❌ Expected 0 history items, got {len(history_data['history'])}")
            return False

        if history_data['total_versions'] != 1:
            print(f"❌ Expected 1 total version, got {history_data['total_versions']}")
            return False

        print("✅ Initial history is empty (as expected)")
    except Exception as e:
        print(f"❌ History check error: {e}")
        return False

    # Step 5: Edit comment - first edit
    print("\n5. Editing comment (first edit)...")
    update_data = {
        "content": "Updated comment content - version 2"
    }

    try:
        response = httpx.put(
            f"{BASE_URL}/api/diagrams/{diagram_id}/comments/{comment_id}",
            json=update_data,
            headers=headers,
            timeout=10.0
        )
        if response.status_code != 200:
            print(f"❌ Comment update failed: {response.status_code} - {response.text}")
            return False

        print(f"✅ Comment updated (version 2)")
    except Exception as e:
        print(f"❌ Comment update error: {e}")
        return False

    # Wait a moment to ensure timestamp difference
    time.sleep(1)

    # Step 6: Edit comment - second edit
    print("\n6. Editing comment (second edit)...")
    update_data = {
        "content": "Updated comment content - version 3"
    }

    try:
        response = httpx.put(
            f"{BASE_URL}/api/diagrams/{diagram_id}/comments/{comment_id}",
            json=update_data,
            headers=headers,
            timeout=10.0
        )
        if response.status_code != 200:
            print(f"❌ Comment update failed: {response.status_code} - {response.text}")
            return False

        print(f"✅ Comment updated (version 3)")
    except Exception as e:
        print(f"❌ Comment update error: {e}")
        return False

    # Wait a moment
    time.sleep(1)

    # Step 7: Edit comment - third edit
    print("\n7. Editing comment (third edit)...")
    update_data = {
        "content": "Final comment content - version 4"
    }

    try:
        response = httpx.put(
            f"{BASE_URL}/api/diagrams/{diagram_id}/comments/{comment_id}",
            json=update_data,
            headers=headers,
            timeout=10.0
        )
        if response.status_code != 200:
            print(f"❌ Comment update failed: {response.status_code} - {response.text}")
            return False

        print(f"✅ Comment updated (version 4)")
    except Exception as e:
        print(f"❌ Comment update error: {e}")
        return False

    # Step 8: Get complete history
    print("\n8. Retrieving complete edit history...")
    try:
        response = httpx.get(
            f"{BASE_URL}/api/diagrams/{diagram_id}/comments/{comment_id}/history",
            headers=headers,
            timeout=10.0
        )
        if response.status_code != 200:
            print(f"❌ History retrieval failed: {response.status_code} - {response.text}")
            return False

        history_data = response.json()

        print(f"\n   Comment ID: {history_data['comment_id']}")
        print(f"   Total Versions: {history_data['total_versions']}")

        # Verify current version
        current = history_data['current_version']
        print(f"\n   CURRENT VERSION:")
        print(f"   - Content: {current['content']}")
        print(f"   - Created by: {current['created_by'].get('full_name', current['created_by']['email'])}")
        print(f"   - Created at: {current['created_at']}")
        print(f"   - Updated at: {current['updated_at']}")

        if current['content'] != "Final comment content - version 4":
            print(f"❌ Current version content mismatch")
            return False

        # Verify history
        history = history_data['history']
        print(f"\n   EDIT HISTORY ({len(history)} edits):")

        if len(history) != 3:
            print(f"❌ Expected 3 history items, got {len(history)}")
            return False

        # History should be in reverse chronological order (newest first)
        expected_contents = [
            "Updated comment content - version 3",  # Most recent edit
            "Updated comment content - version 2",
            "Initial comment content - version 1"   # Original content
        ]

        for i, item in enumerate(history):
            print(f"\n   Version {item['version_number']}:")
            print(f"   - Old Content: {item['old_content']}")
            print(f"   - Edited by: {item['edited_by'].get('full_name', item['edited_by']['email'])}")
            print(f"   - Edited at: {item['edited_at']}")

            if item['old_content'] != expected_contents[i]:
                print(f"❌ History content mismatch at index {i}")
                print(f"   Expected: {expected_contents[i]}")
                print(f"   Got: {item['old_content']}")
                return False

        # Verify chronological ordering
        if history[0]['version_number'] < history[-1]['version_number']:
            print(f"❌ History not in descending order")
            return False

        print(f"\n✅ History retrieved successfully")
        print(f"✅ All versions captured correctly")
        print(f"✅ Chronological ordering verified")

    except Exception as e:
        print(f"❌ History retrieval error: {e}")
        return False

    # Step 9: Verify total versions count
    print("\n9. Verifying version count...")
    if history_data['total_versions'] != 4:  # 1 current + 3 edits
        print(f"❌ Expected 4 total versions, got {history_data['total_versions']}")
        return False
    print(f"✅ Total version count correct: 4")

    print("\n" + "="*60)
    print("✅ FEATURE #447 TEST PASSED")
    print("="*60)
    return True

if __name__ == "__main__":
    try:
        success = test_comment_history()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
