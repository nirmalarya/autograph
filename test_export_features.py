#!/usr/bin/env python3
"""
Test Export Features (#484-496)
- PNG export (1x, 2x, 4x)
- PNG export options (transparent, custom background)
- SVG export (vector, scalable)
- PDF export
"""

import requests
import json
import time
import base64
from datetime import datetime

# Base URLs
AUTH_URL = "http://localhost:8085"
DIAGRAM_URL = "http://localhost:8082"

def decode_jwt_payload(token):
    """Decode JWT payload to get user_id."""
    parts = token.split('.')
    if len(parts) >= 2:
        payload = parts[1]
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    return None

def setup_test_user():
    """Register and login a test user."""
    email = f"exporttest_{int(time.time())}@example.com"
    password = "TestPass123!"
    
    # Register
    try:
        requests.post(f"{AUTH_URL}/register", json={
            "email": email,
            "password": password,
            "username": "exporttest"
        }, timeout=5)
    except:
        pass
    
    # Login
    response = requests.post(f"{AUTH_URL}/login", json={
        "email": email,
        "password": password
    }, timeout=5)
    
    if response.status_code == 200:
        data = response.json()
        token = data["access_token"]
        payload = decode_jwt_payload(token)
        user_id = payload.get("sub")
        return token, user_id, email
    
    raise Exception(f"Login failed: {response.status_code}")

def create_test_diagram(token, user_id):
    """Create a test diagram for export testing."""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }
    
    response = requests.post(f"{DIAGRAM_URL}/", json={
        "title": "Export Test Diagram",
        "file_type": "canvas",
        "canvas_data": {"shapes": [
            {"id": "shape1", "type": "rectangle", "x": 100, "y": 100, "width": 200, "height": 100},
            {"id": "shape2", "type": "circle", "x": 400, "y": 200, "radius": 50}
        ]},
        "note_content": "Test diagram for exports"
    }, headers=headers, timeout=5)
    
    if response.status_code in [200, 201]:
        return response.json()["id"]
    
    raise Exception(f"Failed to create diagram: {response.status_code}")

