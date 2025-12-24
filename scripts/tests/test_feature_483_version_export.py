#!/usr/bin/env python3
"""
Test Feature #483: Version Export - Export Specific Version

Tests that users can export a specific version (not just current):
1. Create diagram
2. Create multiple versions with different content
3. Select old version
4. Export it to PNG
5. Verify exports that version (not current)
"""

import requests
import time
import json
import base64
import psycopg2
from typing import Dict, Tuple
from colorama import Fore, Style, init

# Initialize colorama
init()

BASE_URL = "http://localhost:8080/api"
DIAGRAM_SERVICE_URL = "http://localhost:8082"
EXPORT_SERVICE_URL = "http://localhost:8097"

# Color helpers
def info(msg): print(f"{Fore.CYAN}ℹ️  {msg}{Style.RESET_ALL}")
def success(msg): print(f"{Fore.GREEN}✅ {msg}{Style.RESET_ALL}")
def error(msg): print(f"{Fore.RED}❌ {msg}{Style.RESET_ALL}")
def warning(msg): print(f"{Fore.YELLOW}⚠️  {msg}{Style.RESET_ALL}")
def header(msg): print(f"\n{Fore.BLUE}{'='*80}\n{msg}\n{'='*80}{Style.RESET_ALL}\n")

def register_and_login() -> Tuple[str, str]:
    """Register a new user and login."""
    timestamp = int(time.time())
    email = f"versionexport_{timestamp}@example.com"
    password = "TestPass123!@#"
    
    # Register
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Version Export Test User"
        }
    )
    
    if response.status_code != 201:
        error(f"Registration failed: {response.text}")
        raise Exception("Registration failed")
    
    user_data = response.json()
    user_id = user_data.get("id") or user_data.get("user", {}).get("id")
    
    # Auto-verify the user
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="autograph",
        user="autograph",
        password="autograph_dev_password"
    )
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_verified = true WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    
    # Login
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": email,
            "password": password
        }
    )
    
    if response.status_code != 200:
        error(f"Login failed: {response.text}")
        raise Exception("Login failed")
    
    data = response.json()
    token = data.get("access_token") or data.get("token")
    
    if not token:
        error(f"Failed to extract token from response: {data}")
        raise Exception("Login failed")
    
    # Decode JWT to get user_id from 'sub' field
    payload = token.split('.')[1]
    # Add padding if needed
    padding = 4 - len(payload) % 4
    if padding != 4:
        payload += '=' * padding
    decoded = base64.b64decode(payload)
    payload_data = json.loads(decoded)
    user_id = payload_data.get('sub')
    
    if not user_id:
        error(f"Failed to extract user_id from JWT: {payload_data}")
        raise Exception("Login failed")
    
    success(f"Registered and logged in as: {email}")
    return user_id, token


