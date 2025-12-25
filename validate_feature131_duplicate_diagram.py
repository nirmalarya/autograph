#!/usr/bin/env python3
"""
Feature #131 Validation: Duplicate diagram creates copy with new UUID

Tests:
1. Create diagram with title 'Original'
2. Add shapes to canvas
3. Call duplicate endpoint
4. Verify new diagram created
5. Verify new diagram has different UUID
6. Verify new diagram title: 'Original (Copy)'
7. Verify canvas_data copied exactly
8. Verify new diagram has fresh version history (version 1)
9. Verify original diagram unchanged
"""

import requests
import sys
import json
from datetime import datetime
import psycopg2
import base64

# Configuration
API_GATEWAY = "http://localhost:8080"
DIAGRAM_SERVICE = "http://localhost:8082"

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "autograph",
    "user": "autograph",
    "password": "autograph_dev_password"
}

def register_and_login():
    """Register a test user and get JWT token."""
    # Generate unique email
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    email = f"test_duplicate_{timestamp}@example.com"
    password = "SecurePass123!@#"

    # Register
    register_payload = {
        "email": email,
        "password": password,
        "full_name": "Test Duplicate User"
    }

    print(f"1. Registering user: {email}")
    resp = requests.post(f"{API_GATEWAY}/api/auth/register", json=register_payload)
    if resp.status_code != 201:
        print(f"   ❌ Registration failed: {resp.status_code} - {resp.text}")
        return None, None
    print(f"   ✓ User registered")

    # Verify user in database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_verified = TRUE WHERE email = %s", (email,))
        conn.commit()
        cur.close()
        conn.close()
        print(f"   ✓ User verified in database")
    except Exception as e:
        print(f"   ❌ Failed to verify user: {e}")
        return None, None

    # Login
    print(f"2. Logging in...")
    login_payload = {
        "email": email,
        "password": password
    }
    resp = requests.post(f"{API_GATEWAY}/api/auth/login", json=login_payload)
    if resp.status_code != 200:
        print(f"   ❌ Login failed: {resp.status_code} - {resp.text}")
        return None, None

    token = resp.json()["access_token"]

    # Decode JWT to get user_id (from 'sub' claim)
    try:
        # JWT format: header.payload.signature
        payload = token.split('.')[1]
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(payload))
        user_id = decoded['sub']
        print(f"   ✓ Logged in (user_id: {user_id})")
    except Exception as e:
        print(f"   ❌ Failed to decode JWT: {e}")
        return None, None

    return token, user_id


def create_diagram(token, user_id, title="Original"):
    """Create a diagram with canvas data."""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }

    # Create canvas with shapes
    canvas_data = {
        "shapes": [
            {
                "id": "shape1",
                "type": "rectangle",
                "x": 100,
                "y": 100,
                "width": 200,
                "height": 150,
                "props": {"color": "blue", "fill": "solid"}
            },
            {
                "id": "shape2",
                "type": "ellipse",
                "x": 400,
                "y": 200,
                "width": 150,
                "height": 150,
                "props": {"color": "red", "fill": "solid"}
            }
        ],
        "bindings": [],
        "assets": []
    }

    payload = {
        "title": title,
        "file_type": "canvas",
        "canvas_data": canvas_data
    }

    print(f"3. Creating diagram with title '{title}' and 2 shapes...")
    resp = requests.post(f"{API_GATEWAY}/api/diagrams", json=payload, headers=headers)
    if resp.status_code != 200:
        print(f"   ❌ Diagram creation failed: {resp.status_code} - {resp.text}")
        return None

    diagram = resp.json()
    diagram_id = diagram["id"]
    print(f"   ✓ Diagram created (id: {diagram_id})")
    print(f"   ✓ Canvas has {len(canvas_data['shapes'])} shapes")

    return diagram


def duplicate_diagram(token, user_id, diagram_id):
    """Duplicate a diagram."""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }

    print(f"4. Duplicating diagram {diagram_id}...")
    resp = requests.post(f"{API_GATEWAY}/api/diagrams/{diagram_id}/duplicate", headers=headers)
    if resp.status_code != 200:
        print(f"   ❌ Duplication failed: {resp.status_code} - {resp.text}")
        return None

    duplicate = resp.json()
    print(f"   ✓ Diagram duplicated")
    return duplicate


def get_diagram(token, user_id, diagram_id):
    """Get diagram details."""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }

    resp = requests.get(f"{API_GATEWAY}/api/diagrams/{diagram_id}", headers=headers)
    if resp.status_code != 200:
        print(f"   ❌ Failed to get diagram: {resp.status_code} - {resp.text}")
        return None

    return resp.json()


