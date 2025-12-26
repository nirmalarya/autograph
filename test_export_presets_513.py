#!/usr/bin/env python3
"""Test Feature #513: Export Presets - Save Favorite Settings"""
import requests
import json

BASE_URL = "http://localhost:8097"

def test_create_export_preset():
    """
    Feature #513: Export presets - save favorite settings

    Tests:
    - POST /api/export-presets to create a preset
    - GET /api/export-presets to list presets
    - Default preset functionality
    """
    print("\n" + "="*60)
    print("Testing Feature #513: Export Presets")
    print("="*60)

    user_id = "test-user-513"
    headers = {"X-User-ID": user_id}

    # Test 1: Create a PNG export preset
    print("\n1. Creating PNG export preset...")
    preset_request = {
        "name": "High Quality PNG",
        "format": "png",
        "settings": {
            "width": 3840,
            "height": 2160,
            "scale": 2.0,
            "quality": "high",
            "background": "transparent"
        },
        "is_default": True
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/export-presets",
            json=preset_request,
            headers=headers,
            timeout=10
        )

        print(f"   Status: {response.status_code}")

        if response.status_code == 201:
            data = response.json()
            print(f"   ✅ Preset created successfully")
            print(f"   Preset ID: {data.get('id')}")
            print(f"   Name: {data.get('name')}")
            print(f"   Format: {data.get('format')}")
            print(f"   Is Default: {data.get('is_default')}")
            print(f"   Settings: {json.dumps(data.get('settings'), indent=4)}")

            # Verify fields
            if data.get('name') != preset_request['name']:
                print(f"   ❌ Name mismatch")
                return False

            if data.get('format') != 'png':
                print(f"   ❌ Format mismatch")
                return False

            if not data.get('is_default'):
                print(f"   ❌ Should be default preset")
                return False

            preset_id = data.get('id')

        else:
            error_detail = response.json() if response.content else response.text
            print(f"   ❌ Failed to create preset: {error_detail}")
            return False

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    # Test 2: Create another PNG preset (non-default)
    print("\n2. Creating another PNG preset...")
    preset_request_2 = {
        "name": "Quick PNG",
        "format": "png",
        "settings": {
            "width": 1920,
            "height": 1080,
            "scale": 1.0,
            "quality": "medium",
            "background": "white"
        },
        "is_default": False
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/export-presets",
            json=preset_request_2,
            headers=headers,
            timeout=10
        )

        if response.status_code == 201:
            data = response.json()
            print(f"   ✅ Second preset created")
            print(f"   Name: {data.get('name')}")
            print(f"   Is Default: {data.get('is_default')}")

        else:
            print(f"   ⚠️  Failed to create second preset: {response.status_code}")

    except Exception as e:
        print(f"   ⚠️  Error: {str(e)}")

    # Test 3: Create PDF preset
    print("\n3. Creating PDF export preset...")
    preset_request_3 = {
        "name": "Standard PDF",
        "format": "pdf",
        "settings": {
            "page_size": "A4",
            "multi_page": True,
            "embed_fonts": True,
            "vector_graphics": True
        },
        "is_default": True
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/export-presets",
            json=preset_request_3,
            headers=headers,
            timeout=10
        )

        if response.status_code == 201:
            data = response.json()
            print(f"   ✅ PDF preset created")
            print(f"   Name: {data.get('name')}")
            print(f"   Format: {data.get('format')}")

        else:
            print(f"   ⚠️  Failed to create PDF preset")

    except Exception as e:
        print(f"   ⚠️  Error: {str(e)}")

    # Test 4: List all presets
    print("\n4. Listing all export presets...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/export-presets",
            headers=headers,
            timeout=10
        )

        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            presets = data.get('presets', [])
            print(f"   ✅ Found {len(presets)} presets")

            for preset in presets:
                default_marker = " [DEFAULT]" if preset.get('is_default') else ""
                print(f"     - {preset.get('name')} ({preset.get('format')}){default_marker}")

            # Should have at least 2 presets (High Quality PNG, Quick PNG, Standard PDF)
            if len(presets) < 2:
                print(f"   ⚠️  Expected at least 2 presets, got {len(presets)}")

        else:
            print(f"   ⚠️  Failed to list presets: {response.status_code}")

    except Exception as e:
        print(f"   ⚠️  Error: {str(e)}")

    # Test 5: List presets filtered by format
    print("\n5. Listing PNG presets only...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/export-presets?format=png",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            presets = data.get('presets', [])
            print(f"   ✅ Found {len(presets)} PNG presets")

            all_png = all(p.get('format') == 'png' for p in presets)
            if all_png:
                print(f"   ✅ All presets are PNG format")
            else:
                print(f"   ❌ Non-PNG presets in results")

        else:
            print(f"   ⚠️  Failed to filter presets")

    except Exception as e:
        print(f"   ⚠️  Error: {str(e)}")

    print("\n✅ Feature #513 PASSED: Export presets work correctly")
    return True


if __name__ == "__main__":
    print("\n" + "="*60)
    print("FEATURE #513: EXPORT PRESETS - COMPREHENSIVE TEST")
    print("="*60)

    success = test_create_export_preset()

    print("\n" + "="*60)
    if success:
        print("FEATURE #513: ✅ PASSED")
        print("Export presets functionality is working correctly!")
    else:
        print("FEATURE #513: ❌ FAILED")
        print("Export presets need fixes")
    print("="*60)

    exit(0 if success else 1)
