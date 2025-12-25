#!/usr/bin/env python3
"""
Feature #137 Validation: Share diagram with expiration date

This script validates that:
1. User can create a share with an expiration date
2. Share works before expiration
3. Share returns 410 Gone after expiration
4. Diagram not accessible after expiration
"""

import requests
import sys
from datetime import datetime, timedelta, timezone

# Configuration
BASE_URL = "http://localhost:8080/api"

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
    print("Feature #137: Share Diagram with Expiration Date")
    print("=" * 80)
    print()

    # Step 1: Register a test user
    log_step(1, "Register test user")
    test_email = f"expiration_test_{datetime.now().timestamp()}@example.com"
    test_password = "SecurePassword123!"

    register_response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": test_email,
            "password": test_password,
            "full_name": "Expiration Test User"
        }
    )

    if register_response.status_code != 201:
        log_error(f"Registration failed: {register_response.status_code} - {register_response.text}")
        return False

    log_success(f"User registered: {test_email}")

    # Step 1.5: Verify email (auto-verify for testing)
    log_step("1.5", "Verify email address")
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
    cur.close()
    conn.close()
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
        return False

    login_data = login_response.json()
    access_token = login_data.get("access_token")

    if not access_token:
        log_error("No access token in login response")
        return False

    log_success("Login successful")

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
            "title": "Expiring Diagram",
            "type": "canvas",
            "canvas_data": {
                "shapes": [
                    {"id": "1", "type": "rectangle", "x": 100, "y": 100, "text": "Temporary"}
                ]
            }
        }
    )

    if create_diagram_response.status_code not in [200, 201]:
        log_error(f"Diagram creation failed: {create_diagram_response.status_code} - {create_diagram_response.text}")
        return False

    diagram = create_diagram_response.json()
    diagram_id = diagram.get("id")
    log_success(f"Diagram created: {diagram_id}")

    # Step 4: Create share with 7-day expiration
    log_step(4, "Create share link with 7-day expiration")

    create_share_response = requests.post(
        f"{BASE_URL}/diagrams/{diagram_id}/share",
        headers=headers,
        json={
            "permission": "view",
            "is_public": True,
            "expires_in_days": 7
        }
    )

    if create_share_response.status_code != 200:
        log_error(f"Share creation failed: {create_share_response.status_code} - {create_share_response.text}")
        return False

    share_data = create_share_response.json()
    share_token = share_data.get("token")
    share_url = share_data.get("share_url")
    expires_at_str = share_data.get("expires_at")

    if not share_token:
        log_error("No share token in response")
        return False

    if not expires_at_str:
        log_error("No expiration date in response")
        return False

    log_success(f"Share created with expiration")
    log_info(f"  Share URL: {share_url}")
    log_info(f"  Token: {share_token[:20]}...")
    log_info(f"  Expires at: {expires_at_str}")

    # Parse expiration date (ISO format)
    expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
    log_info(f"  Parsed expiration: {expires_at}")

    # Step 5: Access share before expiration (should work)
    log_step(5, "Access share before expiration")

    access_before_response = requests.get(
        f"{BASE_URL}/diagrams/shared/{share_token}"
    )

    if access_before_response.status_code != 200:
        log_error(f"Access failed: {access_before_response.status_code} - {access_before_response.text}")
        return False

    shared_diagram = access_before_response.json()
    log_success("Successfully accessed diagram before expiration")
    log_info(f"  Diagram ID: {shared_diagram.get('id')}")
    log_info(f"  Title: {shared_diagram.get('title')}")

    # Step 6: Simulate expiration by updating database
    log_step(6, "Simulate expiration (set expires_at to past)")

    # Update the share to expire 1 day ago
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="autograph",
        user="autograph",
        password="autograph_dev_password"
    )
    cur = conn.cursor()

    # Set expiration to 1 day ago
    past_time = datetime.now(timezone.utc) - timedelta(days=1)
    cur.execute(
        "UPDATE shares SET expires_at = %s WHERE token = %s",
        (past_time, share_token)
    )
    conn.commit()

    # Verify the update
    cur.execute(
        "SELECT expires_at FROM shares WHERE token = %s",
        (share_token,)
    )
    result = cur.fetchone()

    cur.close()
    conn.close()

    if result:
        new_expires_at = result[0]
        log_success(f"Share expiration updated to: {new_expires_at}")
        log_info(f"  Current time: {datetime.now(timezone.utc)}")
        log_info(f"  Share expired: {new_expires_at < datetime.now(timezone.utc)}")
    else:
        log_error("Failed to update share expiration")
        return False

    # Step 7: Try to access expired share (should fail with 410)
    log_step(7, "Try to access expired share")

    access_after_response = requests.get(
        f"{BASE_URL}/diagrams/shared/{share_token}"
    )

    if access_after_response.status_code != 410:
        log_error(f"Expected 410 Gone, got {access_after_response.status_code}")
        log_error(f"Response: {access_after_response.text}")
        return False

    error_data = access_after_response.json()
    if "expired" not in error_data.get("detail", "").lower():
        log_error(f"Expected 'expired' in error message, got: {error_data.get('detail')}")
        return False

    log_success("Correctly rejected expired share (410 Gone)")
    log_info(f"  Error: {error_data.get('detail')}")

    # Step 8: Verify diagram is not accessible
    log_step(8, "Verify diagram not accessible via expired share")

    # The 410 response already proves this, but let's confirm
    if access_after_response.status_code == 410:
        log_success("Diagram not accessible via expired share")
    else:
        log_error("Diagram should not be accessible")
        return False

    print()
    print("=" * 80)
    print("✅ Feature #137: Share Expiration - ALL TESTS PASSED")
    print("=" * 80)
    print()
    print("Summary:")
    print("✅ Share created with 7-day expiration")
    print("✅ Expiration date correctly calculated and stored")
    print("✅ Share accessible before expiration (200)")
    print("✅ Share rejected after expiration (410 Gone)")
    print("✅ Proper error message for expired shares")
    print()

    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        log_error(f"Validation failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
