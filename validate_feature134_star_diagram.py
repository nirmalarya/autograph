#!/usr/bin/env python3
"""
Feature #134 Validation: Star/favorite diagram for quick access

Tests:
1. Register user and verify email
2. Login and obtain JWT token
3. Create test diagram
4. Verify diagram not starred initially
5. Star the diagram using PUT /{diagram_id}/star
6. Verify diagram is starred
7. List starred diagrams using GET /starred
8. Verify diagram appears in starred list
9. Unstar the diagram (toggle again)
10. Verify diagram is unstarred
11. List starred diagrams - verify diagram removed
"""

import requests
import sys
import json
from datetime import datetime
import psycopg2
import base64

API_BASE = "http://localhost:8080/api"

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "autograph",
    "user": "autograph",
    "password": "autograph_dev_password"
}

def log(message, data=None):
    """Print test step with optional data."""
    print(f"\n{'='*80}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    if data:
        print(json.dumps(data, indent=2))
    print('='*80)

def main():
    """Run validation tests."""

    print("\n" + "="*80)
    print("FEATURE #134 VALIDATION: Star/favorite diagram for quick access")
    print("="*80)

    # Test data
    test_email = f"star_test_{datetime.now().timestamp()}@example.com"
    test_password = "SecurePass123!"

    try:
        # Step 1: Register user
        log("Step 1: Register user")
        register_response = requests.post(
            f"{API_BASE}/auth/register",
            json={
                "email": test_email,
                "password": test_password,
                "full_name": "Star Test User"
            }
        )

        if register_response.status_code != 201:
            print(f"❌ Registration failed: {register_response.status_code}")
            print(register_response.text)
            return False

        print(f"✅ User registered")

        # Step 2: Verify email (direct DB update)
        log("Step 2: Verify email via database")
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("UPDATE users SET is_verified = TRUE WHERE email = %s", (test_email,))
            conn.commit()
            cur.close()
            conn.close()
            print(f"✅ User verified in database")
        except Exception as e:
            print(f"❌ Failed to verify user: {e}")
            return False

        # Step 3: Login
        log("Step 3: Login and obtain JWT token")
        login_response = requests.post(
            f"{API_BASE}/auth/login",
            json={
                "email": test_email,
                "password": test_password
            }
        )

        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(login_response.text)
            return False

        token = login_response.json()["access_token"]

        # Decode JWT to get user_id
        try:
            payload = token.split('.')[1]
            payload += '=' * (4 - len(payload) % 4)
            decoded = json.loads(base64.urlsafe_b64decode(payload))
            user_id = decoded['sub']
        except Exception as e:
            print(f"❌ Failed to decode JWT: {e}")
            return False

        headers = {
            "Authorization": f"Bearer {token}",
            "X-User-ID": user_id
        }
        print(f"✅ Login successful, token obtained (user_id: {user_id})")

        # Step 4: Create test diagram
        log("Step 4: Create test diagram")
        diagram_data = {
            "title": "Test Diagram for Starring",
            "diagram_type": "canvas",
            "canvas_data": {
                "shapes": [
                    {"id": "shape1", "type": "rectangle", "x": 100, "y": 100}
                ]
            }
        }

        diagram_response = requests.post(
            f"{API_BASE}/diagrams",
            headers=headers,
            json=diagram_data
        )

        if diagram_response.status_code not in [200, 201]:
            print(f"❌ Diagram creation failed: {diagram_response.status_code}")
            print(diagram_response.text)
            return False

        diagram_id = diagram_response.json()["id"]
        initial_starred = diagram_response.json().get("is_starred", False)

        print(f"✅ Diagram created: {diagram_id}")
        print(f"   Title: {diagram_data['title']}")
        print(f"   Initial is_starred: {initial_starred}")

        # Step 5: Verify not starred initially
        if initial_starred:
            print(f"⚠️ Warning: Diagram starred by default (expected false)")

        # Step 6: Star the diagram
        log("Step 6: Star the diagram using PUT /{diagram_id}/star")
        star_response = requests.put(
            f"{API_BASE}/diagrams/{diagram_id}/star",
            headers=headers
        )

        if star_response.status_code not in [200, 204]:
            print(f"❌ Star diagram failed: {star_response.status_code}")
            print(star_response.text)
            return False

        star_result = star_response.json() if star_response.content else {}
        print(f"✅ Star endpoint called successfully")
        if star_result:
            print(f"   Response: {star_result.get('message', 'No message')}")
            print(f"   is_starred: {star_result.get('is_starred')}")

        # Step 7: Verify diagram is starred (GET diagram)
        log("Step 7: Verify diagram is starred")
        diagram_check = requests.get(
            f"{API_BASE}/diagrams/{diagram_id}",
            headers=headers
        )

        if diagram_check.status_code != 200:
            print(f"❌ Failed to retrieve diagram: {diagram_check.status_code}")
            return False

        starred_diagram = diagram_check.json()
        is_starred_now = starred_diagram.get("is_starred", False)

        if not is_starred_now:
            print(f"❌ Diagram not starred!")
            print(f"   Expected is_starred: True")
            print(f"   Got is_starred: {is_starred_now}")
            return False

        print(f"✅ Diagram is starred: {is_starred_now}")

        # Step 8: List starred diagrams
        log("Step 8: List starred diagrams using GET /starred")
        starred_list_response = requests.get(
            f"{API_BASE}/diagrams/starred",
            headers=headers
        )

        if starred_list_response.status_code != 200:
            print(f"❌ Failed to list starred diagrams: {starred_list_response.status_code}")
            print(starred_list_response.text)
            return False

        starred_diagrams = starred_list_response.json().get("diagrams", [])
        total_starred = starred_list_response.json().get("total", 0)

        print(f"✅ Starred diagrams listed successfully")
        print(f"   Total starred: {total_starred}")

        # Step 9: Verify diagram appears in starred list
        log("Step 9: Verify diagram appears in starred list")
        starred_ids = [d["id"] for d in starred_diagrams]

        if diagram_id not in starred_ids:
            print(f"❌ Diagram not found in starred list!")
            print(f"   Expected diagram ID: {diagram_id}")
            print(f"   Found diagrams: {starred_ids}")
            return False

        print(f"✅ Diagram appears in starred list")
        print(f"   Diagram ID: {diagram_id}")
        print(f"   Position in starred list: {starred_ids.index(diagram_id) + 1}")

        # Step 10: Unstar the diagram (toggle again)
        log("Step 10: Unstar the diagram (toggle star again)")
        unstar_response = requests.put(
            f"{API_BASE}/diagrams/{diagram_id}/star",
            headers=headers
        )

        if unstar_response.status_code not in [200, 204]:
            print(f"❌ Unstar diagram failed: {unstar_response.status_code}")
            print(unstar_response.text)
            return False

        unstar_result = unstar_response.json() if unstar_response.content else {}
        print(f"✅ Unstar endpoint called successfully")
        if unstar_result:
            print(f"   Response: {unstar_result.get('message', 'No message')}")
            print(f"   is_starred: {unstar_result.get('is_starred')}")

        # Step 11: Verify diagram is unstarred
        log("Step 11: Verify diagram is unstarred")
        diagram_final_check = requests.get(
            f"{API_BASE}/diagrams/{diagram_id}",
            headers=headers
        )

        if diagram_final_check.status_code != 200:
            print(f"❌ Failed to retrieve diagram: {diagram_final_check.status_code}")
            return False

        final_diagram = diagram_final_check.json()
        is_starred_final = final_diagram.get("is_starred", False)

        if is_starred_final:
            print(f"❌ Diagram still starred!")
            print(f"   Expected is_starred: False")
            print(f"   Got is_starred: {is_starred_final}")
            return False

        print(f"✅ Diagram is unstarred: {not is_starred_final}")

        # Step 12: List starred diagrams - verify diagram removed
        log("Step 12: List starred diagrams - verify diagram removed")
        starred_final_response = requests.get(
            f"{API_BASE}/diagrams/starred",
            headers=headers
        )

        if starred_final_response.status_code != 200:
            print(f"❌ Failed to list starred diagrams: {starred_final_response.status_code}")
            return False

        starred_final = starred_final_response.json().get("diagrams", [])
        starred_final_ids = [d["id"] for d in starred_final]

        if diagram_id in starred_final_ids:
            print(f"❌ Diagram still appears in starred list!")
            print(f"   Diagram ID: {diagram_id}")
            print(f"   Starred list: {starred_final_ids}")
            return False

        print(f"✅ Diagram removed from starred list")
        print(f"   Current starred count: {len(starred_final)}")

        # Final summary
        log("✅ ALL TESTS PASSED", {
            "user_id": user_id,
            "diagram_id": diagram_id,
            "diagram_title": diagram_data["title"],
            "star_toggle_tested": "Yes (starred then unstarred)",
            "starred_list_tested": "Yes (appeared then removed)",
            "tests_passed": "11/11"
        })

        return True

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
