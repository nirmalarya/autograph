#!/usr/bin/env python3
"""
Feature #130 Validation: Restore diagram from trash

This test validates:
1. Create diagram
2. Delete diagram (soft delete)
3. Verify diagram in trash (is_deleted=true, deleted_at set)
4. Restore diagram
5. Verify diagram restored to main list
6. Check database: deleted_at=null, is_deleted=false
7. Verify diagram accessible again
"""

import requests
import psycopg2
import sys
import time
from datetime import datetime

# Configuration
API_BASE = "http://localhost:8080"
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "autograph",
    "user": "autograph",
    "password": "autograph_dev_password"
}

def log(message, level="INFO"):
    """Log with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def register_user(email, password):
    """Register a test user."""
    response = requests.post(
        f"{API_BASE}/api/auth/register",
        json={"email": email, "password": password}
    )
    return response

def verify_email(user_id):
    """Verify user email (bypass for testing)."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET is_verified = true WHERE id = %s",
            (user_id,)
        )
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        log(f"Email verification error: {e}", "ERROR")
        return False

def login_user(email, password):
    """Login and get JWT token."""
    response = requests.post(
        f"{API_BASE}/api/auth/login",
        json={"email": email, "password": password}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def create_diagram(token, title, content):
    """Create a diagram."""
    response = requests.post(
        f"{API_BASE}/api/diagrams/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": title,
            "diagram_type": "canvas",
            "content": content
        }
    )
    return response

def delete_diagram(token, diagram_id, permanent=False):
    """Delete a diagram (soft or hard)."""
    params = {"permanent": "true" if permanent else "false"}
    response = requests.delete(
        f"{API_BASE}/api/diagrams/{diagram_id}",
        headers={"Authorization": f"Bearer {token}"},
        params=params
    )
    return response

