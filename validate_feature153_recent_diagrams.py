#!/usr/bin/env python3
"""
E2E Test for Feature #153: Recent diagrams view

Test steps:
1. Create 15 diagrams
2. Access diagrams 1-10
3. Navigate to /dashboard
4. Click 'Recent' tab
5. Verify only 10 most recently accessed diagrams shown
6. Verify sorted by last accessed time
7. Access diagram 11
8. Verify diagram 11 now in recent list
9. Verify oldest diagram removed from list
"""

import requests
import psycopg2
import sys
import uuid
import time
import base64
import json

# Configuration
API_BASE = "http://localhost:8080"
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "autograph",
    "user": "autograph",
    "password": "autograph_dev_password"
}

def log_step(step_num, description):
    """Log test step."""
    print(f"\n{'='*80}")
    print(f"STEP {step_num}: {description}")
    print(f"{'='*80}")

def log_success(message):
    """Log success message."""
    print(f"✅ {message}")

def log_error(message):
    """Log error message."""
    print(f"❌ {message}")

def cleanup_test_user(email):
    """Clean up test user from database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE email = %s", (email,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        pass  # Ignore cleanup errors

def main():
    """Run E2E test for Feature #153."""
    print("\n" + "="*80)
    print("Feature #153: Recent diagrams view - E2E Test")
    print("="*80)

    # Generate unique test email
    test_email = f"test_recent_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "SecurePass123!"
    diagram_ids = []

    try:
        # STEP 1: Register and verify user
        log_step(1, "Register user and prepare for testing")

        register_response = requests.post(
            f"{API_BASE}/api/auth/register",
            json={
                "email": test_email,
                "password": test_password,
                "full_name": "Test Recent User"
            }
        )

        if register_response.status_code != 201:
            log_error(f"Registration failed: {register_response.text}")
            return False

        log_success("User registered successfully")

        # Mark user as verified in database (skip email verification for test)
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_verified = TRUE WHERE email = %s", (test_email,))
        conn.commit()
        log_success("User marked as verified")

        # STEP 2: Login to get access token
        log_step(2, "Login and get authentication token")

        login_response = requests.post(
            f"{API_BASE}/api/auth/login",
            json={
                "email": test_email,
                "password": test_password
            }
        )

        if login_response.status_code != 200:
            log_error(f"Login failed: {login_response.text}")
            cur.close()
            conn.close()
            return False

        login_data = login_response.json()
        access_token = login_data["access_token"]
        log_success(f"Login successful, got access token")

        # STEP 3: Create 15 diagrams
        log_step(3, "Create 15 test diagrams")

        for i in range(15):
            create_response = requests.post(
                f"{API_BASE}/api/diagrams/",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "title": f"Test Diagram {i+1}",
                    "file_type": "canvas",
                    "canvas_data": {"shapes": []},
                    "note_content": None
                }
            )

            if create_response.status_code not in [200, 201]:
                log_error(f"Failed to create diagram {i+1}: {create_response.text}")
                cur.close()
                conn.close()
                return False

            diagram_data = create_response.json()
            diagram_ids.append(diagram_data["id"])

        log_success(f"Created 15 diagrams")

        # STEP 4: Access diagrams 1-10 to set last_accessed_at
        log_step(4, "Access diagrams 1-10 to track recent access")

        for i in range(10):
            diagram_id = diagram_ids[i]
            get_response = requests.get(
                f"{API_BASE}/api/diagrams/{diagram_id}",
                headers={
                    "Authorization": f"Bearer {access_token}"
                }
            )

            if get_response.status_code != 200:
                log_error(f"Failed to access diagram {i+1}: {get_response.text}")
                cur.close()
                conn.close()
                return False

            # Small delay to ensure different timestamps
            time.sleep(0.1)

        log_success("Accessed diagrams 1-10")

        # STEP 5: Get recent diagrams
        log_step(5, "Fetch recent diagrams via API")

        recent_response = requests.get(
            f"{API_BASE}/api/diagrams/recent",
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )

        if recent_response.status_code != 200:
            log_error(f"Failed to get recent diagrams: {recent_response.text}")
            cur.close()
            conn.close()
            return False

        recent_data = recent_response.json()
        recent_diagrams = recent_data["diagrams"]
        log_success(f"Got {len(recent_diagrams)} recent diagrams")

        # STEP 6: Verify only 10 diagrams returned
        log_step(6, "Verify only 10 most recently accessed diagrams shown")

        if len(recent_diagrams) != 10:
            log_error(f"Expected 10 diagrams, got {len(recent_diagrams)}")
            cur.close()
            conn.close()
            return False

        log_success("Exactly 10 diagrams returned")

        # STEP 7: Verify sorted by last accessed time
        log_step(7, "Verify diagrams sorted by last accessed time (most recent first)")

        last_accessed_times = [d.get("last_accessed_at") for d in recent_diagrams]

        # Check all have last_accessed_at
        if None in last_accessed_times:
            log_error("Some diagrams missing last_accessed_at timestamp")
            cur.close()
            conn.close()
            return False

        # Check sorted descending (most recent first)
        is_sorted = all(
            last_accessed_times[i] >= last_accessed_times[i+1]
            for i in range(len(last_accessed_times)-1)
        )

        if not is_sorted:
            log_error(f"Diagrams not sorted by last_accessed_at")
            log_error(f"Timestamps: {last_accessed_times}")
            cur.close()
            conn.close()
            return False

        log_success("Diagrams sorted by last accessed time (most recent first)")
        log_success(f"  First accessed: {last_accessed_times[0]}")
        log_success(f"  Last accessed: {last_accessed_times[-1]}")

        # STEP 8: Access diagram 11
        log_step(8, "Access diagram 11 to add it to recent list")

        diagram_11_id = diagram_ids[10]  # 0-indexed
        get_response = requests.get(
            f"{API_BASE}/api/diagrams/{diagram_11_id}",
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )

        if get_response.status_code != 200:
            log_error(f"Failed to access diagram 11: {get_response.text}")
            cur.close()
            conn.close()
            return False

        log_success("Accessed diagram 11")
        time.sleep(0.2)  # Ensure timestamp is newer

        # STEP 9: Verify diagram 11 now in recent list
        log_step(9, "Verify diagram 11 now in recent list and oldest removed")

        recent_response = requests.get(
            f"{API_BASE}/api/diagrams/recent",
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )

        if recent_response.status_code != 200:
            log_error(f"Failed to get recent diagrams: {recent_response.text}")
            cur.close()
            conn.close()
            return False

        recent_data = recent_response.json()
        recent_diagrams = recent_data["diagrams"]
        recent_ids = [d["id"] for d in recent_diagrams]

        # Verify diagram 11 is in the list
        if diagram_11_id not in recent_ids:
            log_error(f"Diagram 11 not in recent list")
            log_error(f"Recent IDs: {recent_ids}")
            cur.close()
            conn.close()
            return False

        log_success("Diagram 11 is in recent list")

        # Verify it's at the top (most recent)
        if recent_ids[0] == diagram_11_id:
            log_success("Diagram 11 is at top of list (most recent)")
        else:
            log_error(f"Diagram 11 not at top of list (position: {recent_ids.index(diagram_11_id) + 1})")

        # Verify oldest diagram (diagram 1) removed from list
        oldest_id = diagram_ids[0]
        if oldest_id in recent_ids:
            log_error(f"Oldest diagram (diagram 1) still in recent list")
            cur.close()
            conn.close()
            return False

        log_success("Oldest diagram (diagram 1) removed from list")

        # Print final recent list
        print("\n" + "="*80)
        print("RECENT DIAGRAMS (Final State)")
        print("="*80)
        for i, d in enumerate(recent_diagrams, 1):
            print(f"{i}. {d['title']} (accessed: {d['last_accessed_at']})")

        # Cleanup
        cur.close()
        conn.close()
        cleanup_test_user(test_email)

        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED")
        print("="*80)
        print("Feature #153 (Recent Diagrams) is working correctly!")
        print("="*80)
        return True

    except Exception as e:
        log_error(f"Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        cleanup_test_user(test_email)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
