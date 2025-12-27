#!/usr/bin/env python3
"""
Feature 584: Folder Permissions - Control Access
Tests adding users with view-only and edit permissions to folders.
"""

import requests
import json
import time

# Configuration
DIAGRAM_SERVICE_URL = "https://localhost:8082"
OWNER_USER_ID = "584-folder-owner"
VIEWER_USER_ID = "584-folder-viewer"
EDITOR_USER_ID = "584-folder-editor"

def test_folder_permissions():
    """Test folder permissions: add, list, verify, and remove."""

    print("=" * 80)
    print("Feature 584: Folder Permissions - Control Access")
    print("=" * 80)

    folder_id = None

    try:
        # Step 1: Create a test folder as owner
        print("\n[Step 1] Creating test folder as owner...")
        response = requests.post(
            f"{DIAGRAM_SERVICE_URL}/folders",
            json={"name": "Shared Project Folder"},
            headers={"X-User-ID": OWNER_USER_ID},
            verify=False
        )
        assert response.status_code == 201, f"Failed to create folder: {response.text}"
        folder_data = response.json()
        folder_id = folder_data["id"]
        print(f"✓ Created folder: {folder_id}")

        # Step 2: Add view-only permission for viewer user
        print("\n[Step 2] Adding view-only permission for viewer...")
        response = requests.post(
            f"{DIAGRAM_SERVICE_URL}/folders/{folder_id}/permissions",
            json={
                "user_id": VIEWER_USER_ID,
                "permission": "view"
            },
            headers={"X-User-ID": OWNER_USER_ID},
            verify=False
        )
        assert response.status_code == 201, f"Failed to add view permission: {response.text}"
        view_permission = response.json()
        print(f"✓ Added view permission: {view_permission}")

        # Step 3: Add edit permission for editor user
        print("\n[Step 3] Adding edit permission for editor...")
        response = requests.post(
            f"{DIAGRAM_SERVICE_URL}/folders/{folder_id}/permissions",
            json={
                "user_id": EDITOR_USER_ID,
                "permission": "edit"
            },
            headers={"X-User-ID": OWNER_USER_ID},
            verify=False
        )
        assert response.status_code == 201, f"Failed to add edit permission: {response.text}"
        edit_permission = response.json()
        print(f"✓ Added edit permission: {edit_permission}")

        # Step 4: List all permissions as owner
        print("\n[Step 4] Listing all permissions as owner...")
        response = requests.get(
            f"{DIAGRAM_SERVICE_URL}/folders/{folder_id}/permissions",
            headers={"X-User-ID": OWNER_USER_ID},
            verify=False
        )
        assert response.status_code == 200, f"Failed to list permissions: {response.text}"
        permissions_data = response.json()
        permissions = permissions_data["permissions"]
        print(f"✓ Found {len(permissions)} permission(s)")

        # Verify both permissions exist
        viewer_perm = next((p for p in permissions if p["user_id"] == VIEWER_USER_ID), None)
        editor_perm = next((p for p in permissions if p["user_id"] == EDITOR_USER_ID), None)

        assert viewer_perm is not None, "Viewer permission not found"
        assert viewer_perm["permission"] == "view", f"Expected 'view', got {viewer_perm['permission']}"
        print(f"  ✓ Viewer has 'view' permission")

        assert editor_perm is not None, "Editor permission not found"
        assert editor_perm["permission"] == "edit", f"Expected 'edit', got {editor_perm['permission']}"
        print(f"  ✓ Editor has 'edit' permission")

        # Step 5: Verify viewer can access folder (list permissions)
        print("\n[Step 5] Verifying viewer can access folder...")
        response = requests.get(
            f"{DIAGRAM_SERVICE_URL}/folders/{folder_id}/permissions",
            headers={"X-User-ID": VIEWER_USER_ID},
            verify=False
        )
        assert response.status_code == 200, f"Viewer cannot access folder: {response.text}"
        print(f"✓ Viewer can access folder")

        # Step 6: Verify viewer cannot edit (try to add permission - should fail)
        print("\n[Step 6] Verifying viewer cannot add permissions (view-only)...")
        response = requests.post(
            f"{DIAGRAM_SERVICE_URL}/folders/{folder_id}/permissions",
            json={
                "user_id": "some-other-user",
                "permission": "view"
            },
            headers={"X-User-ID": VIEWER_USER_ID},
            verify=False
        )
        # Viewer should NOT be able to add permissions (only owner can)
        assert response.status_code in [403, 404], f"Viewer should not be able to add permissions, got {response.status_code}"
        print(f"✓ Viewer cannot add permissions (view-only enforced)")

        # Step 7: Update viewer permission to edit
        print("\n[Step 7] Updating viewer permission to edit...")
        response = requests.post(
            f"{DIAGRAM_SERVICE_URL}/folders/{folder_id}/permissions",
            json={
                "user_id": VIEWER_USER_ID,
                "permission": "edit"
            },
            headers={"X-User-ID": OWNER_USER_ID},
            verify=False
        )
        assert response.status_code == 201, f"Failed to update permission: {response.text}"
        print(f"✓ Updated viewer permission to edit")

        # Verify update
        response = requests.get(
            f"{DIAGRAM_SERVICE_URL}/folders/{folder_id}/permissions",
            headers={"X-User-ID": OWNER_USER_ID},
            verify=False
        )
        assert response.status_code == 200
        permissions = response.json()["permissions"]
        viewer_perm = next((p for p in permissions if p["user_id"] == VIEWER_USER_ID), None)
        assert viewer_perm["permission"] == "edit", "Permission not updated"
        print(f"✓ Verified permission updated to edit")

        # Step 8: Remove editor permission
        print("\n[Step 8] Removing editor permission...")
        response = requests.delete(
            f"{DIAGRAM_SERVICE_URL}/folders/{folder_id}/permissions/{EDITOR_USER_ID}",
            headers={"X-User-ID": OWNER_USER_ID},
            verify=False
        )
        assert response.status_code == 200, f"Failed to remove permission: {response.text}"
        print(f"✓ Removed editor permission")

        # Verify removal
        response = requests.get(
            f"{DIAGRAM_SERVICE_URL}/folders/{folder_id}/permissions",
            headers={"X-User-ID": OWNER_USER_ID},
            verify=False
        )
        assert response.status_code == 200
        permissions = response.json()["permissions"]
        editor_perm = next((p for p in permissions if p["user_id"] == EDITOR_USER_ID), None)
        assert editor_perm is None, "Editor permission still exists"
        print(f"✓ Verified editor permission removed")

        # Step 9: Verify editor can no longer access folder
        print("\n[Step 9] Verifying editor can no longer access folder...")
        response = requests.get(
            f"{DIAGRAM_SERVICE_URL}/folders/{folder_id}/permissions",
            headers={"X-User-ID": EDITOR_USER_ID},
            verify=False
        )
        assert response.status_code in [403, 404], f"Editor should not have access, got {response.status_code}"
        print(f"✓ Editor cannot access folder after permission removed")

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED - Feature 584: Folder Permissions")
        print("=" * 80)
        print("\nVerified:")
        print("  ✓ Add user with view-only permission")
        print("  ✓ Add user with edit permission")
        print("  ✓ List all permissions")
        print("  ✓ User with view permission can view folder contents")
        print("  ✓ User with view permission cannot edit/add permissions")
        print("  ✓ Update permission from view to edit")
        print("  ✓ Remove user permission")
        print("  ✓ User cannot access after permission removed")

        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        if folder_id:
            print("\n[Cleanup] Deleting test folder...")
            try:
                response = requests.delete(
                    f"{DIAGRAM_SERVICE_URL}/folders/{folder_id}",
                    headers={"X-User-ID": OWNER_USER_ID},
                    verify=False
                )
                if response.status_code == 200:
                    print("✓ Cleanup successful")
            except Exception as e:
                print(f"⚠ Cleanup warning: {e}")

if __name__ == "__main__":
    # Suppress SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    success = test_folder_permissions()
    exit(0 if success else 1)
