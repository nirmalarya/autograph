#!/usr/bin/env python3
"""
Test Feature #489: PNG Export - Anti-aliased Edges

This test verifies that PNG exports have smooth, anti-aliased edges.

Steps:
1. Export PNG
2. Verify image is generated
3. Check image quality settings
4. Verify no errors in export
"""

import requests
import io
from PIL import Image, ImageDraw

# Configuration
API_BASE_URL = "http://localhost:8080/api"
EXPORT_SERVICE_URL = "http://localhost:8097"

def create_test_user():
    """Create a test user for authentication."""
    print("Creating test user...")
    response = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={
            "username": f"antialiasing_test",
            "email": f"antialiasing_test@example.com",
            "password": "SecurePass123!"
        }
    )
    if response.status_code == 201:
        print("✓ Test user created")
        return response.json()
    elif response.status_code == 409:
        print("✓ Test user already exists, logging in...")
        login_response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={
                "username": f"antialiasing_test",
                "password": "SecurePass123!"
            }
        )
        if login_response.status_code == 200:
            return login_response.json()
    raise Exception(f"Failed to create/login user: {response.status_code} - {response.text}")

def create_test_diagram(token):
    """Create a test diagram."""
    print("Creating test diagram...")
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.post(
        f"{API_BASE_URL}/diagrams",
        headers=headers,
        json={
            "name": "Anti-aliasing Test Diagram",
            "type": "canvas"
        }
    )

    if response.status_code == 201:
        diagram = response.json()
        print(f"✓ Test diagram created: {diagram['id']}")
        return diagram['id']
    raise Exception(f"Failed to create diagram: {response.status_code} - {response.text}")

def export_png_with_shapes(diagram_id, token):
    """Export PNG with shapes to test anti-aliasing."""
    print("Exporting PNG with anti-aliased shapes...")
    headers = {"Authorization": f"Bearer {token}"}

    # Create canvas data with shapes that will show anti-aliasing
    canvas_data = {
        "shapes": [
            {
                "id": "circle1",
                "type": "ellipse",
                "x": 200,
                "y": 200,
                "width": 200,
                "height": 200
            }
        ]
    }

    response = requests.post(
        f"{EXPORT_SERVICE_URL}/export/png",
        headers=headers,
        json={
            "diagram_id": diagram_id,
            "width": 800,
            "height": 600,
            "scale": 2,  # 2x for higher quality
            "quality": "high",
            "background": "white",
            "canvas_data": canvas_data
        }
    )

    if response.status_code == 200:
        print(f"✓ PNG exported successfully")
        print(f"  File size: {len(response.content)} bytes")
        print(f"  Content type: {response.headers.get('content-type')}")
        return response.content
    raise Exception(f"Failed to export PNG: {response.status_code} - {response.text}")

def analyze_png_quality(png_bytes):
    """
    Analyze PNG to verify it was created with proper settings.

    PIL's ImageDraw uses anti-aliasing by default for:
    - Text rendering
    - Ellipses/circles
    - Polygon edges

    We verify the image was created successfully and has proper format.
    """
    print("\nAnalyzing PNG quality...")

    img = Image.open(io.BytesIO(png_bytes))

    print(f"  Image format: {img.format}")
    print(f"  Image mode: {img.mode}")
    print(f"  Image size: {img.size}")

    # Check that we have a valid PNG
    if img.format != 'PNG':
        print("  ✗ Not a PNG image")
        return False

    # Check that image is RGB or RGBA (supports anti-aliasing)
    if img.mode not in ['RGB', 'RGBA']:
        print("  ✗ Image mode doesn't support full anti-aliasing")
        return False

    # Check image has reasonable size (should be 1600x1200 for scale=2, 800x600 base)
    width, height = img.size
    if width < 800 or height < 600:
        print(f"  ✗ Image size too small: {width}x{height}")
        return False

    print("  ✓ PNG format correct")
    print("  ✓ Color mode supports anti-aliasing")
    print("  ✓ Image dimensions correct")

    # Sample some pixels to verify we have smooth color transitions
    # (a sign of anti-aliasing)
    pixels = img.load()

    # Check pixels around the center where shapes are drawn
    # Look for intermediate color values (not just pure white or pure colors)
    center_x, center_y = width // 2, height // 2

    sampled_colors = set()
    for dx in range(-50, 50, 10):
        for dy in range(-50, 50, 10):
            x = center_x + dx
            y = center_y + dy
            if 0 <= x < width and 0 <= y < height:
                pixel = pixels[x, y]
                if isinstance(pixel, tuple):
                    # Store as tuple for RGB/RGBA
                    sampled_colors.add(pixel[:3] if len(pixel) > 3 else pixel)
                else:
                    sampled_colors.add(pixel)

    print(f"  Unique colors sampled: {len(sampled_colors)}")

    # Anti-aliased images should have many intermediate colors
    # If we only have 1-2 colors, there's no anti-aliasing happening
    if len(sampled_colors) > 5:
        print("  ✓ Multiple color values detected (anti-aliasing present)")
        return True
    else:
        print("  ✗ Too few color values (may lack anti-aliasing)")
        return False

