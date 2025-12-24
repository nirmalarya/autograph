#!/usr/bin/env python3
"""Test Feature #131: Trash auto-deletes diagrams after 30 days."""

import requests
import json
import time
import jwt
import os
import subprocess
from datetime import datetime, timedelta, timezone

BASE_URL = "http://localhost:8082"
AUTH_URL = "http://localhost:8085"

def run_sql(sql):
    """Run SQL command in PostgreSQL container."""
    result = subprocess.run(
        ["docker", "exec", "autograph-postgres", "psql", "-U", "autograph", "-d", "autograph", "-c", sql],
        capture_output=True,
        text=True
    )
    return result.stdout, result.returncode

def test_trash_auto_delete():
    """Test that diagrams in trash are automatically deleted after 30 days."""
    
    print("=" * 80)
    print("FEATURE #131: TRASH AUTO-DELETES DIAGRAMS AFTER 30 DAYS")
    print("=" * 80)
    
    # Step 1: Register and login
    print("\n1. Register and login user...")
    user_email = f"trash_test_{int(time.time())}@example.com"
    register_data = {
        "email": user_email,
        "password": "SecurePass123!",
        "full_name": "Trash Test User"
    }
    
    response = requests.post(f"{AUTH_URL}/register", json=register_data)
    if response.status_code not in [200, 201]:
        print(f"❌ Registration failed: {response.status_code}")
        print(response.text)
        return False
    
    print("✅ User registered")
    
    # Login
    login_data = {
        "email": user_email,
        "password": "SecurePass123!"
    }
    
    response = requests.post(f"{AUTH_URL}/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        return False
    
    tokens = response.json()
    access_token = tokens["access_token"]
    
    # Decode JWT to get user_id
    decoded = jwt.decode(access_token, options={"verify_signature": False})
    user_id = decoded["sub"]
    print(f"✅ User logged in (user_id: {user_id})")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-User-ID": user_id
    }
    
    # Step 2: Create two diagrams
    print("\n2. Create two diagrams...")
    
    # Diagram 1 (will be 31 days old)
    diagram_data_1 = {
        "title": "Old Diagram (31 days)",
        "type": "canvas",
        "canvas_data": {"shapes": [], "version": 1},
        "note_content": "This diagram should be deleted"
    }
    
    response = requests.post(f"{BASE_URL}/", json=diagram_data_1, headers=headers)
    if response.status_code not in [200, 201]:
        print(f"❌ Diagram 1 creation failed: {response.status_code}")
        print(response.text)
        return False
    
    diagram_1 = response.json()
    diagram_id_1 = diagram_1["id"]
    print(f"✅ Diagram 1 created (id: {diagram_id_1})")
    
    # Diagram 2 (will be 29 days old)
    diagram_data_2 = {
        "title": "Recent Diagram (29 days)",
        "type": "canvas",
        "canvas_data": {"shapes": [], "version": 1},
        "note_content": "This diagram should NOT be deleted"
    }
    
    response = requests.post(f"{BASE_URL}/", json=diagram_data_2, headers=headers)
    if response.status_code not in [200, 201]:
        print(f"❌ Diagram 2 creation failed: {response.status_code}")
        print(response.text)
        return False
    
    diagram_2 = response.json()
    diagram_id_2 = diagram_2["id"]
    print(f"✅ Diagram 2 created (id: {diagram_id_2})")
    
    # Step 3: Soft delete both diagrams
    print("\n3. Soft delete both diagrams...")
    
    response = requests.delete(f"{BASE_URL}/{diagram_id_1}", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to delete diagram 1: {response.status_code}")
        print(response.text)
        return False
    
    print(f"✅ Diagram 1 moved to trash")
    
    response = requests.delete(f"{BASE_URL}/{diagram_id_2}", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to delete diagram 2: {response.status_code}")
        print(response.text)
        return False
    
    print(f"✅ Diagram 2 moved to trash")
    
    # Step 4: Mock time by updating deleted_at in database
    print("\n4. Mock time by updating deleted_at timestamps...")
    
    # Update diagram 1 to be 31 days old
    old_deleted_at_1 = datetime.now(timezone.utc) - timedelta(days=31)
    sql_1 = f"UPDATE files SET deleted_at = '{old_deleted_at_1.isoformat()}' WHERE id = '{diagram_id_1}';"
    output, code = run_sql(sql_1)
    
    if code != 0:
        print(f"❌ Failed to update diagram 1 timestamp")
        print(output)
        return False
    
    print(f"✅ Diagram 1 deleted_at set to: {old_deleted_at_1.isoformat()}")
    
    # Update diagram 2 to be 29 days old
    old_deleted_at_2 = datetime.now(timezone.utc) - timedelta(days=29)
    sql_2 = f"UPDATE files SET deleted_at = '{old_deleted_at_2.isoformat()}' WHERE id = '{diagram_id_2}';"
    output, code = run_sql(sql_2)
    
    if code != 0:
        print(f"❌ Failed to update diagram 2 timestamp")
        print(output)
        return False
    
    print(f"✅ Diagram 2 deleted_at set to: {old_deleted_at_2.isoformat()}")
    
    # Step 5: Run cleanup job
    print("\n5. Run cleanup job...")
    
    import subprocess
    result = subprocess.run(
        ["python3", "cleanup_trash.py"],
        capture_output=True,
        text=True
    )
    
    print("Cleanup job output:")
    print(result.stdout)
    
    if result.returncode != 0:
        print(f"❌ Cleanup job failed with exit code {result.returncode}")
        print(result.stderr)
        return False
    
    print("✅ Cleanup job completed successfully")
    
    # Step 6: Verify diagram 1 (31 days old) is permanently deleted
    print("\n6. Verify diagram 1 (31 days old) is permanently deleted...")
    
    # Check if diagram 1 exists
    sql = f"SELECT COUNT(*) FROM files WHERE id = '{diagram_id_1}';"
    output, code = run_sql(sql)
    
    if "0" not in output:
        print(f"❌ Diagram 1 still exists in database")
        print(output)
        return False
    
    print("✅ Diagram 1 permanently deleted from database")
    
    # Check versions also deleted
    sql = f"SELECT COUNT(*) FROM versions WHERE file_id = '{diagram_id_1}';"
    output, code = run_sql(sql)
    
    if "0" not in output:
        print(f"❌ Diagram 1 versions still exist")
        print(output)
        return False
    
    print("✅ Diagram 1 versions also deleted")
    
    # Step 7: Verify diagram 2 (29 days old) still in trash
    print("\n7. Verify diagram 2 (29 days old) still in trash...")
    
    # Check if diagram 2 exists
    sql = f"SELECT COUNT(*) FROM files WHERE id = '{diagram_id_2}';"
    output, code = run_sql(sql)
    
    if "1" not in output:
        print(f"❌ Diagram 2 not found in database (should still exist)")
        print(output)
        return False
    
    # Check if diagram 2 is marked as deleted
    sql = f"SELECT is_deleted FROM files WHERE id = '{diagram_id_2}';"
    output, code = run_sql(sql)
    
    if "t" not in output:  # PostgreSQL boolean true is 't'
        print(f"❌ Diagram 2 not marked as deleted")
        print(output)
        return False
    
    print("✅ Diagram 2 still in trash (not deleted)")
    print(f"   Deleted at: {old_deleted_at_2.isoformat()}")
    
    # Calculate days in trash
    days_in_trash = 29  # We set it to 29 days
    print(f"   Days in trash: {days_in_trash}")
    
    # Step 8: Test API access to verify deletion
    print("\n8. Test API access to verify deletion...")
    
    # Diagram 1 should return 404
    response = requests.get(f"{BASE_URL}/{diagram_id_1}", headers=headers)
    if response.status_code != 404:
        print(f"❌ Diagram 1 should return 404, got {response.status_code}")
        return False
    
    print("✅ Diagram 1 returns 404 (not found)")
    
    # Diagram 2 should return 404 (because it's deleted, not because it doesn't exist)
    response = requests.get(f"{BASE_URL}/{diagram_id_2}", headers=headers)
    if response.status_code != 404:
        print(f"❌ Diagram 2 should return 404 (deleted), got {response.status_code}")
        return False
    
    print("✅ Diagram 2 returns 404 (in trash)")
    
    # Clean up diagram 2
    print("\n9. Clean up diagram 2...")
    response = requests.delete(f"{BASE_URL}/{diagram_id_2}?permanent=true", headers=headers)
    if response.status_code != 200:
        print(f"⚠️  Failed to clean up diagram 2: {response.status_code}")
    else:
        print("✅ Diagram 2 cleaned up")
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED - Feature #131 Complete!")
    print("=" * 80)
    print("\nSummary:")
    print("  • Diagram deleted 31 days ago: permanently deleted ✓")
    print("  • Diagram deleted 29 days ago: still in trash ✓")
    print("  • Cleanup job runs successfully ✓")
    print("  • Versions also deleted ✓")
    
    return True


if __name__ == "__main__":
    try:
        success = test_trash_auto_delete()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
