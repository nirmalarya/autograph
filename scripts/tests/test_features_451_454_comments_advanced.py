#!/usr/bin/env python3
"""
Test Features #451-454: Advanced Comments Features
- Comment sorting (oldest, newest, most reactions)
- Comment permalinks
- Private comments
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
    email = f"commentadv_{int(time.time())}@example.com"
    password = "TestPass123!"
    
    # Register
    try:
        requests.post(f"{AUTH_URL}/register", json={
            "email": email,
            "password": password,
            "username": "commentadvtest"
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
        "title": "Comment Advanced Test Diagram",
        "file_type": "canvas",
        "canvas_data": {"shapes": [{"id": "shape1", "type": "rectangle"}]}
    }, headers=headers, timeout=5)
    
    if response.status_code in [200, 201]:
        return response.json()["id"]
    
    raise Exception(f"Failed to create diagram: {response.status_code}")

def run_tests():
    """Run all advanced comment feature tests."""
    print("=" * 80)
    print("TESTING FEATURES #451-454: ADVANCED COMMENTS")
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
    
    # Create test comments for sorting
    print("\n📝 SETUP: Creating test comments with reactions...")
    comment_ids = []
    
    # Comment 1 - oldest, no reactions
    time.sleep(0.1)
    response = requests.post(
        f"{DIAGRAM_URL}/{diagram_id}/comments",
        headers=headers,
        json={"content": "First comment - oldest"},
        timeout=5
    )
    if response.status_code == 201:
        comment_ids.append(response.json()["id"])
        print(f"✅ Created comment 1: {comment_ids[0]}")
    
    # Comment 2 - middle, 1 reaction
    time.sleep(0.1)
    response = requests.post(
        f"{DIAGRAM_URL}/{diagram_id}/comments",
        headers=headers,
        json={"content": "Second comment - middle"},
        timeout=5
    )
    if response.status_code == 201:
        c2_id = response.json()["id"]
        comment_ids.append(c2_id)
        print(f"✅ Created comment 2: {c2_id}")
        
        # Add 1 reaction
        requests.post(
            f"{DIAGRAM_URL}/{diagram_id}/comments/{c2_id}/reactions",
            headers=headers,
            json={"emoji": "👍"},
            timeout=5
        )
    
    # Comment 3 - newest, 3 reactions
    time.sleep(0.1)
    response = requests.post(
        f"{DIAGRAM_URL}/{diagram_id}/comments",
        headers=headers,
        json={"content": "Third comment - newest with most reactions"},
        timeout=5
    )
    if response.status_code == 201:
        c3_id = response.json()["id"]
        comment_ids.append(c3_id)
        print(f"✅ Created comment 3: {c3_id}")
        
        # Add 3 reactions
        for emoji in ["👍", "❤️", "😄"]:
            time.sleep(0.05)
            requests.post(
                f"{DIAGRAM_URL}/{diagram_id}/comments/{c3_id}/reactions",
                headers=headers,
                json={"emoji": emoji},
                timeout=5
            )
    
    print(f"✅ Created {len(comment_ids)} test comments with reactions")
    
    # Test #451: Comment sorting - oldest first
    print("\n" + "=" * 80)
    print("Feature #451: Comment sorting - oldest first")
    print("=" * 80)
    total += 1
    try:
        response = requests.get(
            f"{DIAGRAM_URL}/{diagram_id}/comments",
            headers=headers,
            params={"sort_by": "oldest"},
            timeout=5
        )
        if response.status_code == 200:
            comments = response.json()["comments"]
            if len(comments) >= 3:
                # Verify order: comment 1, 2, 3
                first_comment = comments[0]
                last_comment = comments[-1]
                
                if "First comment" in first_comment["content"]:
                    print(f"✅ PASS: Oldest comment first")
                    print(f"   First: {first_comment['content']}")
                    print(f"   Last: {last_comment['content']}")
                    passed += 1
                else:
                    print(f"❌ FAIL: Wrong order")
            else:
                print(f"❌ FAIL: Not enough comments")
        else:
            print(f"❌ FAIL: Status {response.status_code}")
    except Exception as e:
        print(f"❌ FAIL: {e}")
    
    # Test #452: Comment sorting - most reactions
    print("\n" + "=" * 80)
    print("Feature #452: Comment sorting - most reactions")
    print("=" * 80)
    total += 1
    try:
        response = requests.get(
            f"{DIAGRAM_URL}/{diagram_id}/comments",
            headers=headers,
            params={"sort_by": "most_reactions"},
            timeout=5
        )
        if response.status_code == 200:
            comments = response.json()["comments"]
            if len(comments) >= 3:
                first_comment = comments[0]
                total_reactions = first_comment.get("total_reactions", 0)
                
                if total_reactions == 3 and "Third comment" in first_comment["content"]:
                    print(f"✅ PASS: Most reactions comment first")
                    print(f"   Comment: {first_comment['content']}")
                    print(f"   Reactions: {total_reactions}")
                    passed += 1
                else:
                    print(f"❌ FAIL: Wrong sorting")
                    print(f"   First comment reactions: {total_reactions}")
            else:
                print(f"❌ FAIL: Not enough comments")
        else:
            print(f"❌ FAIL: Status {response.status_code}")
    except Exception as e:
        print(f"❌ FAIL: {e}")
    
    # Test #453: Comment permalinks
    print("\n" + "=" * 80)
    print("Feature #453: Comment permalinks")
    print("=" * 80)
    total += 1
    try:
        response = requests.get(
            f"{DIAGRAM_URL}/{diagram_id}/comments",
            headers=headers,
            timeout=5
        )
        if response.status_code == 200:
            comments = response.json()["comments"]
            if len(comments) > 0:
                first_comment = comments[0]
                permalink = first_comment.get("permalink")
                
                if permalink and f"comment-{first_comment['id']}" in permalink:
                    print(f"✅ PASS: Permalink generated")
                    print(f"   Permalink: {permalink}")
                    print(f"   Contains comment ID: ✓")
                    passed += 1
                else:
                    print(f"❌ FAIL: Invalid permalink")
                    print(f"   Permalink: {permalink}")
            else:
                print(f"❌ FAIL: No comments found")
        else:
            print(f"❌ FAIL: Status {response.status_code}")
    except Exception as e:
        print(f"❌ FAIL: {e}")
    
    # Test #454: Private comments
    print("\n" + "=" * 80)
    print("Feature #454: Private comments")
    print("=" * 80)
    total += 1
    try:
        # Create private comment
        response = requests.post(
            f"{DIAGRAM_URL}/{diagram_id}/comments",
            headers=headers,
            json={
                "content": "This is a private comment",
                "is_private": True
            },
            timeout=5
        )
        if response.status_code == 201:
            private_comment_data = response.json()
            is_private = private_comment_data.get("is_private", False)
            
            if is_private:
                print(f"✅ PASS: Private comment created")
                print(f"   Comment ID: {private_comment_data['id']}")
                print(f"   is_private: {is_private}")
                passed += 1
            else:
                print(f"❌ FAIL: is_private not set")
                print(f"   is_private: {is_private}")
        else:
            print(f"❌ FAIL: Status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ FAIL: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! 🎉")
    else:
        print("\n⚠️  Some tests failed - review implementation")

if __name__ == "__main__":
    run_tests()
