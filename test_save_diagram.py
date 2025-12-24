#!/usr/bin/env python3
"""
Test Feature #660: Save diagram persists changes successfully

This script tests the save diagram functionality end-to-end:
1. Register/login a test user
2. Create a new diagram
3. Update the diagram (save changes)
4. Retrieve the diagram again
5. Verify changes persisted
"""

import requests
import json
import uuid
import time
from datetime import datetime

# Configuration
AUTH_SERVICE_URL = "http://localhost:8085"
DIAGRAM_SERVICE_URL = "http://localhost:8082"
API_GATEWAY_URL = "http://localhost:8080"

def test_save_diagram():
    """Test the complete save diagram flow."""

    print("\n" + "="*80)
    print("TEST: Feature #660 - Save Diagram Persists Changes")
    print("="*80 + "\n")

    # Step 1: Create a test user
    print("Step 1: Creating test user...")
    test_email = f"test-save-{uuid.uuid4().hex[:8]}@example.com"
    test_password = "TestPassword123!"

    register_response = requests.post(
        f"{AUTH_SERVICE_URL}/register",
        json={
            "email": test_email,
            "password": test_password,
            "name": "Test Save User"
        }
    )

    if register_response.status_code not in [200, 201]:
        print(f"❌ Registration failed: {register_response.status_code}")
        print(f"   Response: {register_response.text}")
        return False

    user_data = register_response.json()
    user_id = user_data.get("id")

    print(f"✅ User created: {test_email}")
    print(f"   User ID: {user_id}")

    if not user_id:
        print("❌ Missing user ID!")
        return False

    # Step 1.5: Verify email (for testing - directly via database)
    print("\nStep 1.5: Verifying email (test mode)...")

    # For testing, we'll directly mark the user as verified in the database
    # In production, this would be done via the /email/verify endpoint
    import psycopg2
    try:
        conn = psycopg2.connect(
            dbname="autograph",
            user="autograph",
            password="autograph_dev_password",
            host="localhost",
            port="5432"
        )
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_verified = true WHERE id = %s", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Email verified")
    except Exception as e:
        print(f"❌ Failed to verify email: {e}")
        return False

    # Step 1.6: Login to get access token
    print("\nStep 1.6: Logging in to get access token...")

    login_response = requests.post(
        f"{AUTH_SERVICE_URL}/login",
        json={
            "email": test_email,
            "password": test_password
        }
    )

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(f"   Response: {login_response.text}")
        return False

    login_data = login_response.json()
    access_token = login_data.get("access_token")

    print(f"✅ Logged in successfully")
    print(f"   Access token: {access_token[:20]}..." if access_token else "   No access token!")

    if not access_token:
        print("❌ Missing access token!")
        return False

    # Step 2: Create a new diagram
    print("\nStep 2: Creating new diagram...")

    initial_canvas_data = {
        "shapes": [
            {"id": "shape1", "type": "rectangle", "x": 100, "y": 100, "width": 200, "height": 100}
        ]
    }

    create_response = requests.post(
        f"{DIAGRAM_SERVICE_URL}",
        headers={
            "X-User-ID": user_id,
            "Content-Type": "application/json"
        },
        json={
            "title": "Test Save Diagram",
            "description": "Testing save functionality",
            "diagram_type": "canvas",
            "canvas_data": initial_canvas_data
        }
    )

    if create_response.status_code not in [200, 201]:
        print(f"❌ Diagram creation failed: {create_response.status_code}")
        print(f"   Response: {create_response.text}")
        return False

    diagram = create_response.json()
    diagram_id = diagram.get("id")

    print(f"✅ Diagram created: {diagram.get('title')}")
    print(f"   Diagram ID: {diagram_id}")
    print(f"   Initial shapes: {len(initial_canvas_data['shapes'])}")

    # Wait a moment
    time.sleep(1)

    # Step 3: Update the diagram (add more shapes)
    print("\nStep 3: Updating diagram (saving changes)...")

    updated_canvas_data = {
        "shapes": [
            {"id": "shape1", "type": "rectangle", "x": 100, "y": 100, "width": 200, "height": 100},
            {"id": "shape2", "type": "circle", "x": 400, "y": 200, "radius": 50},
            {"id": "shape3", "type": "text", "x": 150, "y": 300, "content": "Test Save"}
        ]
    }

    update_response = requests.put(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}",
        headers={
            "X-User-ID": user_id,
            "Content-Type": "application/json"
        },
        json={
            "title": "Test Save Diagram (Updated)",
            "canvas_data": updated_canvas_data
        }
    )

    if update_response.status_code != 200:
        print(f"❌ Diagram update failed: {update_response.status_code}")
        print(f"   Response: {update_response.text}")
        return False

    updated_diagram = update_response.json()

    print(f"✅ Diagram updated successfully")
    print(f"   New title: {updated_diagram.get('title')}")
    print(f"   New shapes count: {len(updated_canvas_data['shapes'])}")

    # Wait a moment
    time.sleep(1)

    # Step 4: Retrieve the diagram again
    print("\nStep 4: Retrieving diagram to verify persistence...")

    get_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}",
        headers={
            "X-User-ID": user_id
        }
    )

    if get_response.status_code != 200:
        print(f"❌ Diagram retrieval failed: {get_response.status_code}")
        print(f"   Response: {get_response.text}")
        return False

    retrieved_diagram = get_response.json()

    print(f"✅ Diagram retrieved successfully")

    # Step 5: Verify changes persisted
    print("\nStep 5: Verifying changes persisted...")

    # Check title
    expected_title = "Test Save Diagram (Updated)"
    actual_title = retrieved_diagram.get("title")

    if actual_title != expected_title:
        print(f"❌ Title mismatch!")
        print(f"   Expected: {expected_title}")
        print(f"   Actual: {actual_title}")
        return False

    print(f"✅ Title persisted: {actual_title}")

    # Check canvas data
    retrieved_canvas = retrieved_diagram.get("canvas_data", {})
    retrieved_shapes = retrieved_canvas.get("shapes", [])

    if len(retrieved_shapes) != 3:
        print(f"❌ Shapes count mismatch!")
        print(f"   Expected: 3 shapes")
        print(f"   Actual: {len(retrieved_shapes)} shapes")
        return False

    print(f"✅ Canvas data persisted: {len(retrieved_shapes)} shapes")

    # Check specific shape
    shape3 = next((s for s in retrieved_shapes if s.get("id") == "shape3"), None)
    if not shape3:
        print(f"❌ Shape3 (text) not found!")
        return False

    if shape3.get("content") != "Test Save":
        print(f"❌ Shape3 content mismatch!")
        print(f"   Expected: 'Test Save'")
        print(f"   Actual: {shape3.get('content')}")
        return False

    print(f"✅ Text content persisted: '{shape3.get('content')}'")

    # Final success
    print("\n" + "="*80)
    print("✅ FEATURE #660 PASSING: Save diagram persists changes successfully!")
    print("="*80 + "\n")

    return True

if __name__ == "__main__":
    try:
        success = test_save_diagram()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
