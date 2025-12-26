#!/usr/bin/env python3
"""
E2E Test for Feature #472: Version history: Version labels: tag important versions

Test Steps:
1. Select version
2. Add label: 'Before redesign'
3. Save
4. Verify label visible in timeline
5. Search by label

Expected:
✓ Can select a version
✓ Can add a label to the version
✓ Label is saved successfully
✓ Label appears in the version timeline
✓ Can search/filter versions by label
"""

import requests
import sys
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8080/api/diagrams"
TEST_EMAIL = "test_feature_472@example.com"
TEST_PASSWORD = "SecurePassword123!@#"

def main():
    print("=" * 80)
    print("FEATURE #472: Version history: Version labels: tag important versions")
    print("=" * 80)

    # Step 1: Login (user already created with email verified)
    print("\n[1/8] Logging in...")
    login_response = requests.post(
        "http://localhost:8080/api/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
    )

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)
        return False

    auth_data = login_response.json()
    token = auth_data["access_token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    print("✓ Logged in successfully")

    # Step 2: Create diagram
    print("\n[2/8] Creating test diagram...")
    diagram_response = requests.post(
        BASE_URL,
        headers=headers,
        json={
            "title": "Version Labels Test",
            "diagram_type": "canvas",
            "canvas_data": {"shapes": [{"id": "1", "type": "rect", "x": 0, "y": 0}]}
        }
    )

    if diagram_response.status_code not in [200, 201]:
        print(f"❌ Failed to create diagram: {diagram_response.status_code}")
        print(diagram_response.text)
        return False

    diagram = diagram_response.json()
    diagram_id = diagram["id"]
    print(f"✓ Created diagram: {diagram_id}")

    # Step 3: Create multiple versions to have a timeline
    print("\n[3/8] Creating version history (v2 and v3)...")

    # Update to create v2
    update_response = requests.put(
        f"{BASE_URL}/{diagram_id}",
        headers=headers,
        json={
            "title": "Version Labels Test",
            "diagram_type": "canvas",
            "canvas_data": {"shapes": [{"id": "1", "type": "rect", "x": 10, "y": 10}]},
            "version_description": "Version 2 - first update"
        }
    )

    if update_response.status_code != 200:
        print(f"❌ Failed to create v2: {update_response.status_code}")
        return False

    # Update again for v3
    update_response = requests.put(
        f"{BASE_URL}/{diagram_id}",
        headers=headers,
        json={
            "title": "Version Labels Test",
            "diagram_type": "canvas",
            "canvas_data": {"shapes": [{"id": "1", "type": "rect", "x": 20, "y": 20}]},
            "version_description": "Version 3 - second update"
        }
    )

    if update_response.status_code != 200:
        print(f"❌ Failed to create v3: {update_response.status_code}")
        return False

    print("✓ Created 3 versions (v1, v2, v3)")

    # Step 4: STEP 1 - Select version (get versions list)
    print("\n[4/8] TEST STEP 1: Select version from timeline...")
    versions_response = requests.get(
        f"{BASE_URL}/{diagram_id}/versions",
        headers=headers
    )

    if versions_response.status_code != 200:
        print(f"❌ Failed to get versions: {versions_response.status_code}")
        return False

    versions_data = versions_response.json()
    versions = versions_data.get("versions", [])

    print(f"Found {len(versions)} versions in timeline")

    if len(versions) < 2:
        print(f"❌ Expected at least 2 versions, got {len(versions)}")
        return False

    # Find version 2 (the middle one)
    target_version = None
    for v in versions:
        if v.get("version_number") == 2:
            target_version = v
            break

    if not target_version:
        # Fallback to second version in list
        target_version = versions[1] if len(versions) >= 2 else versions[0]

    version_id = target_version["id"]
    print(f"✓ STEP 1 COMPLETE: Selected version 2 (ID: {version_id})")

    # Step 5: STEP 2 - Add label 'Before redesign'
    print("\n[5/8] TEST STEP 2: Add label 'Before redesign'...")
    label_text = "Before redesign"
    label_response = requests.patch(
        f"{BASE_URL}/{diagram_id}/versions/{version_id}/label",
        headers=headers,
        json={
            "label": label_text
        }
    )

    if label_response.status_code != 200:
        print(f"❌ Failed to add label: {label_response.status_code}")
        print(label_response.text)
        return False

    labeled_version = label_response.json()
    print(f"✓ STEP 2 COMPLETE: Added label '{labeled_version.get('label')}'")

    # Step 6: STEP 3 - Save (already saved by API, verify with GET)
    print("\n[6/8] TEST STEP 3: Verify label saved...")
    get_version_response = requests.get(
        f"{BASE_URL}/{diagram_id}/versions/{version_id}",
        headers=headers
    )

    if get_version_response.status_code != 200:
        print(f"❌ Failed to get version: {get_version_response.status_code}")
        return False

    version_detail = get_version_response.json()
    if version_detail.get("label") != label_text:
        print(f"❌ Label not saved correctly: expected '{label_text}', got '{version_detail.get('label')}'")
        return False

    print(f"✓ STEP 3 COMPLETE: Label saved successfully")

    # Step 7: STEP 4 - Verify label visible in timeline
    print("\n[7/8] TEST STEP 4: Verify label visible in timeline...")
    timeline_response = requests.get(
        f"{BASE_URL}/{diagram_id}/versions",
        headers=headers
    )

    if timeline_response.status_code != 200:
        print(f"❌ Failed to get timeline: {timeline_response.status_code}")
        return False

    timeline_data = timeline_response.json()
    timeline_versions = timeline_data.get("versions", [])

    # Find our labeled version in the timeline
    labeled_in_timeline = False
    for v in timeline_versions:
        if v.get("id") == version_id:
            if v.get("label") == label_text:
                labeled_in_timeline = True
                print(f"   Found version 2 in timeline with label: '{v.get('label')}'")
                break
            else:
                print(f"❌ Version found in timeline but label mismatch: '{v.get('label')}'")
                return False

    if not labeled_in_timeline:
        print(f"❌ Labeled version not found in timeline")
        return False

    print(f"✓ STEP 4 COMPLETE: Label visible in timeline")

    # Step 8: STEP 5 - Search by label
    print("\n[8/8] TEST STEP 5: Search versions by label...")
    search_response = requests.get(
        f"{BASE_URL}/{diagram_id}/versions",
        headers=headers,
        params={"search": label_text}
    )

    if search_response.status_code != 200:
        print(f"❌ Failed to search versions: {search_response.status_code}")
        print(search_response.text)
        return False

    search_data = search_response.json()
    search_results = search_data.get("versions", [])

    # Check if our labeled version is in the search results
    found_in_search = False
    for v in search_results:
        if v.get("label") == label_text:
            found_in_search = True
            print(f"   Found version with label '{label_text}' in search results")
            break

    if not found_in_search:
        print(f"❌ Labeled version not found in search results")
        print(f"   Search returned {len(search_results)} versions")
        return False

    print(f"✓ STEP 5 COMPLETE: Can search/filter by label (found {len(search_results)} matching results)")

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY - ALL 5 REQUIRED STEPS")
    print("=" * 80)
    print("✓ STEP 1: Select version - PASS")
    print("✓ STEP 2: Add label 'Before redesign' - PASS")
    print("✓ STEP 3: Save - PASS")
    print("✓ STEP 4: Verify label visible in timeline - PASS")
    print("✓ STEP 5: Search by label - PASS")
    print("\n✅ Feature #472 PASSING")
    print("=" * 80)

    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
