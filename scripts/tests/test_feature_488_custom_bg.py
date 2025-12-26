#!/usr/bin/env python3
"""
Feature #488: PNG Export with Custom Background Color
Tests PNG export with various background colors including custom hex colors.
"""
import requests
import hashlib
from PIL import Image
import io
import urllib.parse

# Configuration
API_BASE_URL = "http://localhost:8080/api"

def setup():
    """Create test user and diagram."""
    # Use pre-verified test user
    email = "feature488@test.com"
    password = "SecurePass123!"

    # Login to get token
    login_response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"email": email, "password": password}
    )

    if login_response.status_code != 200:
        raise Exception(f"Failed to login: {login_response.text}")

    token = login_response.json()["access_token"]

    # Create diagram
    create_response = requests.post(
        f"{API_BASE_URL}/diagrams",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Feature 488 - Custom Background Test",
            "type": "canvas",
            "canvas_data": {
                "shapes": [
                    {"id": "1", "type": "rectangle", "x": 100, "y": 100, "width": 200, "height": 100}
                ]
            }
        }
    )

    if create_response.status_code not in [200, 201]:
        raise Exception(f"Failed to create diagram: {create_response.text}")

    diagram_id = create_response.json()["id"]

    return token, diagram_id


def get_dominant_color(image_bytes):
    """Get the dominant color from an image."""
    img = Image.open(io.BytesIO(image_bytes))
    # Get pixel at top-left corner (background)
    pixels = img.getdata()
    # Get first pixel (should be background)
    if img.mode == 'RGBA':
        r, g, b, a = pixels[0]
    else:
        r, g, b = pixels[0]
    return (r, g, b)


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def test_custom_background_blue():
    """Test PNG export with custom blue background (#3498db)."""
    print("\n" + "="*70)
    print("TEST: PNG Export with Custom Blue Background")
    print("="*70)

    token, diagram_id = setup()

    # Export with custom blue background
    background = "#3498db"
    # URL-encode the # symbol
    background_encoded = urllib.parse.quote(background, safe='')
    export_response = requests.post(
        f"{API_BASE_URL}/diagrams/{diagram_id}/export/png?background={background_encoded}",
        headers={"Authorization": f"Bearer {token}"}
    )

    print(f"\n1. Export PNG with background={background}")
    print(f"   Status: {export_response.status_code}")
    print(f"   Content-Type: {export_response.headers.get('Content-Type')}")
    print(f"   Size: {len(export_response.content)} bytes")

    assert export_response.status_code == 200, f"Expected 200, got {export_response.status_code}"
    assert export_response.headers.get('Content-Type') == 'image/png', "Expected PNG content type"

    # Verify image has blue background
    dominant_color = get_dominant_color(export_response.content)
    expected_color = hex_to_rgb(background)

    print(f"\n2. Verify blue background")
    print(f"   Expected RGB: {expected_color}")
    print(f"   Actual RGB: {dominant_color}")

    # Allow small tolerance for JPEG-like compression artifacts
    color_diff = sum(abs(a - b) for a, b in zip(dominant_color, expected_color))
    assert color_diff <= 10, f"Background color mismatch: expected {expected_color}, got {dominant_color}"

    print(f"   ✓ Color match (diff: {color_diff})")
    print("\n✅ PASSED: Custom blue background")
    return True


def test_custom_background_white():
    """Test PNG export with white background."""
    print("\n" + "="*70)
    print("TEST: PNG Export with White Background")
    print("="*70)

    token, diagram_id = setup()

    # Export with white background
    background = "white"
    export_response = requests.post(
        f"{API_BASE_URL}/diagrams/{diagram_id}/export/png?background={background}",
        headers={"Authorization": f"Bearer {token}"}
    )

    print(f"\n1. Export PNG with background=white")
    print(f"   Status: {export_response.status_code}")

    assert export_response.status_code == 200, f"Expected 200, got {export_response.status_code}"

    # Verify image has white background
    dominant_color = get_dominant_color(export_response.content)
    expected_color = (255, 255, 255)

    print(f"\n2. Verify white background")
    print(f"   Expected RGB: {expected_color}")
    print(f"   Actual RGB: {dominant_color}")

    assert dominant_color == expected_color, f"Background color mismatch"

    print("\n✅ PASSED: White background")
    return True