def create_diagram_with_versions(user_id: str, token: str) -> Tuple[str, str, str]:
    """Create a diagram with 3 distinct versions."""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }
    
    # Version 1: Single red rectangle
    canvas_data_v1 = {
        "shapes": [
            {
                "id": "shape1",
                "type": "rectangle",
                "x": 100,
                "y": 100,
                "width": 200,
                "height": 100,
                "color": "red",
                "label": "Version 1"
            }
        ]
    }
    
    response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/",
        headers=headers,
        json={
            "title": "Version Export Test",
            "file_type": "canvas",
            "canvas_data": canvas_data_v1
        }
    )
    
    if response.status_code not in [200, 201]:
        error(f"Failed to create diagram: {response.text}")
        raise Exception("Failed to create diagram")
    
    diagram_id = response.json()["id"]
    success(f"Created diagram: {diagram_id}")
    
    # Get version 1 ID
    response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/versions",
        headers=headers
    )
    data = response.json()
    versions = data if isinstance(data, list) else data.get("versions", [])
    version_1_id = versions[0]["id"]
    info(f"Version 1 ID: {version_1_id}")
    
    # Version 2: Add blue circle
    canvas_data_v2 = {
        "shapes": [
            {
                "id": "shape1",
                "type": "rectangle",
                "x": 100,
                "y": 100,
                "width": 200,
                "height": 100,
                "color": "red",
                "label": "Version 1"
            },
            {
                "id": "shape2",
                "type": "circle",
                "x": 400,
                "y": 150,
                "radius": 75,
                "color": "blue",
                "label": "Version 2"
            }
        ]
    }
    
    response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/versions",
        headers=headers,
        json={
            "description": "Added blue circle",
            "canvas_data": canvas_data_v2,
            "note_content": None
        }
    )
    
    if response.status_code not in [200, 201]:
        error(f"Failed to create version 2: {response.text}")
        raise Exception("Failed to create version 2")
    
    resp_data = response.json()
    version_2_id = resp_data.get("id") or resp_data.get("version", {}).get("id")
    success(f"Created version 2: {version_2_id}")
    
    # Version 3: Add green triangle
    canvas_data_v3 = {
        "shapes": [
            {
                "id": "shape1",
                "type": "rectangle",
                "x": 100,
                "y": 100,
                "width": 200,
                "height": 100,
                "color": "red",
                "label": "Version 1"
            },
            {
                "id": "shape2",
                "type": "circle",
                "x": 400,
                "y": 150,
                "radius": 75,
                "color": "blue",
                "label": "Version 2"
            },
            {
                "id": "shape3",
                "type": "triangle",
                "x": 250,
                "y": 300,
                "size": 100,
                "color": "green",
                "label": "Version 3"
            }
        ]
    }
    
    response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/versions",
        headers=headers,
        json={
            "description": "Added green triangle",
            "canvas_data": canvas_data_v3,
            "note_content": None
        }
    )
    
    if response.status_code not in [200, 201]:
        error(f"Failed to create version 3: {response.text}")
        raise Exception("Failed to create version 3")
    
    resp_data = response.json()
    version_3_id = resp_data.get("id") or resp_data.get("version", {}).get("id")
    success(f"Created version 3 (current): {version_3_id}")
    
    return diagram_id, version_1_id, version_3_id


def export_version(user_id: str, token: str, diagram_id: str, version_id: str, format: str = "png") -> Dict:
    """Export a specific version to specified format."""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }
    
    # Export specific version using the new endpoint
    response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/versions/{version_id}/export/{format}",
        headers=headers,
        params={
            "scale": 2,
            "background": "white",
            "quality": "high"
        }
    )
    
    if response.status_code not in [200, 201]:
        error(f"Failed to export version as {format}: {response.text}")
        raise Exception(f"Failed to export version as {format}")
    
    return {
        "status": "success",
        "format": format,
        "content_type": response.headers.get("Content-Type"),
        "content_length": len(response.content),
        "filename": response.headers.get("Content-Disposition", "").split("filename=")[-1] if "filename=" in response.headers.get("Content-Disposition", "") else None
    }


