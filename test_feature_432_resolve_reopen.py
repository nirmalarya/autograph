#!/usr/bin/env python3
"""
Test Feature #432: Comments - Resolve/Reopen Workflow

Tests the ability to:
1. Add a comment
2. Resolve the comment
3. Verify comment is marked as resolved
4. Reopen the comment
5. Verify comment is active again
"""

import requests
import json
import sys
import subprocess
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8080"
AUTH_SERVICE_URL = "http://localhost:8085"

def print_step(step_num, description):
    """Print a test step."""
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {description}")
    print('='*60)

def register_and_login():
    """Register a test user and get auth token."""
    print_step(1, "Register and login test user")

    # Generate unique username
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    username = f"testuser_{timestamp}"
    email = f"{username}@test.com"
    password = "SecurePass123!"

    # Register
    register_data = {
        "username": username,
        "email": email,
        "password": password
    }

    print(f"Registering user: {username}")
    response = requests.post(f"{AUTH_SERVICE_URL}/register", json=register_data)

    if response.status_code != 201:
        print(f"❌ Registration failed: {response.status_code}")
        print(response.text)
        return None, None

    print(f"✅ User registered successfully")

    # Get user_id from registration response
    reg_data = response.json()
    user_id = reg_data.get("user_id") or reg_data.get("id")
    print(f"   User ID from registration: {user_id}")

    if not user_id:
        print(f"   Registration response: {reg_data}")
        print(f"❌ Could not get user_id from registration")
        return None, None

    # Verify email (bypass email verification for testing)
    print(f"Verifying email in database")
    try:
        result = subprocess.run([
            'docker', 'exec', 'autograph-postgres',
            'psql', '-U', 'autograph', '-d', 'autograph',
            '-c', f"UPDATE users SET is_verified = true WHERE email = '{email}'"
        ], capture_output=True, text=True, timeout=10)

        if result.returncode == 0 and "UPDATE 1" in result.stdout:
            print(f"✅ Email verified successfully")
        else:
            print(f"⚠️ Email verification may have failed: {result.stdout}")
    except Exception as e:
        print(f"⚠️ Could not verify email in DB: {e}")

    # Login
    login_data = {
        "email": email,
        "password": password
    }

    print(f"Logging in as {username}")
    response = requests.post(f"{AUTH_SERVICE_URL}/login", json=login_data)

    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        return None, None

    data = response.json()
    token = data.get("access_token")
    # Use the user_id from registration, not login response
    # (login might not return user_id)

    print(f"✅ Login successful")
    print(f"   User ID: {user_id}")
    print(f"   Token: {token[:20]}...")

    return token, user_id

def create_diagram(token, user_id):
    """Create a test diagram."""
    print_step(2, "Create test diagram")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id,
        "Content-Type": "application/json"
    }

    diagram_data = {
        "title": f"Test Diagram - Resolve/Reopen Comments {datetime.now().isoformat()}",
        "type": "canvas",
        "description": "Testing comment resolve/reopen workflow"
    }

    response = requests.post(
        f"{API_BASE_URL}/api/diagrams/",
        headers=headers,
        json=diagram_data
    )

    if response.status_code not in [200, 201]:
        print(f"❌ Failed to create diagram: {response.status_code}")
        print(response.text)
        return None

    diagram = response.json()
    diagram_id = diagram.get("id")

    print(f"✅ Diagram created successfully")
    print(f"   Diagram ID: {diagram_id}")

    return diagram_id

def create_comment(token, user_id, diagram_id):
    """Create a test comment on the diagram."""
    print_step(3, "Add comment to diagram")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id,
        "Content-Type": "application/json"
    }

    comment_data = {
        "content": "This is a test comment for resolve/reopen workflow"
    }

    response = requests.post(
        f"{API_BASE_URL}/api/diagrams/{diagram_id}/comments",
        headers=headers,
        json=comment_data
    )

    if response.status_code != 201:
        print(f"❌ Failed to create comment: {response.status_code}")
        print(response.text)
        return None

    comment = response.json()
    comment_id = comment.get("id")

    print(f"✅ Comment created successfully")
    print(f"   Comment ID: {comment_id}")
    print(f"   Content: {comment.get('content')}")
    print(f"   Is Resolved: {comment.get('is_resolved', False)}")

    # Verify comment is not resolved initially
    if comment.get('is_resolved', False):
        print(f"❌ Comment should not be resolved initially")
        return None

    return comment_id

def resolve_comment(token, user_id, diagram_id, comment_id):
    """Mark the comment as resolved."""
    print_step(4, "Resolve the comment")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id,
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{API_BASE_URL}/api/diagrams/{diagram_id}/comments/{comment_id}/resolve",
        headers=headers
    )

    if response.status_code != 200:
        print(f"❌ Failed to resolve comment: {response.status_code}")
        print(response.text)
        return False

    result = response.json()

    print(f"✅ Comment resolved successfully")
    print(f"   Comment ID: {result.get('comment_id')}")
    print(f"   Is Resolved: {result.get('is_resolved')}")
    print(f"   Resolved At: {result.get('resolved_at')}")

    # Verify comment is marked as resolved
    if not result.get('is_resolved'):
        print(f"❌ Comment should be marked as resolved")
        return False

    return True

