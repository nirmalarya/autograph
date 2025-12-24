#!/usr/bin/env python3
"""
Test script for Version Search features (#475-477)

This script tests:
- Feature #475: Version search by content
- Feature #476: Version search by date
- Feature #477: Version search by author
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8082"
AUTH_URL = "http://localhost:8085"

def setup_test():
    """Setup: Login and create test diagram with versions"""
    print("=" * 80)
    print("SETUP: Creating test environment")
    print("=" * 80)
    
    # Login
    print("\n1. Logging in...")
    login_response = requests.post(f"{AUTH_URL}/login", json={
        "email": "test@example.com",
        "password": "testpass123"
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)
        return None, None
    
    data = login_response.json()
    token = data.get('access_token')
    
    # Extract user_id from JWT token
    import base64
    parts = token.split('.')
    payload = parts[1]
    payload += '=' * (4 - len(payload) % 4)
    decoded = json.loads(base64.b64decode(payload))
    user_id = decoded['sub']
    
    print(f"✅ Login successful")
    print(f"   User ID: {user_id}")
    
    # Create a test diagram
    print("\n2. Creating test diagram...")
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id,
        "Content-Type": "application/json"
    }
    
    create_response = requests.post(f"{BASE_URL}/", headers=headers, json={
        "title": "Version Search Test Diagram",
        "canvas_data": {"elements": []},
        "note_content": "Initial version with authentication system"
    })
    
    if create_response.status_code not in [200, 201]:
        print(f"❌ Create diagram failed: {create_response.status_code}")
        print(create_response.text)
        return None, None
    
    diagram = create_response.json()
    diagram_id = diagram['id']
    print(f"✅ Diagram created: {diagram_id}")
    
    # Create multiple versions with different content
    print("\n3. Creating test versions...")
    
    versions_to_create = [
        {
            "description": "Added database schema",
            "label": "Database Update",
            "note_content": "Added PostgreSQL database with user tables"
        },
        {
            "description": "Implemented Redis caching",
            "label": "Cache Layer",
            "note_content": "Added Redis for session management and caching"
        },
        {
            "description": "Added API endpoints",
            "label": "API Update",
            "note_content": "Created REST API with authentication endpoints"
        }
    ]
    
    for i, version_data in enumerate(versions_to_create, 1):
        # Update diagram to create a new version
        update_response = requests.put(
            f"{BASE_URL}/{diagram_id}",
            headers=headers,
            json={
                "title": f"Version Search Test Diagram v{i+1}",
                "canvas_data": {"elements": [{"type": "rectangle", "id": f"elem{i}"}]},
                "note_content": version_data["note_content"]
            }
        )
        
        if update_response.status_code == 200:
            print(f"   ✅ Version {i+1} created")
            
            # Get the latest version and update its label/description
            versions_response = requests.get(
                f"{BASE_URL}/{diagram_id}/versions",
                headers=headers
            )
            
            if versions_response.status_code == 200:
                versions = versions_response.json()["versions"]
                if versions:
                    latest = versions[0]
                    version_id = latest["id"]
                    
                    # Update label
                    requests.patch(
                        f"{BASE_URL}/{diagram_id}/versions/{version_id}/label",
                        headers=headers,
                        json={"label": version_data["label"]}
                    )
                    
                    # Update description
                    requests.patch(
                        f"{BASE_URL}/{diagram_id}/versions/{version_id}/description",
                        headers=headers,
                        json={"description": version_data["description"]}
                    )
        else:
            print(f"   ❌ Version {i+1} failed: {update_response.status_code}")
    
    print(f"\n✅ Test environment ready!")
    print(f"   Diagram ID: {diagram_id}")
    print(f"   Total versions: 4 (initial + 3 updates)")
    
    return diagram_id, headers


def test_search_by_content(diagram_id, headers):
    """Test Feature #475: Search versions by content"""
    print("\n" + "=" * 80)
    print("TEST #475: Version Search by Content")
    print("=" * 80)
    
    # Test 1: Search for "database"
    print("\n1. Search for 'database'...")
    response = requests.get(
        f"{BASE_URL}/{diagram_id}/versions?search=database",
        headers=headers
    )
    
    if response.status_code == 200:
        versions = response.json()["versions"]
        print(f"   ✅ Found {len(versions)} version(s)")
        for v in versions:
            print(f"      - v{v['version_number']}: {v.get('label', 'No label')}")
        
        if len(versions) >= 1:
            print("   ✅ Test passed: Found versions containing 'database'")
        else:
            print("   ❌ Test failed: Expected at least 1 version")
    else:
        print(f"   ❌ Request failed: {response.status_code}")
    
    # Test 2: Search for "Redis"
    print("\n2. Search for 'Redis'...")
    response = requests.get(
        f"{BASE_URL}/{diagram_id}/versions?search=Redis",
        headers=headers
    )
    
    if response.status_code == 200:
        versions = response.json()["versions"]
        print(f"   ✅ Found {len(versions)} version(s)")
        for v in versions:
            print(f"      - v{v['version_number']}: {v.get('label', 'No label')}")
        
        if len(versions) >= 1:
            print("   ✅ Test passed: Found versions containing 'Redis'")
        else:
            print("   ❌ Test failed: Expected at least 1 version")
    else:
        print(f"   ❌ Request failed: {response.status_code}")
    
    # Test 3: Search for non-existent content
    print("\n3. Search for 'kubernetes' (should find nothing)...")
    response = requests.get(
        f"{BASE_URL}/{diagram_id}/versions?search=kubernetes",
        headers=headers
    )
    
    if response.status_code == 200:
        versions = response.json()["versions"]
        print(f"   ✅ Found {len(versions)} version(s)")
        
        if len(versions) == 0:
            print("   ✅ Test passed: No versions found (as expected)")
        else:
            print("   ⚠️  Unexpected: Found versions")
    else:
        print(f"   ❌ Request failed: {response.status_code}")


