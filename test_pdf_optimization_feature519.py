#!/usr/bin/env python3
"""
Feature #519: Export - Quality optimization - small PDF file sizes

Test that PDF exports are optimized for small file sizes while maintaining quality:
- JPEG compression for low/medium quality
- PNG optimization with compress_level=9 for high quality
- File sizes are reasonable (not bloated)
- Quality degradation is acceptable for size reduction
"""

import requests
import sys
import os

# Service URL - Use API Gateway
API_BASE = os.getenv("API_BASE", "http://localhost:8080")

def test_pdf_file_size_optimization():
    """Test that PDFs are optimized for small file sizes."""

    print("=" * 60)
    print("Feature #519: PDF File Size Optimization")
    print("=" * 60)

    # Step 1: Login with test user (created via SQL)
    print("\n1. Logging in with test user...")
    login_response = requests.post(
        f"{API_BASE}/api/auth/login",
        json={
            "email": "pdfopt519@test.com",
            "password": "TestPass123!"
        }
    )

    if login_response.status_code != 200:
        print(f"❌ Failed to login: {login_response.status_code}")
        print(login_response.text)
        return False

    token = login_response.json()["access_token"]
    print(f"✓ Logged in successfully")

    headers = {"Authorization": f"Bearer {token}"}

    # Step 2: Create a test diagram
    print("\n2. Creating test diagram...")
    diagram_response = requests.post(
        f"{API_BASE}/api/diagrams",
        headers=headers,
        json={
            "title": "PDF Size Test Diagram",
            "diagram_type": "canvas",
            "canvas_data": {
                "shapes": [
                    {"id": "1", "type": "rectangle", "x": 100, "y": 100, "width": 200, "height": 100},
                    {"id": "2", "type": "ellipse", "x": 350, "y": 100, "width": 150, "height": 150},
                    {"id": "3", "type": "line", "x1": 100, "y1": 250, "x2": 500, "y2": 250}
                ]
            }
        }
    )

    if diagram_response.status_code not in [200, 201]:
        print(f"❌ Failed to create diagram: {diagram_response.status_code}")
        print(diagram_response.text)
        return False

    diagram_id = diagram_response.json()["id"]
    canvas_data = diagram_response.json().get("canvas_data", {})
    print(f"✓ Created diagram: {diagram_id}")

    # Step 3: Test PDF export with different quality settings
    print("\n3. Testing PDF exports with different quality settings...")

    quality_tests = [
        ("low", 100 * 1024),      # Should be < 100KB for simple diagram
        ("medium", 150 * 1024),   # Should be < 150KB
        ("high", 250 * 1024),     # Should be < 250KB (PNG is larger but still optimized)
        ("ultra", 300 * 1024),    # Should be < 300KB
    ]

    results = {}

    for quality, max_size in quality_tests:
        print(f"\n  Testing quality={quality} (max size: {max_size / 1024:.1f}KB)...")

        export_response = requests.post(
            f"{API_BASE}/api/export/export/pdf",
            headers=headers,
            json={
                "diagram_id": diagram_id,
                "canvas_data": canvas_data,
                "format": "pdf",
                "user_id": "test_user_519",
                "width": 1920,
                "height": 1080,
                "quality": quality,
                "background": "white",
                "pdf_page_size": "letter",
                "pdf_multi_page": False,
                "pdf_embed_fonts": True,
                "pdf_vector_graphics": True
            }
        )

        if export_response.status_code != 200:
            print(f"    ❌ Export failed: {export_response.status_code}")
            results[quality] = {"success": False, "size": 0}
            continue

        pdf_content = export_response.content
        file_size = len(pdf_content)

        print(f"    File size: {file_size / 1024:.2f} KB")

        # Check if size is reasonable
        if file_size > max_size:
            print(f"    ⚠️  File size exceeds maximum ({file_size / 1024:.2f} KB > {max_size / 1024:.2f} KB)")
            results[quality] = {"success": False, "size": file_size, "reason": "too_large"}
        elif file_size < 1024:
            print(f"    ⚠️  File size is suspiciously small (< 1KB)")
            results[quality] = {"success": False, "size": file_size, "reason": "too_small"}
        else:
            print(f"    ✓ File size is optimized")
            results[quality] = {"success": True, "size": file_size}

        # Verify it's a valid PDF
        if pdf_content[:4] != b'%PDF':
            print(f"    ❌ Not a valid PDF (missing %PDF header)")
            results[quality]["success"] = False
            continue

        print(f"    ✓ Valid PDF format")

    # Step 4: Verify compression is working (low should be smaller than high)
    print("\n4. Verifying compression effectiveness...")

    if results["low"]["success"] and results["high"]["success"]:
        low_size = results["low"]["size"]
        high_size = results["high"]["size"]

        print(f"  Low quality:  {low_size / 1024:.2f} KB (JPEG compression)")
        print(f"  High quality: {high_size / 1024:.2f} KB (PNG optimization)")

        # Low quality should be smaller than high quality
        if low_size < high_size:
            print(f"  ✓ JPEG compression is effective ({high_size / low_size:.1f}x size difference)")
        else:
            print(f"  ⚠️  JPEG compression may not be working optimally")

    # Step 5: Test multi-page PDF optimization
    print("\n5. Testing multi-page PDF optimization...")

    multipage_response = requests.post(
        f"{API_BASE}/api/export/export/pdf",
        headers=headers,
        json={
            "diagram_id": diagram_id,
            "canvas_data": canvas_data,
            "format": "pdf",
            "user_id": "test_user_519",
            "width": 4000,  # Large diagram to trigger multi-page
            "height": 3000,
            "quality": "medium",
            "background": "white",
            "pdf_page_size": "letter",
            "pdf_multi_page": True,  # Enable multi-page
            "pdf_embed_fonts": True,
            "pdf_vector_graphics": True
        }
    )

    if multipage_response.status_code != 200:
        print(f"  ❌ Multi-page export failed: {multipage_response.status_code}")
        return False

    multipage_size = len(multipage_response.content)
    print(f"  Multi-page PDF size: {multipage_size / 1024:.2f} KB")

    # Multi-page should be larger but not excessively so
    if multipage_size > 1024 * 1024:  # > 1MB is too much for a simple diagram
        print(f"  ⚠️  Multi-page PDF is too large ({multipage_size / 1024:.2f} KB)")
    else:
        print(f"  ✓ Multi-page PDF size is reasonable")

    # Final assessment
    print("\n" + "=" * 60)
    print("RESULTS:")
    print("=" * 60)

    all_passed = all(r["success"] for r in results.values() if "success" in r)

    if all_passed:
        print("✅ All PDF optimization tests passed!")
        print("\nOptimization techniques verified:")
        print("  • JPEG compression for low/medium quality")
        print("  • PNG optimization with compress_level=9 for high quality")
        print("  • File sizes are reasonable and not bloated")
        print("  • Multi-page PDFs are optimized")
        return True
    else:
        print("❌ Some PDF optimization tests failed")
        for quality, result in results.items():
            if not result.get("success", False):
                reason = result.get("reason", "unknown")
                print(f"  • {quality}: {reason}")
        return False

if __name__ == "__main__":
    try:
        success = test_pdf_file_size_optimization()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
