#!/usr/bin/env python3
"""
Feature #159: Diagram comment count badge
Validates that diagrams correctly track comment counts.

Steps:
1. Create diagram
2. Verify comment_count=0
3. Add comment
4. Verify comment_count=1
5. Add 5 more comments
6. Verify comment_count=6
7. View dashboard
8. Verify comment count badge displayed on diagram card
9. Delete 2 comments
10. Verify comment_count=4
"""

import requests
import sys
import time

# Configuration
API_BASE_URL = "http://localhost:8080"  # API Gateway
DIAGRAM_SERVICE_URL = "http://localhost:8082"  # Direct to diagram service
AUTH_SERVICE_URL = "http://localhost:8085"  # Direct to auth service

def print_step(step_num, description):
    """Print a test step."""
    print(f"\n{'='*60}")
    print(f"Step {step_num}: {description}")
    print('='*60)

def register_and_login():
    """Register a new user and get JWT token."""
    print_step(0, "Setup - Register and login user")

    # Create unique user
    timestamp = int(time.time())
    email = f"user_feature159_{timestamp}@test.com"
    password = "SecurePass123!@#"
    username = f"user159_{timestamp}"

    # Register
    register_data = {
        "email": email,
        "password": password,
        "username": username
    }

    print(f"Registering user: {email}")
    response = requests.post(f"{AUTH_SERVICE_URL}/register", json=register_data)

    if response.status_code != 201:
        print(f"❌ Registration failed: {response.status_code}")
        print(response.text)
        return None, None

    print("✅ User registered")

    # Auto-verify email (for testing)
    user_data = response.json()
    print(f"Registration response: {user_data}")
    user_id = user_data.get('user_id') or user_data.get('id')

    print(f"User ID from registration: {user_id}")

    # Update user as verified in database
    import psycopg2
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="autograph",
        user="autograph",
        password="autograph_dev_password"
    )
    cur = conn.cursor()

    # First check current status
    cur.execute("SELECT is_verified FROM users WHERE id = %s", (user_id,))
    result = cur.fetchone()
    print(f"Before update - is_verified: {result[0] if result else 'NOT FOUND'}")

    # Update verification status
    cur.execute("UPDATE users SET is_verified = true WHERE id = %s", (user_id,))
    rows_updated = cur.rowcount
    conn.commit()

    # Verify the update
    cur.execute("SELECT is_verified FROM users WHERE id = %s", (user_id,))
    result = cur.fetchone()
    print(f"After update - is_verified: {result[0] if result else 'NOT FOUND'}")
    print(f"Rows updated: {rows_updated}")

    cur.close()
    conn.close()
    print("✅ Email auto-verified")

    # Login
    login_data = {
        "email": email,
        "password": password
    }

    print("Logging in...")
    response = requests.post(f"{AUTH_SERVICE_URL}/login", json=login_data)

    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        return None, None

    token_data = response.json()
    access_token = token_data.get('access_token')

    if not access_token:
        print("❌ No access token received")
        return None, None

    print(f"✅ Logged in successfully")
    print(f"User ID: {user_id}")

    return access_token, user_id

def create_diagram(token, user_id, title="Comment Count Test Diagram"):
    """Create a test diagram."""
    print(f"Creating diagram: {title}")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }

    diagram_data = {
        "title": title,
        "file_type": "canvas",
        "canvas_data": {
            "elements": [],
            "version": "1.0"
        }
    }

    response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/",
        headers=headers,
        json=diagram_data
    )

    if response.status_code not in [200, 201]:
        print(f"❌ Failed to create diagram: {response.status_code}")
        print(response.text)
        return None

    diagram = response.json()
    diagram_id = diagram.get('id')
    print(f"✅ Diagram created: {diagram_id}")

    return diagram_id

def get_diagram(token, user_id, diagram_id):
    """Get diagram details."""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }

    response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}",
        headers=headers
    )

    if response.status_code != 200:
        print(f"❌ Failed to get diagram: {response.status_code}")
        print(response.text)
        return None

    return response.json()

def add_comment(token, user_id, diagram_id, content):
    """Add a comment to the diagram."""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }

    comment_data = {
        "content": content,
        "is_private": False
    }

    response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/comments",
        headers=headers,
        json=comment_data
    )

    if response.status_code != 201:
        print(f"❌ Failed to add comment: {response.status_code}")
        print(response.text)
        return None

    comment = response.json()
    comment_id = comment.get('id')
    print(f"✅ Comment added: {comment_id}")

    return comment_id

