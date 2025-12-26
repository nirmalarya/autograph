#!/usr/bin/env python3
"""
Feature 459: Version history: Version snapshots: full note_content per version

Test that each version stores and returns the full note_content that existed
at that point in time.

Steps:
1. Create v1 with text A
2. Edit to v2 with text B
3. View v1 - verify text A
4. View v2 - verify text B
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8080"
AUTH_BASE = "http://localhost:8085"
DIAGRAM_SERVICE_URL = "http://localhost:8082"

def test_note_version_snapshots():
    """Test that note_content is fully snapshotted per version."""

    print("\n" + "="*80)
    print("Feature 459: Version snapshots - full note_content per version")
    print("="*80)

    # Test user credentials
    email = "test459@example.com"
    password = "SecurePass123!"

    # Step 1: Register and login
    print("\n1. Creating test user and logging in...")
    register_response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Test User 459"
        }
    )

    if register_response.status_code not in [200, 201]:
        # User might already exist, try login
        print("   User already exists, logging in...")

    login_response = requests.post(
        f"{AUTH_BASE}/login",
        json={
            "email": email,
            "password": password
        }
    )

    assert login_response.status_code == 200, f"Login failed: {login_response.status_code}"
    login_data = login_response.json()
    token = login_data["access_token"]

    # Decode JWT to get user_id
    import base64
    payload = token.split('.')[1]
    # Add padding if needed
    payload += '=' * (4 - len(payload) % 4)
    decoded = json.loads(base64.b64decode(payload))
    user_id = decoded["sub"]

    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }

    print(f"   ✓ Logged in as user: {user_id}")

    # Step 2: Create a note diagram with version 1 text
    print("\n2. Creating note diagram with version 1 text...")
    text_v1 = "This is the original note content for version 1.\nIt has multiple lines.\nAnd some details."

    create_response = requests.post(
        f"{BASE_URL}/api/diagrams",
        headers=headers,
        json={
            "title": "Note Version Test",
            "type": "note",
            "note_content": text_v1
        }
    )

    assert create_response.status_code in [200, 201], f"Create failed: {create_response.status_code} - {create_response.text}"
    diagram = create_response.json()
    diagram_id = diagram["id"]

    print(f"   ✓ Created note diagram: {diagram_id}")
    print(f"   ✓ V1 text: '{text_v1[:50]}...'")

    # Step 3: Manually create version 1
    print("\n3. Creating manual version snapshot for v1...")
    v1_create_response = requests.post(
        f"{BASE_URL}/api/diagrams/{diagram_id}/versions",
        headers=headers,
        json={
            "description": "Version 1 snapshot"
        }
    )

    assert v1_create_response.status_code in [200, 201], f"Create v1 failed: {v1_create_response.status_code}"
    print(f"   ✓ Created version 1 snapshot")

    # Step 4: Get versions - should have v1
    print("\n4. Checking version 1 was created...")
    versions_response = requests.get(
        f"{BASE_URL}/api/diagrams/{diagram_id}/versions",
        headers=headers
    )

    assert versions_response.status_code == 200, f"Get versions failed: {versions_response.status_code}"
    versions_data = versions_response.json()
    versions = versions_data["versions"]

    assert len(versions) >= 1, f"Expected at least 1 version, got {len(versions)}"
    v1 = versions[0]
    v1_id = v1["id"]

    print(f"   ✓ Version 1 created: {v1_id} (version_number: {v1['version_number']})")

    # Step 5: Update note to version 2 text
    print("\n5. Updating note to version 2 text...")
    text_v2 = "This is COMPLETELY DIFFERENT text for version 2.\nThe old content is gone.\nNew content here!"

    update_response = requests.put(
        f"{BASE_URL}/api/diagrams/{diagram_id}",
        headers=headers,
        json={
            "note_content": text_v2
        }
    )

    assert update_response.status_code == 200, f"Update failed: {update_response.status_code} - {update_response.text}"

    print(f"   ✓ Updated note content")
    print(f"   ✓ V2 text: '{text_v2[:50]}...'")

    # Step 6: Manually create version 2
    print("\n6. Creating manual version snapshot for v2...")
    v2_create_response = requests.post(
        f"{BASE_URL}/api/diagrams/{diagram_id}/versions",
        headers=headers,
        json={
            "description": "Version 2 snapshot"
        }
    )

    assert v2_create_response.status_code in [200, 201], f"Create v2 failed: {v2_create_response.status_code}"
    print(f"   ✓ Created version 2 snapshot")

    # Step 7: Get versions - should now have v2
    print("\n7. Checking version 2 was created...")
    versions_response = requests.get(
        f"{BASE_URL}/api/diagrams/{diagram_id}/versions",
        headers=headers
    )

    assert versions_response.status_code == 200, f"Get versions failed: {versions_response.status_code}"
    versions_data = versions_response.json()
    versions = versions_data["versions"]

    assert len(versions) >= 2, f"Expected at least 2 versions, got {len(versions)}"
    v2 = versions[1] if len(versions) > 1 else versions[0]
    v2_id = v2["id"]

    print(f"   ✓ Version 2 created: {v2_id} (version_number: {v2['version_number']})")

    # Step 8: View version 1 - verify it has the ORIGINAL text
    print("\n8. Viewing version 1 - should have original text...")
    v1_response = requests.get(
        f"{BASE_URL}/api/diagrams/{diagram_id}/versions/{v1_id}",
        headers=headers,
        params={"include_content": "true"}
    )

    assert v1_response.status_code == 200, f"Get v1 failed: {v1_response.status_code}"
    v1_data = v1_response.json()
    v1_content = v1_data.get("note_content", "")

    print(f"   V1 note_content: '{v1_content[:80]}...'")
    assert v1_content == text_v1, f"V1 content mismatch!\nExpected: {text_v1}\nGot: {v1_content}"
    print(f"   ✓ Version 1 has correct original text!")

    # Step 9: View version 2 - verify it has the UPDATED text
    print("\n9. Viewing version 2 - should have updated text...")
    v2_response = requests.get(
        f"{BASE_URL}/api/diagrams/{diagram_id}/versions/{v2_id}",
        headers=headers,
        params={"include_content": "true"}
    )

    assert v2_response.status_code == 200, f"Get v2 failed: {v2_response.status_code}"
    v2_data = v2_response.json()
    v2_content = v2_data.get("note_content", "")

    print(f"   V2 note_content: '{v2_content[:80]}...'")
    assert v2_content == text_v2, f"V2 content mismatch!\nExpected: {text_v2}\nGot: {v2_content}"
    print(f"   ✓ Version 2 has correct updated text!")

    # Step 10: Verify current diagram has v2 text
    print("\n10. Verifying current diagram has latest text...")
    current_response = requests.get(
        f"{BASE_URL}/api/diagrams/{diagram_id}",
        headers=headers
    )

    assert current_response.status_code == 200, f"Get diagram failed: {current_response.status_code}"
    current_data = current_response.json()
    current_content = current_data.get("note_content", "")

    assert current_content == text_v2, f"Current content should match v2"
    print(f"   ✓ Current diagram has v2 text (latest)")

    # Summary
    print("\n" + "="*80)
    print("FEATURE 459: PASSING ✅")
    print("="*80)
    print("\nVerified:")
    print("✓ Version 1 stores complete snapshot of original note_content")
    print("✓ Version 2 stores complete snapshot of updated note_content")
    print("✓ Each version is independent (v1 unchanged when v2 created)")
    print("✓ Viewing v1 returns original text")
    print("✓ Viewing v2 returns updated text")
    print("✓ Current diagram matches latest version")
    print("\nImplementation:")
    print("- Version model has note_content field (Text column)")
    print("- create_version_snapshot() copies full note_content from file")
    print("- get_version_content() returns stored note_content")
    print("- GET /diagrams/{id}/versions/{version_id} includes note_content")
    print("- Full snapshots ensure version history integrity")

    return True

if __name__ == "__main__":
    try:
        success = test_note_version_snapshots()
        if success:
            print("\n✅ All tests passed!")
            exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