def verify_comment_resolved(token, user_id, diagram_id, comment_id):
    """Verify the comment is marked as resolved."""
    print_step(5, "Verify comment is marked as resolved")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }

    response = requests.get(
        f"{API_BASE_URL}/api/diagrams/{diagram_id}/comments",
        headers=headers
    )

    if response.status_code != 200:
        print(f"❌ Failed to fetch comments: {response.status_code}")
        print(response.text)
        return False

    data = response.json()

    # Handle different response formats
    if isinstance(data, list):
        comments = data
    elif isinstance(data, dict):
        comments = data.get('comments', data.get('data', []))
    else:
        print(f"❌ Unexpected response format: {type(data)}")
        return False

    # Find our comment
    our_comment = None
    for comment in comments:
        if isinstance(comment, dict) and comment.get('id') == comment_id:
            our_comment = comment
            break

    if not our_comment:
        print(f"❌ Comment not found in comments list")
        return False

    print(f"✅ Comment found in comments list")
    print(f"   Is Resolved: {our_comment.get('is_resolved')}")
    print(f"   Resolved At: {our_comment.get('resolved_at')}")
    print(f"   Resolved By: {our_comment.get('resolved_by')}")

    # Verify it's marked as resolved
    if not our_comment.get('is_resolved'):
        print(f"❌ Comment should be marked as resolved")
        return False

    if not our_comment.get('resolved_at'):
        print(f"❌ Comment should have resolved_at timestamp")
        return False

    if not our_comment.get('resolved_by'):
        print(f"❌ Comment should have resolved_by user")
        return False

    print(f"✅ Comment is correctly marked as resolved")
    return True

def reopen_comment(token, user_id, diagram_id, comment_id):
    """Reopen the resolved comment."""
    print_step(6, "Reopen the comment")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id,
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{API_BASE_URL}/api/diagrams/{diagram_id}/comments/{comment_id}/reopen",
        headers=headers
    )

    if response.status_code != 200:
        print(f"❌ Failed to reopen comment: {response.status_code}")
        print(response.text)
        return False

    result = response.json()

    print(f"✅ Comment reopened successfully")
    print(f"   Comment ID: {result.get('comment_id')}")
    print(f"   Is Resolved: {result.get('is_resolved')}")

    # Verify comment is not resolved
    if result.get('is_resolved'):
        print(f"❌ Comment should not be marked as resolved after reopening")
        return False

    return True

def verify_comment_active(token, user_id, diagram_id, comment_id):
    """Verify the comment is active again (not resolved)."""
    print_step(7, "Verify comment is active again")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }

    response = requests.get(
        f"{API_BASE_URL}/api/diagrams/{diagram_id}/comments",
        headers=headers
    )

    if response.status_code != 200:
        print(f"❌ Failed to fetch comments: {response.status_code}")
        print(response.text)
        return False

    data = response.json()

    # Handle different response formats
    if isinstance(data, list):
        comments = data
    elif isinstance(data, dict):
        comments = data.get('comments', data.get('data', []))
    else:
        print(f"❌ Unexpected response format: {type(data)}")
        return False

    # Find our comment
    our_comment = None
    for comment in comments:
        if isinstance(comment, dict) and comment.get('id') == comment_id:
            our_comment = comment
            break

    if not our_comment:
        print(f"❌ Comment not found in comments list")
        return False

    print(f"✅ Comment found in comments list")
    print(f"   Is Resolved: {our_comment.get('is_resolved')}")
    print(f"   Resolved At: {our_comment.get('resolved_at')}")
    print(f"   Resolved By: {our_comment.get('resolved_by')}")

    # Verify it's not resolved
    if our_comment.get('is_resolved'):
        print(f"❌ Comment should not be marked as resolved")
        return False

    if our_comment.get('resolved_at'):
        print(f"❌ Comment should not have resolved_at timestamp")
        return False

    if our_comment.get('resolved_by'):
        print(f"❌ Comment should not have resolved_by user")
        return False

    print(f"✅ Comment is correctly marked as active (not resolved)")
    return True

def main():
    """Run the complete test."""
    print("\n" + "="*60)
    print("Feature #432: Comments - Resolve/Reopen Workflow")
    print("="*60)

    # Step 1: Register and login
    token, user_id = register_and_login()
    if not token or not user_id:
        print("\n❌ TEST FAILED: Could not authenticate")
        sys.exit(1)

    # Step 2: Create diagram
    diagram_id = create_diagram(token, user_id)
    if not diagram_id:
        print("\n❌ TEST FAILED: Could not create diagram")
        sys.exit(1)

    # Step 3: Add comment
    comment_id = create_comment(token, user_id, diagram_id)
    if not comment_id:
        print("\n❌ TEST FAILED: Could not create comment")
        sys.exit(1)

    # Step 4: Resolve comment
    if not resolve_comment(token, user_id, diagram_id, comment_id):
        print("\n❌ TEST FAILED: Could not resolve comment")
        sys.exit(1)

    # Step 5: Verify comment is resolved
    if not verify_comment_resolved(token, user_id, diagram_id, comment_id):
        print("\n❌ TEST FAILED: Comment not properly resolved")
        sys.exit(1)

    # Step 6: Reopen comment
    if not reopen_comment(token, user_id, diagram_id, comment_id):
        print("\n❌ TEST FAILED: Could not reopen comment")
        sys.exit(1)

    # Step 7: Verify comment is active
    if not verify_comment_active(token, user_id, diagram_id, comment_id):
        print("\n❌ TEST FAILED: Comment not properly reopened")
        sys.exit(1)

    # All tests passed
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED - Feature #432 is working correctly!")
    print("="*60)
    print("\nSummary:")
    print("✅ Comment created")
    print("✅ Comment resolved successfully")
    print("✅ Comment marked as resolved with timestamp")
    print("✅ Comment reopened successfully")
    print("✅ Comment marked as active again")
    print("\nFeature #432: PASS ✅")

    sys.exit(0)

if __name__ == "__main__":
    main()