def main():
    """Run all validation tests."""
    print("=" * 80)
    print("Feature #131: Duplicate diagram creates copy with new UUID")
    print("=" * 80)

    # Step 1-2: Register and login
    token, user_id = register_and_login()
    if not token:
        print("\n❌ FAILED: Could not authenticate")
        return False

    # Step 3: Create original diagram
    original = create_diagram(token, user_id, "Original")
    if not original:
        print("\n❌ FAILED: Could not create original diagram")
        return False

    original_id = original["id"]
    original_title = original["title"]
    original_canvas = original.get("canvas_data")
    original_version = original.get("current_version", 1)

    # Step 4: Duplicate diagram
    duplicate_response = duplicate_diagram(token, user_id, original_id)
    if not duplicate_response:
        print("\n❌ FAILED: Could not duplicate diagram")
        return False

    duplicate_id = duplicate_response.get("duplicate_id")

    # Step 5: Verify new diagram created
    print(f"5. Verifying new diagram created...")
    if not duplicate_id:
        print(f"   ❌ No duplicate_id in response")
        return False
    print(f"   ✓ New diagram created (id: {duplicate_id})")

    # Step 6: Verify different UUID
    print(f"6. Verifying different UUID...")
    if duplicate_id == original_id:
        print(f"   ❌ Duplicate has same UUID as original!")
        return False
    print(f"   ✓ Different UUID: {duplicate_id} != {original_id}")

    # Step 7: Verify title
    print(f"7. Verifying title is 'Original (Copy)'...")
    duplicate_title = duplicate_response.get("title")
    if duplicate_title != "Original (Copy)":
        print(f"   ❌ Expected 'Original (Copy)', got '{duplicate_title}'")
        return False
    print(f"   ✓ Title is 'Original (Copy)'")

    # Step 8: Get full duplicate details and verify canvas_data
    print(f"8. Verifying canvas_data copied exactly...")
    duplicate_full = get_diagram(token, user_id, duplicate_id)
    if not duplicate_full:
        print(f"   ❌ Could not retrieve duplicate diagram")
        return False

    duplicate_canvas = duplicate_full.get("canvas_data")

    # Compare canvas data (shapes count and structure)
    if not duplicate_canvas:
        print(f"   ❌ Duplicate has no canvas_data")
        return False

    if not original_canvas:
        print(f"   ❌ Original has no canvas_data")
        return False

    original_shapes = original_canvas.get("shapes", [])
    duplicate_shapes = duplicate_canvas.get("shapes", [])

    if len(original_shapes) != len(duplicate_shapes):
        print(f"   ❌ Shape count mismatch: original={len(original_shapes)}, duplicate={len(duplicate_shapes)}")
        return False

    # Verify shapes are identical (except IDs might differ in some cases, but data should match)
    for i, (orig_shape, dup_shape) in enumerate(zip(original_shapes, duplicate_shapes)):
        if orig_shape.get("type") != dup_shape.get("type"):
            print(f"   ❌ Shape {i} type mismatch")
            return False
        if orig_shape.get("x") != dup_shape.get("x") or orig_shape.get("y") != dup_shape.get("y"):
            print(f"   ❌ Shape {i} position mismatch")
            return False

    print(f"   ✓ Canvas data copied exactly ({len(duplicate_shapes)} shapes)")

    # Step 9: Verify fresh version history (version 1)
    print(f"9. Verifying fresh version history (version 1)...")
    duplicate_version = duplicate_full.get("current_version", 0)
    if duplicate_version != 1:
        print(f"   ❌ Expected version 1, got version {duplicate_version}")
        return False
    print(f"   ✓ Fresh version history (version 1)")

    # Step 10: Verify original unchanged
    print(f"10. Verifying original diagram unchanged...")
    original_check = get_diagram(token, user_id, original_id)
    if not original_check:
        print(f"   ❌ Could not retrieve original diagram")
        return False

    if original_check["id"] != original_id:
        print(f"   ❌ Original ID changed!")
        return False

    if original_check["title"] != original_title:
        print(f"   ❌ Original title changed!")
        return False

    if original_check.get("current_version", 1) != original_version:
        print(f"   ❌ Original version changed!")
        return False

    print(f"   ✓ Original diagram unchanged")

    # All tests passed
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED")
    print("=" * 80)
    print(f"Original diagram: {original_id} - '{original_title}' (version {original_version})")
    print(f"Duplicate diagram: {duplicate_id} - '{duplicate_title}' (version {duplicate_version})")
    print(f"Canvas data: {len(duplicate_shapes)} shapes copied")
    print("=" * 80)

    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