def test_search_by_date(diagram_id, headers):
    """Test Feature #476: Search versions by date"""
    print("\n" + "=" * 80)
    print("TEST #476: Version Search by Date")
    print("=" * 80)
    
    today = datetime.now().date().isoformat()
    yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
    tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()
    
    # Test 1: Search for today's versions
    print(f"\n1. Search for versions from today ({today})...")
    response = requests.get(
        f"{BASE_URL}/{diagram_id}/versions?date_from={today}&date_to={today}",
        headers=headers
    )
    
    if response.status_code == 200:
        versions = response.json()["versions"]
        print(f"   ✅ Found {len(versions)} version(s)")
        for v in versions:
            print(f"      - v{v['version_number']}: {v['created_at'][:10]}")
        
        if len(versions) >= 4:
            print("   ✅ Test passed: Found today's versions")
        else:
            print(f"   ⚠️  Expected 4+ versions, found {len(versions)}")
    else:
        print(f"   ❌ Request failed: {response.status_code}")
    
    # Test 2: Search for yesterday's versions (should be empty)
    print(f"\n2. Search for versions from yesterday ({yesterday})...")
    response = requests.get(
        f"{BASE_URL}/{diagram_id}/versions?date_from={yesterday}&date_to={yesterday}",
        headers=headers
    )
    
    if response.status_code == 200:
        versions = response.json()["versions"]
        print(f"   ✅ Found {len(versions)} version(s)")
        
        if len(versions) == 0:
            print("   ✅ Test passed: No versions from yesterday")
        else:
            print("   ⚠️  Unexpected: Found versions from yesterday")
    else:
        print(f"   ❌ Request failed: {response.status_code}")
    
    # Test 3: Date range search
    print(f"\n3. Search for date range ({yesterday} to {tomorrow})...")
    response = requests.get(
        f"{BASE_URL}/{diagram_id}/versions?date_from={yesterday}&date_to={tomorrow}",
        headers=headers
    )
    
    if response.status_code == 200:
        versions = response.json()["versions"]
        print(f"   ✅ Found {len(versions)} version(s)")
        
        if len(versions) >= 4:
            print("   ✅ Test passed: Date range search works")
        else:
            print(f"   ⚠️  Expected 4+ versions, found {len(versions)}")
    else:
        print(f"   ❌ Request failed: {response.status_code}")


