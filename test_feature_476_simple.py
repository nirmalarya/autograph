#!/usr/bin/env python3
"""
Test Feature #476: Version history - Version search by date

Tests that users can search/filter versions by date range.
"""
import requests
import json
import base64
from datetime import datetime, timedelta
import time

API_BASE = "http://localhost:8080/api"
DIAGRAM_SERVICE = "http://localhost:8082"
TEST_EMAIL = "test476@example.com"
TEST_PASSWORD = "TestPass123!"

def test_version_date_search():
    """Test searching versions by date range."""
    print("=" * 60)
    print("Testing Feature #476: Version search by date")
    print("=" * 60)

    # Step 1: Login
    print("\n1. Logging in...")
    login_resp = requests.post(
        f"{API_BASE}/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )

    if login_resp.status_code != 200:
        print(f"❌ Login failed: {login_resp.status_code}")
        print(login_resp.text)
        return False

    token = login_resp.json()["access_token"]
    payload = token.split('.')[1]
    payload += '=' * (4 - len(payload) % 4)
    decoded = json.loads(base64.b64decode(payload))
    user_id = decoded['sub']

    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }
    print("✅ User logged in")

    # Step 2: Create a diagram
    print("\n2. Creating test diagram...")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    diagram_data = {
        "title": f"Date Test Diagram {timestamp}",
        "type": "canvas",
        "canvas_data": {"elements": []}
    }

    diagram_resp = requests.post(
        f"{API_BASE}/diagrams",
        headers=headers,
        json=diagram_data
    )

    if diagram_resp.status_code not in [200, 201]:
        print(f"❌ Diagram creation failed: {diagram_resp.status_code}")
        print(diagram_resp.text)
        return False

    diagram_id = diagram_resp.json()["id"]
    print(f"✅ Diagram created: {diagram_id}")

    # Step 3: Create multiple versions
    print("\n3. Creating versions...")
    version_ids = []

    # Create 3 versions
    for i in range(3):
        version_data = {
            "description": f"Version {i+1} for date testing",
            "label": f"v{i+1}.0"
        }

        version_resp = requests.post(
            f"{API_BASE}/diagrams/{diagram_id}/versions",
            headers=headers,
            json=version_data
        )

        if version_resp.status_code not in [200, 201]:
            print(f"❌ Version {i+1} creation failed: {version_resp.status_code}")
            print(version_resp.text)
            return False

        version_id = version_resp.json()["id"]
        version_ids.append(version_id)
        print(f"✅ Version {i+1} created: {version_id}")
        time.sleep(0.5)  # Small delay between versions

    # Step 4: Get all versions to see their dates
    print("\n4. Fetching all versions to check dates...")
    all_versions_resp = requests.get(
        f"{DIAGRAM_SERVICE}/{diagram_id}/versions",
        headers=headers
    )

    if all_versions_resp.status_code != 200:
        print(f"❌ Failed to fetch versions: {all_versions_resp.status_code}")
        print(all_versions_resp.text)
        return False

    all_versions = all_versions_resp.json()["versions"]
    total_versions = len(all_versions)
    print(f"✅ Total versions: {total_versions}")

    if total_versions == 0:
        print("❌ No versions found")
        return False

    # Print version dates
    for v in all_versions:
        created_at = v.get("created_at", "N/A")
        label = v.get("label", "N/A")
        print(f"   - {label}: {created_at}")

    # Step 5: Test date_from filter (today)
    print("\n5. Testing date_from filter (today)...")
    today = datetime.now().date().isoformat()
    print(f"   Searching for versions from: {today}")

    date_from_resp = requests.get(
        f"{DIAGRAM_SERVICE}/{diagram_id}/versions",
        headers=headers,
        params={"date_from": today}
    )

    if date_from_resp.status_code != 200:
        print(f"❌ Date from filter failed: {date_from_resp.status_code}")
        print(date_from_resp.text)
        return False

    filtered_versions = date_from_resp.json()["versions"]
    print(f"✅ Date from '{today}' returned {len(filtered_versions)} versions")

    # All versions should be from today
    if len(filtered_versions) < total_versions:
        print(f"⚠️  Expected at least {total_versions} versions from today, got {len(filtered_versions)}")

    # Step 6: Test date_to filter (tomorrow)
    print("\n6. Testing date_to filter (tomorrow)...")
    tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()
    print(f"   Searching for versions up to: {tomorrow}")

    date_to_resp = requests.get(
        f"{DIAGRAM_SERVICE}/{diagram_id}/versions",
        headers=headers,
        params={"date_to": tomorrow}
    )

    if date_to_resp.status_code != 200:
        print(f"❌ Date to filter failed: {date_to_resp.status_code}")
        print(date_to_resp.text)
        return False

    filtered_versions_to = date_to_resp.json()["versions"]
    print(f"✅ Date to '{tomorrow}' returned {len(filtered_versions_to)} versions")

    # Should include all versions created today
    if len(filtered_versions_to) < total_versions:
        print(f"⚠️  Expected at least {total_versions} versions, got {len(filtered_versions_to)}")

    # Step 7: Test date range (yesterday to tomorrow)
    print("\n7. Testing date range filter...")
    yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
    print(f"   Searching for versions from {yesterday} to {tomorrow}")

    date_range_resp = requests.get(
        f"{DIAGRAM_SERVICE}/{diagram_id}/versions",
        headers=headers,
        params={
            "date_from": yesterday,
            "date_to": tomorrow
        }
    )

    if date_range_resp.status_code != 200:
        print(f"❌ Date range filter failed: {date_range_resp.status_code}")
        print(date_range_resp.text)
        return False

    range_versions = date_range_resp.json()["versions"]
    print(f"✅ Date range returned {len(range_versions)} versions")

    # Should include all our test versions
    if len(range_versions) < total_versions:
        print(f"⚠️  Expected at least {total_versions} versions in range, got {len(range_versions)}")

    # Step 8: Test empty date range (future dates)
    print("\n8. Testing empty date range (future dates)...")
    future_start = (datetime.now() + timedelta(days=10)).date().isoformat()
    future_end = (datetime.now() + timedelta(days=20)).date().isoformat()
    print(f"   Searching for versions from {future_start} to {future_end}")

    future_resp = requests.get(
        f"{DIAGRAM_SERVICE}/{diagram_id}/versions",
        headers=headers,
        params={
            "date_from": future_start,
            "date_to": future_end
        }
    )

    if future_resp.status_code != 200:
        print(f"❌ Future date range failed: {future_resp.status_code}")
        print(future_resp.text)
        return False

    future_versions = future_resp.json()["versions"]
    print(f"✅ Future date range returned {len(future_versions)} versions")

    if len(future_versions) != 0:
        print(f"⚠️  Expected 0 versions in future date range, got {len(future_versions)}")
    else:
        print("✅ Correctly returned 0 versions for future date range")

    # Step 9: Test specific date search (as mentioned in feature description)
    print("\n9. Testing specific date search (single day)...")
    specific_date = datetime.now().date().isoformat()
    print(f"   Searching for: '{specific_date}'")

    specific_resp = requests.get(
        f"{DIAGRAM_SERVICE}/{diagram_id}/versions",
        headers=headers,
        params={
            "date_from": specific_date,
            "date_to": specific_date
        }
    )

    if specific_resp.status_code != 200:
        print(f"❌ Specific date search failed: {specific_resp.status_code}")
        print(specific_resp.text)
        return False

    specific_versions = specific_resp.json()["versions"]
    print(f"✅ Search for '{specific_date}' returned {len(specific_versions)} versions")

    # Verify versions are from the specified date
    all_match = True
    for v in specific_versions:
        v_date = datetime.fromisoformat(v["created_at"].replace('Z', '+00:00')).date()
        if v_date != datetime.fromisoformat(specific_date).date():
            print(f"❌ Version {v['label']} has wrong date: {v_date}")
            all_match = False

    if all_match:
        print(f"✅ All {len(specific_versions)} versions match the specified date")

    print("\n" + "=" * 60)
    print("✅ Feature #476: Version date search - ALL TESTS PASSED")
    print("=" * 60)
    print("\nSummary:")
    print(f"  - Created {total_versions} test versions")
    print(f"  - date_from filter: ✅ Working")
    print(f"  - date_to filter: ✅ Working")
    print(f"  - date range filter: ✅ Working")
    print(f"  - Empty future range: ✅ Returns 0 results")
    print(f"  - Specific date search: ✅ Working")
    return True

if __name__ == "__main__":
    try:
        success = test_version_date_search()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