def test_custom_background_black():
    """Test PNG export with black background (#000000)."""
    print("\n" + "="*70)
    print("TEST: PNG Export with Black Background")
    print("="*70)

    token, diagram_id = setup()

    # Export with black background
    background = "#000000"
    background_encoded = urllib.parse.quote(background, safe='')
    export_response = requests.post(
        f"{API_BASE_URL}/diagrams/{diagram_id}/export/png?background={background_encoded}",
        headers={"Authorization": f"Bearer {token}"}
    )

    print(f"\n1. Export PNG with background={background}")
    print(f"   Status: {export_response.status_code}")

    assert export_response.status_code == 200, f"Expected 200, got {export_response.status_code}"

    # Verify image has black background
    dominant_color = get_dominant_color(export_response.content)
    expected_color = (0, 0, 0)

    print(f"\n2. Verify black background")
    print(f"   Expected RGB: {expected_color}")
    print(f"   Actual RGB: {dominant_color}")

    assert dominant_color == expected_color, f"Background color mismatch"

    print("\n✅ PASSED: Black background")
    return True


def test_custom_background_red():
    """Test PNG export with custom red background (#e74c3c)."""
    print("\n" + "="*70)
    print("TEST: PNG Export with Custom Red Background")
    print("="*70)

    token, diagram_id = setup()

    # Export with custom red background
    background = "#e74c3c"
    background_encoded = urllib.parse.quote(background, safe='')
    export_response = requests.post(
        f"{API_BASE_URL}/diagrams/{diagram_id}/export/png?background={background_encoded}",
        headers={"Authorization": f"Bearer {token}"}
    )

    print(f"\n1. Export PNG with background={background}")
    print(f"   Status: {export_response.status_code}")

    assert export_response.status_code == 200, f"Expected 200, got {export_response.status_code}"

    # Verify image has red background
    dominant_color = get_dominant_color(export_response.content)
    expected_color = hex_to_rgb(background)

    print(f"\n2. Verify red background")
    print(f"   Expected RGB: {expected_color}")
    print(f"   Actual RGB: {dominant_color}")

    color_diff = sum(abs(a - b) for a, b in zip(dominant_color, expected_color))
    assert color_diff <= 10, f"Background color mismatch"

    print(f"   ✓ Color match (diff: {color_diff})")
    print("\n✅ PASSED: Custom red background")
    return True


def test_custom_background_green():
    """Test PNG export with custom green background (#2ecc71)."""
    print("\n" + "="*70)
    print("TEST: PNG Export with Custom Green Background")
    print("="*70)

    token, diagram_id = setup()

    # Export with custom green background
    background = "#2ecc71"
    background_encoded = urllib.parse.quote(background, safe='')
    export_response = requests.post(
        f"{API_BASE_URL}/diagrams/{diagram_id}/export/png?background={background_encoded}",
        headers={"Authorization": f"Bearer {token}"}
    )

    print(f"\n1. Export PNG with background={background}")
    print(f"   Status: {export_response.status_code}")

    assert export_response.status_code == 200, f"Expected 200, got {export_response.status_code}"

    # Verify image has green background
    dominant_color = get_dominant_color(export_response.content)
    expected_color = hex_to_rgb(background)

    print(f"\n2. Verify green background")
    print(f"   Expected RGB: {expected_color}")
    print(f"   Actual RGB: {dominant_color}")

    color_diff = sum(abs(a - b) for a, b in zip(dominant_color, expected_color))
    assert color_diff <= 10, f"Background color mismatch"

    print(f"   ✓ Color match (diff: {color_diff})")
    print("\n✅ PASSED: Custom green background")
    return True


if __name__ == "__main__":
    try:
        # Test various background colors
        test_custom_background_blue()
        test_custom_background_white()
        test_custom_background_black()
        test_custom_background_red()
        test_custom_background_green()

        print("\n" + "="*70)
        print("🎉 ALL TESTS PASSED - Feature #488 Complete!")
        print("="*70)
        print("\nSUMMARY:")
        print("✓ Blue background (#3498db)")
        print("✓ White background (white)")
        print("✓ Black background (#000000)")
        print("✓ Red background (#e74c3c)")
        print("✓ Green background (#2ecc71)")
        print("\nFeature #488 is working correctly!")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
