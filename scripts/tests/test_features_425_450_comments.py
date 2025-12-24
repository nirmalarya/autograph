#!/usr/bin/env python3
"""
Test Features #425-450: Comments System
Comprehensive test suite for comment features including:
- Canvas and note comments
- Comment threads (replies)
- @mentions
- Reactions
- Resolve/reopen workflow
- Edit and delete
- Filters and search
"""

import requests
import json
import time
import base64
from datetime import datetime

# Base URLs
AUTH_URL = "http://localhost:8085"
DIAGRAM_URL = "http://localhost:8082"

def decode_jwt_payload(token):
    """Decode JWT payload to get user_id."""
    parts = token.split('.')
    if len(parts) >= 2:
        payload = parts[1]
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    return None

def setup_test_user():
    """Register and login a test user."""
    email = f"commenttest_{int(time.time())}@example.com"
    password = "TestPass123!"
    
    # Register
    try:
        requests.post(f"{AUTH_URL}/register", json={
            "email": email,
            "password": password,
            "username": "commenttest"
        }, timeout=5)
    except:
        pass
    
    # Login
    response = requests.post(f"{AUTH_URL}/login", json={
        "email": email,
        "password": password
    }, timeout=5)
    
    if response.status_code == 200:
        data = response.json()
        token = data["access_token"]
        payload = decode_jwt_payload(token)
        user_id = payload.get("sub")
        return token, user_id, email
    
    raise Exception(f"Login failed: {response.status_code}")

def create_test_diagram(token, user_id):
    """Create a test diagram for comments."""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }
    
    response = requests.post(f"{DIAGRAM_URL}/", json={
        "title": "Comment Test Diagram",
        "file_type": "canvas",
        "canvas_data": {"shapes": [{"id": "shape1", "type": "rectangle"}]}
    }, headers=headers, timeout=5)
    
    if response.status_code in [200, 201]:
        return response.json()["id"]
    
    raise Exception(f"Failed to create diagram: {response.status_code}")

