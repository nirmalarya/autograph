#!/usr/bin/env python3
"""
Feature 205: Icon Library - 3000+ icons (AWS, Azure, GCP, SimpleIcons)
Tests that the icon library contains 3000+ icons from multiple providers.
"""
import requests
import json
import sys

API_BASE = "http://localhost:8080"

def test_icon_library():
    """Test that icon library has 3000+ icons."""
    print("=" * 60)
    print("Feature 205: Icon Library (3000+ icons)")
    print("=" * 60)

    # First, register and login
    print("\n1. Setting up test user...")
    register_response = requests.post(f"{API_BASE}/auth/register", json={
        "email": f"icontest205@example.com",
        "password": "SecurePass123!",
        "name": "Icon Test User"
    })

    if register_response.status_code not in [200, 201]:
        print(f"   ❌ Registration failed: {register_response.status_code}")
        print(f"   Response: {register_response.text}")
        return False

    # Login
    login_response = requests.post(f"{API_BASE}/auth/login", json={
        "email": f"icontest205@example.com",
        "password": "SecurePass123!"
    })

    if login_response.status_code != 200:
        print(f"   ❌ Login failed: {login_response.status_code}")
        return False

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   ✅ User authenticated")

    # Test 1: Get all icon categories
    print("\n2. Testing icon categories endpoint...")
    categories_response = requests.get(f"{API_BASE}/icons/categories", headers=headers)

    if categories_response.status_code != 200:
        print(f"   ❌ Failed to get categories: {categories_response.status_code}")
        return False

    categories = categories_response.json()
    print(f"   ✅ Found {len(categories)} categories")

    # Verify we have categories from different providers
    providers = set(cat.get('provider', '') for cat in categories)
    print(f"   Providers: {', '.join(providers)}")

    required_providers = {'aws', 'azure', 'gcp', 'simple-icons'}
    if not required_providers.issubset(providers):
        print(f"   ❌ Missing providers. Expected: {required_providers}, Got: {providers}")
        return False
    print(f"   ✅ All required providers present")

    # Test 2: Count total icons across all categories
    print("\n3. Counting total icons...")
    total_icons = sum(cat.get('icon_count', 0) for cat in categories)
    print(f"   Total icons in categories: {total_icons}")

    if total_icons < 3000:
        print(f"   ❌ Not enough icons! Need 3000+, got {total_icons}")
        return False
    print(f"   ✅ Icon library has 3000+ icons ({total_icons} icons)")

    # Test 3: Verify AWS icons
    print("\n4. Verifying AWS icons...")
    aws_categories = [cat for cat in categories if cat.get('provider') == 'aws']
    aws_icon_count = sum(cat.get('icon_count', 0) for cat in aws_categories)
    print(f"   AWS categories: {len(aws_categories)}")
    print(f"   AWS icons: {aws_icon_count}")

    if aws_icon_count < 100:
        print(f"   ❌ Not enough AWS icons (expected 100+, got {aws_icon_count})")
        return False
    print(f"   ✅ AWS icons present ({aws_icon_count})")

    # Test 4: Verify Azure icons
    print("\n5. Verifying Azure icons...")
    azure_categories = [cat for cat in categories if cat.get('provider') == 'azure']
    azure_icon_count = sum(cat.get('icon_count', 0) for cat in azure_categories)
    print(f"   Azure categories: {len(azure_categories)}")
    print(f"   Azure icons: {azure_icon_count}")

    if azure_icon_count < 100:
        print(f"   ❌ Not enough Azure icons (expected 100+, got {azure_icon_count})")
        return False
    print(f"   ✅ Azure icons present ({azure_icon_count})")

    # Test 5: Verify GCP icons
    print("\n6. Verifying GCP icons...")
    gcp_categories = [cat for cat in categories if cat.get('provider') == 'gcp']
    gcp_icon_count = sum(cat.get('icon_count', 0) for cat in gcp_categories)
    print(f"   GCP categories: {len(gcp_categories)}")
    print(f"   GCP icons: {gcp_icon_count}")

    if gcp_icon_count < 50:
        print(f"   ❌ Not enough GCP icons (expected 50+, got {gcp_icon_count})")
        return False
    print(f"   ✅ GCP icons present ({gcp_icon_count})")

    # Test 6: Verify SimpleIcons/Brand icons
    print("\n7. Verifying Brand/SimpleIcons...")
    brand_categories = [cat for cat in categories if cat.get('provider') == 'simple-icons']
    brand_icon_count = sum(cat.get('icon_count', 0) for cat in brand_categories)
    print(f"   Brand categories: {len(brand_categories)}")
    print(f"   Brand icons: {brand_icon_count}")

    if brand_icon_count < 100:
        print(f"   ❌ Not enough brand icons (expected 100+, got {brand_icon_count})")
        return False
    print(f"   ✅ Brand icons present ({brand_icon_count})")

    # Test 7: Get a specific icon
    print("\n8. Testing individual icon retrieval...")
    # Search for React icon first
    search_response = requests.get(
        f"{API_BASE}/icons/search",
        params={"q": "react", "limit": 1},
        headers=headers
    )

    if search_response.status_code != 200:
        print(f"   ❌ Search failed: {search_response.status_code}")
        return False

    search_results = search_response.json()
    if len(search_results) == 0:
        print("   ⚠️  No React icon found (acceptable for generated icons)")
    else:
        icon_id = search_results[0]['id']
        icon_response = requests.get(f"{API_BASE}/icons/{icon_id}", headers=headers)

        if icon_response.status_code != 200:
            print(f"   ❌ Failed to get icon: {icon_response.status_code}")
            return False

        icon = icon_response.json()
        print(f"   ✅ Retrieved icon: {icon.get('name', 'Unknown')}")
        print(f"      Provider: {icon.get('provider')}")
        print(f"      Has SVG: {bool(icon.get('svg_data'))}")

    print("\n" + "=" * 60)
    print("✅ FEATURE 205 PASSED: Icon Library (3000+ icons)")
    print("=" * 60)
    print(f"Summary:")
    print(f"  - Total icons: {total_icons}")
    print(f"  - AWS: {aws_icon_count}")
    print(f"  - Azure: {azure_icon_count}")
    print(f"  - GCP: {gcp_icon_count}")
    print(f"  - Brands: {brand_icon_count}")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = test_icon_library()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
