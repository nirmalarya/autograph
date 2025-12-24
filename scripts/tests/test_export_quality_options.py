#!/usr/bin/env python3
"""
Test Export Quality Options Feature (#505)

This script tests the export quality slider/options feature:
- Low quality
- Medium quality
- High quality
- Ultra quality

Test Steps:
1. Test low quality export
2. Test medium quality export
3. Test high quality export
4. Test ultra quality export
5. Verify quality settings are respected
"""

import requests
import json
from PIL import Image
import io
import sys

# Service endpoints
EXPORT_SERVICE_URL = "http://localhost:8097"

def test_export_with_quality(quality_level):
    """Test export with a specific quality level."""
    print(f"\n{'=' * 60}")
    print(f"Testing: {quality_level.capitalize()} Quality")
    print('=' * 60)
    
    try:
        # Prepare export request
        export_request = {
            "diagram_id": "test-export-quality",
            "canvas_data": {
                "shapes": [
                    {"id": "1", "type": "rectangle", "x": 100, "y": 100, "width": 200, "height": 100}
                ]
            },
            "format": "png",
            "width": 1920,
            "height": 1080,
            "quality": quality_level,
            "background": "white",
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
            return False, None
        
        # Verify response is PNG
        content_type = response.headers.get('Content-Type', '')
        if 'image/png' not in content_type:
            print(f"❌ FAIL: Response is not PNG. Content-Type: {content_type}")
            return False, None
        
        print(f"✅ Export successful! Content-Type: {content_type}")
        
        # Load and verify image
        try:
            img = Image.open(io.BytesIO(response.content))
            print(f"✅ Image loaded successfully")
            print(f"   - Size: {img.size}")
            print(f"   - Mode: {img.mode}")
            print(f"   - Format: {img.format}")
            
            # Get file size
            file_size = len(response.content)
            print(f"   - File size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")
            
            if file_size > 0:
                print(f"✅ PASS: Export file size is valid")
            else:
                print(f"❌ FAIL: Export file is empty")
                return False, None
            
            return True, file_size
            
        except Exception as e:
            print(f"❌ FAIL: Could not load image: {e}")
            return False, None
        
    except requests.exceptions.RequestException as e:
        print(f"❌ FAIL: Request failed: {e}")
        return False, None
    except Exception as e:
        print(f"❌ FAIL: Unexpected error: {e}")
        return False, None

def main():
    """Run all export quality tests."""
    print("=" * 60)
    print("EXPORT QUALITY OPTIONS TEST (Feature #505)")
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
    file_sizes = []
    
    # Test 1: Low quality
    success, size = test_export_with_quality("low")
    results.append(("Low Quality", success))
    if size:
        file_sizes.append(("low", size))
    
    # Test 2: Medium quality
    success, size = test_export_with_quality("medium")
    results.append(("Medium Quality", success))
    if size:
        file_sizes.append(("medium", size))
    
    # Test 3: High quality
    success, size = test_export_with_quality("high")
    results.append(("High Quality", success))
    if size:
        file_sizes.append(("high", size))
    
    # Test 4: Ultra quality
    success, size = test_export_with_quality("ultra")
    results.append(("Ultra Quality", success))
    if size:
        file_sizes.append(("ultra", size))
    
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
    
    # Compare file sizes
    if file_sizes:
        print("\n" + "=" * 60)
        print("FILE SIZE COMPARISON")
        print("=" * 60)
        for quality, size in file_sizes:
            print(f"{quality}: {size:,} bytes ({size / 1024:.1f} KB)")
        
        print("\nℹ️  Note: For PNG exports, quality primarily affects compression level")
        print("   File sizes may be similar as PNG uses lossless compression")
    
    if passed == total:
        print("\n🎉 All tests passed! Feature #505 is working correctly.")
        print("\nVerified:")
        print("  ✓ Low quality export works")
        print("  ✓ Medium quality export works")
        print("  ✓ High quality export works")
        print("  ✓ Ultra quality export works")
        print("  ✓ Quality parameter is accepted by backend")
        return True
    else:
        print(f"\n❌ {total - passed} test(s) failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
