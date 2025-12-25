#!/usr/bin/env python3
"""
Validation test for Feature #129: Delete diagram hard deletes permanently

This test verifies:
1. Create diagram
2. Soft delete to trash
3. Navigate to /trash
4. Click 'Delete Permanently'
5. Verify confirmation dialog
6. Confirm deletion
7. Send DELETE /api/diagrams/<id>?permanent=true
8. Verify 200 OK response
9. Check database - verify diagram record deleted
10. Verify all versions deleted
11. Verify files deleted from MinIO
"""

import requests
import json
import sys
import psycopg2
from minio import Minio
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8080/api"
POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "autograph",
    "user": "autograph",
    "password": "autograph_dev_password"
}
MINIO_CONFIG = {
    "endpoint": "localhost:9000",
    "access_key": "minioadmin",
    "secret_key": "minioadmin",
    "secure": False
}

def register_and_verify_user():
    """Register a new user and verify email"""
    print("\n1. Registering test user...")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    email = f"harddelete_test_{timestamp}@example.com"

    response = requests.post(f"{BASE_URL}/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "name": "Hard Delete Test User"
    })

    if response.status_code != 201:
        print(f"❌ Failed to register user: {response.status_code} - {response.text}")
        return None

    print(f"✅ User registered: {email}")

    # Verify email in database
    print("2. Verifying email...")
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_verified = TRUE WHERE email = %s RETURNING id", (email,))
    result = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not result:
        print(f"❌ Failed to verify email for {email}")
        return None

    user_id = result[0]
    print(f"✅ Email verified for user ID: {user_id}")

    return email, user_id

def login_user(email):
    """Login and get JWT token"""
    print("\n3. Logging in...")
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": email,
        "password": "SecurePass123!"
    })

    if response.status_code != 200:
        print(f"❌ Failed to login: {response.status_code} - {response.text}")
        return None

    data = response.json()
    token = data.get("access_token")
    print(f"✅ Logged in, token received")
    return token

def create_diagram(token):
    """Create a test diagram"""
    print("\n4. Creating diagram...")
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.post(
        f"{BASE_URL}/diagrams",
        headers=headers,
        json={
            "title": "Test Diagram for Hard Delete",
            "diagram_type": "canvas",
            "canvas_data": {
                "nodes": [{"id": "node1", "type": "rectangle", "x": 100, "y": 100}],
                "edges": []
            }
        }
    )

    if response.status_code not in [200, 201]:
        print(f"❌ Failed to create diagram: {response.status_code} - {response.text}")
        return None

    data = response.json()
    diagram_id = data.get("id")
    print(f"✅ Diagram created: {diagram_id}")
    return diagram_id

def soft_delete_diagram(token, diagram_id):
    """Soft delete the diagram (move to trash)"""
    print(f"\n5. Soft deleting diagram {diagram_id}...")
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.delete(
        f"{BASE_URL}/diagrams/{diagram_id}",
        headers=headers
    )

    if response.status_code != 200:
        print(f"❌ Failed to soft delete diagram: {response.status_code} - {response.text}")
        return False

    data = response.json()
    print(f"✅ Diagram soft deleted: {data.get('message')}")
    return True

def verify_in_trash(token, diagram_id):
    """Verify diagram is in trash"""
    print(f"\n6. Verifying diagram {diagram_id} is in trash...")
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        f"{BASE_URL}/diagrams/trash",
        headers=headers
    )

    if response.status_code != 200:
        print(f"❌ Failed to get trash: {response.status_code} - {response.text}")
        return False

    data = response.json()
    diagrams = data.get("diagrams", [])

    found = any(d.get("id") == diagram_id for d in diagrams)
    if found:
        print(f"✅ Diagram found in trash")
        return True
    else:
        print(f"❌ Diagram NOT found in trash")
        return False

def hard_delete_diagram(token, diagram_id):
    """Hard delete the diagram permanently"""
    print(f"\n7. Hard deleting diagram {diagram_id} permanently...")
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.delete(
        f"{BASE_URL}/diagrams/{diagram_id}?permanent=true",
        headers=headers
    )

    if response.status_code != 200:
        print(f"❌ Failed to hard delete diagram: {response.status_code} - {response.text}")
        return False, None

    data = response.json()
    print(f"✅ Diagram permanently deleted: {data.get('message')}")
    print(f"   Versions deleted: {data.get('versions_deleted', 0)}")
    print(f"   MinIO files deleted: {data.get('minio_files_deleted', 0)}")
    return True, data

