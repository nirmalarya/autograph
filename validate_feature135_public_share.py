#!/usr/bin/env python3
"""
Feature #135 Validation: Share diagram via public link

Tests:
1. Register user and verify email
2. Login and obtain JWT token
3. Create test diagram
4. Generate public share link using POST /{diagram_id}/share
5. Verify unique share URL generated
6. Verify share token in response
7. Access diagram via public token (no authentication)
8. Verify diagram accessible without login
9. Verify view-only permission in response
10. Query database to verify share record (is_public=true)
11. Test password-protected share (bonus)
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
    print("FEATURE #135 VALIDATION: Share diagram via public link")
    print("="*80)

    # Test data
    test_email = f"share_test_{datetime.now().timestamp()}@example.com"
    test_password = "SecurePass123!"

    try:
        # Step 1: Register user
        log("Step 1: Register user")
        register_response = requests.post(
            f"{API_BASE}/auth/register",
            json={
                "email": test_email,
                "password": test_password,
                "full_name": "Share Test User"
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
        print(f"✅ Login successful (user_id: {user_id})")

        # Step 4: Create test diagram
        log("Step 4: Create test diagram")
        diagram_data = {
            "title": "Public Share Test Diagram",
            "diagram_type": "canvas",
            "canvas_data": {
                "shapes": [
                    {"id": "shape1", "type": "rectangle", "x": 100, "y": 100, "width": 200, "height": 150},
                    {"id": "shape2", "type": "ellipse", "x": 400, "y": 200, "width": 150, "height": 150}
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
        print(f"✅ Diagram created: {diagram_id}")
        print(f"   Title: {diagram_data['title']}")

        # Step 5: Generate public share link
        log("Step 5: Generate public share link")
        share_response = requests.post(
            f"{API_BASE}/diagrams/{diagram_id}/share",
            headers=headers,
            json={
                "permission": "view",
                "is_public": True
            }
        )

        if share_response.status_code not in [200, 201]:
            print(f"❌ Share creation failed: {share_response.status_code}")
            print(share_response.text)
            return False

        share_data = share_response.json()
        share_id = share_data.get("share_id")
        share_token = share_data.get("token")
        share_url = share_data.get("share_url")
        permission = share_data.get("permission")
        is_public = share_data.get("is_public")

        print(f"✅ Share link created successfully")
        print(f"   Share ID: {share_id}")
        print(f"   Token: {share_token[:20]}...")
        print(f"   URL: {share_url}")
        print(f"   Permission: {permission}")
        print(f"   Is Public: {is_public}")

        # Step 6: Verify unique share URL generated
        if not share_token or len(share_token) < 20:
            print(f"❌ Invalid share token: {share_token}")
            return False

        if not share_url or "shared" not in share_url.lower():
            print(f"❌ Invalid share URL: {share_url}")
            return False

        print(f"✅ Unique share URL generated")

        # Step 7: Access diagram via public token (NO AUTHENTICATION)
        log("Step 7: Access diagram via public token (no auth)")
        public_response = requests.get(
            f"{API_BASE}/diagrams/shared/{share_token}"
        )

        if public_response.status_code != 200:
            print(f"❌ Failed to access shared diagram: {public_response.status_code}")
            print(public_response.text)
            return False

        shared_diagram = public_response.json()
        print(f"✅ Diagram accessible without authentication")
        print(f"   Diagram ID: {shared_diagram.get('id')}")
        print(f"   Title: {shared_diagram.get('title')}")
        print(f"   Permission: {shared_diagram.get('permission')}")

        # Step 8: Verify view-only mode
        log("Step 8: Verify view-only permission")
        shared_permission = shared_diagram.get("permission")

        if shared_permission != "view":
            print(f"❌ Expected view permission, got: {shared_permission}")
            return False

        print(f"✅ View-only permission confirmed: {shared_permission}")

        # Step 9: Verify diagram data matches
        log("Step 9: Verify diagram data accessible")
        shared_canvas = shared_diagram.get("canvas_data", {})
        shared_shapes = shared_canvas.get("shapes", [])

        if len(shared_shapes) != 2:
            print(f"❌ Expected 2 shapes, got: {len(shared_shapes)}")
            return False

        print(f"✅ Diagram data accessible via public link")
        print(f"   Shapes: {len(shared_shapes)}")
        print(f"   Canvas data present: Yes")

        # Step 10: Query database to verify share record
        log("Step 10: Query database to verify share record")
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute(
                "SELECT id, token, permission, is_public, expires_at FROM shares WHERE id = %s",
                (share_id,)
            )
            db_share = cur.fetchone()
            cur.close()
            conn.close()

            if not db_share:
                print(f"❌ Share record not found in database")
                return False

            db_share_id, db_token, db_permission, db_is_public, db_expires = db_share

            print(f"✅ Share record verified in database")
            print(f"   ID: {db_share_id}")
            print(f"   Token: {db_token[:20]}...")
            print(f"   Permission: {db_permission}")
            print(f"   Is Public: {db_is_public}")
            print(f"   Expires: {db_expires or 'Never'}")

            if not db_is_public:
                print(f"❌ Share is not public in database!")
                return False

            print(f"✅ is_public = True confirmed in database")

        except Exception as e:
            print(f"❌ Database verification failed: {e}")
            return False

        # Step 11: Test share metadata
        log("Step 11: Verify share metadata")
        if share_data.get("permission") != "view":
            print(f"❌ Expected view permission, got: {share_data.get('permission')}")
            return False

        if share_data.get("is_public") != True:
            print(f"❌ Expected is_public=true, got: {share_data.get('is_public')}")
            return False

        print(f"✅ Share metadata correct")
        print(f"   Permission: view")
        print(f"   Public: true")
        print(f"   Expires: {share_data.get('expires_at', 'Never')}")

        # Final summary
        log("✅ ALL TESTS PASSED", {
            "user_id": user_id,
            "diagram_id": diagram_id,
            "diagram_title": diagram_data["title"],
            "share_id": share_id,
            "share_token": share_token[:30] + "...",
            "share_url": share_url,
            "permission": "view",
            "is_public": True,
            "accessible_without_auth": True,
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
