#!/usr/bin/env python3
"""
Test Feature #476: Version history - Version search by date

Tests that users can search/filter versions by date range.
"""
import requests
import json
from datetime import datetime, timedelta

API_BASE = "http://localhost:8080/api/v1"

def test_version_date_search():
    """Test searching versions by date range."""
    print("=" * 60)
    print("Testing Feature #476: Version search by date")
    print("=" * 60)

    # Step 1: Register and login
    print("\n1. Setting up test user...")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    test_email = f"date_test_{timestamp}@example.com"
    test_password = "SecurePass123!"

    register_data = {
        "email": test_email,
        "password": test_password,
        "full_name": "Date Test User"
    }

    register_resp = requests.post(
        f"{API_BASE}/auth/register",
        json=register_data
    )

    if register_resp.status_code != 201:
        print(f"❌ Registration failed: {register_resp.status_code}")
        print(register_resp.text)
        return False

    print(f"✅ User registered: {test_email}")

    # Login
    login_data = {
        "username": test_email,
        "password": test_password
    }

    login_resp = requests.post(
        f"{API_BASE}/auth/login",
        data=login_data
    )

    if login_resp.status_code != 200:
        print(f"❌ Login failed: {login_resp.status_code}")
        return False

    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ User logged in")

    # Step 2: Create a diagram
    print("\n2. Creating test diagram...")
    diagram_data = {
        "name": f"Date Test Diagram {timestamp}",
        "type": "canvas",
        "canvas_data": {"elements": []}
    }

    diagram_resp = requests.post(
        f"{API_BASE}/diagrams",
        headers=headers,
        json=diagram_data
    )

    if diagram_resp.status_code != 201:
        print(f"❌ Diagram creation failed: {diagram_resp.status_code}")
        return False

    diagram_id = diagram_resp.json()["id"]
    print(f"✅ Diagram created: {diagram_id}")

    # Step 3: Create multiple versions with different timestamps
    print("\n3. Creating versions with different dates...")
    version_ids = []

    # Create 3 versions
    for i in range(3):
        version_data = {
            "description": f"Version {i+1} created at different time",
            "label": f"v{i+1}"
        }

        version_resp = requests.post(
            f"{API_BASE}/diagrams/{diagram_id}/versions",
            headers=headers,
            json=version_data
        )

        if version_resp.status_code != 201:
            print(f"❌ Version {i+1} creation failed: {version_resp.status_code}")
            return False

        version_id = version_resp.json()["id"]
        version_ids.append(version_id)
        print(f"✅ Version {i+1} created: {version_id}")

    # Step 4: Get all versions to see their dates
    print("\n4. Fetching all versions to see dates...")
    all_versions_resp = requests.get(
        f"{API_BASE}/diagrams/{diagram_id}/versions",
        headers=headers
    )

    if all_versions_resp.status_code != 200:
        print(f"❌ Failed to fetch versions: {all_versions_resp.status_code}")
        return False

    all_versions = all_versions_resp.json()["versions"]
    total_versions = len(all_versions)
    print(f"✅ Total versions: {total_versions}")

    if total_versions == 0:
        print("❌ No versions found")
        return False

    # Get date range
    dates = [datetime.fromisoformat(v["created_at"].replace('Z', '+00:00')) for v in all_versions]
    oldest_date = min(dates)
    newest_date = max(dates)

    print(f"   Oldest version: {oldest_date.isoformat()}")
    print(f"   Newest version: {newest_date.isoformat()}")

    # Step 5: Test date filtering - get versions from today
    print("\n5. Testing date_from filter (today)...")
    today = datetime.now().date().isoformat()

    date_from_resp = requests.get(
        f"{API_BASE}/diagrams/{diagram_id}/versions",
        headers=headers,
        params={"date_from": today}
    )

    if date_from_resp.status_code != 200:
        print(f"❌ Date from filter failed: {date_from_resp.status_code}")
        return False

    filtered_versions = date_from_resp.json()["versions"]
    print(f"✅ Date from '{today}' returned {len(filtered_versions)} versions")

    # All versions should be from today
    if len(filtered_versions) != total_versions:
        print(f"⚠️  Expected {total_versions} versions from today, got {len(filtered_versions)}")

    # Step 6: Test date_to filter - get versions up to tomorrow
    print("\n6. Testing date_to filter (tomorrow)...")
    tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()

    date_to_resp = requests.get(
        f"{API_BASE}/diagrams/{diagram_id}/versions",
        headers=headers,
        params={"date_to": tomorrow}
    )

    if date_to_resp.status_code != 200:
        print(f"❌ Date to filter failed: {date_to_resp.status_code}")
        return False

    filtered_versions_to = date_to_resp.json()["versions"]
    print(f"✅ Date to '{tomorrow}' returned {len(filtered_versions_to)} versions")

    # Step 7: Test date range - get versions from yesterday to tomorrow
    print("\n7. Testing date range filter...")
    yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()

    date_range_resp = requests.get(
        f"{API_BASE}/diagrams/{diagram_id}/versions",
        headers=headers,
        params={
            "date_from": yesterday,
            "date_to": tomorrow
        }
    )

    if date_range_resp.status_code != 200:
        print(f"❌ Date range filter failed: {date_range_resp.status_code}")
        return False

    range_versions = date_range_resp.json()["versions"]
    print(f"✅ Date range '{yesterday}' to '{tomorrow}' returned {len(range_versions)} versions")

    # Should return all versions created today
    if len(range_versions) != total_versions:
        print(f"⚠️  Expected {total_versions} versions in range, got {len(range_versions)}")

    # Step 8: Test empty date range (future dates)
    print("\n8. Testing empty date range (future dates)...")
    future_start = (datetime.now() + timedelta(days=10)).date().isoformat()
    future_end = (datetime.now() + timedelta(days=20)).date().isoformat()

    future_resp = requests.get(
        f"{API_BASE}/diagrams/{diagram_id}/versions",
        headers=headers,
        params={
            "date_from": future_start,
            "date_to": future_end
        }
    )

    if future_resp.status_code != 200:
        print(f"❌ Future date range failed: {future_resp.status_code}")
        return False

    future_versions = future_resp.json()["versions"]
    print(f"✅ Future date range returned {len(future_versions)} versions")

    if len(future_versions) != 0:
        print(f"⚠️  Expected 0 versions in future date range, got {len(future_versions)}")
    else:
        print("✅ Correctly returned 0 versions for future date range")

    # Step 9: Test specific date search (as in feature description)
    print("\n9. Testing specific date search...")
    specific_date = datetime.now().date().isoformat()

    specific_resp = requests.get(
        f"{API_BASE}/diagrams/{diagram_id}/versions",
        headers=headers,
        params={
            "date_from": specific_date,
            "date_to": specific_date
        }
    )

    if specific_resp.status_code != 200:
        print(f"❌ Specific date search failed: {specific_resp.status_code}")
        return False

    specific_versions = specific_resp.json()["versions"]
    print(f"✅ Search for '{specific_date}' returned {len(specific_versions)} versions")

    # Verify versions are from the specified date
    for v in specific_versions:
        v_date = datetime.fromisoformat(v["created_at"].replace('Z', '+00:00')).date()
        if v_date != datetime.fromisoformat(specific_date).date():
            print(f"❌ Version {v['id']} has wrong date: {v_date}")
            return False

    print("✅ All versions match the specified date")

    print("\n" + "=" * 60)
    print("✅ Feature #476: Version date search - ALL TESTS PASSED")
    print("=" * 60)
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