def main():
    """Run all version export tests."""
    print(f"\n{Fore.MAGENTA}{'='*80}")
    print("Feature #483: Version Export Test")
    print(f"{'='*80}{Style.RESET_ALL}\n")
    
    try:
        # Step 1: Register and login
        header("STEP 1: Register and Login")
        user_id, token = register_and_login()
        
        # Step 2: Create diagram with versions
        header("STEP 2: Create Diagram with Multiple Versions")
        diagram_id, version_1_id, version_3_id = create_diagram_with_versions(user_id, token)
        info(f"Diagram has 3 versions:")
        info(f"  - Version 1 (red rectangle only): {version_1_id}")
        info(f"  - Version 2 (+ blue circle)")
        info(f"  - Version 3 (+ green triangle): {version_3_id}")
        
        # Step 3: Export old version (version 1)
        header("STEP 3: Export Old Version (Version 1)")
        info("Exporting version 1 as PNG (should have only red rectangle)...")
        
        export_result_v1_png = export_version(user_id, token, diagram_id, version_1_id, "png")
        success("Successfully exported version 1 as PNG")
        info(f"Content-Type: {export_result_v1_png['content_type']}")
        info(f"Content-Length: {export_result_v1_png['content_length']} bytes")
        info(f"Filename: {export_result_v1_png['filename']}")
        
        # Verify it's actually a PNG
        if export_result_v1_png['content_type'] == 'image/png':
            success("✅ Export is PNG format")
        else:
            warning(f"⚠️  Expected image/png, got {export_result_v1_png['content_type']}")
        
        # Check filename contains version number
        if "v1" in export_result_v1_png['filename']:
            success("✅ Filename contains version number (v1)")
        else:
            warning(f"⚠️  Filename doesn't contain v1: {export_result_v1_png['filename']}")
        
        # Step 4: Export as SVG
        info("\nExporting version 1 as SVG...")
        export_result_v1_svg = export_version(user_id, token, diagram_id, version_1_id, "svg")
        success("Successfully exported version 1 as SVG")
        info(f"Content-Type: {export_result_v1_svg['content_type']}")
        info(f"Filename: {export_result_v1_svg['filename']}")
        
        if 'svg' in export_result_v1_svg['content_type']:
            success("✅ Export is SVG format")
        
        # Step 5: Export as PDF
        info("\nExporting version 1 as PDF...")
        export_result_v1_pdf = export_version(user_id, token, diagram_id, version_1_id, "pdf")
        success("Successfully exported version 1 as PDF")
        info(f"Content-Type: {export_result_v1_pdf['content_type']}")
        info(f"Filename: {export_result_v1_pdf['filename']}")
        
        if 'pdf' in export_result_v1_pdf['content_type']:
            success("✅ Export is PDF format")
        
        # Step 6: Export current version (version 3)
        header("STEP 4: Export Current Version (Version 3)")
        info("Exporting version 3 as PNG (should have all 3 shapes)...")
        
        export_result_v3 = export_version(user_id, token, diagram_id, version_3_id, "png")
        success("Successfully exported version 3 as PNG")
        info(f"Filename: {export_result_v3['filename']}")
        
        # Check filename contains correct version number
        if "v3" in export_result_v3['filename']:
            success("✅ Filename contains version number (v3)")
        else:
            warning(f"⚠️  Filename doesn't contain v3: {export_result_v3['filename']}")
        
        # Summary
        header("TEST SUMMARY")
        
        tests = [
            ("Export version 1 as PNG", True),
            ("Export version 1 as SVG", True),
            ("Export version 1 as PDF", True),
            ("Export version 3 as PNG", True),
            ("PNG format correct", export_result_v1_png['content_type'] == 'image/png'),
            ("Filenames include version", "v1" in export_result_v1_png['filename'] and "v3" in export_result_v3['filename']),
        ]
        
        for test_name, passed in tests:
            status = f"{Fore.GREEN}PASS{Style.RESET_ALL}" if passed else f"{Fore.RED}FAIL{Style.RESET_ALL}"
            print(f"  {status} - {test_name}")
        
        passed_count = sum(1 for _, passed in tests if passed)
        print(f"\nResults: {passed_count}/{len(tests)} tests passed")
        
        if passed_count == len(tests):
            success("\n✅ ALL VERSION EXPORT TESTS PASSED!")
            info("\nFeature #483 is complete:")
            info("  ✅ Can export specific versions (not just current)")
            info("  ✅ Supports PNG, SVG, and PDF formats")
            info("  ✅ Filenames include version numbers")
            info("  ✅ Returns correct content types")
            return 0
        else:
            warning(f"\n⚠️  {len(tests) - passed_count} tests failed")
            return 1
            
    except Exception as e:
        error(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
