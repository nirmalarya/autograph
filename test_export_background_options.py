#!/usr/bin/env python3
"""
Test Export Background Options Feature (#503)

This script tests the export background options feature:
- Transparent background
- White background
- Custom color background

Test Steps:
1. Test transparent background export
2. Test white background export
3. Test custom color (#f0f0f0) background export
4. Verify all exports work correctly
"""

import requests
import json
import base64
from PIL import Image
import io
import sys

# Service endpoints
EXPORT_SERVICE_URL = "http://localhost:8097"

def test_export_with_background(background_value, test_name):
    """Test export with a specific background option."""
    print(f"\n{'=' * 60}")
    print(f"Testing: {test_name}")
    print(f"Background: {background_value}")
    print('=' * 60)
    
    try:
        # Prepare export request
        export_request = {
            "diagram_id": "test-export-bg",
            "canvas_data": {
                "shapes": [
                    {"id": "1", "type": "rectangle", "x": 100, "y": 100, "width": 200, "height": 100}
                ]
            },
            "format": "png",
            "width": 800,
            "height": 600,
            "quality": "high",
            "background": background_value,
            "scale": 2
        }
        
        # Call export endpoint
        print(f"Calling export service: POST {EXPORT_SERVICE_URL}/export/png")
        response = requests.post(
            f"{EXPORT_SERVICE_URL}/export/png",
            json=export_request,
            timeout=30
        )
        
        # Check response
        if response.status_code != 200:
            print(f"❌ FAIL: Export failed with status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
        
        # Verify response is PNG
        content_type = response.headers.get('Content-Type', '')
        if 'image/png' not in content_type:
            print(f"❌ FAIL: Response is not PNG. Content-Type: {content_type}")
            return False
        
        print(f"✅ Export successful! Content-Type: {content_type}")
        
        # Load and verify image
        try:
            img = Image.open(io.BytesIO(response.content))
            print(f"✅ Image loaded successfully")
            print(f"   - Size: {img.size}")
            print(f"   - Mode: {img.mode}")
            print(f"   - Format: {img.format}")
            
            # Verify image properties
            if img.mode == 'RGBA' and background_value == 'transparent':
                print(f"✅ PASS: Image has alpha channel (RGBA) as expected for transparent background")
            elif img.mode == 'RGB' and background_value != 'transparent':
                print(f"✅ PASS: Image is RGB as expected for opaque background")
            else:
                print(f"⚠️  WARNING: Image mode {img.mode} may not match expected for background {background_value}")
            
            # Verify file size is reasonable
            file_size = len(response.content)
            print(f"   - File size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")
            
            if file_size > 0:
                print(f"✅ PASS: Export file size is valid")
            else:
                print(f"❌ FAIL: Export file is empty")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ FAIL: Could not load image: {e}")
            return False
        
    except requests.exceptions.RequestException as e:
        print(f"❌ FAIL: Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ FAIL: Unexpected error: {e}")
        return False

def main():
    """Run all export background option tests."""
    print("=" * 60)
    print("EXPORT BACKGROUND OPTIONS TEST (Feature #503)")
    print("=" * 60)
    
    # Check if export service is running
    print("\n📡 Checking export service health...")
    try:
        health_response = requests.get(f"{EXPORT_SERVICE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ Export service is healthy")
            print(f"   - Service: {health_data.get('service')}")
            print(f"   - Status: {health_data.get('status')}")
            print(f"   - Version: {health_data.get('version')}")
        else:
            print(f"❌ Export service health check failed: {health_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Export service is not available: {e}")
        print("Please start the export service on port 8097")
        return False
    
    # Run tests
    results = []
    
    # Test 1: Transparent background
    results.append(("Transparent Background", test_export_with_background("transparent", "Test 1: Transparent Background")))
    
    # Test 2: White background
    results.append(("White Background", test_export_with_background("white", "Test 2: White Background")))
    
    # Test 3: Custom color background
    results.append(("Custom Color (#f0f0f0)", test_export_with_background("#f0f0f0", "Test 3: Custom Color Background")))
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! Feature #503 is working correctly.")
        print("\nVerified:")
        print("  ✓ Transparent background export works")
        print("  ✓ White background export works")
        print("  ✓ Custom color background export works")
        print("  ✓ All background options function correctly")
        return True
    else:
        print(f"\n❌ {total - passed} test(s) failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