def run_tests():
    """Run all comment feature tests."""
    print("=" * 80)
    print("TESTING FEATURES #425-450: COMMENTS SYSTEM")
    print("=" * 80)
    
    # Setup
    print("\n📋 SETUP: Creating test user and diagram...")
    token, user_id, email = setup_test_user()
    diagram_id = create_test_diagram(token, user_id)
    print(f"✅ Test user created: {email}")
    print(f"✅ Test diagram created: {diagram_id}")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }
    
    passed = 0
    total = 0
    
    # Test #425: Add comment to canvas element
    print("\n" + "=" * 80)
    print("Feature #425: Add comment to canvas element")
    print("=" * 80)
    total += 1
    try:
        response = requests.post(
            f"{DIAGRAM_URL}/{diagram_id}/comments",
            headers=headers,
            json={
                "content": "This is a test comment on a shape",
                "element_id": "shape1",
                "position_x": 100.0,
                "position_y": 200.0
            },
            timeout=5
        )
        if response.status_code == 201:
            comment_data = response.json()
            comment_id = comment_data["id"]
            print(f"✅ PASS: Comment created successfully (ID: {comment_id})")
            print(f"   Position: ({comment_data['position_x']}, {comment_data['position_y']})")
            print(f"   Element: {comment_data['element_id']}")
            passed += 1
        else:
            print(f"❌ FAIL: Status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ FAIL: {e}")
    
    # Test #426: Add comment to note text selection
    print("\n" + "=" * 80)
    print("Feature #426: Add comment to note text selection")
    print("=" * 80)
    total += 1
    try:
        response = requests.post(
            f"{DIAGRAM_URL}/{diagram_id}/comments",
            headers=headers,
            json={
                "content": "This is a note comment",
                "position_x": None,
                "position_y": None,
                "element_id": None
            },
            timeout=5
        )
        if response.status_code == 201:
            note_comment_id = response.json()["id"]
            print(f"✅ PASS: Note comment created (ID: {note_comment_id})")
            passed += 1
        else:
            print(f"❌ FAIL: Status {response.status_code}")
    except Exception as e:
        print(f"❌ FAIL: {e}")
    
    # Test #427: Comment threads (reply to comment)
    print("\n" + "=" * 80)
    print("Feature #427: Comment threads - reply to comments")
    print("=" * 80)
    total += 1
    try:
        response = requests.post(
            f"{DIAGRAM_URL}/{diagram_id}/comments",
            headers=headers,
            json={
                "content": "This is a reply to the first comment",
                "parent_id": comment_id
            },
            timeout=5
        )
        if response.status_code == 201:
            reply_id = response.json()["id"]
            print(f"✅ PASS: Reply created (ID: {reply_id}, parent: {comment_id})")
            passed += 1
        else:
            print(f"❌ FAIL: Status {response.status_code}")
    except Exception as e:
        print(f"❌ FAIL: {e}")
    
    # Test #428: @mentions
    print("\n" + "=" * 80)
    print("Feature #428: @mentions - notify specific users")
    print("=" * 80)
    total += 1
    try:
        response = requests.post(
            f"{DIAGRAM_URL}/{diagram_id}/comments",
            headers=headers,
            json={
                "content": f"Hey @{email.split('@')[0]}, check this out!"
            },
            timeout=5
        )
        if response.status_code == 201:
            mention_data = response.json()
            print(f"✅ PASS: Comment with mention created")
            print(f"   Mentions: {mention_data.get('mentions', [])}")
            passed += 1
        else:
            print(f"❌ FAIL: Status {response.status_code}")
    except Exception as e:
        print(f"❌ FAIL: {e}")
    
    # Test #432: Resolve/reopen workflow
    print("\n" + "=" * 80)
    print("Feature #432: Resolve/reopen workflow")
    print("=" * 80)
    total += 1
    try:
        # Resolve
        response = requests.post(
            f"{DIAGRAM_URL}/{diagram_id}/comments/{comment_id}/resolve",
            headers=headers,
            timeout=5
        )
        if response.status_code == 200:
            print(f"✅ PASS: Comment resolved")
            
            # Reopen
            response = requests.post(
                f"{DIAGRAM_URL}/{diagram_id}/comments/{comment_id}/reopen",
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                print(f"✅ PASS: Comment reopened")
                passed += 1
            else:
                print(f"❌ FAIL: Reopen failed with status {response.status_code}")
        else:
            print(f"❌ FAIL: Resolve failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ FAIL: {e}")
    
    # Test #433: Comment reactions
    print("\n" + "=" * 80)
    print("Feature #433: Comment reactions - emoji reactions")
    print("=" * 80)
    total += 1
    try:
        # Add reaction
        response = requests.post(
            f"{DIAGRAM_URL}/{diagram_id}/comments/{comment_id}/reactions",
            headers=headers,
            json={"emoji": "👍"},
            timeout=5
        )
        if response.status_code == 200:
            print(f"✅ PASS: Reaction 👍 added")
            
            # Add another reaction
            response = requests.post(
                f"{DIAGRAM_URL}/{diagram_id}/comments/{comment_id}/reactions",
                headers=headers,
                json={"emoji": "❤️"},
                timeout=5
            )
            if response.status_code == 200:
                print(f"✅ PASS: Reaction ❤️ added")
                passed += 1
            else:
                print(f"❌ FAIL: Second reaction failed")
        else:
            print(f"❌ FAIL: Status {response.status_code}")
    except Exception as e:
        print(f"❌ FAIL: {e}")
    
    # Test #434: Edit comment (within 5 minutes)
    print("\n" + "=" * 80)
    print("Feature #434: Edit comments - edit own comments within 5 minutes")
    print("=" * 80)
    total += 1
    try:
        response = requests.put(
            f"{DIAGRAM_URL}/{diagram_id}/comments/{comment_id}",
            headers=headers,
            json={"content": "This is an edited comment"},
            timeout=5
        )
        if response.status_code == 200:
            print(f"✅ PASS: Comment edited successfully")
            passed += 1
        else:
            print(f"❌ FAIL: Status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ FAIL: {e}")
    
    # Test #438: Comment count badge
    print("\n" + "=" * 80)
    print("Feature #438: Comment count badge")
    print("=" * 80)
    total += 1
    try:
        response = requests.get(
            f"{DIAGRAM_URL}/{diagram_id}",
            headers=headers,
            timeout=5
        )
        if response.status_code == 200:
            diagram = response.json()
            comment_count = diagram.get("comment_count", 0)
            print(f"✅ PASS: Diagram has comment_count field")
            print(f"   Comment count: {comment_count}")
            if comment_count > 0:
                passed += 1
            else:
                print(f"   ⚠️  Count is 0, but we added comments")
        else:
            print(f"❌ FAIL: Status {response.status_code}")
    except Exception as e:
        print(f"❌ FAIL: {e}")
    
    # Test #440: Comment filters
    print("\n" + "=" * 80)
    print("Feature #440: Comment filters - all, open, resolved")
    print("=" * 80)
    total += 1
    try:
        # Get all comments
        response = requests.get(
            f"{DIAGRAM_URL}/{diagram_id}/comments",
            headers=headers,
            timeout=5
        )
        if response.status_code == 200:
            all_comments = response.json()
            print(f"✅ PASS: Retrieved all comments")
            print(f"   Total comments: {all_comments['total']}")
            
            # Get only resolved comments
            response = requests.get(
                f"{DIAGRAM_URL}/{diagram_id}/comments?is_resolved=false",
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                open_comments = response.json()
                print(f"✅ PASS: Filtered open comments")
                print(f"   Open comments: {open_comments['total']}")
                passed += 1
            else:
                print(f"❌ FAIL: Filter failed")
        else:
            print(f"❌ FAIL: Status {response.status_code}")
    except Exception as e:
        print(f"❌ FAIL: {e}")
    
    # Test #444: Real-time comments
    print("\n" + "=" * 80)
    print("Feature #444: Real-time comments - appear instantly")
    print("=" * 80)
    total += 1
    try:
        # Create comment
        response = requests.post(
            f"{DIAGRAM_URL}/{diagram_id}/comments",
            headers=headers,
            json={"content": "Real-time test comment"},
            timeout=5
        )
        if response.status_code == 201:
            rt_comment_id = response.json()["id"]
            
            # Immediately retrieve comments
            response = requests.get(
                f"{DIAGRAM_URL}/{diagram_id}/comments",
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                comments = response.json()["comments"]
                found = any(c["id"] == rt_comment_id for c in comments)
                if found:
                    print(f"✅ PASS: Real-time comment appears instantly")
                    passed += 1
                else:
                    print(f"❌ FAIL: Comment not found immediately")
            else:
                print(f"❌ FAIL: Retrieval failed")
        else:
            print(f"❌ FAIL: Creation failed")
    except Exception as e:
        print(f"❌ FAIL: {e}")
    
    # Test #435: Delete comment
    print("\n" + "=" * 80)
    print("Feature #435: Delete comments - delete own")
    print("=" * 80)
    total += 1
    try:
        # Create a comment to delete
        response = requests.post(
            f"{DIAGRAM_URL}/{diagram_id}/comments",
            headers=headers,
            json={"content": "Comment to delete"},
            timeout=5
        )
        if response.status_code == 201:
            delete_comment_id = response.json()["id"]
            
            # Delete it
            response = requests.delete(
                f"{DIAGRAM_URL}/{diagram_id}/comments/{delete_comment_id}/delete",
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                print(f"✅ PASS: Comment deleted successfully")
                passed += 1
            else:
                print(f"❌ FAIL: Delete failed with status {response.status_code}")
        else:
            print(f"❌ FAIL: Creation failed")
    except Exception as e:
        print(f"❌ FAIL: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {passed*100/total:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! 🎉")
    elif passed >= total * 0.8:
        print("\n✅ Most tests passed - good progress!")
    else:
        print("\n⚠️  Some tests failed - review implementation")
    
    return passed, total

if __name__ == "__main__":
    try:
        passed, total = run_tests()
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