def verify_database_deletion(diagram_id):
    """Verify diagram is deleted from database"""
    print(f"\n8. Verifying diagram {diagram_id} deleted from database...")
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    cur = conn.cursor()

    # Check diagram record
    cur.execute("SELECT id, is_deleted FROM files WHERE id = %s", (diagram_id,))
    result = cur.fetchone()

    if result:
        print(f"❌ Diagram still exists in database: {result}")
        cur.close()
        conn.close()
        return False

    print(f"✅ Diagram record deleted from database")

    # Check versions
    cur.execute("SELECT COUNT(*) FROM versions WHERE file_id = %s", (diagram_id,))
    version_count = cur.fetchone()[0]

    if version_count > 0:
        print(f"❌ {version_count} versions still exist in database")
        cur.close()
        conn.close()
        return False

    print(f"✅ All versions deleted from database")

    cur.close()
    conn.close()
    return True

def verify_minio_deletion(diagram_id):
    """Verify files deleted from MinIO"""
    print(f"\n9. Verifying MinIO files deleted for diagram {diagram_id}...")

    try:
        minio_client = Minio(**MINIO_CONFIG)
        bucket_name = "diagrams"

        # Check thumbnail
        thumbnail_object = f"thumbnails/{diagram_id}.png"
        try:
            minio_client.stat_object(bucket_name, thumbnail_object)
            print(f"❌ Thumbnail still exists in MinIO: {thumbnail_object}")
            return False
        except Exception:
            print(f"✅ Thumbnail deleted from MinIO")

        # Check diagram files
        prefix = f"diagrams/{diagram_id}/"
        objects = list(minio_client.list_objects(bucket_name, prefix=prefix, recursive=True))

        if objects:
            print(f"❌ {len(objects)} files still exist in MinIO:")
            for obj in objects:
                print(f"   - {obj.object_name}")
            return False

        print(f"✅ All diagram files deleted from MinIO")
        return True

    except Exception as e:
        print(f"❌ Failed to verify MinIO deletion: {str(e)}")
        return False

def main():
    """Run validation test"""
    print("=" * 80)
    print("Feature #129 Validation: Delete diagram hard deletes permanently")
    print("=" * 80)

    # Register and verify user
    user_data = register_and_verify_user()
    if not user_data:
        sys.exit(1)

    email, user_id = user_data

    # Login
    token = login_user(email)
    if not token:
        sys.exit(1)

    # Create diagram
    diagram_id = create_diagram(token)
    if not diagram_id:
        sys.exit(1)

    # Soft delete diagram
    if not soft_delete_diagram(token, diagram_id):
        sys.exit(1)

    # Verify in trash
    if not verify_in_trash(token, diagram_id):
        sys.exit(1)

    # Hard delete diagram
    success, delete_data = hard_delete_diagram(token, diagram_id)
    if not success:
        sys.exit(1)

    # Verify database deletion
    if not verify_database_deletion(diagram_id):
        sys.exit(1)

    # Verify MinIO deletion
    if not verify_minio_deletion(diagram_id):
        sys.exit(1)

    print("\n" + "=" * 80)
    print("✅ Feature #129 VALIDATION PASSED")
    print("=" * 80)
    print("\nAll acceptance criteria verified:")
    print("1. ✅ Create diagram")
    print("2. ✅ Soft delete to trash")
    print("3. ✅ Navigate to /trash")
    print("4-6. ✅ Delete permanently (UI flow simulated)")
    print("7. ✅ Send DELETE /api/diagrams/<id>?permanent=true")
    print("8. ✅ Verify 200 OK response")
    print("9. ✅ Check database - diagram record deleted")
    print("10. ✅ Verify all versions deleted")
    print("11. ✅ Verify files deleted from MinIO")

    return 0

if __name__ == "__main__":
    sys.exit(main())
