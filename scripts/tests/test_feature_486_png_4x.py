#!/usr/bin/env python3
"""
Test Feature #486: PNG Export - 4x Resolution (Ultra)

Tests that PNG exports can be generated at 4x resolution for ultra-high quality:
1. Create diagram
2. Export as PNG with scale=4
3. Verify PNG is generated
4. Verify resolution is higher than 2x (larger file size)
"""

import requests
import time
import json
import base64
import psycopg2
from typing import Tuple
from colorama import Fore, Style, init

init()

BASE_URL = "http://localhost:8080/api"
DIAGRAM_SERVICE_URL = "http://localhost:8082"

def info(msg): print(f"{Fore.CYAN}ℹ️  {msg}{Style.RESET_ALL}")
def success(msg): print(f"{Fore.GREEN}✅ {msg}{Style.RESET_ALL}")
def error(msg): print(f"{Fore.RED}❌ {msg}{Style.RESET_ALL}")
def header(msg): print(f"\n{Fore.BLUE}{'='*80}\n{msg}\n{'='*80}{Style.RESET_ALL}\n")

def register_and_login() -> Tuple[str, str]:
    timestamp = int(time.time())
    email = f"png4x_{timestamp}@example.com"
    password = "TestPass123!@#"

    response = requests.post(f"{BASE_URL}/auth/register", json={"email": email, "password": password, "full_name": "PNG 4x Test"})
    if response.status_code != 201:
        raise Exception("Registration failed")

    user_id = response.json().get("id") or response.json().get("user", {}).get("id")

    conn = psycopg2.connect(host="localhost", port=5432, database="autograph", user="autograph", password="autograph_dev_password")
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_verified = true WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

    response = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    if response.status_code != 200:
        raise Exception("Login failed")

    token = response.json().get("access_token") or response.json().get("token")
    payload = token.split('.')[1]
    padding = 4 - len(payload) % 4
    if padding != 4:
        payload += '=' * padding
    user_id = json.loads(base64.b64decode(payload)).get('sub')

    success(f"Logged in as: {email}")
    return user_id, token

def create_diagram(user_id: str, token: str) -> str:
    headers = {"Authorization": f"Bearer {token}", "X-User-ID": user_id}
    response = requests.post(f"{DIAGRAM_SERVICE_URL}/", headers=headers, json={
        "title": "PNG 4x Ultra Test",
        "file_type": "canvas",
        "canvas_data": {"shapes": [{"id": "s1", "type": "rectangle", "x": 100, "y": 100, "width": 400, "height": 300}]}
    })
    diagram_id = response.json()["id"]
    success(f"Created diagram: {diagram_id}")
    return diagram_id

def export_png(user_id: str, token: str, diagram_id: str, scale: int) -> dict:
    headers = {"Authorization": f"Bearer {token}", "X-User-ID": user_id}
    response = requests.post(f"{DIAGRAM_SERVICE_URL}/{diagram_id}/export/png", headers=headers, params={"scale": scale})
    if response.status_code not in [200, 201]:
        raise Exception(f"Export failed: {response.text}")
    return {"content_length": len(response.content), "content_type": response.headers.get("Content-Type")}

def main():
    print(f"\n{Fore.MAGENTA}{'='*80}\nFeature #486: PNG Export - 4x Resolution (Ultra)\n{'='*80}{Style.RESET_ALL}\n")

    try:
        header("STEP 1: Setup")
        user_id, token = register_and_login()
        diagram_id = create_diagram(user_id, token)

        header("STEP 2: Export at Different Resolutions")
        result_1x = export_png(user_id, token, diagram_id, 1)
        success(f"1x: {result_1x['content_length']:,} bytes")

        result_2x = export_png(user_id, token, diagram_id, 2)
        success(f"2x: {result_2x['content_length']:,} bytes")

        result_4x = export_png(user_id, token, diagram_id, 4)
        success(f"4x: {result_4x['content_length']:,} bytes")

        header("STEP 3: Verify Quality Progression")
        ratio_2x = result_2x['content_length'] / result_1x['content_length']
        ratio_4x = result_4x['content_length'] / result_2x['content_length']
        info(f"2x/1x ratio: {ratio_2x:.2f}x")
        info(f"4x/2x ratio: {ratio_4x:.2f}x")

        tests = [
            ("4x export successful", result_4x['content_length'] > 0),
            ("4x returns image/png", result_4x['content_type'] == 'image/png'),
            ("4x > 2x > 1x (quality progression)", result_4x['content_length'] > result_2x['content_length'] > result_1x['content_length']),
            ("4x is significantly larger than 2x", ratio_4x > 1.3),
        ]

        header("TEST SUMMARY")
        for test_name, passed in tests:
            status = f"{Fore.GREEN}PASS{Style.RESET_ALL}" if passed else f"{Fore.RED}FAIL{Style.RESET_ALL}"
            print(f"  {status} - {test_name}")

        passed_count = sum(1 for _, passed in tests if passed)
        print(f"\nResults: {passed_count}/{len(tests)} tests passed")

        if passed_count == len(tests):
            success("\n✅ ALL 4X ULTRA RESOLUTION TESTS PASSED!")
            return 0
        else:
            return 1

    except Exception as e:
        error(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