def run_tests():
    """Run all export tests."""
    print("=" * 80)
    print("TESTING EXPORT FEATURES #484-496")
    print("=" * 80)
    
    # Setup
    print("\n📋 SETUP: Creating test user and diagram...")
    token, user_id, email = setup_test_user()
    diagram_id = create_test_diagram(token, user_id)
    print(f"✅ Test user created: {email}")
    print(f"✅ Test diagram created: {diagram_id}")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }
    
    passed = 0
    total = 0
    
    # Test: PNG export 1x
    print("\n" + "=" * 80)
    print("Feature #484: PNG export 1x resolution")
    print("=" * 80)
    total += 1
    try:
        response = requests.post(
            f"{DIAGRAM_URL}/{diagram_id}/export/png?scale=1",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            if response.headers.get("content-type") == "image/png":
                print(f"✅ PASS: PNG export 1x successful")
                print(f"   Content-Type: {response.headers.get('content-type')}")
                print(f"   Size: {len(response.content)} bytes")
                passed += 1
            else:
                print(f"❌ FAIL: Wrong content type: {response.headers.get('content-type')}")
        else:
            print(f"❌ FAIL: Status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ FAIL: {e}")
    
    # Test: PNG export 2x (retina)
    print("\n" + "=" * 80)
    print("Feature #485: PNG export 2x resolution (retina)")
    print("=" * 80)
    total += 1
    try:
        response = requests.post(
            f"{DIAGRAM_URL}/{diagram_id}/export/png?scale=2",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            if response.headers.get("content-type") == "image/png":
                print(f"✅ PASS: PNG export 2x successful")
                print(f"   Content-Type: {response.headers.get('content-type')}")
                print(f"   Size: {len(response.content)} bytes (should be larger than 1x)")
                passed += 1
            else:
                print(f"❌ FAIL: Wrong content type")
        else:
            print(f"❌ FAIL: Status {response.status_code}")
    except Exception as e:
        print(f"❌ FAIL: {e}")
    
    # Test: PNG export 4x (ultra)
    print("\n" + "=" * 80)
    print("Feature #486: PNG export 4x resolution (ultra)")
    print("=" * 80)
    total += 1
    try:
        response = requests.post(
            f"{DIAGRAM_URL}/{diagram_id}/export/png?scale=4",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            if response.headers.get("content-type") == "image/png":
                print(f"✅ PASS: PNG export 4x successful")
                print(f"   Content-Type: {response.headers.get('content-type')}")
                print(f"   Size: {len(response.content)} bytes")
                passed += 1
            else:
                print(f"❌ FAIL: Wrong content type")
        else:
            print(f"❌ FAIL: Status {response.status_code}")
    except Exception as e:
        print(f"❌ FAIL: {e}")
    
    # Test: PNG export transparent background
    print("\n" + "=" * 80)
    print("Feature #487: PNG export transparent background")
    print("=" * 80)
    total += 1
    try:
        response = requests.post(
            f"{DIAGRAM_URL}/{diagram_id}/export/png?scale=2&background=transparent",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            if response.headers.get("content-type") == "image/png":
                print(f"✅ PASS: PNG export with transparent background successful")
                print(f"   Background: transparent")
                print(f"   Size: {len(response.content)} bytes")
                passed += 1
            else:
                print(f"❌ FAIL: Wrong content type")
        else:
            print(f"❌ FAIL: Status {response.status_code}")
    except Exception as e:
        print(f"❌ FAIL: {e}")
    
    # Test: PNG export white background
    print("\n" + "=" * 80)
    print("Feature #488: PNG export white background")
    print("=" * 80)
    total += 1
    try:
        response = requests.post(
            f"{DIAGRAM_URL}/{diagram_id}/export/png?scale=2&background=white",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            if response.headers.get("content-type") == "image/png":
                print(f"✅ PASS: PNG export with white background successful")
                print(f"   Background: white")
                print(f"   Size: {len(response.content)} bytes")
                passed += 1
            else:
                print(f"❌ FAIL: Wrong content type")
        else:
            print(f"❌ FAIL: Status {response.status_code}")
    except Exception as e:
        print(f"❌ FAIL: {e}")
    
    # Test: SVG export
    print("\n" + "=" * 80)
    print("Features #490-493: SVG export (vector, scalable)")
    print("=" * 80)
    total += 1
    try:
        response = requests.post(
            f"{DIAGRAM_URL}/{diagram_id}/export/svg",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            content_type = response.headers.get("content-type")
            if "svg" in content_type:
                # Check if it's valid SVG
                svg_content = response.text
                if svg_content.startswith('<?xml') and '<svg' in svg_content:
                    print(f"✅ PASS: SVG export successful")
                    print(f"   Content-Type: {content_type}")
                    print(f"   Size: {len(svg_content)} bytes")
                    print(f"   Valid SVG: ✓")
                    passed += 1
                else:
                    print(f"❌ FAIL: Invalid SVG format")
            else:
                print(f"❌ FAIL: Wrong content type: {content_type}")
        else:
            print(f"❌ FAIL: Status {response.status_code}")
    except Exception as e:
        print(f"❌ FAIL: {e}")
    
    # Test: PDF export
    print("\n" + "=" * 80)
    print("Feature #494: PDF export")
    print("=" * 80)
    total += 1
    try:
        response = requests.post(
            f"{DIAGRAM_URL}/{diagram_id}/export/pdf",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            if response.headers.get("content-type") == "application/pdf":
                # Check if it's valid PDF
                pdf_content = response.content
                if pdf_content.startswith(b'%PDF'):
                    print(f"✅ PASS: PDF export successful")
                    print(f"   Content-Type: {response.headers.get('content-type')}")
                    print(f"   Size: {len(pdf_content)} bytes")
                    print(f"   Valid PDF: ✓")
                    passed += 1
                else:
                    print(f"❌ FAIL: Invalid PDF format")
            else:
                print(f"❌ FAIL: Wrong content type: {response.headers.get('content-type')}")
        else:
            print(f"❌ FAIL: Status {response.status_code}")
    except Exception as e:
        print(f"❌ FAIL: {e}")
    
    # Test: Export count tracking
    print("\n" + "=" * 80)
    print("Bonus: Export count tracking")
    print("=" * 80)
    try:
        response = requests.get(
            f"{DIAGRAM_URL}/{diagram_id}",
            headers=headers,
            timeout=5
        )
        if response.status_code == 200:
            diagram_data = response.json()
            export_count = diagram_data.get("export_count", 0)
            if export_count >= 7:  # We did 7 exports
                print(f"✅ BONUS: Export count tracked correctly")
                print(f"   Export count: {export_count}")
            else:
                print(f"⚠️ Export count may not be accurate: {export_count}")
        else:
            print(f"⚠️ Could not check export count")
    except Exception as e:
        print(f"⚠️ Could not check export count: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! 🎉")
    elif passed >= total * 0.8:
        print("\n✅ Most tests passed!")
    else:
        print("\n⚠️  Some tests failed - review implementation")

if __name__ == "__main__":
    run_tests()