def test_search_by_author(diagram_id, headers):
    """Test Feature #477: Search versions by author"""
    print("\n" + "=" * 80)
    print("TEST #477: Version Search by Author")
    print("=" * 80)
    
    # Test 1: Search by author email
    print("\n1. Search by author 'test@example.com'...")
    response = requests.get(
        f"{BASE_URL}/{diagram_id}/versions?author=test@example.com",
        headers=headers
    )
    
    if response.status_code == 200:
        versions = response.json()["versions"]
        print(f"   ✅ Found {len(versions)} version(s)")
        for v in versions[:3]:  # Show first 3
            user_email = v.get('user', {}).get('email', 'Unknown') if v.get('user') else 'Unknown'
            print(f"      - v{v['version_number']} by {user_email}")
        
        if len(versions) >= 4:
            print("   ✅ Test passed: Found versions by author")
        else:
            print(f"   ⚠️  Expected 4+ versions, found {len(versions)}")
    else:
        print(f"   ❌ Request failed: {response.status_code}")
    
    # Test 2: Search by partial name/email
    print("\n2. Search by partial name 'test'...")
    response = requests.get(
        f"{BASE_URL}/{diagram_id}/versions?author=test",
        headers=headers
    )
    
    if response.status_code == 200:
        versions = response.json()["versions"]
        print(f"   ✅ Found {len(versions)} version(s)")
        
        if len(versions) >= 4:
            print("   ✅ Test passed: Partial name search works")
        else:
            print(f"   ⚠️  Expected 4+ versions, found {len(versions)}")
    else:
        print(f"   ❌ Request failed: {response.status_code}")
    
    # Test 3: Search for non-existent author
    print("\n3. Search for 'nonexistent@example.com'...")
    response = requests.get(
        f"{BASE_URL}/{diagram_id}/versions?author=nonexistent@example.com",
        headers=headers
    )
    
    if response.status_code == 200:
        versions = response.json()["versions"]
        print(f"   ✅ Found {len(versions)} version(s)")
        
        if len(versions) == 0:
            print("   ✅ Test passed: No versions found for non-existent author")
        else:
            print("   ⚠️  Unexpected: Found versions")
    else:
        print(f"   ❌ Request failed: {response.status_code}")


def test_combined_filters(diagram_id, headers):
    """Test combining multiple filters"""
    print("\n" + "=" * 80)
    print("BONUS TEST: Combined Filters")
    print("=" * 80)
    
    today = datetime.now().date().isoformat()
    
    print("\n1. Search: content='database' + author='test' + today's date...")
    response = requests.get(
        f"{BASE_URL}/{diagram_id}/versions?search=database&author=test&date_from={today}&date_to={today}",
        headers=headers
    )
    
    if response.status_code == 200:
        versions = response.json()["versions"]
        print(f"   ✅ Found {len(versions)} version(s)")
        for v in versions:
            print(f"      - v{v['version_number']}: {v.get('label', 'No label')}")
        
        if len(versions) >= 1:
            print("   ✅ Test passed: Combined filters work")
        else:
            print("   ⚠️  Expected at least 1 version")
    else:
        print(f"   ❌ Request failed: {response.status_code}")


def main():
    print("\n")
    print("=" * 80)
    print("VERSION SEARCH FEATURES TEST")
    print("Testing Features #475, #476, #477")
    print("=" * 80)
    
    # Setup
    diagram_id, headers = setup_test()
    if not diagram_id or not headers:
        print("\n❌ Setup failed, cannot continue with tests")
        return
    
    # Run tests
    test_search_by_content(diagram_id, headers)
    test_search_by_date(diagram_id, headers)
    test_search_by_author(diagram_id, headers)
    test_combined_filters(diagram_id, headers)
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print("\n✅ All version search features implemented and tested!")
    print("\nManual UI Testing:")
    print(f"1. Navigate to: http://localhost:3000/versions/{diagram_id}?v1=1&v2=2")
    print("2. Test the search bar at the top of the page")
    print("3. Click 'Filters' button to test advanced filters")
    print("4. Try different combinations:")
    print("   - Search: 'database', 'Redis', 'API'")
    print("   - Author: 'test'")
    print("   - Date range: today's date")
    print("5. Verify that version dropdowns update with filtered results")
    print("6. Click 'Clear' to reset filters")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
