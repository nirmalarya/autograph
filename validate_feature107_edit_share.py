#!/usr/bin/env python3
"""
Feature #107 Validation: Permission check - shared diagram with edit access

Test Steps:
1. User A creates diagram
2. User A shares diagram with User B (edit access)
3. User B accesses diagram
4. Verify User B can view diagram
5. User B edits diagram
6. Verify 200 OK response
7. Verify changes saved
8. User B attempts to delete diagram
9. Verify 403 Forbidden (only owner can delete)
"""

import requests
import json
import time
import sys
import psycopg2

BASE_URL = "http://localhost:8080"
AUTH_SERVICE = "http://localhost:8085"
DIAGRAM_SERVICE = "http://localhost:8082"

def generate_email(prefix):
    """Generate unique email with timestamp"""
    timestamp = int(time.time() * 1000)
    return f"{prefix}_{timestamp}@example.com"

def verify_email_in_db(user_id):
    """Mark user as verified in database."""
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="autograph",
        user="autograph",
        password="autograph_dev_password"
    )
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_verified = true WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

def register_and_verify_user(email, password, full_name):
    """Register a user and verify their email"""
    print(f"\n📝 Registering user: {email}")

    # Register
    response = requests.post(
        f"{AUTH_SERVICE}/register",
        json={
            "email": email,
            "password": password,
            "full_name": full_name
        }
    )

    if response.status_code != 201:
        print(f"❌ Registration failed: {response.status_code} - {response.text}")
        return None

    user_data = response.json()
    user_id = user_data["id"]
    print(f"✅ User registered: {user_id}")

    # Verify email in database
    print(f"📧 Verifying email in database...")
    verify_email_in_db(user_id)
    print(f"✅ Email verified")

    # Login to get token
    response = requests.post(
        f"{AUTH_SERVICE}/login",
        json={
            "email": email,
            "password": password
        }
    )

    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None

    token_data = response.json()
    access_token = token_data["access_token"]

    print(f"✅ Logged in successfully")
    return {
        "id": user_id,
        "email": email,
        "access_token": access_token
    }

def create_diagram(user, title):
    """Create a diagram for a user"""
    print(f"\n🎨 Creating diagram '{title}' for {user['email']}")

    response = requests.post(
        f"{DIAGRAM_SERVICE}/",
        headers={
            "Authorization": f"Bearer {user['access_token']}",
            "X-User-ID": user['id']
        },
        json={
            "title": title,
            "canvas_data": {
                "elements": [
                    {"type": "rectangle", "x": 100, "y": 100, "width": 200, "height": 100, "text": "Original Content"}
                ]
            }
        }
    )

    if response.status_code not in [200, 201]:
        print(f"❌ Diagram creation failed: {response.status_code} - {response.text}")
        return None

    diagram = response.json()
    diagram_id = diagram.get("id")
    print(f"✅ Diagram created: {diagram_id}")
    return diagram_id

def share_diagram_with_user(owner, diagram_id, shared_with_email, permission):
    """Share diagram with another user"""
    print(f"\n🔗 Sharing diagram {diagram_id} with {shared_with_email} ({permission} access)")

    response = requests.post(
        f"{DIAGRAM_SERVICE}/{diagram_id}/share",
        headers={
            "Authorization": f"Bearer {owner['access_token']}",
            "X-User-ID": owner['id']
        },
        json={
            "permission": permission,
            "shared_with_email": shared_with_email
        }
    )

    if response.status_code not in [200, 201]:
        print(f"❌ Share creation failed: {response.status_code} - {response.text}")
        return None

    share = response.json()
    print(f"✅ Diagram shared successfully")
    return share

def get_diagram(user, diagram_id):
    """Get diagram details"""
    print(f"\n👁️  User {user['email']} accessing diagram {diagram_id}")

    response = requests.get(
        f"{DIAGRAM_SERVICE}/{diagram_id}",
        headers={
            "Authorization": f"Bearer {user['access_token']}",
            "X-User-ID": user['id']
        }
    )

    if response.status_code != 200:
        print(f"❌ Get diagram failed: {response.status_code} - {response.text}")
        return None

    diagram = response.json()
    print(f"✅ Diagram retrieved successfully")
    print(f"   Title: {diagram.get('title', 'N/A')}")
    print(f"   Owner: {diagram.get('owner', {}).get('email', 'N/A')}")
    return diagram

def update_diagram(user, diagram_id, new_content):
    """Update diagram content"""
    print(f"\n✏️  User {user['email']} editing diagram {diagram_id}")

    response = requests.put(
        f"{DIAGRAM_SERVICE}/{diagram_id}",
        headers={
            "Authorization": f"Bearer {user['access_token']}",
            "X-User-ID": user['id']
        },
        json={
            "canvas_data": new_content
        }
    )

    print(f"   Response: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ Diagram updated successfully")
        return response.json()
    else:
        print(f"❌ Update failed: {response.text}")
        return None

