#!/usr/bin/env python3
"""
E2E Test for Feature #154: Shared with me view

Test steps:
1. User A shares diagram with User B
2. User B logs in
3. Navigate to /dashboard
4. Click 'Shared with me' tab
5. Verify shared diagram appears
6. Verify owner shown as User A
7. Verify permission level shown (view/edit)
8. User A shares another diagram
9. Verify new diagram appears in list
"""

import requests
import psycopg2
import sys
import uuid
import time

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
        }
    )

    if register_response.status_code != 201:
        return None, f"Registration failed: {register_response.text}"

    # Mark as verified
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
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
        }
    )

    if login_response.status_code != 200:
        return None, f"Login failed: {login_response.text}"

    return login_response.json()["access_token"], None

def main():
    """Run E2E test for Feature #154."""
    print("\n" + "="*80)
    print("Feature #154: Shared with me view - E2E Test")
    print("="*80)

    # Generate unique test emails
    suffix = uuid.uuid4().hex[:8]
    user_a_email = f"test_sharer_{suffix}@example.com"
    user_b_email = f"test_sharee_{suffix}@example.com"
    password = "SecurePass123!"

    diagram_ids = []

    try:
        # STEP 1: Register and login User A (sharer)
        log_step(1, "Register and login User A (diagram owner)")

        token_a, error = register_and_login(user_a_email, password, "User A Sharer")
        if error:
            log_error(error)
            return False

        log_success(f"User A registered and logged in: {user_a_email}")

        # STEP 2: Register and login User B (sharee)
        log_step(2, "Register and login User B (recipient)")

        token_b, error = register_and_login(user_b_email, password, "User B Recipient")
        if error:
            log_error(error)
            return False

        log_success(f"User B registered and logged in: {user_b_email}")

        # STEP 3: User A creates a diagram
        log_step(3, "User A creates a diagram")

        create_response = requests.post(
            f"{API_BASE}/api/diagrams/",
            headers={
                "Authorization": f"Bearer {token_a}",
                "Content-Type": "application/json"
            },
            json={
                "title": "Shared Diagram 1",
                "file_type": "canvas",
                "canvas_data": {"shapes": []},
                "note_content": None
            }
        )

        if create_response.status_code not in [200, 201]:
            log_error(f"Failed to create diagram: {create_response.text}")
            return False

        diagram1_id = create_response.json()["id"]
        diagram_ids.append(diagram1_id)
        log_success(f"Created diagram 1: {diagram1_id}")

        # STEP 4: User A shares diagram with User B (view permission)
        log_step(4, "User A shares diagram 1 with User B (view permission)")

        share_response = requests.post(
            f"{API_BASE}/api/diagrams/{diagram1_id}/share",
            headers={
                "Authorization": f"Bearer {token_a}",
                "Content-Type": "application/json"
            },
            json={
                "shared_with_email": user_b_email,
                "permission": "view"
            }
        )

        if share_response.status_code not in [200, 201]:
            log_error(f"Failed to share diagram: {share_response.text}")
            return False

        log_success("Diagram 1 shared with User B (view permission)")

        # STEP 5: User B checks shared-with-me
        log_step(5, "User B checks 'Shared with me' list")

        shared_response = requests.get(
            f"{API_BASE}/api/diagrams/shared-with-me",
            headers={
                "Authorization": f"Bearer {token_b}"
            }
        )

        if shared_response.status_code != 200:
            log_error(f"Failed to get shared diagrams: {shared_response.text}")
            return False

        shared_data = shared_response.json()
        shared_diagrams = shared_data["diagrams"]
        log_success(f"Got {len(shared_diagrams)} shared diagrams")

        # STEP 6: Verify shared diagram appears
        log_step(6, "Verify shared diagram 1 appears in list")

        if len(shared_diagrams) != 1:
            log_error(f"Expected 1 shared diagram, got {len(shared_diagrams)}")
            return False

        shared_diagram = shared_diagrams[0]

        if shared_diagram["id"] != diagram1_id:
            log_error(f"Wrong diagram ID. Expected {diagram1_id}, got {shared_diagram['id']}")
            return False

        log_success("Shared diagram 1 appears in list")

        # STEP 7: Verify owner shown as User A
        log_step(7, "Verify owner shown as User A")

        if shared_diagram.get("owner_email") != user_a_email:
            log_error(f"Wrong owner. Expected {user_a_email}, got {shared_diagram.get('owner_email')}")
            return False

        log_success(f"Owner correctly shown as: {user_a_email}")

        # STEP 8: Verify permission level shown
        log_step(8, "Verify permission level shown (view)")

        if shared_diagram.get("permission") != "view":
            log_error(f"Wrong permission. Expected 'view', got {shared_diagram.get('permission')}")
            return False

        log_success("Permission level correctly shown as: view")

        # STEP 9: User A creates and shares another diagram
        log_step(9, "User A creates and shares another diagram (edit permission)")

        create_response2 = requests.post(
            f"{API_BASE}/api/diagrams/",
            headers={
                "Authorization": f"Bearer {token_a}",
                "Content-Type": "application/json"
            },
            json={
                "title": "Shared Diagram 2",
                "file_type": "note",
                "canvas_data": None,
                "note_content": "This is shared with edit permission"
            }
        )

        if create_response2.status_code not in [200, 201]:
            log_error(f"Failed to create diagram 2: {create_response2.text}")
            return False

        diagram2_id = create_response2.json()["id"]
        diagram_ids.append(diagram2_id)
        log_success(f"Created diagram 2: {diagram2_id}")

        # Share with edit permission
        share_response2 = requests.post(
            f"{API_BASE}/api/diagrams/{diagram2_id}/share",
            headers={
                "Authorization": f"Bearer {token_a}",
                "Content-Type": "application/json"
            },
            json={
                "shared_with_email": user_b_email,
                "permission": "edit"
            }
        )

        if share_response2.status_code not in [200, 201]:
            log_error(f"Failed to share diagram 2: {share_response2.text}")
            return False

        log_success("Diagram 2 shared with User B (edit permission)")
        time.sleep(0.2)  # Small delay

        # STEP 10: Verify new diagram appears in list
        log_step(10, "Verify both diagrams appear in shared list")

        shared_response2 = requests.get(
            f"{API_BASE}/api/diagrams/shared-with-me",
            headers={
                "Authorization": f"Bearer {token_b}"
            }
        )

        if shared_response2.status_code != 200:
            log_error(f"Failed to get shared diagrams: {shared_response2.text}")
            return False

        shared_data2 = shared_response2.json()
        shared_diagrams2 = shared_data2["diagrams"]

        if len(shared_diagrams2) != 2:
            log_error(f"Expected 2 shared diagrams, got {len(shared_diagrams2)}")
            return False

        log_success("Both diagrams appear in shared list")

        # Verify diagram 2 details
        diagram2 = next((d for d in shared_diagrams2 if d["id"] == diagram2_id), None)
        if not diagram2:
            log_error("Diagram 2 not found in list")
            return False

        if diagram2.get("permission") != "edit":
            log_error(f"Wrong permission for diagram 2. Expected 'edit', got {diagram2.get('permission')}")
            return False

        log_success("Diagram 2 has correct 'edit' permission")

        # Print final shared list
        print("\n" + "="*80)
        print("SHARED WITH ME (Final State)")
        print("="*80)
        for i, d in enumerate(shared_diagrams2, 1):
            print(f"{i}. {d['title']}")
            print(f"   Owner: {d.get('owner_email')}")
            print(f"   Permission: {d.get('permission')}")
            print(f"   Shared at: {d.get('shared_at')}")

        # Cleanup
        cleanup_test_users([user_a_email, user_b_email])

        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED")
        print("="*80)
        print("Feature #154 (Shared with me) is working correctly!")
        print("="*80)
        return True

    except Exception as e:
        log_error(f"Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        cleanup_test_users([user_a_email, user_b_email])
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
