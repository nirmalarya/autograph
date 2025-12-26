#!/usr/bin/env python3
"""Test comprehensive audit logging for login, diagram creation, and diagram deletion."""

import requests
import json
import time

API_GATEWAY = "http://localhost:8080"

def test_audit_logging():
    """Test audit logging for all user actions."""

    print("=" * 80)
    print("TESTING COMPREHENSIVE AUDIT LOGGING")
    print("=" * 80)

    # Step 1: Login (creates audit log via auth service)
    print("\n[Step 1] Testing login audit logging...")
    login_response = requests.post(
        f"{API_GATEWAY}/auth/register",
        json={
            "email": "auditlog@test.com",
            "password": "TestPass123!",
            "full_name": "Audit Test User"
        }
    )

    if login_response.status_code in [200, 201]:
        print(f"✅ Registration successful")
        login_data = login_response.json()
        token = login_data.get("access_token")
        user_id = login_data.get("user", {}).get("id")
    elif login_response.status_code == 400:
        # User already exists, try logging in
        print("User exists, logging in...")
        login_response = requests.post(
            f"{API_GATEWAY}/auth/login",
            json={
                "email": "auditlog@test.com",
                "password": "TestPass123!"
            }
        )
        if login_response.status_code == 200:
            print(f"✅ Login successful")
            login_data = login_response.json()
            token = login_data.get("access_token")
            user_id = login_data.get("user", {}).get("id")
        else:
            print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
            return False
    else:
        print(f"❌ Registration failed: {login_response.status_code} - {login_response.text}")
        return False

    print(f"   User ID: {user_id}")
    print(f"   Token: {token[:30]}...")

    # Step 2: Create diagram (creates audit log via diagram service)
    print("\n[Step 2] Testing diagram creation audit logging...")
    create_response = requests.post(
        f"{API_GATEWAY}/diagrams/",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "title": "Audit Test Diagram",
            "file_type": "canvas",
            "canvas_data": {"shapes": [], "version": "1.0"}
        }
    )

    if create_response.status_code in [200, 201]:
        print(f"✅ Diagram created successfully")
        diagram = create_response.json()
        diagram_id = diagram.get("id")
        print(f"   Diagram ID: {diagram_id}")
        print(f"   Title: {diagram.get('title')}")
    else:
        print(f"❌ Diagram creation failed: {create_response.status_code} - {create_response.text}")
        return False

    # Step 3: Update diagram (creates audit log)
    print("\n[Step 3] Testing diagram update audit logging...")
    time.sleep(1)
    update_response = requests.put(
        f"{API_GATEWAY}/diagrams/{diagram_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "title": "Audit Test Diagram - Updated",
            "canvas_data": {"shapes": [{"type": "rect", "x": 10, "y": 10}], "version": "1.1"}
        }
    )

    if update_response.status_code == 200:
        print(f"✅ Diagram updated successfully")
        updated_diagram = update_response.json()
        print(f"   New title: {updated_diagram.get('title')}")
        print(f"   Version: {updated_diagram.get('current_version')}")
    else:
        print(f"❌ Diagram update failed: {update_response.status_code} - {update_response.text}")

    # Step 4: Delete diagram (creates audit log via diagram service)
    print("\n[Step 4] Testing diagram deletion audit logging...")
    time.sleep(1)
    delete_response = requests.delete(
        f"{API_GATEWAY}/diagrams/{diagram_id}",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    if delete_response.status_code in [200, 204]:
        print(f"✅ Diagram deleted successfully (soft delete)")
        print(f"   Response: {delete_response.json() if delete_response.text else 'No content'}")
    else:
        print(f"❌ Diagram deletion failed: {delete_response.status_code} - {delete_response.text}")

    # Step 5: Verify audit logs
    print("\n[Step 5] Verifying audit logs in database...")
    import subprocess

    # Check login audit log
    result = subprocess.run([
        "docker", "exec", "autograph-postgres", "psql", "-U", "autograph", "-d", "autograph",
        "-c", f"SELECT action, resource_type, resource_id, extra_data FROM audit_log WHERE user_id = '{user_id}' AND action = 'login_success' ORDER BY created_at DESC LIMIT 1;"
    ], capture_output=True, text=True)

    if "login_success" in result.stdout:
        print("✅ Login audit log found")
    else:
        print("⚠️  Login audit log not found (might be registration_success)")

    # Check diagram creation audit log
    result = subprocess.run([
        "docker", "exec", "autograph-postgres", "psql", "-U", "autograph", "-d", "autograph",
        "-c", f"SELECT action, resource_type, resource_id FROM audit_log WHERE user_id = '{user_id}' AND action = 'create_diagram' ORDER BY created_at DESC LIMIT 1;"
    ], capture_output=True, text=True)

    if "create_diagram" in result.stdout:
        print("✅ Diagram creation audit log found")
    else:
        print("❌ Diagram creation audit log NOT found")
        print(f"   Output: {result.stdout}")

    # Check diagram update audit log
    result = subprocess.run([
        "docker", "exec", "autograph-postgres", "psql", "-U", "autograph", "-d", "autograph",
        "-c", f"SELECT action, resource_type, resource_id FROM audit_log WHERE user_id = '{user_id}' AND action = 'update_diagram' ORDER BY created_at DESC LIMIT 1;"
    ], capture_output=True, text=True)

    if "update_diagram" in result.stdout:
        print("✅ Diagram update audit log found")
    else:
        print("❌ Diagram update audit log NOT found")

    # Check diagram deletion audit log
    result = subprocess.run([
        "docker", "exec", "autograph-postgres", "psql", "-U", "autograph", "-d", "autograph",
        "-c", f"SELECT action, resource_type, resource_id FROM audit_log WHERE user_id = '{user_id}' AND action LIKE 'delete_diagram%' ORDER BY created_at DESC LIMIT 1;"
    ], capture_output=True, text=True)

    if "delete_diagram" in result.stdout:
        print("✅ Diagram deletion audit log found")
    else:
        print("❌ Diagram deletion audit log NOT found")

    # Show all audit logs for this user
    print("\n[Step 6] All audit logs for test user:")
    result = subprocess.run([
        "docker", "exec", "autograph-postgres", "psql", "-U", "autograph", "-d", "autograph",
        "-c", f"SELECT action, resource_type, resource_id, created_at FROM audit_log WHERE user_id = '{user_id}' ORDER BY created_at;"
    ], capture_output=True, text=True)
    print(result.stdout)

    print("\n" + "=" * 80)
    print("AUDIT LOGGING TEST COMPLETE")
    print("=" * 80)

    return True

if __name__ == "__main__":
    test_audit_logging()
