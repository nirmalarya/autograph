#!/usr/bin/env python3
"""
Feature #136 Validation: Share diagram with password protection

This script validates that:
1. User can create a share with password protection
2. Password prompt is required when accessing the shared link
3. Wrong password returns error
4. Correct password grants access
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
    print("Feature #136: Share Diagram with Password Protection")
    print("=" * 80)
    print()

    # Step 1: Register a test user
    log_step(1, "Register test user")
    test_email = f"password_share_test_{datetime.now().timestamp()}@example.com"
    test_password = "SecurePassword123!"

    register_response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": test_email,
            "password": test_password,
            "full_name": "Password Share Test User"
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
    user_id = login_data.get("user", {}).get("id")

    if not access_token:
        log_error("No access token in login response")
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
            "title": "Password Protected Diagram",
            "type": "canvas",
            "canvas_data": {
                "shapes": [
                    {"id": "1", "type": "rectangle", "x": 100, "y": 100, "text": "Confidential"}
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

    # Step 4: Create password-protected share link
    log_step(4, "Create password-protected share link")
    share_password = "SecurePass123"

    create_share_response = requests.post(
        f"{BASE_URL}/diagrams/{diagram_id}/share",
        headers=headers,
        json={
            "permission": "view",
            "is_public": True,
            "password": share_password
        }
    )

    if create_share_response.status_code != 200:
        log_error(f"Share creation failed: {create_share_response.status_code} - {create_share_response.text}")
        return False

    share_data = create_share_response.json()
    share_token = share_data.get("token")
    share_url = share_data.get("share_url")
    has_password = share_data.get("has_password")

    if not share_token:
        log_error("No share token in response")
        return False

    if not has_password:
        log_error("Password protection not enabled on share")
        return False

    log_success(f"Password-protected share created")
    log_info(f"  Share URL: {share_url}")
    log_info(f"  Token: {share_token[:20]}...")
    log_info(f"  Has password: {has_password}")

    # Step 5: Try to access without password (should fail)
    log_step(5, "Try to access shared diagram without password")

    access_no_password_response = requests.get(
        f"{BASE_URL}/diagrams/shared/{share_token}"
    )

    if access_no_password_response.status_code != 401:
        log_error(f"Expected 401 Unauthorized, got {access_no_password_response.status_code}")
        return False

    error_data = access_no_password_response.json()
    if "password required" not in error_data.get("detail", "").lower():
        log_error(f"Expected 'Password required' error, got: {error_data.get('detail')}")
        return False

    log_success("Correctly rejected access without password (401 Unauthorized)")
    log_info(f"  Error: {error_data.get('detail')}")

    # Step 6: Try to access with wrong password (should fail)
    log_step(6, "Try to access with wrong password")

    wrong_password = "WrongPassword123"
    access_wrong_password_response = requests.get(
        f"{BASE_URL}/diagrams/shared/{share_token}",
        params={"password": wrong_password}
    )

    if access_wrong_password_response.status_code != 401:
        log_error(f"Expected 401 Unauthorized, got {access_wrong_password_response.status_code}")
        return False

    error_data = access_wrong_password_response.json()
    if "invalid password" not in error_data.get("detail", "").lower():
        log_error(f"Expected 'Invalid password' error, got: {error_data.get('detail')}")
        return False

    log_success("Correctly rejected wrong password (401 Unauthorized)")
    log_info(f"  Error: {error_data.get('detail')}")

    # Step 7: Access with correct password (should succeed)
    log_step(7, "Access with correct password")

    access_correct_password_response = requests.get(
        f"{BASE_URL}/diagrams/shared/{share_token}",
        params={"password": share_password}
    )

    if access_correct_password_response.status_code != 200:
        log_error(f"Access failed: {access_correct_password_response.status_code} - {access_correct_password_response.text}")
        return False

    shared_diagram = access_correct_password_response.json()

    # Verify diagram data
    if shared_diagram.get("id") != diagram_id:
        log_error(f"Diagram ID mismatch: expected {diagram_id}, got {shared_diagram.get('id')}")
        return False

    if shared_diagram.get("title") != "Password Protected Diagram":
        log_error(f"Title mismatch: expected 'Password Protected Diagram', got {shared_diagram.get('title')}")
        return False

    if shared_diagram.get("permission") != "view":
        log_error(f"Permission mismatch: expected 'view', got {shared_diagram.get('permission')}")
        return False

    log_success("Successfully accessed diagram with correct password")
    log_info(f"  Diagram ID: {shared_diagram.get('id')}")
    log_info(f"  Title: {shared_diagram.get('title')}")
    log_info(f"  Permission: {shared_diagram.get('permission')}")
    log_info(f"  View count: {shared_diagram.get('view_count')}")

    # Step 8: Verify password protection in database (optional)
    log_step(8, "Verify password protection is persisted")

    # Get share details via API (owner access)
    get_shares_response = requests.get(
        f"{BASE_URL}/diagrams/{diagram_id}/shares",
        headers=headers
    )

    if get_shares_response.status_code == 200:
        shares = get_shares_response.json()
        if shares:
            share = shares[0]
            if "has_password" in share and share["has_password"]:
                log_success("Password protection verified in share metadata")
            else:
                log_info("Share metadata does not expose password protection status (security by design)")
        else:
            log_info("No shares returned from API")
    else:
        log_info(f"Could not verify shares via API (status {get_shares_response.status_code})")

    print()
    print("=" * 80)
    print("✅ Feature #136: Password-Protected Sharing - ALL TESTS PASSED")
    print("=" * 80)
    print()
    print("Summary:")
    print("✅ Share created with password protection")
    print("✅ Access denied without password (401)")
    print("✅ Access denied with wrong password (401)")
    print("✅ Access granted with correct password (200)")
    print("✅ Diagram data accessible after authentication")
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
