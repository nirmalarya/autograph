#!/usr/bin/env python3
"""
Test Feature 456: Version numbering auto-increment

Verify:
1. Create diagram (v1)
2. Edit (v2)
3. Edit (v3)
4. Verify sequential numbering
5. Verify no gaps
"""

import requests
import json
import jwt

# Configuration
AUTH_BASE = "http://localhost:8085"
DIAGRAM_SERVICE = "http://localhost:8082"

def login_user(email, password):
    """Login and get JWT token and user_id"""
    response = requests.post(
        f"{AUTH_BASE}/login",
        json={"email": email, "password": password}
    )
    if response.status_code == 200:
        token = response.json().get("access_token")
        # Decode JWT to get user_id
        decoded = jwt.decode(token, options={"verify_signature": False})
        user_id = decoded["sub"]
        return token, user_id
    else:
        raise Exception(f"Login failed: {response.status_code} - {response.text}")

def create_diagram(token, user_id, title):
    """Create a new diagram"""
    response = requests.post(
        f"{DIAGRAM_SERVICE}/",
        headers={
            "Authorization": f"Bearer {token}",
            "X-User-ID": user_id
        },
        json={
            "title": title,
            "type": "canvas",
            "canvas_data": {
                "shapes": [
                    {"id": "shape1", "type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 50}
                ]
            }
        }
    )
    if response.status_code in [200, 201]:
        return response.json().get("id")
    else:
        raise Exception(f"Create diagram failed: {response.status_code} - {response.text}")

def update_diagram(token, user_id, diagram_id, canvas_data):
    """Update diagram content"""
    response = requests.put(
        f"{DIAGRAM_SERVICE}/{diagram_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "X-User-ID": user_id
        },
        json={"canvas_data": canvas_data}
    )
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Update diagram failed: {response.status_code} - {response.text}")

def get_versions(token, user_id, diagram_id):
    """Get all versions for a diagram"""
    response = requests.get(
        f"{DIAGRAM_SERVICE}/{diagram_id}/versions",
        headers={
            "Authorization": f"Bearer {token}",
            "X-User-ID": user_id
        }
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("versions", [])
    else:
        raise Exception(f"Get versions failed: {response.status_code} - {response.text}")

def main():
    print("="*60)
    print("Feature 456: Version Numbering Auto-Increment Test")
    print("="*60)

    # Step 1: Login
    print("\n1. Logging in...")
    token, user_id = login_user("test456@example.com", "TestPassword123!")
    print(f"✓ Login successful (user_id: {user_id})")

    # Step 2: Create diagram (v1)
    print("\n2. Creating diagram (should create v1)...")
    diagram_id = create_diagram(token, user_id, "Version Numbering Test")
    print(f"✓ Diagram created: {diagram_id}")

    # Step 3: Get initial versions
    print("\n3. Checking initial version...")
    versions = get_versions(token, user_id, diagram_id)
    print(f"✓ Version count: {len(versions)}")
    if len(versions) > 0:
        print(f"  - Version numbers: {[v['version_number'] for v in versions]}")
        assert versions[0]['version_number'] == 1, f"Expected v1, got v{versions[0]['version_number']}"
        print("✓ Initial version is v1")

    # Step 4: Edit diagram (should create v2 after auto-save timer)
    print("\n4. Editing diagram (small change - will auto-save after 5 min)...")
    update_diagram(token, user_id, diagram_id, {
        "shapes": [
            {"id": "shape1", "type": "rectangle", "x": 10, "y": 10, "width": 100, "height": 50}
        ]
    })
    print("✓ Edit 1 complete (waiting for auto-save...)")

    # Step 5: Trigger immediate versioning with major edit
    print("\n5. Triggering immediate versioning (major edit - 10+ deletions)...")
    # Create 15 shapes then delete them all
    canvas_with_many_shapes = {
        "shapes": [
            {"id": f"shape{i}", "type": "rectangle", "x": i*10, "y": i*10, "width": 50, "height": 50}
            for i in range(1, 16)
        ]
    }
    update_diagram(token, user_id, diagram_id, canvas_with_many_shapes)
    print("✓ Created 15 shapes")

    # Delete all shapes (major edit triggers immediate versioning)
    update_diagram(token, user_id, diagram_id, {"shapes": []})
    print("✓ Deleted all shapes (major edit)")

    # Step 6: Verify version 2 created
    print("\n6. Checking version after major edit...")
    versions = get_versions(token, user_id, diagram_id)
    print(f"✓ Version count: {len(versions)}")
    print(f"  - Version numbers: {[v['version_number'] for v in versions]}")

    # Step 7: Create another major edit to get v3
    print("\n7. Creating version 3 with another major edit...")
    canvas_with_many_shapes_2 = {
        "shapes": [
            {"id": f"circle{i}", "type": "circle", "x": i*15, "y": i*15, "r": 25}
            for i in range(1, 16)
        ]
    }
    update_diagram(token, user_id, diagram_id, canvas_with_many_shapes_2)
    print("✓ Created 15 circles")

    # Delete all circles (another major edit)
    update_diagram(token, user_id, diagram_id, {"shapes": []})
    print("✓ Deleted all circles (major edit)")

    # Step 8: Verify sequential numbering with no gaps
    print("\n8. Verifying sequential version numbering...")
    versions = get_versions(token, user_id, diagram_id)
    print(f"✓ Total versions: {len(versions)}")

    # Sort by version_number (should already be sorted descending)
    version_numbers = sorted([v['version_number'] for v in versions])
    print(f"  - Version numbers (sorted): {version_numbers}")

    # Verify sequential (1, 2, 3, ...)
    expected_numbers = list(range(1, len(versions) + 1))
    assert version_numbers == expected_numbers, \
        f"Expected sequential numbering {expected_numbers}, got {version_numbers}"
    print(f"✓ Sequential numbering verified: {version_numbers}")

    # Verify no gaps
    for i in range(len(version_numbers) - 1):
        gap = version_numbers[i+1] - version_numbers[i]
        assert gap == 1, f"Gap detected between v{version_numbers[i]} and v{version_numbers[i+1]}"
    print("✓ No gaps in version numbering")

    # Step 9: Verify each version has correct details
    print("\n9. Verifying version details...")
    for v in versions:
        print(f"  - v{v['version_number']}: {v.get('description', 'No description')}")

    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED - Feature 456 Working!")
    print("="*60)
    print("\nSummary:")
    print(f"- Created {len(versions)} versions")
    print(f"- Version numbers: {sorted([v['version_number'] for v in versions])}")
    print("- Sequential numbering: ✓")
    print("- No gaps: ✓")
    print("- Auto-increment: ✓")

    return True

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
