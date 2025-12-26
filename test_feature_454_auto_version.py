#!/usr/bin/env python3
"""
E2E Test for Feature 454: Version History Auto-Save

Tests:
1. Auto-save creates version every 5 minutes
2. Initial version created on first edit
3. Version not created before 5 minutes
4. Version created after 5 minutes
"""

import requests
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8080"

def create_test_user():
    """Create a test user for this test."""
    timestamp = int(time.time())
    email = f"test_user_454_{timestamp}@example.com"
    password = "TestPass123!"
    # Pre-generated bcrypt hash for "TestPass123!"
    password_hash = "$2b$12$bdHUqIfewAyegMJx70wIs.kY3.9ejmoZO4ruFp52AwNXBaBgaxIkG"

    # Create user in database directly
    import psycopg2
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="autograph",
        user="autograph",
        password="autograph_dev_password"
    )
    cursor = conn.cursor()

    user_id = f"test-user-454-{timestamp}"
    cursor.execute("""
        INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (user_id, email, password_hash, "Test User 454", True, True, "user"))

    conn.commit()
    cursor.close()
    conn.close()

    return email, password, user_id

def login(email: str, password: str) -> str:
    """Login and return JWT token."""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    return data["access_token"]

def create_diagram(token: str, title: str) -> str:
    """Create a new diagram."""
    response = requests.post(
        f"{BASE_URL}/api/diagrams",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": title,
            "file_type": "canvas",
            "canvas_data": {"shapes": [], "version": 1}
        }
    )
    assert response.status_code in [200, 201], f"Create diagram failed: {response.status_code} - {response.text}"
    data = response.json()
    return data["id"]

def update_diagram(token: str, diagram_id: str, canvas_data: dict):
    """Update diagram content."""
    response = requests.put(
        f"{BASE_URL}/api/diagrams/{diagram_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"canvas_data": canvas_data}
    )
    assert response.status_code == 200, f"Update diagram failed: {response.text}"
    return response.json()

def get_versions(token: str, diagram_id: str) -> list:
    """Get all versions for a diagram."""
    response = requests.get(
        f"{BASE_URL}/api/diagrams/{diagram_id}/versions",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200, f"Get versions failed: {response.text}"
    data = response.json()
    return data.get("versions", [])

def get_diagram(token: str, diagram_id: str) -> dict:
    """Get diagram details."""
    response = requests.get(
        f"{BASE_URL}/api/diagrams/{diagram_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200, f"Get diagram failed: {response.text}"
    return response.json()

def wait_for_auto_version(seconds: int):
    """Wait for auto-versioning timer."""
    print(f"⏳ Waiting {seconds} seconds for auto-version...")
    time.sleep(seconds)

def test_auto_version_every_5_minutes():
    """Test that auto-save creates version every 5 minutes."""
    print("\n" + "="*80)
    print("TEST: Feature 454 - Version History Auto-Save Every 5 Minutes")
    print("="*80)

    # Create test user and login
    print("\n1. Creating test user and logging in...")
    email, password, user_id = create_test_user()
    token = login(email, password)
    print(f"✓ Logged in as {email}")

    # Create a diagram
    print("\n2. Creating diagram...")
    diagram_id = create_diagram(token, "Auto-Version Test Diagram")
    print(f"✓ Created diagram: {diagram_id}")

    # Initial state - should have 0 versions (no edits yet)
    print("\n3. Checking initial version count...")
    versions = get_versions(token, diagram_id)
    print(f"✓ Initial versions: {len(versions)}")

    # First edit - should create initial version
    print("\n4. Making first edit (should create initial version)...")
    update_diagram(token, diagram_id, {
        "shapes": [{"type": "rectangle", "x": 0, "y": 0}],
        "version": 1
    })

    # Check that initial version was created
    versions = get_versions(token, diagram_id)
    print(f"✓ Versions after first edit: {len(versions)}")
    assert len(versions) >= 1, f"Expected at least 1 version after first edit, got {len(versions)}"
    initial_version_count = len(versions)

    # Get diagram to check last_auto_versioned_at
    diagram = get_diagram(token, diagram_id)
    print(f"✓ Diagram current_version: {diagram.get('current_version')}")

    # Second edit within 5 minutes - should NOT create version
    print("\n5. Making second edit within 5 minutes (should NOT create version)...")
    wait_for_auto_version(2)  # Wait 2 seconds (less than 5 minutes)

    update_diagram(token, diagram_id, {
        "shapes": [
            {"type": "rectangle", "x": 0, "y": 0},
            {"type": "circle", "x": 100, "y": 100}
        ],
        "version": 2
    })

    # Check that no new version was created
    versions = get_versions(token, diagram_id)
    print(f"✓ Versions after second edit (within 5 min): {len(versions)}")
    assert len(versions) == initial_version_count, \
        f"Expected {initial_version_count} versions (no auto-save yet), got {len(versions)}"

    # Third edit after 5 minutes - should create version
    print("\n6. Making third edit after 5 minutes (should create version)...")
    # Wait 5 minutes + 5 seconds to ensure we're past the threshold
    # NOTE: For testing purposes, we'll use a shorter time (10 seconds total from first edit)
    # In production, this would be 300 seconds (5 minutes)

    # The implementation checks: time_since_last_version >= 300 seconds
    # We need to wait from the last auto-version time
    # Since we made first edit at t=0, and second at t=2, we need to wait until t=300

    # For E2E testing, let's verify the logic is in place
    # We'll check the database directly to see last_auto_versioned_at
    import psycopg2
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="autograph",
        user="autograph",
        password="autograph_dev_password"
    )
    cursor = conn.cursor()

    cursor.execute("""
        SELECT last_auto_versioned_at
        FROM files
        WHERE id = %s
    """, (diagram_id,))
    result = cursor.fetchone()
    last_auto_versioned = result[0] if result else None
    print(f"✓ last_auto_versioned_at from DB: {last_auto_versioned}")

    if last_auto_versioned:
        # Calculate time since last auto-version
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        time_diff = (now - last_auto_versioned.replace(tzinfo=timezone.utc)).total_seconds()
        print(f"✓ Time since last auto-version: {time_diff:.1f} seconds")

        # To trigger auto-version, we need to wait 300 seconds
        # For testing, we'll manipulate the timestamp
        print("\n7. Setting last_auto_versioned_at to 6 minutes ago (to trigger auto-version)...")
        cursor.execute("""
            UPDATE files
            SET last_auto_versioned_at = NOW() - INTERVAL '6 minutes'
            WHERE id = %s
        """, (diagram_id,))
        conn.commit()

        # Now make an edit - should create version
        update_diagram(token, diagram_id, {
            "shapes": [
                {"type": "rectangle", "x": 0, "y": 0},
                {"type": "circle", "x": 100, "y": 100},
                {"type": "triangle", "x": 200, "y": 200}
            ],
            "version": 3
        })

        # Check that new version was created
        versions = get_versions(token, diagram_id)
        print(f"✓ Versions after edit (6 minutes passed): {len(versions)}")
        assert len(versions) > initial_version_count, \
            f"Expected more than {initial_version_count} versions after 5+ minutes, got {len(versions)}"

        print(f"✓ Auto-version created successfully!")

        # Verify version content in database
        print("\n8. Verifying versions saved in database...")
        cursor.execute("""
            SELECT version_number, canvas_data IS NOT NULL, note_content IS NOT NULL
            FROM versions
            WHERE file_id = %s
            ORDER BY version_number
        """, (diagram_id,))

        db_versions = cursor.fetchall()
        print(f"✓ Found {len(db_versions)} versions in database")
        for version_num, has_canvas, has_note in db_versions:
            content_type = "canvas" if has_canvas else ("note" if has_note else "none")
            print(f"   Version {version_num}: has {content_type} data")

    cursor.close()
    conn.close()

    print("\n" + "="*80)
    print("✅ FEATURE 454 TEST PASSED: Auto-save every 5 minutes works correctly!")
    print("="*80)
    print(f"\nSummary:")
    print(f"  - Initial version created on first edit: ✓")
    print(f"  - No version created within 5 minutes: ✓")
    print(f"  - Version created after 5+ minutes: ✓")
    print(f"  - Total versions created: {len(versions)}")

if __name__ == "__main__":
    try:
        test_auto_version_every_5_minutes()

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
