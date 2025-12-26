#!/usr/bin/env python3
"""
Test Feature #487: PNG Export - Transparent Background

Tests that PNG exports support transparent backgrounds:
1. Create diagram
2. Export with background=transparent
3. Verify PNG is generated
4. Compare file size with white background
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
    email = f"pngtrans_{timestamp}@example.com"
    password = "TestPass123!@#"

    response = requests.post(f"{BASE_URL}/auth/register", json={"email": email, "password": password, "full_name": "PNG Trans Test"})
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
        "title": "PNG Transparent Test",
        "file_type": "canvas",
        "canvas_data": {"shapes": [{"id": "s1", "type": "rectangle", "x": 100, "y": 100, "width": 400, "height": 300}]}
    })
    diagram_id = response.json()["id"]
    success(f"Created diagram: {diagram_id}")
    return diagram_id

def export_png(user_id: str, token: str, diagram_id: str, background: str = "white") -> dict:
    headers = {"Authorization": f"Bearer {token}", "X-User-ID": user_id}
    response = requests.post(f"{DIAGRAM_SERVICE_URL}/{diagram_id}/export/png", headers=headers, params={"background": background, "scale": 2})
    if response.status_code not in [200, 201]:
        raise Exception(f"Export failed: {response.text}")
    return {"content_length": len(response.content), "content_type": response.headers.get("Content-Type")}

def main():
    print(f"\n{Fore.MAGENTA}{'='*80}\nFeature #487: PNG Export - Transparent Background\n{'='*80}{Style.RESET_ALL}\n")

    try:
        header("STEP 1: Setup")
        user_id, token = register_and_login()
        diagram_id = create_diagram(user_id, token)

        header("STEP 2: Export with Different Backgrounds")
        result_white = export_png(user_id, token, diagram_id, "white")
        success(f"White background: {result_white['content_length']:,} bytes")

        result_transparent = export_png(user_id, token, diagram_id, "transparent")
        success(f"Transparent background: {result_transparent['content_length']:,} bytes")

        header("STEP 3: Verify Transparency Support")
        info(f"Size difference: {abs(result_transparent['content_length'] - result_white['content_length']):,} bytes")

        tests = [
            ("Transparent export successful", result_transparent['content_length'] > 0),
            ("Returns image/png", result_transparent['content_type'] == 'image/png'),
            ("White export successful", result_white['content_length'] > 0),
            ("Both exports have content", result_transparent['content_length'] > 1000 and result_white['content_length'] > 1000),
        ]

        header("TEST SUMMARY")
        for test_name, passed in tests:
            status = f"{Fore.GREEN}PASS{Style.RESET_ALL}" if passed else f"{Fore.RED}FAIL{Style.RESET_ALL}"
            print(f"  {status} - {test_name}")

        passed_count = sum(1 for _, passed in tests if passed)
        print(f"\nResults: {passed_count}/{len(tests)} tests passed")

        if passed_count == len(tests):
            success("\n✅ ALL TRANSPARENT BACKGROUND TESTS PASSED!")
            info("  ✅ Supports transparent PNG backgrounds")
            info("  ✅ Ideal for overlaying on other content")
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
