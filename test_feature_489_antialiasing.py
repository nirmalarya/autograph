#!/usr/bin/env python3
"""
Test Feature #489: PNG Export - Anti-aliased Edges

This test verifies that PNG exports have smooth, anti-aliased edges
rather than jagged, pixelated edges.

Steps:
1. Export PNG
2. Zoom into edges
3. Verify smooth anti-aliasing
4. Verify no jagged edges
"""

import requests
import io
import json
from PIL import Image
import numpy as np

# Configuration
API_BASE_URL = "http://localhost:8080/api"
EXPORT_SERVICE_URL = "http://localhost:8097"

def create_test_user():
    """Create a test user for authentication."""
    print("Creating test user...")
    response = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={
            "username": f"antialiasing_test_user",
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
                "username": f"antialiasing_test_user",
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

    # Create a simple canvas with shapes that will have visible edges
    canvas_data = {
        "shapes": [
            {
                "id": "shape1",
                "type": "rectangle",
                "x": 100,
                "y": 100,
                "width": 200,
                "height": 150,
                "fill": "#3498db",
                "stroke": "#2c3e50",
                "strokeWidth": 3
            },
            {
                "id": "shape2",
                "type": "ellipse",
                "x": 350,
                "y": 100,
                "width": 150,
                "height": 150,
                "fill": "#e74c3c",
                "stroke": "#c0392b",
                "strokeWidth": 3
            },
            {
                "id": "shape3",
                "type": "triangle",
                "x": 200,
                "y": 300,
                "width": 100,
                "height": 100,
                "fill": "#2ecc71",
                "stroke": "#27ae60",
                "strokeWidth": 3
            }
        ]
    }

    response = requests.post(
        f"{API_BASE_URL}/diagrams",
        headers=headers,
        json={
            "name": "Anti-aliasing Test Diagram",
            "type": "canvas",
            "canvas_data": canvas_data
        }
    )

    if response.status_code == 201:
        diagram = response.json()
        print(f"✓ Test diagram created: {diagram['id']}")
        return diagram['id']
    raise Exception(f"Failed to create diagram: {response.status_code} - {response.text}")

def export_png(diagram_id, token, scale=2):
    """Export diagram as PNG."""
    print(f"Exporting PNG (scale={scale}x)...")
    headers = {"Authorization": f"Bearer {token}"}

    # Simple canvas data for export
    canvas_data = {
        "shapes": [
            {
                "id": "circle1",
                "type": "ellipse",
                "x": 200,
                "y": 200,
                "width": 200,
                "height": 200,
                "fill": "#3498db",
                "stroke": "#2c3e50",
                "strokeWidth": 4
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
            "scale": scale,
            "quality": "high",
            "background": "white",
            "canvas_data": canvas_data
        }
    )

    if response.status_code == 200:
        print(f"✓ PNG exported successfully ({len(response.content)} bytes)")
        return response.content
    raise Exception(f"Failed to export PNG: {response.status_code} - {response.text}")

def analyze_edge_antialiasing(png_bytes):
    """
    Analyze PNG image edges for anti-aliasing.

    Anti-aliased edges should have:
    - Gradual color transitions (not sharp jumps)
    - Intermediate pixel values at boundaries
    - Smooth curves (not jagged staircase patterns)

    Returns:
        bool: True if edges appear anti-aliased, False otherwise
    """
    print("\nAnalyzing edge anti-aliasing...")

    # Load image
    img = Image.open(io.BytesIO(png_bytes))
    img_array = np.array(img)

    print(f"  Image size: {img.size}")
    print(f"  Image mode: {img.mode}")

    # Convert to grayscale for edge analysis
    if len(img_array.shape) == 3:
        # RGB image, convert to grayscale
        gray = np.dot(img_array[..., :3], [0.299, 0.587, 0.114])
    else:
        gray = img_array

    # Sample multiple edge regions
    # Look for the circular shape we drew
    height, width = gray.shape
    center_x, center_y = width // 2, height // 2 - 50

    # Sample points around where the circle edge should be
    # For a circle centered at (center_x, center_y) with radius ~80
    radius = 80

    # Check for smooth gradients at edge boundaries
    has_antialiasing = False
    intermediate_pixels = 0
    total_samples = 0

    # Sample along the top edge of the circle
    for x in range(center_x - radius, center_x + radius, 10):
        # Find the edge transition
        for y in range(center_y - radius - 20, center_y - radius + 20):
            if y >= 0 and y < height and x >= 0 and x < width:
                total_samples += 1
                pixel_value = gray[y, x]

                # Check if pixel is an intermediate value (not pure white or pure shape color)
                # Anti-aliased edges should have values between background and foreground
                if 50 < pixel_value < 240:  # Not pure white (255) or pure dark
                    intermediate_pixels += 1

    if total_samples > 0:
        intermediate_ratio = intermediate_pixels / total_samples
        print(f"  Intermediate pixels: {intermediate_pixels}/{total_samples} ({intermediate_ratio*100:.1f}%)")

        # If we have intermediate pixels, that's a sign of anti-aliasing
        # Even a small percentage indicates anti-aliasing is working
        has_antialiasing = intermediate_ratio > 0.05  # At least 5% intermediate pixels

    # Additional check: Look for gradual transitions
    # Sample a vertical line through the circle edge
    x_sample = center_x + radius
    if x_sample < width:
        edge_values = []
        for y in range(max(0, center_y - 30), min(height, center_y + 30)):
            edge_values.append(gray[y, x_sample])

        if len(edge_values) > 1:
            # Calculate gradient changes
            gradients = np.diff(edge_values)
            max_gradient = np.max(np.abs(gradients))
            print(f"  Max gradient change: {max_gradient:.1f}")

            # Anti-aliased edges should have moderate gradients, not sharp jumps
            # A sharp jump would be close to 255 (white to black)
            # Anti-aliased edges should have smaller, more gradual changes
            if max_gradient < 200:  # Not a sharp edge
                has_antialiasing = True

    return has_antialiasing

def verify_no_jagged_edges(png_bytes):
    """
    Verify that edges are smooth, not jagged.

    Jagged edges appear as staircase patterns.
    Anti-aliased edges are smooth curves.
    """
    print("\nVerifying no jagged edges...")

    img = Image.open(io.BytesIO(png_bytes))
    img_array = np.array(img)

    # Convert to grayscale
    if len(img_array.shape) == 3:
        gray = np.dot(img_array[..., :3], [0.299, 0.587, 0.114])
    else:
        gray = img_array

    # Look for staircase patterns along edges
    # A jagged edge would show up as repeated patterns of horizontal/vertical jumps
    # An anti-aliased edge shows smooth transitions

    # We'll check if edge pixels have neighbors that smooth the transition
    # rather than abrupt changes

    height, width = gray.shape

    # Sample the center region where our shapes are
    sample_region = gray[height//4:3*height//4, width//4:3*width//4]

    # Calculate edge strength using Sobel operator
    from scipy import ndimage
    sx = ndimage.sobel(sample_region, axis=0, mode='constant')
    sy = ndimage.sobel(sample_region, axis=1, mode='constant')
    edge_strength = np.hypot(sx, sy)

    # Analyze edge smoothness
    # Jagged edges have high-frequency components
    # Smooth edges have low-frequency components
    mean_edge_strength = np.mean(edge_strength[edge_strength > 0])
    max_edge_strength = np.max(edge_strength)

    print(f"  Mean edge strength: {mean_edge_strength:.2f}")
    print(f"  Max edge strength: {max_edge_strength:.2f}")

    # Anti-aliased edges should have moderate edge strength
    # Very high edge strength indicates sharp, jagged edges
    is_smooth = max_edge_strength < 150

    return is_smooth

def main():
    """Main test function."""
    print("=" * 60)
    print("Feature #489: PNG Export - Anti-aliased Edges")
    print("=" * 60)

    try:
        # Step 1: Create test user
        user_data = create_test_user()
        token = user_data.get('access_token') or user_data.get('token')

        # Step 2: Create test diagram
        diagram_id = create_test_diagram(token)

        # Step 3: Export PNG at 2x scale for better analysis
        png_bytes = export_png(diagram_id, token, scale=2)

        # Save for manual inspection
        with open('/tmp/test_antialiasing.png', 'wb') as f:
            f.write(png_bytes)
        print(f"✓ PNG saved to /tmp/test_antialiasing.png for manual inspection")

        # Step 4: Analyze anti-aliasing
        has_antialiasing = analyze_edge_antialiasing(png_bytes)

        # Step 5: Verify no jagged edges
        has_smooth_edges = verify_no_jagged_edges(png_bytes)

        # Results
        print("\n" + "=" * 60)
        print("TEST RESULTS")
        print("=" * 60)

        if has_antialiasing:
            print("✓ Anti-aliasing detected: Edges show smooth gradients")
        else:
            print("✗ Anti-aliasing not detected: Edges appear sharp")

        if has_smooth_edges:
            print("✓ Smooth edges verified: No jagged patterns detected")
        else:
            print("✗ Jagged edges detected: Edge patterns appear stepped")

        if has_antialiasing and has_smooth_edges:
            print("\n✓ Feature #489 PASSED: PNG export has anti-aliased edges")
            return True
        else:
            print("\n✗ Feature #489 FAILED: PNG export lacks proper anti-aliasing")
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
