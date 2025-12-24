#!/usr/bin/env python3
"""
Test script for Export via API feature.

Tests the POST /api/diagrams/{id}/export endpoint with different formats.
"""

import requests
import json
import uuid
from datetime import datetime

BASE_URL = "http://localhost:8082"
EXPORT_URL = "http://localhost:8097"

def create_test_diagram():
    """Create a test diagram."""
    diagram_data = {
        "title": f"Test Export API Diagram {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "type": "canvas",
        "canvas_data": {
            "shapes": [
                {
                    "id": str(uuid.uuid4()),
                    "type": "rectangle",
                    "x": 100,
                    "y": 100,
                    "width": 200,
                    "height": 100,
                    "fill": "#3b82f6",
                    "stroke": "#1d4ed8"
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "circle",
                    "x": 400,
                    "y": 150,
                    "radius": 50,
                    "fill": "#10b981",
                    "stroke": "#059669"
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "text",
                    "x": 150,
                    "y": 130,
                    "text": "Test Diagram",
                    "fontSize": 16
                }
            ]
        },
        "note_content": "# Test Diagram\n\nThis is a test diagram for API export.",
        "folder_id": None
    }
    
    # Create with Authorization header
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test-token"
    }
    
    response = requests.post(BASE_URL, json=diagram_data, headers=headers)
    
    if response.status_code == 201:
        data = response.json()
        print(f"✓ Created test diagram: {data['id']}")
        return data['id']
    else:
        print(f"✗ Failed to create diagram: {response.status_code}")
        print(f"  Response: {response.text}")
        return None


def test_export_format(diagram_id, format_type):
    """Test exporting a diagram in a specific format."""
    print(f"\nTesting {format_type.upper()} export...")
    
    export_data = {
        "format": format_type,
        "width": 1920,
        "height": 1080,
        "scale": 2,
        "quality": "high",
        "background": "white",
        "user_id": "test-user"
    }
    
    response = requests.post(
        f"{EXPORT_URL}/api/diagrams/{diagram_id}/export",
        json=export_data
    )
    
    if response.status_code == 200:
        content_length = len(response.content)
        content_type = response.headers.get('Content-Type', 'unknown')
        
        print(f"✓ {format_type.upper()} export successful")
        print(f"  - Status: {response.status_code}")
        print(f"  - Content-Type: {content_type}")
        print(f"  - Content-Length: {content_length} bytes")
        
        # Validate content
        if format_type == "png":
            # Check PNG magic number
            if response.content[:8] == b'\x89PNG\r\n\x1a\n':
                print(f"  ✓ Valid PNG file")
                return True
            else:
                print(f"  ✗ Invalid PNG file")
                return False
                
        elif format_type == "svg":
            # Check for SVG XML
            if b'<svg' in response.content[:100]:
                print(f"  ✓ Valid SVG file")
                return True
            else:
                print(f"  ✗ Invalid SVG file")
                return False
                
        elif format_type == "pdf":
            # Check PDF magic number
            if response.content[:4] == b'%PDF':
                print(f"  ✓ Valid PDF file")
                return True
            else:
                print(f"  ✗ Invalid PDF file")
                return False
                
        elif format_type == "json":
            # Try to parse JSON
            try:
                data = json.loads(response.content)
                print(f"  ✓ Valid JSON file")
                print(f"  - Keys: {list(data.keys())}")
                return True
            except:
                print(f"  ✗ Invalid JSON file")
                return False
                
        return True
    else:
        print(f"✗ {format_type.upper()} export failed")
        print(f"  - Status: {response.status_code}")
        print(f"  - Response: {response.text}")
        return False


def test_invalid_diagram():
    """Test exporting a non-existent diagram."""
    print(f"\nTesting invalid diagram ID...")
    
    fake_id = str(uuid.uuid4())
    export_data = {
        "format": "png",
        "user_id": "test-user"
    }
    
    response = requests.post(
        f"{EXPORT_URL}/api/diagrams/{fake_id}/export",
        json=export_data
    )
    
    if response.status_code == 404:
        print(f"✓ Correctly returned 404 for invalid diagram")
        return True
    else:
        print(f"✗ Expected 404, got {response.status_code}")
        return False


def test_invalid_format(diagram_id):
    """Test exporting with invalid format."""
    print(f"\nTesting invalid format...")
    
    export_data = {
        "format": "invalid",
        "user_id": "test-user"
    }
    
    response = requests.post(
        f"{EXPORT_URL}/api/diagrams/{diagram_id}/export",
        json=export_data
    )
    
    if response.status_code == 400:
        print(f"✓ Correctly returned 400 for invalid format")
        return True
    else:
        print(f"✗ Expected 400, got {response.status_code}")
        return False


def main():
    """Run all tests."""
    print("=" * 80)
    print("Testing Export via API Feature")
    print("=" * 80)
    
    # Create test diagram
    diagram_id = create_test_diagram()
    if not diagram_id:
        print("\n✗ Failed to create test diagram. Aborting tests.")
        return
    
    # Test different formats
    results = {
        "PNG Export": test_export_format(diagram_id, "png"),
        "SVG Export": test_export_format(diagram_id, "svg"),
        "PDF Export": test_export_format(diagram_id, "pdf"),
        "JSON Export": test_export_format(diagram_id, "json"),
        "Invalid Diagram": test_invalid_diagram(),
        "Invalid Format": test_invalid_format(diagram_id)
    }
    
    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
