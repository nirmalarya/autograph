#!/usr/bin/env python3
"""
Feature #139 Validation: Share tracking - view count and last accessed

This script validates that:
1. User can create a diagram
2. User can generate a share link
3. Share link access is tracked (view count increments)
4. Last accessed timestamp is updated on each access
5. Share statistics can be retrieved from database
"""

import requests
import sys
import time
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
    print("Feature #139: Share Tracking - View Count and Last Accessed")
    print("=" * 80)
    print()

    # Step 1: Register a test user
    log_step(1, "Register test user")
    test_email = f"share_tracking_test_{datetime.now().timestamp()}@example.com"
    test_password = "SecurePassword123!"

    register_response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": test_email,
            "password": test_password,
            "full_name": "Share Tracking Test User"
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
            "title": "Test Diagram for Share Tracking",
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

    # Step 5: Check initial view count in database
    log_step(5, "Check initial share statistics (should be 0 views)")

    cur.execute(
        "SELECT view_count, last_accessed_at FROM shares WHERE id = %s",
        (share_id,)
    )
    stats = cur.fetchone()
    if stats:
        initial_view_count, initial_last_accessed = stats
        log_success(f"Initial view_count: {initial_view_count or 0}, last_accessed: {initial_last_accessed or 'Never'}")

        if initial_view_count and initial_view_count > 0:
            log_error(f"Initial view count should be 0, but got {initial_view_count}")
            cur.close()
            conn.close()
            return False
    else:
        log_error("Share not found in database")
        cur.close()
        conn.close()
        return False

    # Step 6: Access share link 5 times to simulate multiple views
    log_step(6, "Access share link 5 times")

    for i in range(5):
        time.sleep(0.2)  # Small delay between accesses
        access_response = requests.get(
            f"{DIAGRAM_SERVICE}/shared/{share_token}"
        )

        if access_response.status_code != 200:
            log_error(f"Share access #{i+1} failed: {access_response.status_code}")
            cur.close()
            conn.close()
            return False

        log_info(f"Access #{i+1} successful")

    log_success("Accessed share link 5 times")

    # Step 7: Verify view count is 5
    log_step(7, "Verify view count is 5")

    cur.execute(
        "SELECT view_count, last_accessed_at FROM shares WHERE id = %s",
        (share_id,)
    )
    stats = cur.fetchone()
    if stats:
        view_count, last_accessed = stats
        log_info(f"View count: {view_count}, Last accessed: {last_accessed}")

        if view_count == 5:
            log_success(f"View count correctly incremented to 5")
        else:
            log_error(f"Expected view count 5, got {view_count}")
            cur.close()
            conn.close()
            return False

        if last_accessed:
            log_success(f"Last accessed timestamp updated: {last_accessed}")
        else:
            log_error("Last accessed timestamp not set")
            cur.close()
            conn.close()
            return False
    else:
        log_error("Share not found in database")
        cur.close()
        conn.close()
        return False

    # Step 8: Access one more time
    log_step(8, "Access share link one more time")
    time.sleep(0.5)  # Delay to ensure timestamp changes

    access_response = requests.get(
        f"{DIAGRAM_SERVICE}/shared/{share_token}"
    )

    if access_response.status_code != 200:
        log_error(f"Share access failed: {access_response.status_code}")
        cur.close()
        conn.close()
        return False

    log_success("Share accessed again")

    # Step 9: Verify view count incremented to 6 and timestamp updated
    log_step(9, "Verify view count is 6 and timestamp updated")

    cur.execute(
        "SELECT view_count, last_accessed_at FROM shares WHERE id = %s",
        (share_id,)
    )
    stats = cur.fetchone()
    if stats:
        final_view_count, final_last_accessed = stats
        log_info(f"Final view count: {final_view_count}, Last accessed: {final_last_accessed}")

        if final_view_count == 6:
            log_success(f"View count correctly incremented to 6")
        else:
            log_error(f"Expected view count 6, got {final_view_count}")
            cur.close()
            conn.close()
            return False

        # Compare timestamps to ensure it was updated
        if final_last_accessed and last_accessed:
            if final_last_accessed > last_accessed:
                log_success(f"Last accessed timestamp updated (was: {last_accessed}, now: {final_last_accessed})")
            else:
                log_error("Last accessed timestamp not updated")
                cur.close()
                conn.close()
                return False
        else:
            log_error("Timestamp comparison failed")
            cur.close()
            conn.close()
            return False
    else:
        log_error("Share not found in database")
        cur.close()
        conn.close()
        return False

    cur.close()
    conn.close()

    print()
    print("=" * 80)
    print("✅ Feature #139 Validation: PASSED")
    print("=" * 80)
    print()
    print("Validation Summary:")
    print("  1. ✅ User can create diagram")
    print("  2. ✅ User can generate share link")
    print("  3. ✅ Initial view count is 0")
    print("  4. ✅ Share link access tracked (view count increments)")
    print("  5. ✅ View count reaches 5 after 5 accesses")
    print("  6. ✅ Last accessed timestamp updated on each access")
    print("  7. ✅ View count increments to 6 after additional access")
    print("  8. ✅ Last accessed timestamp updated correctly")
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
