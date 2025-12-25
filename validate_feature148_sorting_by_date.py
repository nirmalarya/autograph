#!/usr/bin/env python3
"""
Feature #148: Diagram sorting by date created (newest/oldest first)

Tests:
1. Create diagram A
2. Wait a moment
3. Create diagram B
4. Wait a moment
5. Create diagram C
6. List diagrams sorted by date created (newest first)
7. Verify order: C, B, A
8. List diagrams sorted by date created (oldest first)
9. Verify order: A, B, C
"""

import requests
import json
import sys
import time

API_BASE = "http://localhost:8080"

def test_feature_148():
    """Test diagram sorting by date created."""

    print("=" * 70)
    print("FEATURE #148: Diagram Sorting by Date Created")
    print("=" * 70)

    # Step 1: Register and login
    print("\n[Step 1] Register and login...")

    email = f"datetest_{int(time.time())}@example.com"
    password = "SecurePass123!@#"

    register_response = requests.post(
        f"{API_BASE}/api/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Date Test User"
        }
    )

    if register_response.status_code != 201:
        print(f"❌ Registration failed: {register_response.status_code}")
        print(register_response.text)
        return False

    print(f"✅ Registered user: {email}")

    # Verify email directly in database (for testing)
    print("✅ Verifying email (test mode)...")
    import psycopg2
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="autograph",
        user="autograph",
        password="autograph_dev_password"
    )
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET is_verified = true WHERE email = %s",
        (email,)
    )
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Email verified")

    # Login
    login_response = requests.post(
        f"{API_BASE}/api/auth/login",
        json={
            "email": email,
            "password": password
        }
    )

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)
        return False

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ Logged in successfully")

    # Step 2-4: Create test diagrams with time delays
    print("\n[Step 2-4] Creating test diagrams A, B, C with time delays...")

    test_diagrams = ["Diagram A", "Diagram B", "Diagram C"]
    created_ids = []
    created_times = []

    for name in test_diagrams:
        create_response = requests.post(
            f"{API_BASE}/api/diagrams",
            headers=headers,
            json={
                "title": name,
                "file_type": "canvas",
                "canvas_data": {"nodes": [], "edges": []}
            }
        )

        if create_response.status_code not in [200, 201]:
            print(f"❌ Failed to create diagram '{name}': {create_response.status_code}")
            print(create_response.text)
            return False

        diagram_data = create_response.json()
        diagram_id = diagram_data["id"]
        created_time = diagram_data["created_at"]

        created_ids.append(diagram_id)
        created_times.append(created_time)
        print(f"✅ Created diagram '{name}' (ID: {diagram_id}, Created: {created_time})")

        # Wait 1 second between creations to ensure different timestamps
        if name != "Diagram C":  # Don't wait after last one
            time.sleep(1.5)

    # Verify we have different timestamps
    print(f"\nTimestamps:")
    for i, (name, timestamp) in enumerate(zip(test_diagrams, created_times)):
        print(f"  {name}: {timestamp}")

    # Give database a moment to settle
    time.sleep(0.5)

    # Step 5: List diagrams sorted by date created (newest first)
    print("\n[Step 5] Listing diagrams sorted by date created (newest first)...")

    list_newest_response = requests.get(
        f"{API_BASE}/api/diagrams",
        headers=headers,
        params={
            "sort_by": "created_at",
            "sort_order": "desc",
            "page_size": 100
        }
    )

    if list_newest_response.status_code != 200:
        print(f"❌ Failed to list diagrams (newest first): {list_newest_response.status_code}")
        print(list_newest_response.text)
        return False

    diagrams_newest = list_newest_response.json()["diagrams"]

    # Filter to our test diagrams
    test_diagrams_newest = [d for d in diagrams_newest if d["title"] in test_diagrams]

    print(f"✅ Retrieved {len(test_diagrams_newest)} test diagrams")

    # Step 6: Verify newest first order (C, B, A)
    print("\n[Step 6] Verifying newest first order (C, B, A)...")

    expected_order_newest = ["Diagram C", "Diagram B", "Diagram A"]
    actual_order_newest = [d["title"] for d in test_diagrams_newest]

    print(f"Expected order: {expected_order_newest}")
    print(f"Actual order:   {actual_order_newest}")

    if actual_order_newest == expected_order_newest:
        print("✅ Newest first sorting is correct")
    else:
        print("❌ Newest first sorting is incorrect")
        # Show timestamps for debugging
        for d in test_diagrams_newest:
            print(f"  {d['title']}: {d['created_at']}")
        return False

    # Step 7: List diagrams sorted by date created (oldest first)
    print("\n[Step 7] Listing diagrams sorted by date created (oldest first)...")

    list_oldest_response = requests.get(
        f"{API_BASE}/api/diagrams",
        headers=headers,
        params={
            "sort_by": "created_at",
            "sort_order": "asc",
            "page_size": 100
        }
    )

    if list_oldest_response.status_code != 200:
        print(f"❌ Failed to list diagrams (oldest first): {list_oldest_response.status_code}")
        print(list_oldest_response.text)
        return False

    diagrams_oldest = list_oldest_response.json()["diagrams"]

    # Filter to our test diagrams
    test_diagrams_oldest = [d for d in diagrams_oldest if d["title"] in test_diagrams]

    print(f"✅ Retrieved {len(test_diagrams_oldest)} test diagrams")

    # Step 8: Verify oldest first order (A, B, C)
    print("\n[Step 8] Verifying oldest first order (A, B, C)...")

    expected_order_oldest = ["Diagram A", "Diagram B", "Diagram C"]
    actual_order_oldest = [d["title"] for d in test_diagrams_oldest]

    print(f"Expected order: {expected_order_oldest}")
    print(f"Actual order:   {actual_order_oldest}")

    if actual_order_oldest == expected_order_oldest:
        print("✅ Oldest first sorting is correct")
    else:
        print("❌ Oldest first sorting is incorrect")
        # Show timestamps for debugging
        for d in test_diagrams_oldest:
            print(f"  {d['title']}: {d['created_at']}")
        return False

    # Cleanup: Delete test diagrams
    print("\n[Cleanup] Deleting test diagrams...")
    for diagram_id in created_ids:
        delete_response = requests.delete(
            f"{API_BASE}/api/diagrams/{diagram_id}",
            headers=headers
        )
        if delete_response.status_code == 204:
            print(f"✅ Deleted diagram {diagram_id}")

    print("\n" + "=" * 70)
    print("✅ FEATURE #148: ALL TESTS PASSED")
    print("=" * 70)
    return True

if __name__ == "__main__":
    try:
        success = test_feature_148()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
