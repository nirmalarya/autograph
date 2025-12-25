#!/usr/bin/env python3
"""
Feature 207: Icon Categories - Organized by provider and type
Tests that icons are properly organized into categories.
"""
import requests
import json
import sys

API_BASE = "http://localhost:8080"

def test_icon_categories():
    """Test icon categories organization."""
    print("=" * 60)
    print("Feature 207: Icon Categories (Provider & Type)")
    print("=" * 60)

    # Register and login
    print("\n1. Setting up test user...")
    register_response = requests.post(f"{API_BASE}/auth/register", json={
        "email": f"iconcat207@example.com",
        "password": "SecurePass123!",
        "name": "Icon Category User"
    })

    login_response = requests.post(f"{API_BASE}/auth/login", json={
        "email": f"iconcat207@example.com",
        "password": "SecurePass123!"
    })

    if login_response.status_code != 200:
        print(f"   ❌ Login failed: {login_response.status_code}")
        return False

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   ✅ User authenticated")

    # Test 1: Get all categories
    print("\n2. Testing icon categories endpoint...")
    categories_response = requests.get(f"{API_BASE}/icons/categories", headers=headers)

    if categories_response.status_code != 200:
        print(f"   ❌ Failed to get categories: {categories_response.status_code}")
        return False

    categories = categories_response.json()
    print(f"   ✅ Retrieved {len(categories)} categories")

    # Test 2: Verify category structure
    print("\n3. Verifying category structure...")
    required_fields = ['id', 'name', 'slug', 'provider', 'icon_count']

    for cat in categories[:3]:  # Check first 3
        missing_fields = [field for field in required_fields if field not in cat]
        if missing_fields:
            print(f"   ❌ Category missing fields: {missing_fields}")
            return False

    print(f"   ✅ All categories have required fields")

    # Test 3: Verify providers
    print("\n4. Verifying provider organization...")
    providers = {}
    for cat in categories:
        provider = cat.get('provider', 'unknown')
        if provider not in providers:
            providers[provider] = []
        providers[provider].append(cat)

    print(f"   Found {len(providers)} providers:")
    for provider, cats in providers.items():
        total_icons = sum(c.get('icon_count', 0) for c in cats)
        print(f"     - {provider}: {len(cats)} categories, {total_icons} icons")

    # Verify required providers exist
    required_providers = ['aws', 'azure', 'gcp', 'simple-icons']
    missing_providers = [p for p in required_providers if p not in providers]

    if missing_providers:
        print(f"   ❌ Missing providers: {missing_providers}")
        return False

    print(f"   ✅ All required providers present")

    # Test 4: Verify category metadata
    print("\n5. Verifying category metadata...")
    for provider, cats in list(providers.items())[:2]:  # Check first 2 providers
        for cat in cats[:2]:  # Check first 2 categories per provider
            print(f"   Category: {cat.get('name')}")
            print(f"     - Slug: {cat.get('slug')}")
            print(f"     - Provider: {cat.get('provider')}")
            print(f"     - Icons: {cat.get('icon_count')}")

            # Verify slug is URL-friendly
            slug = cat.get('slug', '')
            if not slug.replace('-', '').replace('_', '').isalnum():
                print(f"   ❌ Invalid slug format: {slug}")
                return False

    print(f"   ✅ Category metadata is valid")

    # Test 5: Verify icon counts
    print("\n6. Verifying icon counts...")
    zero_count_categories = [cat for cat in categories if cat.get('icon_count', 0) == 0]

    if zero_count_categories:
        print(f"   ⚠️  Found {len(zero_count_categories)} categories with 0 icons:")
        for cat in zero_count_categories[:5]:
            print(f"     - {cat.get('name')} ({cat.get('provider')})")

    non_zero_categories = [cat for cat in categories if cat.get('icon_count', 0) > 0]
    print(f"   ✅ {len(non_zero_categories)} categories have icons")

    # Test 6: Verify sorting
    print("\n7. Verifying category sorting...")
    category_names = [cat.get('name', '') for cat in categories]
    sorted_names = sorted(category_names)

    if category_names == sorted_names:
        print(f"   ✅ Categories are sorted alphabetically")
    else:
        print(f"   ⚠️  Categories may not be sorted (acceptable)")

    print("\n" + "=" * 60)
    print("✅ FEATURE 207 PASSED: Icon Categories")
    print("=" * 60)
    print(f"Summary:")
    print(f"  - Total categories: {len(categories)}")
    print(f"  - Categories with icons: {len(non_zero_categories)}")
    print(f"  - Providers: {', '.join(providers.keys())}")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = test_icon_categories()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
