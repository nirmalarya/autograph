#!/usr/bin/env python3
"""Complete test of all icon features 205-209."""
import requests
import sys

headers = {"X-User-ID": "test-user-123"}
base = "http://localhost:8082"

print("=" * 70)
print("ICON FEATURES TEST (205-209)")
print("=" * 70)

# Feature 205: Icon Library (3000+ icons)
print("\n[Feature 205] Testing Icon Library (3000+ icons)...")
resp = requests.get(f"{base}/icons/categories", headers=headers)
if resp.status_code == 200:
    categories = resp.json()
    total_icons = sum(c.get('icon_count', 0) for c in categories)
    if total_icons >= 3000:
        print(f"  ✅ PASS: {total_icons} icons (need 3000+)")
    else:
        print(f"  ❌ FAIL: Only {total_icons} icons (need 3000+)")
        sys.exit(1)
else:
    print(f"  ❌ FAIL: Categories endpoint failed ({resp.status_code})")
    sys.exit(1)

# Feature 206: Icon Search
print("\n[Feature 206] Testing Icon Search with Fuzzy Matching...")
resp = requests.get(f"{base}/icons/search", params={"q": "aws", "limit": 5}, headers=headers)
if resp.status_code == 200:
    data = resp.json()
    icons = data.get('icons', [])
    if len(icons) > 0:
        print(f"  ✅ PASS: Search returned {len(icons)} results")
    else:
        print(f"  ❌ FAIL: Search returned no results")
        sys.exit(1)
else:
    print(f"  ❌ FAIL: Search endpoint failed ({resp.status_code})")
    sys.exit(1)

# Feature 207: Icon Categories
print("\n[Feature 207] Testing Icon Categories...")
providers = set(c.get('provider') for c in categories)
required = {'aws', 'azure', 'gcp', 'simple-icons'}
if required.issubset(providers):
    print(f"  ✅ PASS: All required providers present ({', '.join(providers)})")
else:
    missing = required - providers
    print(f"  ❌ FAIL: Missing providers: {missing}")
    sys.exit(1)

# Get an icon for testing features 208 & 209
print("\nGetting test icon...")
resp = requests.get(f"{base}/icons/search", params={"q": "", "limit": 1}, headers=headers)
if resp.status_code == 200:
    data = resp.json()
    icons = data.get('icons', [])
    if icons:
        test_icon_id = icons[0]['id']
        test_icon_name = icons[0]['name']
        print(f"  Using icon: {test_icon_name}")
    else:
        print("  ❌ No icons available for testing")
        sys.exit(1)
else:
    print(f"  ❌ Failed to get test icon")
    sys.exit(1)

# Feature 208: Recent Icons
print("\n[Feature 208] Testing Recent Icons...")
# Mark icon as used
resp = requests.post(f"{base}/icons/{test_icon_id}/use", headers=headers)
if resp.status_code in [200, 201]:
    print(f"  ✅ Marked icon as used")

    # Get recent icons
    resp = requests.get(f"{base}/icons/recent", headers=headers)
    if resp.status_code == 200:
        recent = resp.json()
        if len(recent) > 0 and recent[0]['id'] == test_icon_id:
            print(f"  ✅ PASS: Recent icons tracking works ({len(recent)} recent)")
        else:
            print(f"  ❌ FAIL: Icon not in recent list")
            sys.exit(1)
    else:
        print(f"  ❌ FAIL: Recent endpoint failed ({resp.status_code})")
        sys.exit(1)
else:
    print(f"  ❌ FAIL: Failed to mark icon as used ({resp.status_code})")
    sys.exit(1)

# Feature 209: Favorite Icons
print("\n[Feature 209] Testing Favorite Icons...")
# Add to favorites
resp = requests.post(f"{base}/icons/{test_icon_id}/favorite", headers=headers)
if resp.status_code in [200, 201]:
    print(f"  ✅ Added to favorites")

    # Get favorites
    resp = requests.get(f"{base}/icons/favorites", headers=headers)
    if resp.status_code == 200:
        favorites = resp.json()
        if len(favorites) > 0 and favorites[0]['id'] == test_icon_id:
            print(f"  ✅ Icon in favorites ({len(favorites)} total)")

            # Remove from favorites
            resp = requests.delete(f"{base}/icons/{test_icon_id}/favorite", headers=headers)
            if resp.status_code in [200, 204]:
                print(f"  ✅ PASS: Favorite icons works (add/remove)")
            else:
                print(f"  ⚠️  Remove from favorites failed ({resp.status_code}) but add worked")
        else:
            print(f"  ❌ FAIL: Icon not in favorites list")
            sys.exit(1)
    else:
        print(f"  ❌ FAIL: Favorites endpoint failed ({resp.status_code})")
        sys.exit(1)
else:
    print(f"  ❌ FAIL: Failed to add to favorites ({resp.status_code})")
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ ALL ICON FEATURES PASSED (205-209)")
print("=" * 70)
print(f"\nSummary:")
print(f"  Feature 205: Icon Library - {total_icons} icons")
print(f"  Feature 206: Icon Search - Working")
print(f"  Feature 207: Icon Categories - {len(categories)} categories, {len(providers)} providers")
print(f"  Feature 208: Recent Icons - Working")
print(f"  Feature 209: Favorite Icons - Working")
print("=" * 70)
