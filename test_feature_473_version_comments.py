#!/usr/bin/env python3
"""
Feature #473: Version Comments
Test that users can add notes/comments to versions to explain changes.

Test Steps:
1. Select version
2. Add comment: 'Added caching layer'
3. Save
4. Verify comment shown
5. Verify helps understand changes
"""

import requests
import time
import sys

# Configuration
API_BASE = "http://localhost:8080/api"
DIAGRAM_SERVICE = "http://localhost:8082"

def test_version_comments():
    """Test version comments feature."""
    print("\n" + "="*60)
    print("Feature #473: Version Comments")
    print("="*60)

    # Step 1: Register and login
    print("\n1. Setting up test user and diagram...")
    email = f"version_comment_test_{int(time.time())}@test.com"
    password = "SecurePass123!"

    # Register
    register_response = requests.post(
        f"{API_BASE}/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Version Comment Test User"
        }
    )

    if register_response.status_code != 201:
        print(f"❌ Registration failed: {register_response.status_code}")
        return False

    # Login
    login_response = requests.post(
        f"{API_BASE}/auth/login",
        json={
            "email": email,
            "password": password
        }
    )

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False

    token_data = login_response.json()
    token = token_data["access_token"]
    user_id = token_data["user"]["id"]

    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }

    print(f"✓ User created and authenticated: {email}")

    # Step 2: Create a diagram
    print("\n2. Creating test diagram...")
    diagram_response = requests.post(
        f"{API_BASE}/diagrams",
        headers=headers,
        json={
            "title": "Test Diagram for Version Comments",
            "diagram_type": "canvas",
            "content": {"elements": [{"id": "1", "type": "rectangle"}]}
        }
    )

    if diagram_response.status_code != 201:
        print(f"❌ Failed to create diagram: {diagram_response.status_code}")
        return False

    diagram_id = diagram_response.json()["id"]
    print(f"✓ Created diagram: {diagram_id}")

    # Step 3: Make some changes to create a new version
    print("\n3. Creating version 2 with changes...")
    update_response = requests.patch(
        f"{API_BASE}/diagrams/{diagram_id}",
        headers=headers,
        json={
            "content": {
                "elements": [
                    {"id": "1", "type": "rectangle"},
                    {"id": "2", "type": "circle"}  # Added element
                ]
            }
        }
    )

    if update_response.status_code != 200:
        print(f"❌ Failed to update diagram: {update_response.status_code}")
        return False

    print("✓ Created version 2")

    # Step 4: Get versions list
    print("\n4. Getting versions list...")
    versions_response = requests.get(
        f"{DIAGRAM_SERVICE}/{diagram_id}/versions",
        headers=headers
    )

    if versions_response.status_code != 200:
        print(f"❌ Failed to get versions: {versions_response.status_code}")
        return False

    versions = versions_response.json()["versions"]
    print(f"✓ Found {len(versions)} versions")

    if len(versions) < 2:
        print(f"❌ Expected at least 2 versions, got {len(versions)}")
        return False

    # Get version 2 (the one we just created)
    version_2 = [v for v in versions if v["version_number"] == 2][0]
    version_2_id = version_2["id"]
    print(f"✓ Selected version 2 (ID: {version_2_id})")

    # Step 5: Add comment to version
    print("\n5. Adding comment: 'Added caching layer'...")
    comment_response = requests.patch(
        f"{DIAGRAM_SERVICE}/{diagram_id}/versions/{version_2_id}/description",
        headers=headers,
        json={
            "description": "Added caching layer"
        }
    )

    if comment_response.status_code != 200:
        print(f"❌ Failed to add comment: {comment_response.status_code}")
        print(f"Response: {comment_response.text}")
        return False

    updated_version = comment_response.json()
    print(f"✓ Comment saved")

    # Step 6: Verify comment is shown
    print("\n6. Verifying comment shown...")

    if "description" not in updated_version:
        print("❌ Description field not in response")
        return False

    if updated_version["description"] != "Added caching layer":
        print(f"❌ Comment mismatch. Expected 'Added caching layer', got '{updated_version['description']}'")
        return False

    print(f"✓ Comment verified: '{updated_version['description']}'")

    # Step 7: Re-fetch versions to ensure comment persists
    print("\n7. Re-fetching versions to verify persistence...")
    versions_response2 = requests.get(
        f"{DIAGRAM_SERVICE}/{diagram_id}/versions",
        headers=headers
    )

    if versions_response2.status_code != 200:
        print(f"❌ Failed to re-fetch versions: {versions_response2.status_code}")
        return False

    versions2 = versions_response2.json()["versions"]
    version_2_refetch = [v for v in versions2 if v["version_number"] == 2][0]

    if version_2_refetch.get("description") != "Added caching layer":
        print(f"❌ Comment not persisted. Got: {version_2_refetch.get('description')}")
        return False

    print("✓ Comment persisted correctly")

    # Step 8: Verify helps understand changes
    print("\n8. Verifying comment helps understand changes...")
    # The comment should be visible in the version timeline
    # and help users understand what changed in this version

    if not version_2_refetch.get("description"):
        print("❌ No description to help understand changes")
        return False

    # Check that the description is meaningful and non-empty
    if len(version_2_refetch["description"].strip()) == 0:
        print("❌ Description is empty")
        return False

    print(f"✓ Comment helps understand changes: '{version_2_refetch['description']}'")

    # Step 9: Test updating the comment
    print("\n9. Testing comment update...")
    update_comment_response = requests.patch(
        f"{DIAGRAM_SERVICE}/{diagram_id}/versions/{version_2_id}/description",
        headers=headers,
        json={
            "description": "Added caching layer and optimized queries"
        }
    )

    if update_comment_response.status_code != 200:
        print(f"❌ Failed to update comment: {update_comment_response.status_code}")
        return False

    updated_comment = update_comment_response.json()
    if updated_comment["description"] != "Added caching layer and optimized queries":
        print(f"❌ Updated comment mismatch")
        return False

    print("✓ Comment updated successfully")

    # Step 10: Test removing the comment (set to null/empty)
    print("\n10. Testing comment removal...")
    remove_comment_response = requests.patch(
        f"{DIAGRAM_SERVICE}/{diagram_id}/versions/{version_2_id}/description",
        headers=headers,
        json={
            "description": None
        }
    )

    if remove_comment_response.status_code != 200:
        print(f"❌ Failed to remove comment: {remove_comment_response.status_code}")
        return False

    removed_comment = remove_comment_response.json()
    if removed_comment.get("description") is not None and removed_comment.get("description") != "":
        print(f"❌ Comment not removed. Got: {removed_comment.get('description')}")
        return False

    print("✓ Comment removed successfully")

    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED")
    print("="*60)
    print("\nFeature #473 Verification:")
    print("✓ Can select a version")
    print("✓ Can add comment 'Added caching layer'")
    print("✓ Comment saves successfully")
    print("✓ Comment shown in version details")
    print("✓ Comment helps understand changes")
    print("✓ Can update comments")
    print("✓ Can remove comments")

    return True

if __name__ == "__main__":
    try:
        success = test_version_comments()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
