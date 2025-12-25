#!/usr/bin/env python3
"""
Feature #149: Diagram sorting by date updated (recently modified first)

Tests:
1. Create diagrams A, B, C
2. Update diagram B
3. Sort by updated_at desc (recent first)
4. Verify B appears first
5. Update diagram A
6. Verify A now appears first
"""

import requests
import json
import sys
import time

API_BASE = "http://localhost:8080"

def test_feature_149():
    """Test diagram sorting by date updated."""

    print("=" * 70)
    print("FEATURE #149: Diagram Sorting by Date Updated")
    print("=" * 70)

    # Step 1: Register and login
    print("\n[Step 1] Register and login...")

    email = f"updatetest_{int(time.time())}@example.com"
    password = "SecurePass123!@#"

    register_response = requests.post(
        f"{API_BASE}/api/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Update Test User"
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
        time.sleep(0.5)  # Small delay between creations

    # Step 3: Update diagram B
    print("\n[Step 3] Updating diagram B...")
    time.sleep(1)  # Wait to ensure different timestamp

    update_b_response = requests.put(
        f"{API_BASE}/api/diagrams/{created_ids['Diagram B']}",
        headers=headers,
        json={
            "title": "Diagram B",
            "canvas_data": {"nodes": [{"id": "1", "type": "rect"}], "edges": []}
        }
    )

    if update_b_response.status_code not in [200, 204]:
        print(f"❌ Failed to update diagram B: {update_b_response.status_code}")
        print(update_b_response.text)
        return False

    print(f"✅ Updated diagram B")

    # Step 4: List diagrams sorted by updated_at desc
    print("\n[Step 4] Listing diagrams sorted by updated_at (recent first)...")
    time.sleep(0.5)

    list_response = requests.get(
        f"{API_BASE}/api/diagrams",
        headers=headers,
        params={
            "sort_by": "updated_at",
            "sort_order": "desc",
            "page_size": 100
        }
    )

    if list_response.status_code != 200:
        print(f"❌ Failed to list diagrams: {list_response.status_code}")
        return False

    diagrams = list_response.json()["diagrams"]
    test_diagrams_filtered = [d for d in diagrams if d["title"] in test_diagrams]

    print(f"✅ Retrieved {len(test_diagrams_filtered)} test diagrams")

    # Step 5: Verify B appears first
    print("\n[Step 5] Verifying B appears first...")

    first_diagram = test_diagrams_filtered[0]["title"]
    print(f"First diagram: {first_diagram}")

    if first_diagram == "Diagram B":
        print("✅ Diagram B appears first (correct)")
    else:
        print(f"❌ Expected 'Diagram B' first, got '{first_diagram}'")
        return False

    # Step 6: Update diagram A
    print("\n[Step 6] Updating diagram A...")
    time.sleep(1)  # Wait to ensure different timestamp

    update_a_response = requests.put(
        f"{API_BASE}/api/diagrams/{created_ids['Diagram A']}",
        headers=headers,
        json={
            "title": "Diagram A",
            "canvas_data": {"nodes": [{"id": "2", "type": "circle"}], "edges": []}
        }
    )

    if update_a_response.status_code not in [200, 204]:
        print(f"❌ Failed to update diagram A: {update_a_response.status_code}")
        return False

    print(f"✅ Updated diagram A")

    # Step 7: List diagrams again and verify A appears first
    print("\n[Step 7] Listing diagrams again (A should be first now)...")
    time.sleep(0.5)

    list_response2 = requests.get(
        f"{API_BASE}/api/diagrams",
        headers=headers,
        params={
            "sort_by": "updated_at",
            "sort_order": "desc",
            "page_size": 100
        }
    )

    if list_response2.status_code != 200:
        print(f"❌ Failed to list diagrams: {list_response2.status_code}")
        return False

    diagrams2 = list_response2.json()["diagrams"]
    test_diagrams_filtered2 = [d for d in diagrams2 if d["title"] in test_diagrams]

    first_diagram2 = test_diagrams_filtered2[0]["title"]
    print(f"First diagram: {first_diagram2}")

    if first_diagram2 == "Diagram A":
        print("✅ Diagram A now appears first (correct)")
    else:
        print(f"❌ Expected 'Diagram A' first, got '{first_diagram2}'")
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
    print("✅ FEATURE #149: ALL TESTS PASSED")
    print("=" * 70)
    return True

if __name__ == "__main__":
    try:
        success = test_feature_149()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
