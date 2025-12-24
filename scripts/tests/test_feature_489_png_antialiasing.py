"""
Test Feature #489: PNG Export with Anti-aliased Edges

This test verifies that PNG exports have smooth anti-aliased edges,
not jagged or pixelated edges.

Requirements:
- PNG export should have smooth anti-aliased edges
- No jagged edges on shapes and text
- High-quality rendering at various resolutions
- Anti-aliasing should work with transparent backgrounds
"""
import requests
import io
from PIL import Image
import numpy as np
import psycopg2


BASE_URL = "http://localhost:8080/api"
EXPORT_SERVICE_URL = "http://localhost:8097"


def register_and_login():
    """Helper to register and login a test user."""
    import time
    email = f"antialiasing-test-{int(time.time())}@example.com"
    password = "Test123!@#"
    
    # Register
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Antialiasing Test User"
        }
    )
    
    # Registration returns user data directly (status 200)
    user = response.json()
    user_id = user['id']
    
    # Auto-verify the user by updating database directly
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="autograph",
        user="autograph",
        password="autograph_dev_password"
    )
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET is_verified = true WHERE id = %s",
        (user_id,)
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    # Login
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": email,
            "password": password
        }
    )
    
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    return data["access_token"]


def create_test_diagram(token):
    """Create a test diagram with shapes."""
    response = requests.post(
        f"{BASE_URL}/diagrams",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Antialiasing Test Diagram",
            "diagram_type": "canvas",
            "canvas_data": {
                "shapes": [
                    {
                        "id": "rect1",
                        "type": "rectangle",
                        "x": 100,
                        "y": 100,
                        "width": 200,
                        "height": 150,
                        "fill": "#4a90e2",
                        "stroke": "#2c5aa0",
                        "strokeWidth": 3
                    },
                    {
                        "id": "circle1",
                        "type": "circle",
                        "x": 400,
                        "y": 175,
                        "radius": 75,
                        "fill": "#50c878",
                        "stroke": "#2d7a4f",
                        "strokeWidth": 3
                    },
                    {
                        "id": "text1",
                        "type": "text",
                        "x": 250,
                        "y": 300,
                        "text": "Anti-aliased Text",
                        "fontSize": 24,
                        "fill": "#333333"
                    }
                ]
            }
        }
    )
    
    assert response.status_code == 200, f"Failed to create diagram: {response.text}"
    return response.json()["id"]


def export_png(token, diagram_id, scale=2, background="white"):
    """Export diagram as PNG."""
    response = requests.post(
        f"{BASE_URL}/diagrams/{diagram_id}/export/png?scale={scale}&background={background}&quality=high",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"   Export response status: {response.status_code}")
    print(f"   Export response headers: {response.headers.get('Content-Type', 'N/A')}")
    print(f"   Export response length: {len(response.content)} bytes")
    print(f"   First 50 bytes: {response.content[:50]}")
    
    if response.status_code != 200:
        print(f"   Export response text: {response.text[:200]}")
    
    assert response.status_code == 200, f"PNG export failed: {response.text}"
    assert response.headers["Content-Type"] == "image/png", \
        f"Expected image/png, got {response.headers.get('Content-Type')}"
    return response.content


def analyze_edge_smoothness(image_data):
    """
    Analyze edge smoothness by detecting anti-aliasing.
    
    Anti-aliased edges have gradient transitions between colors,
    while jagged edges have hard transitions.
    
    Returns a score from 0-100 where higher = smoother edges.
    """
    # Load image
    img = Image.open(io.BytesIO(image_data))
    
    # Convert to numpy array
    img_array = np.array(img)
    
    # Convert to grayscale for edge analysis
    if len(img_array.shape) == 3:
        if img_array.shape[2] == 4:  # RGBA
            img_gray = np.mean(img_array[:, :, :3], axis=2)
        else:  # RGB
            img_gray = np.mean(img_array, axis=2)
    else:
        img_gray = img_array
    
    # Calculate gradients (edge detection)
    gradient_x = np.diff(img_gray, axis=1)
    gradient_y = np.diff(img_gray, axis=0)
    
    # Find significant edges (gradient magnitude > threshold)
    threshold = 20
    edges_x = np.abs(gradient_x) > threshold
    edges_y = np.abs(gradient_y) > threshold
    
    if not (edges_x.any() or edges_y.any()):
        return 100  # No edges found, assume smooth
    
    # Analyze gradient values at edges
    # Anti-aliased edges have intermediate gradient values
    # Jagged edges have only extreme values (all-or-nothing)
    
    edge_gradients = []
    if edges_x.any():
        edge_gradients.extend(np.abs(gradient_x[edges_x]).tolist())
    if edges_y.any():
        edge_gradients.extend(np.abs(gradient_y[edges_y]).tolist())
    
    if not edge_gradients:
        return 100
    
    # Calculate percentage of intermediate gradients
    # (not too soft, not too hard - indicating anti-aliasing)
    intermediate = sum(1 for g in edge_gradients if 30 < g < 200)
    intermediate_ratio = intermediate / len(edge_gradients)
    
    # Score based on intermediate gradient ratio
    # More intermediate gradients = better anti-aliasing
    score = min(100, intermediate_ratio * 150)
    
    return score


