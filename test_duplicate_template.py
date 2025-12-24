#!/usr/bin/env python3
"""
Test Feature #661: Duplicate template creates exact copy successfully

This script tests the duplicate diagram functionality:
1. Create a test user and login
2. Create a diagram (template)
3. Duplicate the diagram
4. Verify the duplicate is an exact copy (same content, different ID)
"""

import requests
import json
import uuid
import time
import psycopg2

# Configuration
AUTH_SERVICE_URL = "http://localhost:8085"
DIAGRAM_SERVICE_URL = "http://localhost:8082"

def test_duplicate_template():
    """Test the duplicate template functionality."""

    print("\n" + "="*80)
    print("TEST: Feature #661 - Duplicate Template Creates Exact Copy")
    print("="*80 + "\n")

    # Step 1: Create and login test user
    print("Step 1: Creating and logging in test user...")
    test_email = f"test-dup-{uuid.uuid4().hex[:8]}@example.com"
    test_password = "TestPassword123!"

    # Register
    register_response = requests.post(
        f"{AUTH_SERVICE_URL}/register",
        json={"email": test_email, "password": test_password, "name": "Test Duplicate User"}
    )

    if register_response.status_code not in [200, 201]:
        print(f"❌ Registration failed: {register_response.status_code}")
        return False

    user_id = register_response.json().get("id")

    # Verify email
    conn = psycopg2.connect(
        dbname="autograph", user="autograph", password="autograph_dev_password",
        host="localhost", port="5432"
    )
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_verified = true WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

    # Login
    login_response = requests.post(
        f"{AUTH_SERVICE_URL}/login",
        json={"email": test_email, "password": test_password}
    )

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False

    access_token = login_response.json().get("access_token")
    print(f"✅ Logged in as {test_email}")

    # Step 2: Create original diagram (template)
    print("\nStep 2: Creating original diagram (template)...")

    original_canvas_data = {
        "shapes": [
            {"id": "shape1", "type": "rectangle", "x": 100, "y": 100, "width": 200, "height": 100, "fill": "#ff0000"},
            {"id": "shape2", "type": "circle", "x": 400, "y": 200, "radius": 50, "fill": "#00ff00"},
            {"id": "shape3", "type": "text", "x": 150, "y": 300, "content": "Template Diagram"}
        ],
        "connections": [
            {"from": "shape1", "to": "shape2", "type": "arrow"}
        ]
    }

    create_response = requests.post(
        f"{DIAGRAM_SERVICE_URL}",
        headers={"X-User-ID": user_id, "Content-Type": "application/json"},
        json={
            "title": "My Template",
            "description": "Test template for duplication",
            "diagram_type": "canvas",
            "canvas_data": original_canvas_data,
            "note_content": "# Template Notes\n\nThis is a template diagram."
        }
    )

    if create_response.status_code not in [200, 201]:
        print(f"❌ Diagram creation failed: {create_response.status_code}")
        print(f"   Response: {create_response.text}")
        return False

    original = create_response.json()
    original_id = original.get("id")

    print(f"✅ Original diagram created: {original.get('title')}")
    print(f"   ID: {original_id}")
    print(f"   Shapes: {len(original_canvas_data['shapes'])}")

    time.sleep(1)

    # Step 3: Duplicate the diagram
    print("\nStep 3: Duplicating diagram...")

    duplicate_response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/{original_id}/duplicate",
        headers={"X-User-ID": user_id, "Content-Type": "application/json"}
    )

    if duplicate_response.status_code not in [200, 201]:
        print(f"❌ Duplication failed: {duplicate_response.status_code}")
        print(f"   Response: {duplicate_response.text}")
        return False

    duplicate_info = duplicate_response.json()
    duplicate_id = duplicate_info.get("duplicate_id")

    print(f"✅ Diagram duplicated successfully")
    print(f"   Original ID: {duplicate_info.get('original_id')}")
    print(f"   Duplicate ID: {duplicate_id}")
    print(f"   Title: {duplicate_info.get('title')}")

    time.sleep(1)

    # Step 4: Retrieve both diagrams and compare
    print("\nStep 4: Verifying duplicate is exact copy...")

    # Get original
    original_get_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{original_id}",
        headers={"X-User-ID": user_id}
    )

    # Get duplicate
    duplicate_get_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{duplicate_id}",
        headers={"X-User-ID": user_id}
    )

    if original_get_response.status_code != 200 or duplicate_get_response.status_code != 200:
        print(f"❌ Failed to retrieve diagrams")
        return False

    original_full = original_get_response.json()
    duplicate_full = duplicate_get_response.json()

    print(f"✅ Retrieved both diagrams")

    # Step 5: Verify content matches
    print("\nStep 5: Comparing content...")

    # Check IDs are different
    if original_full.get("id") == duplicate_full.get("id"):
        print(f"❌ IDs should be different!")
        print(f"   Original: {original_full.get('id')}")
        print(f"   Duplicate: {duplicate_full.get('id')}")
        return False

    print(f"✅ IDs are different (as expected)")

    # Check title has "(Copy)" appended
    expected_title = "My Template (Copy)"
    actual_title = duplicate_full.get("title")

    if actual_title != expected_title:
        print(f"❌ Title mismatch!")
        print(f"   Expected: {expected_title}")
        print(f"   Actual: {actual_title}")
        return False

    print(f"✅ Title correct: '{actual_title}'")

    # Check canvas_data matches
    original_canvas = original_full.get("canvas_data", {})
    duplicate_canvas = duplicate_full.get("canvas_data", {})

    if len(original_canvas.get("shapes", [])) != len(duplicate_canvas.get("shapes", [])):
        print(f"❌ Shapes count mismatch!")
        print(f"   Original: {len(original_canvas.get('shapes', []))} shapes")
        print(f"   Duplicate: {len(duplicate_canvas.get('shapes', []))} shapes")
        return False

    print(f"✅ Canvas data copied: {len(duplicate_canvas.get('shapes', []))} shapes")

    # Check specific shape content
    original_text_shape = next((s for s in original_canvas.get("shapes", []) if s.get("id") == "shape3"), None)
    duplicate_text_shape = next((s for s in duplicate_canvas.get("shapes", []) if s.get("id") == "shape3"), None)

    if not original_text_shape or not duplicate_text_shape:
        print(f"❌ Text shape not found in duplicate!")
        return False

    if original_text_shape.get("content") != duplicate_text_shape.get("content"):
        print(f"❌ Text content mismatch!")
        return False

    print(f"✅ Text content matches: '{duplicate_text_shape.get('content')}'")

    # Check note_content matches
    if original_full.get("note_content") != duplicate_full.get("note_content"):
        print(f"❌ Note content mismatch!")
        print(f"   Original: {original_full.get('note_content')}")
        print(f"   Duplicate: {duplicate_full.get('note_content')}")
        return False

    print(f"✅ Note content matches")

    # Check connections copied
    if len(original_canvas.get("connections", [])) != len(duplicate_canvas.get("connections", [])):
        print(f"❌ Connections count mismatch!")
        return False

    print(f"✅ Connections copied: {len(duplicate_canvas.get('connections', []))} connections")

    # Final success
    print("\n" + "="*80)
    print("✅ FEATURE #661 PASSING: Duplicate template creates exact copy successfully!")
    print("="*80 + "\n")

    return True

if __name__ == "__main__":
    try:
        success = test_duplicate_template()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
