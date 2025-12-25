#!/usr/bin/env python3
"""
Feature 209: Favorite Icons - Star icons for quick access
Tests favoriting and unfavoriting icons functionality.
"""
import requests
import json
import sys

API_BASE = "http://localhost:8080"

def test_favorite_icons():
    """Test favorite icons functionality."""
    print("=" * 60)
    print("Feature 209: Favorite Icons")
    print("=" * 60)

    # Register and login
    print("\n1. Setting up test user...")
    register_response = requests.post(f"{API_BASE}/auth/register", json={
        "email": f"iconfav209@example.com",
        "password": "SecurePass123!",
        "name": "Favorite Icons User"
    })

    login_response = requests.post(f"{API_BASE}/auth/login", json={
        "email": f"iconfav209@example.com",
        "password": "SecurePass123!"
    })

    if login_response.status_code != 200:
        print(f"   ❌ Login failed: {login_response.status_code}")
        return False

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   ✅ User authenticated")

    # Test 1: Get favorite icons (should be empty initially)
    print("\n2. Testing initial favorites (should be empty)...")
    favorites_response = requests.get(f"{API_BASE}/icons/favorites", headers=headers)

    if favorites_response.status_code != 200:
        print(f"   ❌ Failed to get favorites: {favorites_response.status_code}")
        return False

    favorites = favorites_response.json()
    print(f"   ✅ Initial favorites: {len(favorites)} (expected 0)")

    if len(favorites) > 0:
        print(f"   ⚠️  Expected empty favorites for new user, got {len(favorites)}")

    # Test 2: Find icons to favorite
    print("\n3. Finding icons to favorite...")
    search_response = requests.get(
        f"{API_BASE}/icons/search",
        params={"q": "docker", "limit": 5},
        headers=headers
    )

    if search_response.status_code != 200:
        print(f"   ❌ Icon search failed: {search_response.status_code}")
        return False

    icons = search_response.json()
    if len(icons) == 0:
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

    # Test 3: Add icons to favorites
    print("\n4. Adding icons to favorites...")
    favorited_icon_ids = []

    for i, icon in enumerate(icons[:3]):  # Favorite first 3 icons
        icon_id = icon['id']
        favorite_response = requests.post(
            f"{API_BASE}/icons/{icon_id}/favorite",
            headers=headers
        )

        if favorite_response.status_code not in [200, 201]:
            print(f"   ❌ Failed to favorite icon: {favorite_response.status_code}")
            print(f"   Response: {favorite_response.text}")
            return False

        favorited_icon_ids.append(icon_id)
        print(f"   ✅ Favorited icon {i+1}: {icon.get('name', 'Unknown')}")

    # Test 4: Get favorite icons (should now have entries)
    print("\n5. Retrieving favorite icons...")
    favorites_response = requests.get(f"{API_BASE}/icons/favorites", headers=headers)

    if favorites_response.status_code != 200:
        print(f"   ❌ Failed to get favorites: {favorites_response.status_code}")
        return False

    favorites = favorites_response.json()
    print(f"   ✅ Retrieved {len(favorites)} favorite icons")

    if len(favorites) != len(favorited_icon_ids):
        print(f"   ❌ Expected {len(favorited_icon_ids)} favorites, got {len(favorites)}")
        return False

    # Test 5: Verify favorited icons are all present
    print("\n6. Verifying all favorited icons are present...")
    favorite_ids = [f['id'] for f in favorites]

    for icon_id in favorited_icon_ids:
        if icon_id not in favorite_ids:
            print(f"   ❌ Favorited icon {icon_id} not found in favorites list")
            return False

    print(f"   ✅ All favorited icons are present")

    # Test 6: Verify favorite icons have required fields
    print("\n7. Verifying favorite icon data structure...")
    required_fields = ['id', 'name', 'provider']

    for fav in favorites:
        missing_fields = [field for field in required_fields if field not in fav]
        if missing_fields:
            print(f"   ❌ Favorite icon missing fields: {missing_fields}")
            return False

    print(f"   ✅ All favorite icons have required fields")

    # Test 7: Try to favorite same icon again (should be idempotent)
    print("\n8. Testing duplicate favorite (should be idempotent)...")
    first_icon_id = favorited_icon_ids[0]

    duplicate_response = requests.post(
        f"{API_BASE}/icons/{first_icon_id}/favorite",
        headers=headers
    )

    if duplicate_response.status_code not in [200, 201]:
        print(f"   ❌ Failed to favorite icon again: {duplicate_response.status_code}")
        return False

    favorites_after_duplicate = requests.get(f"{API_BASE}/icons/favorites", headers=headers).json()

    # Count how many times the icon appears
    appearances = sum(1 for f in favorites_after_duplicate if f['id'] == first_icon_id)

    if appearances > 1:
        print(f"   ❌ Icon appears {appearances} times (should be 1)")
        return False

    print(f"   ✅ Duplicate favorite handled correctly (idempotent)")

    # Test 8: Unfavorite an icon
    print("\n9. Unfavoriting an icon...")
    icon_to_unfavorite = favorited_icon_ids[1]  # Unfavorite second icon

    unfavorite_response = requests.delete(
        f"{API_BASE}/icons/{icon_to_unfavorite}/favorite",
        headers=headers
    )

    if unfavorite_response.status_code not in [200, 204]:
        print(f"   ❌ Failed to unfavorite icon: {unfavorite_response.status_code}")
        print(f"   Response: {unfavorite_response.text}")
        return False

    print(f"   ✅ Unfavorited icon successfully")

    # Test 9: Verify icon was removed from favorites
    print("\n10. Verifying icon was removed from favorites...")
    favorites_after_remove = requests.get(f"{API_BASE}/icons/favorites", headers=headers).json()

    if any(f['id'] == icon_to_unfavorite for f in favorites_after_remove):
        print(f"   ❌ Unfavorited icon still in favorites list")
        return False

    expected_count = len(favorited_icon_ids) - 1
    if len(favorites_after_remove) != expected_count:
        print(f"   ❌ Expected {expected_count} favorites, got {len(favorites_after_remove)}")
        return False

    print(f"   ✅ Icon removed from favorites (now {len(favorites_after_remove)} favorites)")

    # Test 10: Try to unfavorite non-existent favorite (should handle gracefully)
    print("\n11. Testing unfavorite of already unfavorited icon...")
    unfavorite_again_response = requests.delete(
        f"{API_BASE}/icons/{icon_to_unfavorite}/favorite",
        headers=headers
    )

    # Should return 404 or 204 (both acceptable)
    if unfavorite_again_response.status_code not in [200, 204, 404]:
        print(f"   ❌ Unexpected status for unfavorite again: {unfavorite_again_response.status_code}")
        return False

    print(f"   ✅ Unfavorite of non-favorite handled correctly")

    # Test 11: Test limit parameter on favorites
    print("\n12. Testing favorites limit parameter...")
    # First, favorite more icons to test limit
    for icon in icons[3:5]:  # Favorite 2 more if available
        requests.post(f"{API_BASE}/icons/{icon['id']}/favorite", headers=headers)

    limit_response = requests.get(
        f"{API_BASE}/icons/favorites",
        params={"limit": 2},
        headers=headers
    )

    if limit_response.status_code != 200:
        print(f"   ❌ Failed to get favorites with limit: {limit_response.status_code}")
        return False

    limited_favorites = limit_response.json()
    if len(limited_favorites) > 2:
        print(f"   ❌ Limit not respected: got {len(limited_favorites)} results (expected ≤2)")
        return False

    print(f"   ✅ Limit parameter working (got {len(limited_favorites)} results)")

    print("\n" + "=" * 60)
    print("✅ FEATURE 209 PASSED: Favorite Icons")
    print("=" * 60)
    print(f"Summary:")
    print(f"  - Icons favorited: {len(favorited_icon_ids)}")
    print(f"  - Icons unfavorited: 1")
    print(f"  - Final favorites count: {len(favorites_after_remove)}")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = test_favorite_icons()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
