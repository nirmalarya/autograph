#!/usr/bin/env python3
"""
Feature #157: Diagram export count tracking

Tests:
1. Create a diagram
2. Export as PNG
3. Verify export_count=1
4. Export as SVG
5. Verify export_count=2
6. Export as PDF
7. Verify export_count=3
8. Get diagram metadata and verify export count
"""

import requests
import json
import sys
import time

API_BASE = "http://localhost:8080"

def test_feature_157():
    """Test diagram export count tracking."""

    print("=" * 70)
    print("FEATURE #157: Diagram Export Count Tracking")
    print("=" * 70)

    # Step 1: Register and login
    print("\n[Step 1] Register and login...")

    email = f"exporttest_{int(time.time())}@example.com"
    password = "SecurePass123!@#"

    register_response = requests.post(
        f"{API_BASE}/api/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Export Test User"
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

    # Step 2: Create a test diagram
    print("\n[Step 2] Creating test diagram...")

    create_response = requests.post(
        f"{API_BASE}/api/diagrams",
        headers=headers,
        json={
            "title": "Export Count Test Diagram",
            "file_type": "canvas",
            "canvas_data": {
                "nodes": [
                    {"id": "1", "type": "rect", "x": 100, "y": 100}
                ],
                "edges": []
            }
        }
    )

    if create_response.status_code not in [200, 201]:
        print(f"❌ Failed to create diagram: {create_response.status_code}")
        return False

    diagram_id = create_response.json()["id"]
    print(f"✅ Created diagram (ID: {diagram_id})")

    # Helper function to check export count in database
    def get_export_count_from_db():
        cursor.execute(
            "SELECT export_count FROM files WHERE id = %s",
            (diagram_id,)
        )
        result = cursor.fetchone()
        return result[0] if result else None

    # Step 3: Export as PNG
    print("\n[Step 3] Exporting diagram as PNG...")

    export_png_response = requests.post(
        f"{API_BASE}/api/diagrams/{diagram_id}/export/png",
        headers=headers
    )

    if export_png_response.status_code not in [200, 201]:
        print(f"❌ Failed to export as PNG: {export_png_response.status_code}")
        print(export_png_response.text)
        return False

    print(f"✅ Exported as PNG")

    # Step 4: Verify export_count=1 in database
    print("\n[Step 4] Verifying export_count=1 in database...")
    time.sleep(0.5)  # Give DB time to update

    export_count_1 = get_export_count_from_db()
    print(f"Export count in DB: {export_count_1}")

    if export_count_1 == 1:
        print("✅ Export count is 1 (correct)")
    else:
        print(f"❌ Expected export_count=1, got {export_count_1}")
        # Don't fail yet, continue to check if it's being tracked

    # Step 5: Export as SVG
    print("\n[Step 5] Exporting diagram as SVG...")

    export_svg_response = requests.post(
        f"{API_BASE}/api/diagrams/{diagram_id}/export/svg",
        headers=headers
    )

    if export_svg_response.status_code not in [200, 201]:
        print(f"❌ Failed to export as SVG: {export_svg_response.status_code}")
        print(export_svg_response.text)
        return False

    print(f"✅ Exported as SVG")

    # Step 6: Verify export_count=2
    print("\n[Step 6] Verifying export_count=2 in database...")
    time.sleep(0.5)

    export_count_2 = get_export_count_from_db()
    print(f"Export count in DB: {export_count_2}")

    if export_count_2 == 2:
        print("✅ Export count is 2 (correct)")
    else:
        print(f"❌ Expected export_count=2, got {export_count_2}")

    # Step 7: Export as PDF
    print("\n[Step 7] Exporting diagram as PDF...")

    export_pdf_response = requests.post(
        f"{API_BASE}/api/diagrams/{diagram_id}/export/pdf",
        headers=headers
    )

    if export_pdf_response.status_code not in [200, 201]:
        print(f"❌ Failed to export as PDF: {export_pdf_response.status_code}")
        print(export_pdf_response.text)
        return False

    print(f"✅ Exported as PDF")

    # Step 8: Verify export_count=3
    print("\n[Step 8] Verifying export_count=3 in database...")
    time.sleep(0.5)

    export_count_3 = get_export_count_from_db()
    print(f"Export count in DB: {export_count_3}")

    if export_count_3 == 3:
        print("✅ Export count is 3 (correct)")
    else:
        print(f"❌ Expected export_count=3, got {export_count_3}")
        cursor.close()
        conn.close()
        return False

    # Step 9: Get diagram metadata and verify export count
    print("\n[Step 9] Getting diagram metadata...")

    get_response = requests.get(
        f"{API_BASE}/api/diagrams/{diagram_id}",
        headers=headers
    )

    if get_response.status_code != 200:
        print(f"❌ Failed to get diagram: {get_response.status_code}")
        cursor.close()
        conn.close()
        return False

    diagram_data = get_response.json()
    export_count_api = diagram_data.get("export_count")

    print(f"Export count from API: {export_count_api}")

    if export_count_api == 3:
        print("✅ Export count in API response is 3 (correct)")
    else:
        print(f"❌ Expected export_count=3 in API, got {export_count_api}")
        cursor.close()
        conn.close()
        return False

    # Cleanup
    cursor.close()
    conn.close()

    print("\n[Cleanup] Deleting test diagram...")
    delete_response = requests.delete(
        f"{API_BASE}/api/diagrams/{diagram_id}",
        headers=headers
    )
    if delete_response.status_code == 204:
        print(f"✅ Deleted diagram")

    print("\n" + "=" * 70)
    print("✅ FEATURE #157: ALL TESTS PASSED")
    print("=" * 70)
    return True

if __name__ == "__main__":
    try:
        success = test_feature_157()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