def delete_comment(token, user_id, diagram_id, comment_id):
    """Delete a comment."""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }

    response = requests.delete(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/comments/{comment_id}/delete",
        headers=headers
    )

    if response.status_code != 200:
        print(f"❌ Failed to delete comment: {response.status_code}")
        print(response.text)
        return False

    print(f"✅ Comment deleted: {comment_id}")
    return True

def list_diagrams(token, user_id):
    """List all diagrams."""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }

    response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/",
        headers=headers
    )

    if response.status_code != 200:
        print(f"❌ Failed to list diagrams: {response.status_code}")
        print(response.text)
        return []

    result = response.json()
    print(f"List diagrams response: {result}")
    # Try different possible keys for the items
    diagrams = result.get('items', result.get('diagrams', result if isinstance(result, list) else []))
    return diagrams

def validate_comment_count(diagram, expected_count, step_num):
    """Validate that diagram has expected comment count."""
    actual_count = diagram.get('comment_count', 0)

    if actual_count == expected_count:
        print(f"✅ Step {step_num} PASSED: comment_count = {actual_count}")
        return True
    else:
        print(f"❌ Step {step_num} FAILED: Expected comment_count={expected_count}, got {actual_count}")
        return False

def main():
    """Run validation test."""
    print("Starting Feature #159 validation: Diagram comment count badge")
    print("="*60)

    # Setup - Register and login
    token, user_id = register_and_login()
    if not token:
        print("❌ VALIDATION FAILED: Setup failed")
        return False

    # Step 1: Create diagram
    print_step(1, "Create diagram")
    diagram_id = create_diagram(token, user_id)
    if not diagram_id:
        print("❌ VALIDATION FAILED: Could not create diagram")
        return False

    # Step 2: Verify comment_count=0
    print_step(2, "Verify comment_count=0")
    diagram = get_diagram(token, user_id, diagram_id)
    if not diagram:
        print("❌ VALIDATION FAILED: Could not get diagram")
        return False

    if not validate_comment_count(diagram, 0, 2):
        return False

    # Step 3: Add comment
    print_step(3, "Add comment")
    comment1_id = add_comment(token, user_id, diagram_id, "This is the first comment")
    if not comment1_id:
        print("❌ VALIDATION FAILED: Could not add comment")
        return False

    # Step 4: Verify comment_count=1
    print_step(4, "Verify comment_count=1")
    diagram = get_diagram(token, user_id, diagram_id)
    if not validate_comment_count(diagram, 1, 4):
        return False

    # Step 5: Add 5 more comments
    print_step(5, "Add 5 more comments")
    comment_ids = [comment1_id]
    for i in range(2, 7):
        comment_id = add_comment(token, user_id, diagram_id, f"This is comment #{i}")
        if not comment_id:
            print(f"❌ VALIDATION FAILED: Could not add comment #{i}")
            return False
        comment_ids.append(comment_id)

    # Step 6: Verify comment_count=6
    print_step(6, "Verify comment_count=6")
    diagram = get_diagram(token, user_id, diagram_id)
    if not validate_comment_count(diagram, 6, 6):
        return False

    # Step 7: View dashboard (list diagrams)
    print_step(7, "View dashboard")
    diagrams = list_diagrams(token, user_id)
    print(f"✅ Dashboard loaded with {len(diagrams)} diagrams")

    # Step 8: Verify comment count badge displayed on diagram card
    print_step(8, "Verify comment count badge on diagram card")
    found_diagram = None
    for d in diagrams:
        if d.get('id') == diagram_id:
            found_diagram = d
            break

    if not found_diagram:
        print(f"❌ Step 8 FAILED: Diagram {diagram_id} not found in dashboard")
        return False

    if not validate_comment_count(found_diagram, 6, 8):
        return False

    print("✅ Comment count badge correctly displayed in dashboard")

    # Step 9: Delete 2 comments
    print_step(9, "Delete 2 comments")
    if not delete_comment(token, user_id, diagram_id, comment_ids[0]):
        return False
    if not delete_comment(token, user_id, diagram_id, comment_ids[1]):
        return False

    # Step 10: Verify comment_count=4
    print_step(10, "Verify comment_count=4")
    diagram = get_diagram(token, user_id, diagram_id)
    if not validate_comment_count(diagram, 4, 10):
        return False

    print("\n" + "="*60)
    print("✅ ALL VALIDATION STEPS PASSED")
    print("="*60)
    print("\nFeature #159 - Diagram comment count badge: WORKING CORRECTLY")

    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ VALIDATION FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
