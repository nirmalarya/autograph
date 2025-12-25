#!/usr/bin/env python3
"""
Feature #150: Diagram sorting by last viewed

Tests:
1. Create diagrams A, B, C
2. View diagram C (read/get it)
3. View diagram A
4. View diagram B
5. Sort by last_viewed desc
6. Verify order: B, A, C (most recent first)
"""

import requests
import json
import sys
import time

API_BASE = "http://localhost:8080"

def test_feature_150():
    """Test diagram sorting by last viewed."""

    print("=" * 70)
    print("FEATURE #150: Diagram Sorting by Last Viewed")
    print("=" * 70)

    # Step 1: Register and login
    print("\n[Step 1] Register and login...")

    email = f"viewtest_{int(time.time())}@example.com"
    password = "SecurePass123!@#"

    register_response = requests.post(
        f"{API_BASE}/api/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "View Test User"
        }
    )

    if register_response.status_code != 201:
        print(f"❌ Registration failed: {register_response.status_code}")
        return False

    # Verify email
    import psycopg2
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="autograph",
        user="autograph",
        password="autograph_dev_password"
    )
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_verified = true WHERE email = %s", (email,))
    conn.commit()
    cursor.close()
    conn.close()

    # Login
    login_response = requests.post(
        f"{API_BASE}/api/auth/login",
        json={"email": email, "password": password}
    )

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ Logged in successfully")

    # Step 2: Create test diagrams A, B, C
    print("\n[Step 2] Creating test diagrams A, B, C...")

    test_diagrams = ["Diagram A", "Diagram B", "Diagram C"]
    created_ids = {}

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
            return False

        diagram_id = create_response.json()["id"]
        created_ids[name] = diagram_id
        print(f"✅ Created diagram '{name}' (ID: {diagram_id})")
        time.sleep(0.3)

    # Step 3: View diagram C (GET request updates last_accessed_at)
    print("\n[Step 3] Viewing diagram C...")
    time.sleep(1)

    view_c_response = requests.get(
        f"{API_BASE}/api/diagrams/{created_ids['Diagram C']}",
        headers=headers
    )

    if view_c_response.status_code != 200:
        print(f"❌ Failed to view diagram C: {view_c_response.status_code}")
        return False

    print(f"✅ Viewed diagram C")
    time.sleep(1)

    # Step 4: View diagram A
    print("\n[Step 4] Viewing diagram A...")

    view_a_response = requests.get(
        f"{API_BASE}/api/diagrams/{created_ids['Diagram A']}",
        headers=headers
    )

    if view_a_response.status_code != 200:
        print(f"❌ Failed to view diagram A: {view_a_response.status_code}")
        return False

    print(f"✅ Viewed diagram A")
    time.sleep(1)

    # Step 5: View diagram B
    print("\n[Step 5] Viewing diagram B...")

    view_b_response = requests.get(
        f"{API_BASE}/api/diagrams/{created_ids['Diagram B']}",
        headers=headers
    )

    if view_b_response.status_code != 200:
        print(f"❌ Failed to view diagram B: {view_b_response.status_code}")
        return False

    print(f"✅ Viewed diagram B")
    time.sleep(0.5)

    # Step 6: List diagrams sorted by last_viewed desc
    print("\n[Step 6] Listing diagrams sorted by last_viewed (recent first)...")

    list_response = requests.get(
        f"{API_BASE}/api/diagrams",
        headers=headers,
        params={
            "sort_by": "last_viewed",
            "sort_order": "desc",
            "page_size": 100
        }
    )

    if list_response.status_code != 200:
        print(f"❌ Failed to list diagrams: {list_response.status_code}")
        print(list_response.text)
        return False

    diagrams = list_response.json()["diagrams"]
    test_diagrams_filtered = [d for d in diagrams if d["title"] in test_diagrams]

    print(f"✅ Retrieved {len(test_diagrams_filtered)} test diagrams")

    # Step 7: Verify order: B, A, C (most recent first)
    print("\n[Step 7] Verifying order: B, A, C (most recent first)...")

    expected_order = ["Diagram B", "Diagram A", "Diagram C"]
    actual_order = [d["title"] for d in test_diagrams_filtered]

    print(f"Expected order: {expected_order}")
    print(f"Actual order:   {actual_order}")

    # Show last_accessed_at for debugging
    print(f"\nLast accessed timestamps:")
    for d in test_diagrams_filtered:
        print(f"  {d['title']}: {d.get('last_accessed_at', 'None')}")

    if actual_order == expected_order:
        print("✅ Last viewed sorting is correct")
    else:
        print(f"❌ Last viewed sorting is incorrect")
        return False

    # Cleanup
    print("\n[Cleanup] Deleting test diagrams...")
    for name, diagram_id in created_ids.items():
        delete_response = requests.delete(
            f"{API_BASE}/api/diagrams/{diagram_id}",
            headers=headers
        )
        if delete_response.status_code == 204:
            print(f"✅ Deleted {name}")

    print("\n" + "=" * 70)
    print("✅ FEATURE #150: ALL TESTS PASSED")
    print("=" * 70)
    return True

if __name__ == "__main__":
    try:
        success = test_feature_150()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
