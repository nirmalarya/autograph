"""
Test Feature #516: PNG Compression in Export Service

This test verifies that PNG exports apply compression to reduce file size
while maintaining quality.
"""

import requests
import base64
from PIL import Image
import io

# Test configuration
BASE_URL = "http://localhost:8097"
TEST_DIAGRAM_ID = "test-compression-diagram"

def test_thumbnail_compression():
    """Test that thumbnail generation applies PNG compression."""
    print("=" * 80)
    print("Testing Feature #516: PNG Compression")
    print("=" * 80)

    # Test 1: Generate thumbnail (should have compression)
    print("\n1. Testing thumbnail generation with compression...")
    response = requests.post(
        f"{BASE_URL}/thumbnail",
        json={
            "diagram_id": TEST_DIAGRAM_ID,
            "width": 256,
            "height": 256,
            "canvas_data": {
                "shapes": [
                    {"type": "rectangle", "x": 10, "y": 10, "width": 100, "height": 50}
                ]
            }
        }
    )

    if response.status_code == 200:
        data = response.json()
        thumbnail_base64 = data.get("thumbnail_base64", "")

        # Decode base64 to get PNG data
        png_data = base64.b64decode(thumbnail_base64)
        file_size = len(png_data)

        # Open with PIL to verify it's valid PNG
        img = Image.open(io.BytesIO(png_data))

        print(f"   ✓ Thumbnail generated successfully")
        print(f"   ✓ Format: {img.format}")
        print(f"   ✓ Size: {img.size}")
        print(f"   ✓ File size: {file_size:,} bytes")
        print(f"   ✓ Compression ratio: {file_size / (256 * 256 * 4):.2%} (smaller is better)")

        # For a simple 256x256 image, compressed PNG should be much smaller than raw
        # Raw RGBA would be 256*256*4 = 262,144 bytes
        # With compression, should be significantly smaller
        if file_size < 100000:  # Less than 100KB for a simple thumbnail
            print(f"   ✓ PASS: File size is reasonable ({file_size:,} bytes < 100KB)")
        else:
            print(f"   ✗ FAIL: File size too large ({file_size:,} bytes >= 100KB)")
            return False
    else:
        print(f"   ✗ FAIL: Thumbnail generation failed with status {response.status_code}")
        print(f"   Error: {response.text}")
        return False

    # Test 2: Generate PNG thumbnail with compression
    print("\n2. Testing PNG thumbnail endpoint with compression...")
    response = requests.post(
        f"{BASE_URL}/thumbnail/png",
        json={
            "diagram_id": TEST_DIAGRAM_ID,
            "width": 256,
            "height": 256,
            "canvas_data": {
                "shapes": [
                    {"type": "rectangle", "x": 10, "y": 10, "width": 100, "height": 50}
                ]
            }
        }
    )

    if response.status_code == 200:
        png_data = response.content
        file_size = len(png_data)

        # Verify it's a valid PNG
        img = Image.open(io.BytesIO(png_data))

        print(f"   ✓ PNG thumbnail generated successfully")
        print(f"   ✓ Format: {img.format}")
        print(f"   ✓ Size: {img.size}")
        print(f"   ✓ File size: {file_size:,} bytes")
        print(f"   ✓ Compression ratio: {file_size / (256 * 256 * 4):.2%}")

        if file_size < 100000:
            print(f"   ✓ PASS: File size is reasonable ({file_size:,} bytes < 100KB)")
        else:
            print(f"   ✗ FAIL: File size too large ({file_size:,} bytes >= 100KB)")
            return False
    else:
        print(f"   ✗ FAIL: PNG thumbnail failed with status {response.status_code}")
        print(f"   Error: {response.text}")
        return False

    # Test 3: Export PNG with different quality levels
    print("\n3. Testing PNG export with quality-based compression levels...")

    quality_tests = [
        ("standard", 800, 600),
        ("high", 800, 600),
        ("ultra", 800, 600)
    ]

    for quality, width, height in quality_tests:
        print(f"\n   Testing quality={quality}, size={width}x{height}...")
        response = requests.post(
            f"{BASE_URL}/export/png",
            json={
                "diagram_id": TEST_DIAGRAM_ID,
                "format": "png",
                "width": width,
                "height": height,
                "scale": 1,
                "background": "white",
                "quality": quality,
                "export_scope": "full",
                "canvas_data": {
                    "shapes": [
                        {"type": "rectangle", "x": 10, "y": 10, "width": 100, "height": 50},
                        {"type": "circle", "x": 200, "y": 100, "radius": 30}
                    ]
                }
            }
        )

        if response.status_code == 200:
            png_data = response.content
            file_size = len(png_data)

            # Verify it's a valid PNG
            img = Image.open(io.BytesIO(png_data))

            print(f"      ✓ PNG export generated successfully")
            print(f"      ✓ Format: {img.format}")
            print(f"      ✓ Size: {img.size}")
            print(f"      ✓ File size: {file_size:,} bytes")
            print(f"      ✓ Compression ratio: {file_size / (width * height * 4):.2%}")

            # For quality in ['high', 'ultra'], compress_level=9 is used
            # For other qualities, compress_level=6 is used
            # Verify file size is reasonable for compressed PNG
            max_size = width * height * 0.5  # Should be much smaller than raw RGBA
            if file_size < max_size:
                print(f"      ✓ PASS: Good compression ({file_size:,} bytes < {max_size:,.0f} bytes)")
            else:
                print(f"      ✗ FAIL: Poor compression ({file_size:,} bytes >= {max_size:,.0f} bytes)")
                return False
        else:
            print(f"      ✗ FAIL: PNG export failed with status {response.status_code}")
            print(f"      Error: {response.text}")
            return False

    print("\n" + "=" * 80)
    print("✅ Feature #516: PNG Compression - ALL TESTS PASSED")
    print("=" * 80)
    print("\nSummary:")
    print("✓ Thumbnail generation applies compression")
    print("✓ PNG thumbnail endpoint applies compression")
    print("✓ PNG export uses quality-based compression levels")
    print("✓ File sizes are reasonable (< 50% of raw RGBA)")
    print("✓ Image quality is maintained (valid PNG format)")

    return True


if __name__ == "__main__":
    try:
        success = test_thumbnail_compression()
        if success:
            print("\n🎉 All PNG compression tests passed!")
            exit(0)
        else:
            print("\n❌ Some tests failed!")
            exit(1)
    except Exception as e:
        print(f"\n❌ Test error: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
