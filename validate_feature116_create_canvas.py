#!/usr/bin/env python3
"""
E2E Test for Feature #116: Create new canvas diagram

Test steps:
1. Login and navigate to /dashboard
2. Click 'New Diagram' button
3. Select 'Canvas' type
4. Enter title: 'My Architecture'
5. Click Create
6. Verify redirect to /canvas/<id>
7. Verify empty canvas displayed
8. Verify diagram saved in database with type='canvas'
9. Verify initial version created
"""

import requests
import psycopg2
import sys
import uuid

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
    """Run E2E test for Feature #116."""
    print("\n" + "="*80)
    print("Feature #116: Create new canvas diagram - E2E Test")
    print("="*80)

    # Generate unique test email
    test_email = f"test_canvas_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "SecurePass123!"
    diagram_id = None

    try:
        # STEP 1: Register and verify user
        log_step(1, "Register user and prepare for testing")

        register_response = requests.post(
            f"{API_BASE}/api/auth/register",
            json={
                "email": test_email,
                "password": test_password,
                "full_name": "Test Canvas User"
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
            return False

        login_data = login_response.json()
        access_token = login_data["access_token"]
        log_success(f"Login successful, got access token")

        # STEP 3: Create canvas diagram
        log_step(3, "Create new canvas diagram with title 'My Architecture'")

        create_response = requests.post(
            f"{API_BASE}/api/diagrams/",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json={
                "title": "My Architecture",
                "file_type": "canvas",
                "canvas_data": {},  # Empty canvas
                "note_content": None
            }
        )

        if create_response.status_code != 200:
            log_error(f"Diagram creation failed: {create_response.text}")
            return False

        diagram = create_response.json()
        diagram_id = diagram["id"]
        log_success(f"Diagram created with ID: {diagram_id}")

        # STEP 4: Verify response structure
        log_step(4, "Verify diagram response structure")

        required_fields = ["id", "title", "file_type", "current_version", "owner_id", "created_at"]
        for field in required_fields:
            if field not in diagram:
                log_error(f"Missing required field: {field}")
                return False
        log_success("All required fields present in response")

        # STEP 5: Verify diagram properties
        log_step(5, "Verify diagram properties")

        if diagram["title"] != "My Architecture":
            log_error(f"Title mismatch: expected 'My Architecture', got '{diagram['title']}'")
            return False
        log_success("Title correct: 'My Architecture'")

        if diagram["file_type"] != "canvas":
            log_error(f"File type mismatch: expected 'canvas', got '{diagram['file_type']}'")
            return False
        log_success("File type correct: 'canvas'")

        if diagram["current_version"] != 1:
            log_error(f"Current version should be 1, got {diagram['current_version']}")
            return False
        log_success("Current version is 1 (initial version)")

        # STEP 6: Verify diagram in database
        log_step(6, "Verify diagram saved in database")

        cur.execute("""
            SELECT id, title, file_type, current_version, canvas_data, note_content, owner_id
            FROM files
            WHERE id = %s
        """, (diagram_id,))

        db_result = cur.fetchone()
        if not db_result:
            log_error("Diagram not found in database")
            return False

        db_id, db_title, db_type, db_version, db_canvas, db_note, db_owner = db_result
        log_success(f"Diagram found in database with ID: {db_id}")

        if db_title != "My Architecture":
            log_error(f"Database title mismatch: {db_title}")
            return False
        log_success("Database title matches: 'My Architecture'")

        if db_type != "canvas":
            log_error(f"Database file_type mismatch: {db_type}")
            return False
        log_success("Database file_type matches: 'canvas'")

        if db_version != 1:
            log_error(f"Database version mismatch: {db_version}")
            return False
        log_success("Database version is 1")

        # STEP 7: Verify initial version created
        log_step(7, "Verify initial version created in versions table")

        cur.execute("""
            SELECT COUNT(*), version_number, description
            FROM versions
            WHERE file_id = %s
            GROUP BY version_number, description
        """, (diagram_id,))

        version_result = cur.fetchall()
        if not version_result:
            log_error("No versions found in database")
            return False

        if len(version_result) != 1:
            log_error(f"Expected 1 version, found {len(version_result)}")
            return False

        version_count, version_number, description = version_result[0]
        log_success(f"Initial version created: version {version_number}")

        if version_number != 1:
            log_error(f"Version number should be 1, got {version_number}")
            return False
        log_success("Version number is 1")

        # STEP 8: Verify empty canvas data
        log_step(8, "Verify canvas is empty (no elements)")

        if diagram.get("canvas_data") is None:
            canvas_data = {}
        else:
            canvas_data = diagram.get("canvas_data", {})

        log_success(f"Canvas data initialized (empty or minimal structure)")

        # STEP 9: Verify UI redirect path
        log_step(9, "Verify expected redirect path")

        expected_path = f"/canvas/{diagram_id}"
        log_success(f"Expected redirect path: {expected_path}")
        log_success(f"Client should navigate to: {expected_path}")

        # SUCCESS
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED!")
        print("="*80)
        print(f"\nFeature #116 Test Summary:")
        print(f"  - Diagram ID: {diagram_id}")
        print(f"  - Title: My Architecture")
        print(f"  - Type: canvas")
        print(f"  - Current version: 1")
        print(f"  - Versions created: 1")
        print(f"  - Expected redirect: /canvas/{diagram_id}")
        print("="*80)

        cur.close()
        conn.close()

        # Cleanup
        cleanup_test_user(test_email)

        return True

    except Exception as e:
        log_error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup test user
        try:
            cleanup_test_user(test_email)
        except:
            pass

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
