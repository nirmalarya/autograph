#!/usr/bin/env python3
"""
Feature #458: Version history - Version snapshots with full canvas_data per version

Test Steps:
1. Create v1 with 5 shapes
2. Edit to v2 with 10 shapes
3. View v1
4. Verify only 5 shapes
5. View v2
6. Verify 10 shapes

This test verifies that each version stores a complete snapshot of the canvas data,
and that viewing an old version returns the exact canvas state from that point in time.
"""

import requests
import json
import jwt

# Configuration
AUTH_BASE = "http://localhost:8085"
DIAGRAM_SERVICE = "http://localhost:8082"
TEST_EMAIL = "test458@example.com"
TEST_PASSWORD = "test458pass"

def test_version_snapshots_full_canvas_data():
    """Test that each version stores full canvas_data snapshot."""

    print("=" * 70)
    print("Feature #458: Version Snapshots with Full canvas_data")
    print("=" * 70)

    # Step 1: Login
    print("\n1. Logging in...")
    login_response = requests.post(
        f"{AUTH_BASE}/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=10
    )
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    token = login_response.json()["access_token"]

    # Decode JWT to get user_id
    decoded = jwt.decode(token, options={"verify_signature": False})
    user_id = decoded["sub"]

    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }
    print(f"   ✓ Logged in successfully as user {user_id}")

    # Step 2: Create diagram with 5 shapes (v1)
    print("\n2. Creating diagram with 5 shapes (v1)...")
    canvas_data_v1 = {
        "shapes": [
            {"id": "shape1", "type": "rectangle", "x": 0, "y": 0},
            {"id": "shape2", "type": "circle", "x": 100, "y": 100},
            {"id": "shape3", "type": "triangle", "x": 200, "y": 200},
            {"id": "shape4", "type": "star", "x": 300, "y": 300},
            {"id": "shape5", "type": "hexagon", "x": 400, "y": 400}
        ],
        "bindings": [],
        "assets": []
    }

    create_response = requests.post(
        f"{DIAGRAM_SERVICE}/",
        headers=headers,
        json={
            "title": "Feature 458 Test Diagram",
            "type": "canvas",
            "canvas_data": canvas_data_v1
        },
        timeout=10
    )
    assert create_response.status_code in [200, 201], f"Create failed: {create_response.text}"
    diagram_id = create_response.json()["id"]
    print(f"   ✓ Created diagram {diagram_id} with 5 shapes")
    print(f"   ✓ Version 1 created with shapes: {len(canvas_data_v1['shapes'])}")

    # Step 3: Edit diagram to have 10 shapes (create v2)
    print("\n3. Editing diagram to have 10 shapes (v2)...")
    canvas_data_v2 = {
        "shapes": [
            {"id": "shape1", "type": "rectangle", "x": 0, "y": 0},
            {"id": "shape2", "type": "circle", "x": 100, "y": 100},
            {"id": "shape3", "type": "triangle", "x": 200, "y": 200},
            {"id": "shape4", "type": "star", "x": 300, "y": 300},
            {"id": "shape5", "type": "hexagon", "x": 400, "y": 400},
            {"id": "shape6", "type": "pentagon", "x": 500, "y": 500},
            {"id": "shape7", "type": "octagon", "x": 600, "y": 600},
            {"id": "shape8", "type": "ellipse", "x": 700, "y": 700},
            {"id": "shape9", "type": "diamond", "x": 800, "y": 800},
            {"id": "shape10", "type": "arrow", "x": 900, "y": 900}
        ],
        "bindings": [],
        "assets": []
    }

    # Update the diagram (this should create v2)
    update_response = requests.put(
        f"{DIAGRAM_SERVICE}/{diagram_id}",
        headers=headers,
        json={
            "canvas_data": canvas_data_v2
        },
        timeout=10
    )
    assert update_response.status_code == 200, f"Update failed: {update_response.text}"
    print(f"   ✓ Updated diagram to have 10 shapes")
    print(f"   ✓ Version 2 created with shapes: {len(canvas_data_v2['shapes'])}")

    # Step 4: Get versions list
    print("\n4. Fetching versions list...")
    versions_response = requests.get(
        f"{DIAGRAM_SERVICE}/{diagram_id}/versions",
        headers=headers,
        timeout=10
    )
    assert versions_response.status_code == 200, f"Get versions failed: {versions_response.text}"
    versions_data = versions_response.json()
    versions = versions_data.get("versions", [])
    print(f"   ✓ Found {len(versions)} versions")

    # Find version IDs
    version_1 = next((v for v in versions if v["version_number"] == 1), None)
    version_2 = next((v for v in versions if v["version_number"] == 2), None)

    assert version_1 is not None, "Version 1 not found!"
    assert version_2 is not None, "Version 2 not found!"

    version_1_id = version_1["id"]
    version_2_id = version_2["id"]

    print(f"   ✓ Version 1 ID: {version_1_id}")
    print(f"   ✓ Version 2 ID: {version_2_id}")

    # Step 5: View v1 and verify 5 shapes
    print("\n5. Viewing Version 1 (should have 5 shapes)...")
    v1_response = requests.get(
        f"{DIAGRAM_SERVICE}/{diagram_id}/versions/{version_1_id}",
        headers=headers,
        timeout=10
    )
    assert v1_response.status_code == 200, f"Get v1 failed: {v1_response.text}"
    v1_data = v1_response.json()
    v1_canvas_data = v1_data.get("canvas_data", {})
    v1_shapes = v1_canvas_data.get("shapes", [])

    print(f"   ✓ Version 1 canvas_data retrieved")
    print(f"   ✓ Version 1 has {len(v1_shapes)} shapes")

    assert len(v1_shapes) == 5, f"Version 1 should have 5 shapes, but has {len(v1_shapes)}"

    # Verify the shape IDs match v1
    v1_shape_ids = sorted([s["id"] for s in v1_shapes])
    expected_v1_ids = sorted(["shape1", "shape2", "shape3", "shape4", "shape5"])
    assert v1_shape_ids == expected_v1_ids, f"Version 1 shape IDs don't match! Got {v1_shape_ids}, expected {expected_v1_ids}"

    print(f"   ✓ Version 1 has correct 5 shapes: {v1_shape_ids}")

    # Step 6: View v2 and verify 10 shapes
    print("\n6. Viewing Version 2 (should have 10 shapes)...")
    v2_response = requests.get(
        f"{DIAGRAM_SERVICE}/{diagram_id}/versions/{version_2_id}",
        headers=headers,
        timeout=10
    )
    assert v2_response.status_code == 200, f"Get v2 failed: {v2_response.text}"
    v2_data = v2_response.json()
    v2_canvas_data = v2_data.get("canvas_data", {})
    v2_shapes = v2_canvas_data.get("shapes", [])

    print(f"   ✓ Version 2 canvas_data retrieved")
    print(f"   ✓ Version 2 has {len(v2_shapes)} shapes")

    assert len(v2_shapes) == 10, f"Version 2 should have 10 shapes, but has {len(v2_shapes)}"

    # Verify the shape IDs match v2
    v2_shape_ids = sorted([s["id"] for s in v2_shapes])
    expected_v2_ids = sorted([f"shape{i}" for i in range(1, 11)])
    assert v2_shape_ids == expected_v2_ids, f"Version 2 shape IDs don't match! Got {v2_shape_ids}, expected {expected_v2_ids}"

    print(f"   ✓ Version 2 has correct 10 shapes: {v2_shape_ids}")

    # Step 7: Verify current diagram has v2 data
    print("\n7. Verifying current diagram has v2 data...")
    current_response = requests.get(
        f"{DIAGRAM_SERVICE}/{diagram_id}",
        headers=headers,
        timeout=10
    )
    assert current_response.status_code == 200, f"Get current failed: {current_response.text}"
    current_data = current_response.json()
    current_canvas_data = current_data.get("canvas_data", {})
    current_shapes = current_canvas_data.get("shapes", [])

    print(f"   ✓ Current diagram has {len(current_shapes)} shapes")
    assert len(current_shapes) == 10, f"Current should have 10 shapes, but has {len(current_shapes)}"
    print(f"   ✓ Current diagram matches v2")

    # Summary
    print("\n" + "=" * 70)
    print("FEATURE #458: ✅ PASSED")
    print("=" * 70)
    print("\nVerified behaviors:")
    print("✓ Version 1 stores complete snapshot with 5 shapes")
    print("✓ Version 2 stores complete snapshot with 10 shapes")
    print("✓ Each version has independent canvas_data")
    print("✓ Viewing old version returns exact snapshot from that time")
    print("✓ Current diagram reflects latest version (v2)")
    print("\nConclusion: Each version correctly stores full canvas_data snapshot! ✅")
    print("=" * 70)

    return True

if __name__ == "__main__":
    try:
        test_version_snapshots_full_canvas_data()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
