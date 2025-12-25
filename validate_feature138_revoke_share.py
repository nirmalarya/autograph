#!/usr/bin/env python3
"""
Feature #138 Validation: Revoke share link

This script validates that:
1. User can create a diagram
2. User can generate a share link for the diagram
3. Share link is accessible
4. User can revoke the share link (DELETE /{diagram_id}/share/{share_id})
5. Revoked share link returns appropriate error
6. Database record is deleted or is_active=false
"""

import requests
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8080/api"
DIAGRAM_SERVICE = "http://localhost:8082"

def log_step(step_num, description, status=""):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] Step {step_num}: {description} {status}")

def log_success(message):
    print(f"✅ {message}")

def log_error(message):
    print(f"❌ {message}")

def log_info(message):
    print(f"ℹ️  {message}")

def main():
    print("=" * 80)
    print("Feature #138: Revoke Share Link")
    print("=" * 80)
    print()

    # Step 1: Register a test user
    log_step(1, "Register test user")
    test_email = f"revoke_share_test_{datetime.now().timestamp()}@example.com"
    test_password = "SecurePassword123!"

    register_response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": test_email,
            "password": test_password,
            "full_name": "Revoke Share Test User"
        }
    )

    if register_response.status_code != 201:
        log_error(f"Registration failed: {register_response.status_code} - {register_response.text}")
        return False

    log_success(f"User registered: {test_email}")

    # Step 1.5: Verify email (auto-verify for testing)
    log_step("1.5", "Verify email address")

    # Use direct database update to verify email for testing
    import psycopg2
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="autograph",
        user="autograph",
        password="autograph_dev_password"
    )
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET is_verified = true WHERE email = %s",
        (test_email,)
    )
    conn.commit()
    log_success("Email verified")

    # Step 2: Login to get JWT token
    log_step(2, "Login to get authentication token")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": test_email,
            "password": test_password
        }
    )

    if login_response.status_code != 200:
        log_error(f"Login failed: {login_response.status_code} - {login_response.text}")
        cur.close()
        conn.close()
        return False

    login_data = login_response.json()
    access_token = login_data.get("access_token")
    user_id = login_data.get("user", {}).get("id")

    if not access_token:
        log_error("No access token in login response")
        cur.close()
        conn.close()
        return False

    log_success(f"Login successful, user_id: {user_id}")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Step 3: Create a test diagram
    log_step(3, "Create test diagram")
    create_diagram_response = requests.post(
        f"{BASE_URL}/diagrams",
        headers=headers,
        json={
            "title": "Test Diagram for Share Revocation",
            "type": "canvas",
            "canvas_data": {
                "shapes": [
                    {"id": "1", "type": "rectangle", "x": 100, "y": 100, "text": "Test Shape"}
                ]
            }
        }
    )

    if create_diagram_response.status_code not in [200, 201]:
        log_error(f"Diagram creation failed: {create_diagram_response.status_code} - {create_diagram_response.text}")
        cur.close()
        conn.close()
        return False

    diagram = create_diagram_response.json()
    diagram_id = diagram.get("id")
    log_success(f"Diagram created: {diagram_id}")

    # Step 4: Create a share link
    log_step(4, "Create share link")
    create_share_response = requests.post(
        f"{BASE_URL}/diagrams/{diagram_id}/share",
        headers=headers,
        json={
            "permission": "view",
            "is_public": True
        }
    )

    if create_share_response.status_code != 200:
        log_error(f"Share creation failed: {create_share_response.status_code} - {create_share_response.text}")
        cur.close()
        conn.close()
        return False

    share_data = create_share_response.json()
    share_id = share_data.get("share_id")
    share_token = share_data.get("token")
    log_success(f"Share created: {share_id}, token: {share_token[:10]}...")

    # Step 5: Verify share link works (access via token)
    log_step(5, "Verify share link is accessible")
    access_share_response = requests.get(
        f"{DIAGRAM_SERVICE}/shared/{share_token}"
    )

    if access_share_response.status_code != 200:
        log_error(f"Share access failed: {access_share_response.status_code} - {access_share_response.text}")
        cur.close()
        conn.close()
        return False

    log_success("Share link is accessible")

    # Step 6: Revoke the share link
    log_step(6, "Revoke share link (DELETE /{diagram_id}/share/{share_id})")
    revoke_response = requests.delete(
        f"{BASE_URL}/diagrams/{diagram_id}/share/{share_id}",
        headers=headers
    )

    if revoke_response.status_code != 200:
        log_error(f"Share revocation failed: {revoke_response.status_code} - {revoke_response.text}")
        cur.close()
        conn.close()
        return False

    revoke_data = revoke_response.json()
    log_success(f"Share revoked: {revoke_data.get('message')}")

    # Step 7: Attempt to access revoked share link
    log_step(7, "Attempt to access revoked share link")
    access_revoked_response = requests.get(
        f"{DIAGRAM_SERVICE}/shared/{share_token}"
    )

    # Should return 404 (share not found) since record was deleted
    if access_revoked_response.status_code == 404:
        error_detail = access_revoked_response.json().get("detail", "")
        log_success(f"Revoked share correctly returns 404: {error_detail}")
    elif access_revoked_response.status_code == 410:
        # Could also return 410 Gone if using is_active flag
        error_detail = access_revoked_response.json().get("detail", "")
        log_success(f"Revoked share correctly returns 410: {error_detail}")
    else:
        log_error(f"Unexpected response for revoked share: {access_revoked_response.status_code} - {access_revoked_response.text}")
        cur.close()
        conn.close()
        return False

    # Step 8: Check database to verify share record status
    log_step(8, "Check database for share record")

    # Check if share record exists
    cur.execute(
        "SELECT id, is_active FROM shares WHERE id = %s",
        (share_id,)
    )
    share_record = cur.fetchone()

    if share_record is None:
        log_success("Share record deleted from database (hard delete)")
    else:
        share_db_id, is_active = share_record
        if not is_active:
            log_success(f"Share record exists but is_active=false (soft delete)")
        else:
            log_error(f"Share record still exists with is_active=true! This is incorrect.")
            cur.close()
            conn.close()
            return False

    cur.close()
    conn.close()

    print()
    print("=" * 80)
    print("✅ Feature #138 Validation: PASSED")
    print("=" * 80)
    print()
    print("Validation Summary:")
    print("  1. ✅ User can create diagram")
    print("  2. ✅ User can generate share link")
    print("  3. ✅ Share link is accessible")
    print("  4. ✅ User can revoke share link (DELETE endpoint)")
    print("  5. ✅ Revoked share returns 404/410 error")
    print("  6. ✅ Database record deleted or is_active=false")
    print()

    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