def restore_diagram(token, diagram_id):
    """Restore a diagram from trash."""
    response = requests.post(
        f"{API_BASE}/api/diagrams/{diagram_id}/restore",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response

def get_diagram(token, diagram_id):
    """Get a diagram by ID."""
    response = requests.get(
        f"{API_BASE}/api/diagrams/{diagram_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response

def list_diagrams(token, include_deleted=False):
    """List diagrams."""
    params = {"include_deleted": "true" if include_deleted else "false"}
    response = requests.get(
        f"{API_BASE}/api/diagrams/",
        headers={"Authorization": f"Bearer {token}"},
        params=params
    )
    return response

def get_diagram_from_db(diagram_id):
    """Get diagram from database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(
            "SELECT id, title, is_deleted, deleted_at FROM files WHERE id = %s",
            (diagram_id,)
        )
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result
    except Exception as e:
        log(f"Database error: {e}", "ERROR")
        return None

def main():
    """Run feature #130 validation."""
    log("=" * 70)
    log("Feature #130: Restore diagram from trash")
    log("=" * 70)

    # Generate unique test email
    test_email = f"restore_test_{int(time.time())}@example.com"
    test_password = "SecurePass123!@#"

    try:
        # Step 1: Register test user
        log("Step 1: Registering test user...")
        response = register_user(test_email, test_password)
        if response.status_code != 201:
            log(f"Registration failed: {response.status_code} - {response.text}", "ERROR")
            return False
        user_id = response.json().get("id")
        log(f"✅ User registered successfully: {user_id}")

        # Step 2: Verify email
        log("Step 2: Verifying email...")
        if not verify_email(user_id):
            log("Email verification failed", "ERROR")
            return False
        log("✅ Email verified")

        # Step 3: Login
        log("Step 3: Logging in...")
        token = login_user(test_email, test_password)
        if not token:
            log("Login failed", "ERROR")
            return False
        log("✅ Login successful")

        # Step 4: Create diagram
        log("Step 4: Creating diagram...")
        diagram_content = {"nodes": [{"id": "1", "label": "Test"}], "edges": []}
        response = create_diagram(token, "Test Diagram for Restore", diagram_content)
        if response.status_code not in [200, 201]:
            log(f"Diagram creation failed: {response.status_code} - {response.text}", "ERROR")
            return False
        diagram_id = response.json().get("id")
        log(f"✅ Diagram created: {diagram_id}")

        # Step 5: Verify diagram in active list
        log("Step 5: Verifying diagram in active list...")
        response = list_diagrams(token, include_deleted=False)
        if response.status_code != 200:
            log(f"List diagrams failed: {response.status_code}", "ERROR")
            return False
        diagrams = response.json().get("diagrams", [])
        if not any(d["id"] == diagram_id for d in diagrams):
            log("Diagram not found in active list", "ERROR")
            return False
        log("✅ Diagram found in active list")

        # Step 6: Soft delete diagram
        log("Step 6: Soft deleting diagram (move to trash)...")
        response = delete_diagram(token, diagram_id, permanent=False)
        if response.status_code != 200:
            log(f"Soft delete failed: {response.status_code} - {response.text}", "ERROR")
            return False
        log("✅ Diagram moved to trash")

        # Step 7: Verify diagram NOT in active list
        log("Step 7: Verifying diagram NOT in active list...")
        response = list_diagrams(token, include_deleted=False)
        if response.status_code != 200:
            log(f"List diagrams failed: {response.status_code}", "ERROR")
            return False
        diagrams = response.json().get("diagrams", [])
        if any(d["id"] == diagram_id for d in diagrams):
            log("Diagram still in active list (should be in trash)", "ERROR")
            return False
        log("✅ Diagram not in active list")

        # Step 8: Check database - is_deleted=true, deleted_at set
        log("Step 8: Checking database (should be deleted)...")
        db_result = get_diagram_from_db(diagram_id)
        if not db_result:
            log("Diagram not found in database", "ERROR")
            return False
        _, title, is_deleted, deleted_at = db_result
        if not is_deleted:
            log("Database shows is_deleted=false (should be true)", "ERROR")
            return False
        if not deleted_at:
            log("Database shows deleted_at=null (should be set)", "ERROR")
            return False
        log(f"✅ Database confirms deleted: is_deleted={is_deleted}, deleted_at={deleted_at}")

        # Step 9: Restore diagram from trash
        log("Step 9: Restoring diagram from trash...")
        response = restore_diagram(token, diagram_id)
        if response.status_code != 200:
            log(f"Restore failed: {response.status_code} - {response.text}", "ERROR")
            return False
        log("✅ Diagram restore API call successful")

        # Step 10: Verify diagram back in active list
        log("Step 10: Verifying diagram restored to active list...")
        response = list_diagrams(token, include_deleted=False)
        if response.status_code != 200:
            log(f"List diagrams failed: {response.status_code}", "ERROR")
            return False
        diagrams = response.json().get("diagrams", [])
        restored_diagram = next((d for d in diagrams if d["id"] == diagram_id), None)
        if not restored_diagram:
            log("Diagram not found in active list after restore", "ERROR")
            return False
        if restored_diagram.get("is_deleted"):
            log("Diagram still marked as deleted after restore", "ERROR")
            return False
        log("✅ Diagram restored to active list")

        # Step 11: Check database - is_deleted=false, deleted_at=null
        log("Step 11: Checking database (should be restored)...")
        db_result = get_diagram_from_db(diagram_id)
        if not db_result:
            log("Diagram not found in database", "ERROR")
            return False
        _, title, is_deleted, deleted_at = db_result
        if is_deleted:
            log("Database shows is_deleted=true (should be false)", "ERROR")
            return False
        if deleted_at:
            log("Database shows deleted_at set (should be null)", "ERROR")
            return False
        log(f"✅ Database confirms restored: is_deleted={is_deleted}, deleted_at={deleted_at}")

        # Step 12: Verify diagram accessible via GET
        log("Step 12: Verifying diagram accessible via GET...")
        response = get_diagram(token, diagram_id)
        if response.status_code != 200:
            log(f"Get diagram failed: {response.status_code}", "ERROR")
            return False
        diagram_data = response.json()
        if diagram_data.get("id") != diagram_id:
            log("Diagram ID mismatch", "ERROR")
            return False
        if diagram_data.get("is_deleted"):
            log("Diagram still marked as deleted", "ERROR")
            return False
        log("✅ Diagram accessible and not deleted")

        log("=" * 70)
        log("✅ ALL TESTS PASSED - Feature #130 validated successfully!", "SUCCESS")
        log("=" * 70)
        return True

    except Exception as e:
        log(f"Unexpected error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
