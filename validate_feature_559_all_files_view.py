#!/usr/bin/env python3
"""
E2E Test for Feature #559: Organization: Dashboard: All files view

Test steps:
1. Create test user and login
2. Create multiple diagrams (own diagrams)
3. Create second user and share diagram with first user
4. Login as first user
5. Navigate to dashboard and check "All" view
6. Verify all diagrams shown (both own and shared)
"""

import requests
import psycopg2
import sys
import uuid
import time

# Configuration
API_BASE = "https://localhost:8080"
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

def cleanup_test_users(emails):
    """Clean up test users from database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        for email in emails:
            cur.execute("DELETE FROM users WHERE email = %s", (email,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        pass  # Ignore cleanup errors

def register_and_login(email, password, name):
    """Helper to register and login a user."""
    # Register
    register_response = requests.post(
        f"{API_BASE}/api/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": name
        },
        verify=False
    )

    if register_response.status_code != 201:
        return None, None, f"Registration failed: {register_response.text}"

    # Get user_id
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    result = cur.fetchone()
    user_id = result[0] if result else None

    # Mark as verified
    cur.execute("UPDATE users SET is_verified = TRUE WHERE email = %s", (email,))
    conn.commit()
    cur.close()
    conn.close()

    # Login
    login_response = requests.post(
        f"{API_BASE}/api/auth/login",
        json={
            "email": email,
            "password": password
        },
        verify=False
    )

    if login_response.status_code != 200:
        return None, None, f"Login failed: {login_response.text}"

    return login_response.json()["access_token"], user_id, None

def create_diagram(token, name, diagram_type="canvas"):
    """Create a diagram."""
    response = requests.post(
        f"{API_BASE}/api/diagrams/",
        json={
            "name": name,
            "type": diagram_type
        },
        headers={"Authorization": f"Bearer {token}"},
        verify=False
    )

    if response.status_code == 201:
        return response.json()["id"], None
    return None, f"Failed to create diagram: {response.text}"

def share_diagram(token, diagram_id, email, permission="view"):
    """Share a diagram with another user."""
    response = requests.post(
        f"{API_BASE}/api/diagrams/{diagram_id}/share",
        json={
            "email": email,
            "permission": permission
        },
        headers={"Authorization": f"Bearer {token}"},
        verify=False
    )

    if response.status_code == 200:
        return None
    return f"Failed to share diagram: {response.text}"

def list_diagrams(token, page=1, page_size=20):
    """List all diagrams (the default 'All' view)."""
    response = requests.get(
        f"{API_BASE}/api/diagrams/?page={page}&page_size={page_size}",
        headers={"Authorization": f"Bearer {token}"},
        verify=False
    )

    if response.status_code == 200:
        return response.json(), None
    return None, f"Failed to list diagrams: {response.text}"

def main():
    """Run E2E test for Feature #559."""
    print("\n" + "="*80)
    print("Feature #559: Organization: Dashboard: All files view - E2E Test")
    print("="*80)

    test_email_1 = f"test_559_user1_{uuid.uuid4().hex[:8]}@example.com"
    test_email_2 = f"test_559_user2_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPassword123!"

    try:
        # Step 1: Create and login user 1
        log_step(1, "Create and login first user")
        token_1, user_id_1, error = register_and_login(test_email_1, password, "Test User 1")
        if error:
            log_error(error)
            return False
        log_success(f"User 1 registered and logged in: {test_email_1}")

        # Step 2: Create own diagrams for user 1
        log_step(2, "Create own diagrams for user 1")
        own_diagram_ids = []
        for i in range(3):
            diagram_id, error = create_diagram(token_1, f"User 1 Diagram {i+1}")
            if error:
                log_error(error)
                return False
            own_diagram_ids.append(diagram_id)
            log_success(f"Created diagram: User 1 Diagram {i+1} (ID: {diagram_id})")

        # Step 3: Create and login user 2
        log_step(3, "Create and login second user")
        token_2, user_id_2, error = register_and_login(test_email_2, password, "Test User 2")
        if error:
            log_error(error)
            return False
        log_success(f"User 2 registered and logged in: {test_email_2}")

        # Step 4: User 2 creates diagrams and shares with user 1
        log_step(4, "User 2 creates diagrams and shares with user 1")
        shared_diagram_ids = []
        for i in range(2):
            diagram_id, error = create_diagram(token_2, f"User 2 Shared Diagram {i+1}")
            if error:
                log_error(error)
                return False
            log_success(f"User 2 created diagram: User 2 Shared Diagram {i+1} (ID: {diagram_id})")

            # Share with user 1
            error = share_diagram(token_2, diagram_id, test_email_1, "view")
            if error:
                log_error(error)
                return False
            shared_diagram_ids.append(diagram_id)
            log_success(f"Shared diagram {diagram_id} with {test_email_1}")

        # Wait a moment for shares to propagate
        time.sleep(1)

        # Step 5: User 1 lists all diagrams (All view)
        log_step(5, "User 1 fetches 'All Diagrams' view")
        all_diagrams, error = list_diagrams(token_1)
        if error:
            log_error(error)
            return False

        # Step 6: Verify all diagrams shown
        log_step(6, "Verify all diagrams shown (own and shared)")

        if "diagrams" not in all_diagrams:
            log_error("Response does not contain 'diagrams' key")
            log_error(f"Response: {all_diagrams}")
            return False

        diagrams = all_diagrams["diagrams"]
        total_count = all_diagrams.get("total_count", len(diagrams))

        log_success(f"Retrieved {len(diagrams)} diagrams (total: {total_count})")

        # Verify own diagrams are present
        print("\nVerifying own diagrams:")
        own_found = 0
        for diagram_id in own_diagram_ids:
            found = any(d["id"] == diagram_id for d in diagrams)
            if found:
                own_found += 1
                log_success(f"Found own diagram: {diagram_id}")
            else:
                log_error(f"Missing own diagram: {diagram_id}")

        # Verify shared diagrams are present
        print("\nVerifying shared diagrams:")
        shared_found = 0
        for diagram_id in shared_diagram_ids:
            found = any(d["id"] == diagram_id for d in diagrams)
            if found:
                shared_found += 1
                log_success(f"Found shared diagram: {diagram_id}")
            else:
                log_error(f"Missing shared diagram: {diagram_id}")

        # Final verification
        print("\n" + "="*80)
        print("VERIFICATION SUMMARY")
        print("="*80)
        print(f"Own diagrams created: {len(own_diagram_ids)}")
        print(f"Own diagrams found in All view: {own_found}")
        print(f"Shared diagrams: {len(shared_diagram_ids)}")
        print(f"Shared diagrams found in All view: {shared_found}")

        if own_found == len(own_diagram_ids) and shared_found == len(shared_diagram_ids):
            print("\n" + "="*80)
            print("✅ ALL TESTS PASSED - Feature #559 working correctly!")
            print("="*80)
            print("\nThe 'All Diagrams' view successfully shows:")
            print("  ✓ User's own diagrams")
            print("  ✓ Diagrams shared with user")
            return True
        else:
            log_error("Not all diagrams were found in the All view")
            return False

    except Exception as e:
        log_error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        cleanup_test_users([test_email_1, test_email_2])

if __name__ == "__main__":
    # Disable SSL warnings for local testing
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    success = main()
    sys.exit(0 if success else 1)
