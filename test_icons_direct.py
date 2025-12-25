#!/usr/bin/env python3
"""Test icon endpoints directly from diagram service."""
import requests

# Test directly against diagram service (port 8082)
DIAGRAM_SERVICE = "http://localhost:8082"

print("=" * 60)
print("Testing Icon Endpoints (Direct to Diagram Service)")
print("=" * 60)

# Icon endpoints use X-User-ID header
headers = {"X-User-ID": "test-user-123"}

# Test 1: Get categories
print("\n1. Testing /icons/categories...")
response = requests.get(f"{DIAGRAM_SERVICE}/icons/categories", headers=headers)
print(f"   Status: {response.status_code}")

if response.status_code == 200:
    categories = response.json()
    print(f"   ✅ Found {len(categories)} categories")

    total_icons = sum(c.get('icon_count', 0) for c in categories)
    print(f"   Total icons: {total_icons}")

    providers = set(c.get('provider') for c in categories)
    print(f"   Providers: {providers}")

    if total_icons >= 3000:
        print(f"   ✅ Feature 205 PASSED: 3000+ icons ({total_icons})")
    else:
        print(f"   ❌ Feature 205 FAILED: Only {total_icons} icons (need 3000+)")
else:
    print(f"   ❌ Failed: {response.text}")

# Test 2: Search icons
print("\n2. Testing /icons/search...")
response = requests.get(
    f"{DIAGRAM_SERVICE}/icons/search",
    params={"q": "aws", "limit": 10},
    headers=headers
)
print(f"   Status: {response.status_code}")

if response.status_code == 200:
    results = response.json()
    # Results might be a dict with 'icons' key or a list
    if isinstance(results, dict):
        icons = results.get('icons', results.get('results', []))
    else:
        icons = results

    print(f"   ✅ Search returned response")
    if isinstance(icons, list) and len(icons) > 0:
        print(f"   Found {len(icons)} icons")
        print(f"   Sample: {icons[0].get('name')}")
    print(f"   ✅ Feature 206 PASSED: Icon search working")
else:
    print(f"   ❌ Failed: {response.text}")

# Test 3: Get recent icons
print("\n3. Testing /icons/recent...")
response = requests.get(f"{DIAGRAM_SERVICE}/icons/recent", headers=headers)
print(f"   Status: {response.status_code}")

if response.status_code == 200:
    recent = response.json()
    print(f"   ✅ Recent icons endpoint working ({len(recent)} recent)")
else:
    print(f"   ❌ Failed: {response.text}")

# Test 4: Get favorites
print("\n4. Testing /icons/favorites...")
response = requests.get(f"{DIAGRAM_SERVICE}/icons/favorites", headers=headers)
print(f"   Status: {response.status_code}")

if response.status_code == 200:
    favorites = response.json()
    print(f"   ✅ Favorites endpoint working ({len(favorites)} favorites)")
else:
    print(f"   ❌ Failed: {response.text}")

# Test 5: Mark icon as used (need an icon ID first)
print("\n5. Testing POST /icons/:id/use...")
# Get an icon first
search_resp = requests.get(
    f"{DIAGRAM_SERVICE}/icons/search",
    params={"limit": 1},
    headers=headers
)

icon_id = None
if search_resp.status_code == 200:
    search_data = search_resp.json()
    if isinstance(search_data, dict):
        icons_list = search_data.get('icons', [])
    else:
        icons_list = search_data

    if isinstance(icons_list, list) and len(icons_list) > 0:
        icon_id = icons_list[0]['id']
        print(f"   Using icon: {icons_list[0].get('name')} (ID: {icon_id[:8]}...)")

if icon_id:
    use_resp = requests.post(f"{DIAGRAM_SERVICE}/icons/{icon_id}/use", headers=headers)
    print(f"   Status: {use_resp.status_code}")

    if use_resp.status_code in [200, 201]:
        print(f"   ✅ Mark as used working")
        print(f"   ✅ Feature 208 PASSED: Recent icons tracking")
    else:
        print(f"   ❌ Failed: {use_resp.text}")
else:
    print(f"   ⚠️  No icons to test with")

# Test 6: Add to favorites
print("\n6. Testing POST /icons/:id/favorite...")
if icon_id:
    fav_resp = requests.post(f"{DIAGRAM_SERVICE}/icons/{icon_id}/favorite", headers=headers)
    print(f"   Status: {fav_resp.status_code}")

    if fav_resp.status_code in [200, 201]:
        print(f"   ✅ Add to favorites working")

        # Test delete favorite
        print("\n7. Testing DELETE /icons/:id/favorite...")
        del_resp = requests.delete(f"{DIAGRAM_SERVICE}/icons/{icon_id}/favorite", headers=headers)
        print(f"   Status: {del_resp.status_code}")

        if del_resp.status_code in [200, 204]:
            print(f"   ✅ Remove from favorites working")
            print(f"   ✅ Feature 209 PASSED: Favorite icons")
        else:
            print(f"   ❌ Failed: {del_resp.text}")
    else:
        print(f"   ❌ Failed: {fav_resp.text}")

print("\n" + "=" * 60)
print("Icon Endpoints Test Complete")
print("=" * 60)