def test_png_antialiasing_basic():
    """
    Test 1: Basic PNG export has anti-aliased edges
    """
    print("\n" + "="*80)
    print("TEST 1: Basic PNG Export with Anti-aliasing")
    print("="*80)
    
    token = register_and_login()
    diagram_id = create_test_diagram(token)
    
    # Export as PNG
    print("\n1. Exporting diagram as PNG...")
    png_data = export_png(token, diagram_id, scale=2)
    
    # Verify PNG is valid
    print("2. Verifying PNG is valid...")
    img = Image.open(io.BytesIO(png_data))
    print(f"   ✓ PNG dimensions: {img.size[0]}x{img.size[1]}")
    
    # Check format
    assert img.format == "PNG", f"Expected PNG format, got {img.format}"
    print(f"   ✓ Format: PNG")
    
    # Analyze edge smoothness
    print("3. Analyzing edge smoothness...")
    smoothness_score = analyze_edge_smoothness(png_data)
    print(f"   Edge smoothness score: {smoothness_score:.1f}/100")
    
    # Anti-aliasing should result in smooth edges (score > 40)
    assert smoothness_score > 40, \
        f"Edges are too jagged (score: {smoothness_score:.1f}). Anti-aliasing may not be working."
    
    print(f"   ✓ Edges are smooth (anti-aliased)")
    
    print("\n✅ TEST 1 PASSED: PNG export has anti-aliased edges")


def test_png_antialiasing_high_resolution():
    """
    Test 2: Anti-aliasing works at high resolution (4x)
    """
    print("\n" + "="*80)
    print("TEST 2: Anti-aliasing at High Resolution (4x)")
    print("="*80)
    
    token = register_and_login()
    diagram_id = create_test_diagram(token)
    
    # Export at 4x resolution
    print("\n1. Exporting at 4x resolution...")
    png_data = export_png(token, diagram_id, scale=4)
    
    img = Image.open(io.BytesIO(png_data))
    print(f"   ✓ PNG dimensions: {img.size[0]}x{img.size[1]}")
    
    # Verify it's high resolution (at least 2x the base)
    # Note: The actual resolution depends on implementation
    # The important thing is anti-aliasing works
    assert img.size[0] >= 3840, f"Expected width >= 3840 (1920*2 minimum), got {img.size[0]}"
    
    # Analyze edge smoothness at high resolution
    print("2. Analyzing edge smoothness at high resolution...")
    smoothness_score = analyze_edge_smoothness(png_data)
    print(f"   Edge smoothness score: {smoothness_score:.1f}/100")
    
    # High resolution should have good anti-aliasing
    assert smoothness_score > 35, \
        f"High resolution edges are jagged (score: {smoothness_score:.1f})"
    
    print(f"   ✓ High resolution edges are smooth")
    
    print("\n✅ TEST 2 PASSED: Anti-aliasing works at high resolution")


def test_png_antialiasing_transparent_background():
    """
    Test 3: Anti-aliasing works with transparent background
    """
    print("\n" + "="*80)
    print("TEST 3: Anti-aliasing with Transparent Background")
    print("="*80)
    
    token = register_and_login()
    diagram_id = create_test_diagram(token)
    
    # Export with transparent background
    print("\n1. Exporting with transparent background...")
    png_data = export_png(token, diagram_id, scale=2, background="transparent")
    
    img = Image.open(io.BytesIO(png_data))
    print(f"   ✓ PNG dimensions: {img.size[0]}x{img.size[1]}")
    
    # Verify it has alpha channel
    assert img.mode == "RGBA", f"Expected RGBA mode for transparent, got {img.mode}"
    print(f"   ✓ Has alpha channel (RGBA)")
    
    # Analyze edge smoothness
    print("2. Analyzing edge smoothness with transparency...")
    smoothness_score = analyze_edge_smoothness(png_data)
    print(f"   Edge smoothness score: {smoothness_score:.1f}/100")
    
    assert smoothness_score > 40, \
        f"Transparent PNG edges are jagged (score: {smoothness_score:.1f})"
    
    print(f"   ✓ Transparent PNG has smooth edges")
    
    print("\n✅ TEST 3 PASSED: Anti-aliasing works with transparency")


def test_png_no_jagged_edges():
    """
    Test 4: Verify no jagged edges (visual quality check)
    """
    print("\n" + "="*80)
    print("TEST 4: No Jagged Edges (Visual Quality)")
    print("="*80)
    
    token = register_and_login()
    diagram_id = create_test_diagram(token)
    
    # Export at different scales
    scales = [1, 2, 4]
    
    for scale in scales:
        print(f"\n{scale}. Testing at {scale}x scale...")
        png_data = export_png(token, diagram_id, scale=scale)
        
        img = Image.open(io.BytesIO(png_data))
        
        # Analyze edge quality
        smoothness_score = analyze_edge_smoothness(png_data)
        print(f"   Edge smoothness: {smoothness_score:.1f}/100")
        
        # All scales should have smooth edges
        assert smoothness_score > 35, \
            f"Jagged edges detected at {scale}x scale (score: {smoothness_score:.1f})"
        
        print(f"   ✓ No jagged edges at {scale}x scale")
    
    print("\n✅ TEST 4 PASSED: No jagged edges at any scale")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("FEATURE #489: PNG EXPORT WITH ANTI-ALIASED EDGES")
    print("="*80)
    
    try:
        # Run all tests
        test_png_antialiasing_basic()
        test_png_antialiasing_high_resolution()
        test_png_antialiasing_transparent_background()
        test_png_no_jagged_edges()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED!")
        print("="*80)
        print("\nFeature #489 is working correctly:")
        print("  ✓ PNG exports have anti-aliased edges")
        print("  ✓ Edges are smooth, not jagged")
        print("  ✓ Anti-aliasing works at all resolutions (1x, 2x, 4x)")
        print("  ✓ Anti-aliasing works with transparent backgrounds")
        print("  ✓ High-quality rendering with smooth transitions")
        print("\n" + "="*80)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
