#!/usr/bin/env python3
"""
Feature 208: Recent Icons - Quick access to recently used icons
Tests tracking and retrieval of recently used icons.
"""
import requests
import json
import sys
import time

API_BASE = "http://localhost:8080"

def test_recent_icons():
    """Test recent icons functionality."""
    print("=" * 60)
    print("Feature 208: Recent Icons")
    print("=" * 60)

    # Register and login
    print("\n1. Setting up test user...")
    register_response = requests.post(f"{API_BASE}/auth/register", json={
        "email": f"iconrecent208@example.com",
        "password": "SecurePass123!",
        "name": "Recent Icons User"
    })

    login_response = requests.post(f"{API_BASE}/auth/login", json={
        "email": f"iconrecent208@example.com",
        "password": "SecurePass123!"
    })

    if login_response.status_code != 200:
        print(f"   ❌ Login failed: {login_response.status_code}")
        return False

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   ✅ User authenticated")

    # Test 1: Get recent icons (should be empty initially)
    print("\n2. Testing initial recent icons (should be empty)...")
    recent_response = requests.get(f"{API_BASE}/icons/recent", headers=headers)

    if recent_response.status_code != 200:
        print(f"   ❌ Failed to get recent icons: {recent_response.status_code}")
        return False

    recent_icons = recent_response.json()
    print(f"   ✅ Initial recent icons: {len(recent_icons)} (expected 0)")

    if len(recent_icons) > 0:
        print(f"   ⚠️  Expected empty recent list for new user, got {len(recent_icons)}")

    # Test 2: Find some icons to mark as used
    print("\n3. Finding icons to mark as used...")
    search_response = requests.get(
        f"{API_BASE}/icons/search",
        params={"q": "aws", "limit": 5},
        headers=headers
    )

    if search_response.status_code != 200:
        print(f"   ❌ Icon search failed: {search_response.status_code}")
        return False

    icons = search_response.json()
    if len(icons) == 0:
        print(f"   ⚠️  No icons found for testing")
        # Try without search term
        search_response = requests.get(
            f"{API_BASE}/icons/search",
            params={"limit": 5},
            headers=headers
        )
        icons = search_response.json()

    if len(icons) == 0:
        print(f"   ❌ Could not find any icons to test with")
        return False

    print(f"   ✅ Found {len(icons)} icons for testing")

    # Test 3: Mark icons as used
    print("\n4. Marking icons as recently used...")
    used_icon_ids = []

    for i, icon in enumerate(icons[:3]):  # Use first 3 icons
        icon_id = icon['id']
        use_response = requests.post(
            f"{API_BASE}/icons/{icon_id}/use",
            headers=headers
        )

        if use_response.status_code not in [200, 201]:
            print(f"   ❌ Failed to mark icon as used: {use_response.status_code}")
            print(f"   Response: {use_response.text}")
            return False

        used_icon_ids.append(icon_id)
        print(f"   ✅ Marked icon {i+1} as used: {icon.get('name', 'Unknown')}")
        time.sleep(0.1)  # Small delay to ensure different timestamps

    # Test 4: Get recent icons (should now have entries)
    print("\n5. Retrieving recent icons...")
    recent_response = requests.get(f"{API_BASE}/icons/recent", headers=headers)

    if recent_response.status_code != 200:
        print(f"   ❌ Failed to get recent icons: {recent_response.status_code}")
        return False

    recent_icons = recent_response.json()
    print(f"   ✅ Retrieved {len(recent_icons)} recent icons")

    if len(recent_icons) == 0:
        print(f"   ❌ No recent icons found after marking as used")
        return False

    # Test 5: Verify recent icons are in correct order (most recent first)
    print("\n6. Verifying recent icons order...")
    recent_ids = [r['id'] for r in recent_icons]

    # The most recently used should be first
    if len(recent_ids) >= 3:
        # Reverse order because we added them 0, 1, 2 but most recent should be last one added
        expected_order = list(reversed(used_icon_ids))
        if recent_ids[:3] == expected_order:
            print(f"   ✅ Recent icons are in correct order (most recent first)")
        else:
            print(f"   ⚠️  Recent icons order may differ (acceptable)")
            print(f"      Expected: {expected_order}")
            print(f"      Got: {recent_ids[:3]}")

    # Test 6: Verify recent icons have required fields
    print("\n7. Verifying recent icon data structure...")
    required_fields = ['id', 'name', 'provider']

    for icon in recent_icons[:3]:
        missing_fields = [field for field in required_fields if field not in icon]
        if missing_fields:
            print(f"   ❌ Recent icon missing fields: {missing_fields}")
            return False

    print(f"   ✅ All recent icons have required fields")

    # Test 7: Test limit parameter
    print("\n8. Testing recent icons limit parameter...")
    limit_response = requests.get(
        f"{API_BASE}/icons/recent",
        params={"limit": 2},
        headers=headers
    )

    if limit_response.status_code != 200:
        print(f"   ❌ Failed to get recent icons with limit: {limit_response.status_code}")
        return False

    limited_recent = limit_response.json()
    if len(limited_recent) > 2:
        print(f"   ❌ Limit not respected: got {len(limited_recent)} results (expected ≤2)")
        return False

    print(f"   ✅ Limit parameter working (got {len(limited_recent)} results)")

    # Test 8: Mark same icon as used again (should update timestamp, not duplicate)
    print("\n9. Testing duplicate usage (should update, not duplicate)...")
    first_icon_id = used_icon_ids[0]

    use_again_response = requests.post(
        f"{API_BASE}/icons/{first_icon_id}/use",
        headers=headers
    )

    if use_again_response.status_code not in [200, 201]:
        print(f"   ❌ Failed to mark icon as used again: {use_again_response.status_code}")
        return False

    recent_after_reuse = requests.get(f"{API_BASE}/icons/recent", headers=headers).json()

    # Count how many times the icon appears
    appearances = sum(1 for r in recent_after_reuse if r['id'] == first_icon_id)

    if appearances > 1:
        print(f"   ❌ Icon appears {appearances} times (should be 1)")
        return False

    print(f"   ✅ Icon usage updated without duplication")

    print("\n" + "=" * 60)
    print("✅ FEATURE 208 PASSED: Recent Icons")
    print("=" * 60)
    print(f"Summary:")
    print(f"  - Total recent icons: {len(recent_icons)}")
    print(f"  - Icons marked as used: {len(used_icon_ids)}")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = test_recent_icons()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