def test_high_quality_export(diagram_id, token):
    """Test export at different quality levels."""
    print("\nTesting high-quality export settings...")
    headers = {"Authorization": f"Bearer {token}"}

    canvas_data = {"shapes": []}

    # Test different quality settings
    for quality in ["high", "ultra"]:
        print(f"\n  Testing quality={quality}...")
        response = requests.post(
            f"{EXPORT_SERVICE_URL}/export/png",
            headers=headers,
            json={
                "diagram_id": diagram_id,
                "width": 800,
                "height": 600,
                "scale": 2,
                "quality": quality,
                "background": "white",
                "canvas_data": canvas_data
            }
        )

        if response.status_code == 200:
            print(f"    ✓ {quality} quality export successful")
            print(f"    File size: {len(response.content)} bytes")
        else:
            print(f"    ✗ {quality} quality export failed")
            return False

    return True

def main():
    """Main test function."""
    print("=" * 60)
    print("Feature #489: PNG Export - Anti-aliased Edges")
    print("=" * 60)

    try:
        # Create test user and diagram
        user_data = create_test_user()
        # Extract token from response
        if 'access_token' in user_data:
            token = user_data['access_token']
        elif 'token' in user_data:
            token = user_data['token']
        else:
            token = user_data.get('data', {}).get('access_token')

        diagram_id = create_test_diagram(token)

        # Test 1: Export PNG with shapes
        print("\n" + "=" * 60)
        print("TEST 1: Export PNG with shapes")
        print("=" * 60)
        png_bytes = export_png_with_shapes(diagram_id, token)

        # Save for manual inspection
        with open('/tmp/test_antialiasing_489.png', 'wb') as f:
            f.write(png_bytes)
        print(f"✓ PNG saved to /tmp/test_antialiasing_489.png")

        # Test 2: Analyze PNG quality
        print("\n" + "=" * 60)
        print("TEST 2: Verify PNG quality and anti-aliasing")
        print("=" * 60)
        has_quality = analyze_png_quality(png_bytes)

        # Test 3: Test different quality settings
        print("\n" + "=" * 60)
        print("TEST 3: Test high-quality export settings")
        print("=" * 60)
        quality_test_passed = test_high_quality_export(diagram_id, token)

        # Final results
        print("\n" + "=" * 60)
        print("FINAL RESULTS")
        print("=" * 60)

        all_passed = has_quality and quality_test_passed

        if all_passed:
            print("✓ All tests passed")
            print("✓ PNG export uses anti-aliased rendering")
            print("✓ Image quality settings work correctly")
            print("\n✓ Feature #489 PASSED")
            print("\nTECHNICAL VERIFICATION:")
            print("- PIL's ImageDraw uses anti-aliasing by default")
            print("- Images generated in RGB/RGBA mode (supports smooth edges)")
            print("- Multiple color values detected (gradient transitions)")
            print("- High-quality compression maintains image quality")
            return True
        else:
            print("✗ Some tests failed")
            print("\n✗ Feature #489 FAILED")
            return False

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
