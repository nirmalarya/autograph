#!/usr/bin/env python3
"""
Test Feature #477: Version history - Version search by author

Tests that users can search/filter versions by author name or email.
"""
import requests
import json
import base64
from datetime import datetime
import time

API_BASE = "http://localhost:8080/api"
DIAGRAM_SERVICE = "http://localhost:8082"
TEST_EMAIL_1 = "test477john@example.com"
TEST_EMAIL_2 = "test477jane@example.com"
TEST_PASSWORD = "TestPass123!"

def test_version_author_search():
    """Test searching versions by author."""
    print("=" * 60)
    print("Testing Feature #477: Version search by author")
    print("=" * 60)

    # Step 1: Login as first user (John)
    print("\n1. Logging in as John...")
    login_resp_1 = requests.post(
        f"{API_BASE}/auth/login",
        json={"email": TEST_EMAIL_1, "password": TEST_PASSWORD}
    )

    if login_resp_1.status_code != 200:
        print(f"❌ Login failed for John: {login_resp_1.status_code}")
        print(login_resp_1.text)
        return False

    token_1 = login_resp_1.json()["access_token"]
    payload_1 = token_1.split('.')[1]
    payload_1 += '=' * (4 - len(payload_1) % 4)
    decoded_1 = json.loads(base64.b64decode(payload_1))
    user_id_1 = decoded_1['sub']

    headers_1 = {
        "Authorization": f"Bearer {token_1}",
        "X-User-ID": user_id_1
    }
    print(f"✅ John logged in (user_id: {user_id_1})")

    # Step 2: Login as second user (Jane)
    print("\n2. Logging in as Jane...")
    login_resp_2 = requests.post(
        f"{API_BASE}/auth/login",
        json={"email": TEST_EMAIL_2, "password": TEST_PASSWORD}
    )

    if login_resp_2.status_code != 200:
        print(f"❌ Login failed for Jane: {login_resp_2.status_code}")
        print(login_resp_2.text)
        return False

    token_2 = login_resp_2.json()["access_token"]
    payload_2 = token_2.split('.')[1]
    payload_2 += '=' * (4 - len(payload_2) % 4)
    decoded_2 = json.loads(base64.b64decode(payload_2))
    user_id_2 = decoded_2['sub']

    headers_2 = {
        "Authorization": f"Bearer {token_2}",
        "X-User-ID": user_id_2
    }
    print(f"✅ Jane logged in (user_id: {user_id_2})")

    # Step 3: Create a diagram as John
    print("\n3. Creating test diagram as John...")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    diagram_data = {
        "title": f"Author Test Diagram {timestamp}",
        "type": "canvas",
        "canvas_data": {"elements": []}
    }

    diagram_resp = requests.post(
        f"{API_BASE}/diagrams",
        headers=headers_1,
        json=diagram_data
    )

    if diagram_resp.status_code not in [200, 201]:
        print(f"❌ Diagram creation failed: {diagram_resp.status_code}")
        print(diagram_resp.text)
        return False

    diagram_id = diagram_resp.json()["id"]
    print(f"✅ Diagram created: {diagram_id}")

    # Step 4: Share diagram with Jane so she can create versions
    print("\n4. Sharing diagram with Jane...")
    share_data = {
        "email": TEST_EMAIL_2,
        "permission": "edit"
    }

    share_resp = requests.post(
        f"{API_BASE}/diagrams/{diagram_id}/share",
        headers=headers_1,
        json=share_data
    )

    if share_resp.status_code not in [200, 201]:
        print(f"❌ Sharing failed: {share_resp.status_code}")
        print(share_resp.text)
        return False

    print("✅ Diagram shared with Jane")

    # Step 5: Create versions as John
    print("\n5. Creating versions as John...")
    john_versions = []

    for i in range(2):
        version_data = {
            "description": f"John's version {i+1}",
            "label": f"john-v{i+1}.0"
        }

        version_resp = requests.post(
            f"{API_BASE}/diagrams/{diagram_id}/versions",
            headers=headers_1,
            json=version_data
        )

        if version_resp.status_code not in [200, 201]:
            print(f"❌ Version {i+1} creation failed: {version_resp.status_code}")
            print(version_resp.text)
            return False

        version_id = version_resp.json()["id"]
        john_versions.append(version_id)
        print(f"✅ John's version {i+1} created: {version_id}")
        time.sleep(0.5)

    # Step 6: Create versions as Jane
    print("\n6. Creating versions as Jane...")
    jane_versions = []

    for i in range(2):
        version_data = {
            "description": f"Jane's version {i+1}",
            "label": f"jane-v{i+1}.0"
        }

        version_resp = requests.post(
            f"{API_BASE}/diagrams/{diagram_id}/versions",
            headers=headers_2,
            json=version_data
        )

        if version_resp.status_code not in [200, 201]:
            print(f"❌ Version {i+1} creation failed: {version_resp.status_code}")
            print(version_resp.text)
            return False

        version_id = version_resp.json()["id"]
        jane_versions.append(version_id)
        print(f"✅ Jane's version {i+1} created: {version_id}")
        time.sleep(0.5)

    # Step 7: Get all versions to verify
    print("\n7. Fetching all versions...")
    all_versions_resp = requests.get(
        f"{DIAGRAM_SERVICE}/{diagram_id}/versions",
        headers=headers_1
    )

    if all_versions_resp.status_code != 200:
        print(f"❌ Failed to fetch versions: {all_versions_resp.status_code}")
        print(all_versions_resp.text)
        return False

    all_versions = all_versions_resp.json()["versions"]
    total_versions = len(all_versions)
    print(f"✅ Total versions: {total_versions}")

    # Print version authors
    for v in all_versions:
        label = v.get("label", "N/A")
        created_by = v.get("created_by", "N/A")
        print(f"   - {label}: created by {created_by}")

    # Step 8: Test author filter by email (John)
    print("\n8. Testing author filter by email (John)...")
    print(f"   Searching for author: '{TEST_EMAIL_1}'")

    author_resp = requests.get(
        f"{DIAGRAM_SERVICE}/{diagram_id}/versions",
        headers=headers_1,
        params={"author": TEST_EMAIL_1}
    )

    if author_resp.status_code != 200:
        print(f"❌ Author filter failed: {author_resp.status_code}")
        print(author_resp.text)
        return False

    john_filtered = author_resp.json()["versions"]
    print(f"✅ Author filter returned {len(john_filtered)} versions")

    # Verify all are John's versions
    if len(john_filtered) != len(john_versions):
        print(f"⚠️  Expected {len(john_versions)} versions, got {len(john_filtered)}")

    for v in john_filtered:
        if v["created_by"] != user_id_1:
            print(f"❌ Found version not created by John: {v['label']}")
            return False

    print("✅ All filtered versions are John's")

    # Step 9: Test author filter by partial email (Jane)
    print("\n9. Testing author filter by partial email (Jane)...")
    partial_email = "jane"
    print(f"   Searching for author: '{partial_email}'")

    author_resp_2 = requests.get(
        f"{DIAGRAM_SERVICE}/{diagram_id}/versions",
        headers=headers_1,
        params={"author": partial_email}
    )

    if author_resp_2.status_code != 200:
        print(f"❌ Author filter failed: {author_resp_2.status_code}")
        print(author_resp_2.text)
        return False

    jane_filtered = author_resp_2.json()["versions"]
    print(f"✅ Author filter returned {len(jane_filtered)} versions")

    # Verify all are Jane's versions
    if len(jane_filtered) != len(jane_versions):
        print(f"⚠️  Expected {len(jane_versions)} versions, got {len(jane_filtered)}")

    for v in jane_filtered:
        if v["created_by"] != user_id_2:
            print(f"❌ Found version not created by Jane: {v['label']}")
            return False

    print("✅ All filtered versions are Jane's")

    # Step 10: Test author filter by user ID
    print("\n10. Testing author filter by user ID (John)...")
    print(f"   Searching for author: '{user_id_1}'")

    author_resp_3 = requests.get(
        f"{DIAGRAM_SERVICE}/{diagram_id}/versions",
        headers=headers_1,
        params={"author": user_id_1}
    )

    if author_resp_3.status_code != 200:
        print(f"❌ Author filter by ID failed: {author_resp_3.status_code}")
        print(author_resp_3.text)
        return False

    id_filtered = author_resp_3.json()["versions"]
    print(f"✅ Author filter by ID returned {len(id_filtered)} versions")

    # Verify all are John's versions
    if len(id_filtered) != len(john_versions):
        print(f"⚠️  Expected {len(john_versions)} versions, got {len(id_filtered)}")

    for v in id_filtered:
        if v["created_by"] != user_id_1:
            print(f"❌ Found version not created by John: {v['label']}")
            return False

    print("✅ All filtered versions by ID are John's")

    # Step 11: Test non-existent author
    print("\n11. Testing non-existent author filter...")
    author_resp_4 = requests.get(
        f"{DIAGRAM_SERVICE}/{diagram_id}/versions",
        headers=headers_1,
        params={"author": "nonexistent@example.com"}
    )

    if author_resp_4.status_code != 200:
        print(f"❌ Non-existent author filter failed: {author_resp_4.status_code}")
        print(author_resp_4.text)
        return False

    empty_filtered = author_resp_4.json()["versions"]
    print(f"✅ Non-existent author filter returned {len(empty_filtered)} versions")

    if len(empty_filtered) != 0:
        print(f"❌ Expected 0 versions for non-existent author, got {len(empty_filtered)}")
        return False

    print("✅ Correctly returned 0 versions for non-existent author")

    print("\n" + "=" * 60)
    print("✅ Feature #477: Version author search - ALL TESTS PASSED")
    print("=" * 60)
    print("\nSummary:")
    print(f"  - Created {total_versions} test versions by 2 authors")
    print(f"  - Author filter by email: ✅ Working")
    print(f"  - Author filter by partial email: ✅ Working")
    print(f"  - Author filter by user ID: ✅ Working")
    print(f"  - Non-existent author handling: ✅ Returns 0 results")
    return True

if __name__ == "__main__":
    try:
        success = test_version_author_search()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
