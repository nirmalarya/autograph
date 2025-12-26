#!/usr/bin/env python3
"""Test Feature #506: Batch export all diagrams to ZIP"""
import requests
import json
import io
import zipfile

BASE_URL = "http://localhost:8097"

def test_batch_export_to_zip():
    """
    Feature #506: Export - Batch export all diagrams to ZIP

    Tests:
    - POST /export/batch with multiple diagrams
    - Returns ZIP file with all diagrams
    - Proper ZIP structure and content
    """
    print("\n" + "="*60)
    print("Testing Feature #506: Batch Export to ZIP")
    print("="*60)

    # Sample diagram data for batch export
    batch_request = {
        "diagrams": [
            {
                "diagram_id": "test-diagram-1",
                "title": "First Diagram",
                "canvas_data": {
                    "shapes": [
                        {"id": "shape1", "type": "rectangle", "x": 100, "y": 100, "width": 200, "height": 150}
                    ]
                }
            },
            {
                "diagram_id": "test-diagram-2",
                "title": "Second Diagram",
                "canvas_data": {
                    "shapes": [
                        {"id": "shape2", "type": "circle", "x": 300, "y": 200, "radius": 100}
                    ]
                }
            },
            {
                "diagram_id": "test-diagram-3",
                "title": "Third Diagram",
                "canvas_data": {
                    "shapes": [
                        {"id": "shape3", "type": "text", "x": 50, "y": 50, "text": "Hello"}
                    ]
                }
            }
        ],
        "format": "png",
        "width": 1920,
        "height": 1080,
        "scale": 2,
        "quality": "high",
        "background": "white",
        "user_id": "test-user-506"
    }

    try:
        # Test batch export
        print("\n1. Testing batch export to ZIP...")
        response = requests.post(
            f"{BASE_URL}/export/batch",
            json=batch_request,
            timeout=30
        )

        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type')}")
        print(f"   Content-Disposition: {response.headers.get('Content-Disposition')}")

        if response.status_code == 200:
            # Verify it's a ZIP file
            content_type = response.headers.get('Content-Type', '')
            if 'zip' not in content_type:
                print(f"   ❌ Expected ZIP content type, got: {content_type}")
                return False

            # Parse ZIP file
            zip_data = io.BytesIO(response.content)
            with zipfile.ZipFile(zip_data, 'r') as zf:
                files = zf.namelist()
                print(f"   ZIP contains {len(files)} files:")
                for filename in files:
                    file_info = zf.getinfo(filename)
                    print(f"     - {filename} ({file_info.file_size} bytes)")

                # Verify we have all 3 diagrams
                if len(files) != 3:
                    print(f"   ❌ Expected 3 files in ZIP, got {len(files)}")
                    return False

                # Verify filenames
                expected_names = ["First Diagram.png", "Second Diagram.png", "Third Diagram.png"]
                for expected_name in expected_names:
                    if expected_name not in files:
                        print(f"   ❌ Expected file '{expected_name}' not found in ZIP")
                        return False

                print(f"   ✅ All expected files present in ZIP")
                print(f"   ZIP total size: {len(response.content)} bytes")

            print("\n✅ Feature #506 PASSED: Batch export to ZIP works correctly")
            return True
        else:
            print(f"   ❌ Request failed: {response.text}")
            return False

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_export_different_formats():
    """Test batch export with different formats (SVG, PDF, JSON)"""
    print("\n" + "="*60)
    print("Testing Batch Export - Multiple Formats")
    print("="*60)

    formats = ["svg", "pdf", "json"]

    for fmt in formats:
        print(f"\n2. Testing batch export with {fmt.upper()} format...")

        batch_request = {
            "diagrams": [
                {
                    "diagram_id": f"test-diagram-{fmt}-1",
                    "title": f"Diagram {fmt.upper()} One",
                    "canvas_data": {
                        "shapes": [
                            {"id": "shape1", "type": "rectangle", "x": 100, "y": 100}
                        ]
                    }
                },
                {
                    "diagram_id": f"test-diagram-{fmt}-2",
                    "title": f"Diagram {fmt.upper()} Two",
                    "canvas_data": {
                        "shapes": [
                            {"id": "shape2", "type": "circle", "x": 200, "y": 200}
                        ]
                    }
                }
            ],
            "format": fmt,
            "width": 800,
            "height": 600,
            "user_id": "test-user-506"
        }

        # Add PDF-specific parameters
        if fmt == "pdf":
            batch_request["pdf_page_size"] = "A4"
            batch_request["pdf_multi_page"] = False
            batch_request["pdf_embed_fonts"] = True
            batch_request["pdf_vector_graphics"] = True

        try:
            response = requests.post(
                f"{BASE_URL}/export/batch",
                json=batch_request,
                timeout=30
            )

            if response.status_code == 200:
                # Verify ZIP contains correct format files
                zip_data = io.BytesIO(response.content)
                with zipfile.ZipFile(zip_data, 'r') as zf:
                    files = zf.namelist()
                    all_correct_format = all(f.endswith(f".{fmt}") for f in files)
                    if all_correct_format:
                        print(f"   ✅ {fmt.upper()} batch export successful ({len(files)} files)")
                    else:
                        print(f"   ❌ Not all files have .{fmt} extension")
            else:
                print(f"   ❌ {fmt.upper()} batch export failed: {response.status_code}")

        except Exception as e:
            print(f"   ❌ Error testing {fmt}: {str(e)}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("FEATURE #506: BATCH EXPORT TO ZIP - COMPREHENSIVE TEST")
    print("="*60)

    success = test_batch_export_to_zip()
    test_batch_export_different_formats()

    print("\n" + "="*60)
    if success:
        print("FEATURE #506: ✅ PASSED")
        print("Batch export to ZIP functionality is working correctly!")
    else:
        print("FEATURE #506: ❌ FAILED")
        print("Batch export needs fixes")
    print("="*60)

    exit(0 if success else 1)