def delete_diagram(user, diagram_id):
    """Try to delete diagram"""
    print(f"\n🗑️  User {user['email']} attempting to delete diagram {diagram_id}")

    response = requests.delete(
        f"{DIAGRAM_SERVICE}/{diagram_id}",
        headers={
            "Authorization": f"Bearer {user['access_token']}",
            "X-User-ID": user['id']
        }
    )

    print(f"   Response: {response.status_code}")
    return response

def main():
    print("=" * 80)
    print("Feature #107 Validation: Shared diagram with edit access")
    print("=" * 80)

    # Step 1: Register User A
    user_a_email = generate_email("user_a_feature107")
    user_a = register_and_verify_user(user_a_email, "SecurePass123!", "User A")
    if not user_a:
        print("\n❌ FAILED: Could not register User A")
        sys.exit(1)

    # Step 2: Register User B
    user_b_email = generate_email("user_b_feature107")
    user_b = register_and_verify_user(user_b_email, "SecurePass456!", "User B")
    if not user_b:
        print("\n❌ FAILED: Could not register User B")
        sys.exit(1)

    # Step 3: User A creates diagram
    diagram_id = create_diagram(
        user_a,
        "Shared Project Diagram - Feature 107"
    )
    if not diagram_id:
        print("\n❌ FAILED: Could not create diagram")
        sys.exit(1)

    # Step 4: User A shares diagram with User B (edit access)
    share = share_diagram_with_user(user_a, diagram_id, user_b_email, "edit")
    if not share:
        print("\n❌ FAILED: Could not share diagram")
        sys.exit(1)

    # Step 5: User B accesses diagram (view)
    diagram_b_view = get_diagram(user_b, diagram_id)
    if not diagram_b_view:
        print("\n❌ FAILED: User B could not view diagram")
        sys.exit(1)

    # Step 6: User B edits diagram
    new_content = {
        "version": "1.0",
        "elements": [
            {"type": "rectangle", "x": 100, "y": 100, "width": 200, "height": 100, "text": "Original Content"},
            {"type": "circle", "x": 400, "y": 200, "radius": 50, "text": "User B's Addition"}
        ]
    }

    updated_diagram = update_diagram(user_b, diagram_id, new_content)

    # Step 7: Verify changes saved (200 OK)
    if not updated_diagram:
        print("\n❌ FAILED: User B could not edit diagram with edit permission")
        sys.exit(1)

    # Verify the content was actually updated
    diagram_after_edit = get_diagram(user_a, diagram_id)
    if not diagram_after_edit:
        print("\n❌ FAILED: Could not retrieve diagram after edit")
        sys.exit(1)

    if len(diagram_after_edit['canvas_data']['elements']) != 2:
        print(f"\n❌ FAILED: Changes not saved correctly. Expected 2 elements, got {len(diagram_after_edit['canvas_data']['elements'])}")
        sys.exit(1)

    print("\n✅ Changes saved successfully - diagram now has 2 elements")

    # Step 8: User B attempts to delete diagram
    delete_response = delete_diagram(user_b, diagram_id)

    # Step 9: Verify 403 Forbidden (only owner can delete)
    if delete_response.status_code == 403:
        print("✅ DELETE correctly forbidden for shared user (403)")

        # Verify error message
        error_data = delete_response.json()
        if "authorized" in error_data.get("detail", "").lower() or "owner" in error_data.get("detail", "").lower():
            print(f"✅ Correct error message: {error_data.get('detail')}")
        else:
            print(f"⚠️  Unexpected error message: {error_data.get('detail')}")
    else:
        print(f"\n❌ FAILED: Expected 403 Forbidden, got {delete_response.status_code}")
        print(f"   Response: {delete_response.text}")
        sys.exit(1)

    # Bonus: Verify owner can still delete
    print("\n🔍 Bonus check: Owner can still delete their diagram")
    delete_response_owner = delete_diagram(user_a, diagram_id)
    if delete_response_owner.status_code == 200:
        print("✅ Owner successfully deleted diagram")
    else:
        print(f"⚠️  Owner delete failed: {delete_response_owner.status_code}")

    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED - Feature #107 working correctly!")
    print("=" * 80)
    print("\nSummary:")
    print("✅ User B can view shared diagram")
    print("✅ User B can edit shared diagram (with edit permission)")
    print("✅ Changes are saved (200 OK)")
    print("✅ User B cannot delete diagram (403 Forbidden)")
    print("✅ Only owner can delete diagram")
    print("\n")

if __name__ == "__main__":
    main()
