#!/usr/bin/env python3
"""
Test Feature #485: PNG Export - 2x Resolution (Retina)

Tests that PNG exports can be generated at 2x resolution for retina displays:
1. Create diagram
2. Export as PNG with scale=2
3. Verify PNG is generated
4. Verify resolution is higher than 1x (larger file size)
"""

import requests
import time
import json
import base64
import psycopg2
from typing import Tuple
from colorama import Fore, Style, init

# Initialize colorama
init()

BASE_URL = "http://localhost:8080/api"
DIAGRAM_SERVICE_URL = "http://localhost:8082"

# Color helpers
def info(msg): print(f"{Fore.CYAN}ℹ️  {msg}{Style.RESET_ALL}")
def success(msg): print(f"{Fore.GREEN}✅ {msg}{Style.RESET_ALL}")
def error(msg): print(f"{Fore.RED}❌ {msg}{Style.RESET_ALL}")
def warning(msg): print(f"{Fore.YELLOW}⚠️  {msg}{Style.RESET_ALL}")
def header(msg): print(f"\n{Fore.BLUE}{'='*80}\n{msg}\n{'='*80}{Style.RESET_ALL}\n")

def register_and_login() -> Tuple[str, str]:
    """Register a new user and login."""
    timestamp = int(time.time())
    email = f"png2x_{timestamp}@example.com"
    password = "TestPass123!@#"

    # Register
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "PNG 2x Test User"
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


def create_diagram(user_id: str, token: str) -> str:
    """Create a test diagram."""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }

    canvas_data = {
        "shapes": [
            {
                "id": "shape1",
                "type": "rectangle",
                "x": 100,
                "y": 100,
                "width": 400,
                "height": 300,
                "color": "blue",
                "label": "Retina Test"
            }
        ]
    }

    response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/",
        headers=headers,
        json={
            "title": "PNG 2x Retina Test",
            "file_type": "canvas",
            "canvas_data": canvas_data
        }
    )

    if response.status_code not in [200, 201]:
        error(f"Failed to create diagram: {response.text}")
        raise Exception("Failed to create diagram")

    diagram_id = response.json()["id"]
    success(f"Created diagram: {diagram_id}")
    return diagram_id


def export_png(user_id: str, token: str, diagram_id: str, scale: int = 2) -> dict:
    """Export diagram as PNG."""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }

    response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/export/png",
        headers=headers,
        params={
            "scale": scale,
            "background": "white",
            "quality": "high"
        }
    )

    if response.status_code not in [200, 201]:
        error(f"Failed to export PNG: {response.text}")
        raise Exception("Failed to export PNG")

    return {
        "status_code": response.status_code,
        "content_type": response.headers.get("Content-Type"),
        "content_length": len(response.content),
        "content": response.content
    }


def main():
    """Run all PNG 2x resolution tests."""
    print(f"\n{Fore.MAGENTA}{'='*80}")
    print("Feature #485: PNG Export - 2x Resolution (Retina) Test")
    print(f"{'='*80}{Style.RESET_ALL}\n")

    try:
        # Step 1: Register and login
        header("STEP 1: Register and Login")
        user_id, token = register_and_login()

        # Step 2: Create diagram
        header("STEP 2: Create Diagram")
        diagram_id = create_diagram(user_id, token)

        # Step 3: Export at 2x resolution (retina)
        header("STEP 3: Export at 2x Resolution (Retina)")
        info("Exporting at 2x resolution for retina displays...")
        result_2x = export_png(user_id, token, diagram_id, scale=2)
        success(f"Successfully exported at 2x: {result_2x['content_length']} bytes")
        info(f"Content-Type: {result_2x['content_type']}")

        # Step 4: Export at 1x resolution for comparison
        header("STEP 4: Export at 1x Resolution (for comparison)")
        info("Exporting at 1x resolution...")
        result_1x = export_png(user_id, token, diagram_id, scale=1)
        success(f"Successfully exported at 1x: {result_1x['content_length']} bytes")

        # Step 5: Verify 2x is larger than 1x
        header("STEP 5: Verify Retina Quality")
        size_ratio = result_2x['content_length'] / result_1x['content_length']
        info(f"1x size: {result_1x['content_length']:,} bytes")
        info(f"2x size: {result_2x['content_length']:,} bytes")
        info(f"Size ratio (2x/1x): {size_ratio:.2f}x")

        # Summary
        header("TEST SUMMARY")

        tests = [
            ("2x PNG export successful", result_2x['status_code'] in [200, 201]),
            ("2x returns image/png", result_2x['content_type'] == 'image/png'),
            ("2x PNG has content", result_2x['content_length'] > 0),
            ("1x PNG export successful", result_1x['status_code'] in [200, 201]),
            ("2x is larger than 1x (retina quality)", result_2x['content_length'] > result_1x['content_length']),
            ("Size difference reasonable (2x > 1.5x larger)", size_ratio > 1.5),
        ]

        for test_name, passed in tests:
            status = f"{Fore.GREEN}PASS{Style.RESET_ALL}" if passed else f"{Fore.RED}FAIL{Style.RESET_ALL}"
            print(f"  {status} - {test_name}")

        passed_count = sum(1 for _, passed in tests if passed)
        print(f"\nResults: {passed_count}/{len(tests)} tests passed")

        if passed_count == len(tests):
            success("\n✅ ALL PNG 2X RETINA TESTS PASSED!")
            info("\nFeature #485 is complete:")
            info("  ✅ PNG export supports 2x retina resolution")
            info("  ✅ 2x produces larger, higher quality files")
            info("  ✅ Returns correct content type")
            info(f"  ✅ Size ratio: {size_ratio:.2f}x (2x vs 1x)")
            info("  ✅ Ideal for retina displays and high-DPI screens")
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
