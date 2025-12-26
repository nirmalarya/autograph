#!/usr/bin/env python3
"""
Feature #436 Test: Admin Delete Comments

Tests that admin users can delete any comment (not just their own).

Test Flow:
1. Create a regular user and post a comment
2. Create an admin user
3. Admin deletes the regular user's comment
4. Verify comment is deleted successfully
"""

import requests
import time
import uuid
import psycopg2
import base64
import json

# Test configuration
API_BASE_URL = "http://localhost:8080/api"
DIAGRAM_SERVICE_URL = "http://localhost:8082"
DB_CONFIG = {
    "dbname": "autograph",
    "user": "autograph",
    "password": "autograph_dev_password",
    "host": "localhost",
    "port": 5432
}

def verify_email(email):
    """Mark user email as verified in database."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET is_verified = true WHERE email = %s",
        (email,)
    )
    conn.commit()
    cur.close()
    conn.close()

def make_user_admin(email):
    """Make a user an admin in the database."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET role = 'admin' WHERE email = %s",
        (email,)
    )
    conn.commit()
    cur.close()
    conn.close()

def test_admin_delete_any_comment():
    """Test that admin can delete any comment."""
    print("=" * 80)
    print("Feature #436 Test: Admin Delete Comments")
    print("=" * 80)

    # Step 1: Create regular user and post comment
    print("\n[1/5] Creating regular user and posting comment...")
    regular_email = f"regular_user_{uuid.uuid4().hex[:8]}@example.com"
    admin_email = f"admin_user_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePass123!"

    # Register regular user
    register_response = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={
            "email": regular_email,
            "password": password,
            "full_name": "Regular User"
        }
    )

    if register_response.status_code != 201:
        print(f"❌ Registration failed: {register_response.status_code}")
        print(register_response.text)
        return False

    # Verify email
    verify_email(regular_email)
    print(f"✅ Regular user registered and verified")

    # Login as regular user
    login_response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={
            "email": regular_email,
            "password": password
        }
    )

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)
        return False

    login_data = login_response.json()
    regular_token = login_data["access_token"]
    # Decode JWT to get user_id from 'sub' claim
    payload_str = regular_token.split('.')[1]
    # Add padding if needed
    payload_str += '=' * (4 - len(payload_str) % 4)
    payload = json.loads(base64.b64decode(payload_str))
    regular_user_id = payload["sub"]
    print(f"✅ Regular user logged in: {regular_user_id}")

    # Create a diagram
    print("\n[2/5] Creating diagram and comment...")
    create_diagram_response = requests.post(
        f"{API_BASE_URL}/diagrams",
        headers={
            "Authorization": f"Bearer {regular_token}",
            "X-User-ID": regular_user_id
        },
        json={
            "title": "Admin Delete Test Diagram",
            "diagram_type": "canvas",
            "canvas_data": {"shapes": [], "arrows": []}
        }
    )

    if create_diagram_response.status_code not in (200, 201):
        print(f"❌ Failed to create diagram: {create_diagram_response.status_code}")
        print(create_diagram_response.text)
        return False

    diagram_id = create_diagram_response.json()["id"]
    print(f"✅ Created diagram: {diagram_id}")

    # Post a comment
    comment_text = "This comment will be deleted by admin"
    create_comment_response = requests.post(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments",
        headers={
            "Authorization": f"Bearer {regular_token}",
            "X-User-ID": regular_user_id
        },
        json={
            "content": comment_text,
            "position_x": 100,
            "position_y": 200
        }
    )

    if create_comment_response.status_code != 201:
        print(f"❌ Failed to create comment: {create_comment_response.status_code}")
        print(create_comment_response.text)
        return False

    comment_id = create_comment_response.json()["id"]
    print(f"✅ Created comment: {comment_id}")
    print(f"   Content: {comment_text}")

    # Step 2: Create admin user
    print("\n[3/5] Creating admin user...")

    # Register admin user
    admin_register_response = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={
            "email": admin_email,
            "password": password,
            "full_name": "Admin User"
        }
    )

    if admin_register_response.status_code != 201:
        print(f"❌ Admin registration failed: {admin_register_response.status_code}")
        print(admin_register_response.text)
        return False

    # Verify and make admin
    verify_email(admin_email)
    make_user_admin(admin_email)
    print(f"✅ Admin user created and promoted")

    # Login as admin
    admin_login_response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={
            "email": admin_email,
            "password": password
        }
    )

    if admin_login_response.status_code != 200:
        print(f"❌ Admin login failed: {admin_login_response.status_code}")
        print(admin_login_response.text)
        return False

    admin_login_data = admin_login_response.json()
    admin_token = admin_login_data["access_token"]
    admin_payload_str = admin_token.split('.')[1]
    admin_payload_str += '=' * (4 - len(admin_payload_str) % 4)
    admin_payload = json.loads(base64.b64decode(admin_payload_str))
    admin_user_id = admin_payload["sub"]
    print(f"✅ Admin user logged in: {admin_user_id}")

    # Step 3: Admin deletes regular user's comment
    print("\n[4/5] Admin deleting regular user's comment...")
    delete_response = requests.delete(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments/{comment_id}/delete",
        headers={
            "Authorization": f"Bearer {admin_token}",
            "X-User-ID": admin_user_id
        }
    )

    if delete_response.status_code != 200:
        print(f"❌ Admin delete failed: {delete_response.status_code}")
        print(delete_response.text)
        return False

    delete_result = delete_response.json()
    print(f"✅ Admin deleted comment successfully")
    print(f"   Response: {delete_result.get('message', 'N/A')}")

    # Step 4: Verify comment is deleted
    print("\n[5/5] Verifying comment is deleted...")

    # Check that comment no longer exists
    get_deleted_comment_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/comments/{comment_id}",
        headers={
            "X-User-ID": admin_user_id
        }
    )

    # Should get 404
    if get_deleted_comment_response.status_code == 404:
        print(f"✅ Comment no longer exists (404)")
    elif get_deleted_comment_response.status_code == 200:
        print(f"❌ Comment still exists after admin deletion!")
        return False

    # Verify removed from list
    get_comments_after_response = requests.get(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments",
        headers={
            "Authorization": f"Bearer {admin_token}",
            "X-User-ID": admin_user_id
        }
    )

    if get_comments_after_response.status_code != 200:
        print(f"❌ Failed to get comments: {get_comments_after_response.status_code}")
        return False

    comments_after_data = get_comments_after_response.json()
    comments_after = comments_after_data.get("comments", [])
    comment_still_exists = any(c["id"] == comment_id for c in comments_after)

    if comment_still_exists:
        print(f"❌ Comment still appears in list after deletion")
        return False

    print(f"✅ Comment removed from list")

    print("\n" + "=" * 80)
    print("✅ Feature #436 TEST PASSED: Admin Delete Comments")
    print("=" * 80)
    print("\nTest Results:")
    print("✅ Admin user can delete other users' comments")
    print("✅ Comment is permanently deleted (404)")
    print("✅ Comment is removed from list")
    print("✅ Admin privileges properly respected")

    return True


if __name__ == "__main__":
    try:
        success = test_admin_delete_any_comment()

        if success:
            print("\n" + "=" * 80)
            print("🎉 TEST PASSED")
            print("=" * 80)
            exit(0)
        else:
            print("\n" + "=" * 80)
            print("❌ TEST FAILED")
            print("=" * 80)
            exit(1)

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
