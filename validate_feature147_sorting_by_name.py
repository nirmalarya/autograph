#!/usr/bin/env python3
"""
Feature #147: Diagram sorting by name (A-Z, Z-A)

Tests:
1. Create test diagrams with specific names
2. List diagrams sorted by name A-Z
3. Verify correct ascending order
4. List diagrams sorted by name Z-A
5. Verify correct descending order
"""

import requests
import json
import sys
import time

API_BASE = "http://localhost:8080"

def test_feature_147():
    """Test diagram sorting by name."""

    print("=" * 70)
    print("FEATURE #147: Diagram Sorting by Name (A-Z, Z-A)")
    print("=" * 70)

    # Step 1: Register and login
    print("\n[Step 1] Register and login...")

    email = f"sorttest_{int(time.time())}@example.com"
    password = "SecurePass123!@#"

    register_response = requests.post(
        f"{API_BASE}/api/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Sort Test User"
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

    # Step 2: Create test diagrams with specific names
    print("\n[Step 2] Creating test diagrams: 'Zebra', 'Apple', 'Mango'...")

    test_diagrams = ["Zebra", "Apple", "Mango"]
    created_ids = []

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

        diagram_id = create_response.json()["id"]
        created_ids.append(diagram_id)
        print(f"✅ Created diagram '{name}' (ID: {diagram_id})")

    # Give database a moment to settle
    time.sleep(0.5)

    # Step 3: List diagrams sorted by name A-Z
    print("\n[Step 3] Listing diagrams sorted by name (A-Z)...")

    list_asc_response = requests.get(
        f"{API_BASE}/api/diagrams",
        headers=headers,
        params={
            "sort_by": "name",
            "sort_order": "asc",
            "page_size": 100
        }
    )

    if list_asc_response.status_code != 200:
        print(f"❌ Failed to list diagrams (A-Z): {list_asc_response.status_code}")
        print(list_asc_response.text)
        return False

    diagrams_asc = list_asc_response.json()["diagrams"]

    # Filter to our test diagrams
    test_diagrams_asc = [d for d in diagrams_asc if d["title"] in test_diagrams]

    print(f"✅ Retrieved {len(test_diagrams_asc)} test diagrams")

    # Step 4: Verify A-Z order
    print("\n[Step 4] Verifying A-Z order (Apple, Mango, Zebra)...")

    expected_order_asc = ["Apple", "Mango", "Zebra"]
    actual_order_asc = [d["title"] for d in test_diagrams_asc]

    print(f"Expected order: {expected_order_asc}")
    print(f"Actual order:   {actual_order_asc}")

    if actual_order_asc == expected_order_asc:
        print("✅ A-Z sorting is correct")
    else:
        print("❌ A-Z sorting is incorrect")
        return False

    # Step 5: List diagrams sorted by name Z-A
    print("\n[Step 5] Listing diagrams sorted by name (Z-A)...")

    list_desc_response = requests.get(
        f"{API_BASE}/api/diagrams",
        headers=headers,
        params={
            "sort_by": "name",
            "sort_order": "desc",
            "page_size": 100
        }
    )

    if list_desc_response.status_code != 200:
        print(f"❌ Failed to list diagrams (Z-A): {list_desc_response.status_code}")
        print(list_desc_response.text)
        return False

    diagrams_desc = list_desc_response.json()["diagrams"]

    # Filter to our test diagrams
    test_diagrams_desc = [d for d in diagrams_desc if d["title"] in test_diagrams]

    print(f"✅ Retrieved {len(test_diagrams_desc)} test diagrams")

    # Step 6: Verify Z-A order
    print("\n[Step 6] Verifying Z-A order (Zebra, Mango, Apple)...")

    expected_order_desc = ["Zebra", "Mango", "Apple"]
    actual_order_desc = [d["title"] for d in test_diagrams_desc]

    print(f"Expected order: {expected_order_desc}")
    print(f"Actual order:   {actual_order_desc}")

    if actual_order_desc == expected_order_desc:
        print("✅ Z-A sorting is correct")
    else:
        print("❌ Z-A sorting is incorrect")
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
    print("✅ FEATURE #147: ALL TESTS PASSED")
    print("=" * 70)
    return True

if __name__ == "__main__":
    try:
        success = test_feature_147()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
