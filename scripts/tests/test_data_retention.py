#!/usr/bin/env python3
"""
Test Data Retention Policy Feature (#544)

Tests:
1. Get default retention policy
2. Set custom retention policy
3. Run manual cleanup
"""

import requests
import json
import sys
import psycopg2
from datetime import datetime, timedelta

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

API_BASE = "http://localhost:8080"
AUTH_SERVICE = "http://localhost:8085"

def print_test(test_name):
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}TEST: {test_name}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

def print_success(message):
    print(f"  {GREEN}✓{RESET} {message}")

def print_error(message):
    print(f"  {RED}✗{RESET} {message}")

def print_info(message):
    print(f"  {YELLOW}ℹ{RESET} {message}")

def create_admin_user():
    """Create an admin user directly in database."""
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="autograph",
        user="autograph",
        password="autograph_dev_password"
    )
    cursor = conn.cursor()
    
    # Check if admin user already exists
    cursor.execute("SELECT id, email, role FROM users WHERE email = 'admin@test.com'")
    result = cursor.fetchone()
    
    if result:
        user_id, email, role = result
        if role != 'admin':
            # Upgrade to admin
            cursor.execute("UPDATE users SET role = 'admin' WHERE email = 'admin@test.com'")
            conn.commit()
            print_info(f"Upgraded user {email} to admin role")
        else:
            print_info(f"Admin user already exists: {email}")
    else:
        print_error("Admin user not found. Please create one first.")
        sys.exit(1)
    
    cursor.close()
    conn.close()
    return user_id

def login_as_admin():
    """Login as admin and get token."""
    response = requests.post(
        f"{AUTH_SERVICE}/login",
        json={
            "email": "admin@test.com",
            "password": "admin123"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Logged in as admin")
        return data["access_token"]
    else:
        print_error(f"Login failed: {response.status_code}")
        print_error(f"Response: {response.text}")
        sys.exit(1)

def test_get_retention_policy(token):
    """Test 1: Get retention policy configuration."""
    print_test("TEST 1: GET RETENTION POLICY")
    
    response = requests.get(
        f"{AUTH_SERVICE}/admin/config/data-retention",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        policy = response.json()
        print_success("Retrieved retention policy")
        print_info(f"Diagram retention: {policy.get('diagram_retention_days', 'N/A')} days")
        print_info(f"Trash retention: {policy.get('deleted_retention_days', 'N/A')} days")
        print_info(f"Version retention: {policy.get('version_retention_days', 'N/A')} days")
        print_info(f"Enabled: {policy.get('enabled', False)}")
        print_success("TEST 1 PASSED")
        return True
    else:
        print_error(f"Failed to get policy: {response.status_code}")
        print_error(f"Response: {response.text}")
        return False

def test_set_retention_policy(token):
    """Test 2: Set retention policy."""
    print_test("TEST 2: SET RETENTION POLICY")
    
    # Set policy: 2 years for diagrams, 30 days for trash, 1 year for versions
    response = requests.post(
        f"{AUTH_SERVICE}/admin/config/data-retention",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "diagram_retention_days": 730,  # 2 years
            "deleted_retention_days": 30,   # 30 days
            "version_retention_days": 365,  # 1 year
            "enabled": True
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print_success("Set retention policy")
        print_info(f"Policy: {json.dumps(result.get('policy', {}), indent=2)}")
        
        cleanup = result.get('cleanup_results', {})
        print_info(f"Cleanup results:")
        print_info(f"  - Old diagrams found: {cleanup.get('old_diagrams_found', 0)}")
        print_info(f"  - Deleted from trash: {cleanup.get('deleted_from_trash', 0)}")
        print_info(f"  - Old versions found: {cleanup.get('old_versions_found', 0)}")
        
        # Verify policy was set
        verify_response = requests.get(
            f"{AUTH_SERVICE}/admin/config/data-retention",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if verify_response.status_code == 200:
            policy = verify_response.json()
            if policy.get('diagram_retention_days') == 730:
                print_success("Policy verified: diagram_retention_days = 730")
                print_success("TEST 2 PASSED")
                return True
            else:
                print_error(f"Policy mismatch: expected 730, got {policy.get('diagram_retention_days')}")
                return False
        else:
            print_error("Failed to verify policy")
            return False
    else:
        print_error(f"Failed to set policy: {response.status_code}")
        print_error(f"Response: {response.text}")
        return False

def test_manual_cleanup(token):
    """Test 3: Run manual cleanup."""
    print_test("TEST 3: MANUAL CLEANUP")
    
    response = requests.post(
        f"{AUTH_SERVICE}/admin/data-retention/run-cleanup",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print_success("Manual cleanup completed")
        print_info(f"Message: {result.get('message')}")
        
        cleanup = result.get('cleanup_results', {})
        print_info(f"Cleanup results:")
        print_info(f"  - Old diagrams moved to trash: {cleanup.get('old_diagrams_moved_to_trash', 0)}")
        print_info(f"  - Deleted from trash: {cleanup.get('deleted_from_trash', 0)}")
        print_info(f"  - Old versions deleted: {cleanup.get('old_versions_deleted', 0)}")
        
        cutoff_dates = result.get('cutoff_dates', {})
        if cutoff_dates:
            print_info(f"Cutoff dates:")
            print_info(f"  - Diagram cutoff: {cutoff_dates.get('diagram_cutoff', 'N/A')}")
            print_info(f"  - Trash cutoff: {cutoff_dates.get('trash_cutoff', 'N/A')}")
            print_info(f"  - Version cutoff: {cutoff_dates.get('version_cutoff', 'N/A')}")
        
        print_success("TEST 3 PASSED")
        return True
    else:
        print_error(f"Failed to run cleanup: {response.status_code}")
        print_error(f"Response: {response.text}")
        return False

def main():
    print(f"{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}DATA RETENTION POLICY TEST SUITE{RESET}")
    print(f"{BLUE}Feature #544: Enterprise: Data retention policies: auto-delete old data{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")
    
    # Setup
    print_info("Setting up test environment...")
    create_admin_user()
    token = login_as_admin()
    
    # Run tests
    results = []
    results.append(test_get_retention_policy(token))
    results.append(test_set_retention_policy(token))
    results.append(test_manual_cleanup(token))
    
    # Summary
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}TEST SUMMARY{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"{GREEN}✓ ALL TESTS PASSED ({passed}/{total}){RESET}")
        print(f"\n{GREEN}🎉 Feature #544 is fully functional!{RESET}")
        return 0
    else:
        print(f"{RED}✗ SOME TESTS FAILED ({passed}/{total}){RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
