#!/usr/bin/env python3
"""
Test Audit Logging Features with Real Admin User

This script creates a real admin user in the database and tests all audit features.
"""

import requests
import json
import sys
from datetime import datetime, timedelta
import csv
from io import StringIO
import psycopg2

# Configuration
BASE_URL = "http://localhost:8085"
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "autograph",
    "user": "autograph",
    "password": "autograph_dev_password"
}

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_test(message):
    print(f"{BLUE}  {message}{RESET}")

def print_success(message):
    print(f"{GREEN}  ✓ {message}{RESET}")

def print_error(message):
    print(f"{RED}  ✗ {message}{RESET}")

def print_section(message):
    print(f"\n{YELLOW}{'='*80}{RESET}")
    print(f"{YELLOW}{message}{RESET}")
    print(f"{YELLOW}{'='*80}{RESET}")


def create_admin_user():
    """Create an admin user directly in the database."""
    print_section("SETUP: CREATING ADMIN USER")
    
    try:
        # First, register a user via API
        register_data = {
            "email": f"test_admin_{datetime.now().timestamp()}@test.com",
            "password": "AdminPass123!",
            "full_name": "Test Admin"
        }
        
        response = requests.post(f"{BASE_URL}/register", json=register_data)
        if response.status_code not in [200, 201]:
            print_error(f"Failed to register user: {response.status_code}")
            return None, None
        
        user_data = response.json()
        user_id = user_data["id"]
        user_email = user_data["email"]
        print_success(f"User registered: {user_email}")
        
        # Update user role to admin in database
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute(
            "UPDATE users SET role = 'admin' WHERE id = %s",
            (user_id,)
        )
        conn.commit()
        
        cur.close()
        conn.close()
        
        print_success(f"User upgraded to admin role")
        
        return user_email, register_data["password"]
        
    except Exception as e:
        print_error(f"Failed to create admin user: {str(e)}")
        return None, None


def test_comprehensive_audit_logging():
    """Test comprehensive audit logging with real admin."""
    print_section("TEST 1: COMPREHENSIVE AUDIT LOGGING")
    
    # Create admin user
    admin_email, admin_password = create_admin_user()
    if not admin_email:
        print_error("Failed to create admin user")
        return False
    
    try:
        # Login as admin
        print_test("Step 1: Logging in as admin...")
        
        login_response = requests.post(
            f"{BASE_URL}/token",
            data={
                "username": admin_email,
                "password": admin_password
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if login_response.status_code != 200:
            print_error(f"Failed to login: {login_response.status_code}")
            return False
        
        tokens = login_response.json()
        access_token = tokens["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        print_success("Admin logged in successfully")
        
        # Fetch all audit logs
        print_test("Step 2: Fetching all audit logs...")
        
        response = requests.get(
            f"{BASE_URL}/admin/audit-logs",
            headers=headers,
            params={"skip": 0, "limit": 10}
        )
        
        if response.status_code != 200:
            print_error(f"Failed to fetch audit logs: {response.status_code} - {response.text}")
            return False
        
        audit_data = response.json()
        print_success(f"Fetched {len(audit_data['audit_logs'])} audit logs")
        print_success(f"Total audit logs in system: {audit_data['total']}")
        
        # Display sample audit log
        if audit_data['audit_logs']:
            sample = audit_data['audit_logs'][0]
            print_test(f"Sample audit log:")
            print_test(f"  - Action: {sample['action']}")
            print_test(f"  - User: {sample.get('user_email', 'N/A')}")
            print_test(f"  - IP: {sample.get('ip_address', 'N/A')}")
            print_test(f"  - Created: {sample['created_at']}")
        
        # Test filtering by action
        print_test("Step 3: Testing filter by action (register)...")
        
        response = requests.get(
            f"{BASE_URL}/admin/audit-logs",
            headers=headers,
            params={"action": "register", "limit": 5}
        )
        
        if response.status_code != 200:
            print_error(f"Failed to filter by action: {response.status_code}")
            return False
        
        register_logs = response.json()
        print_success(f"Found {register_logs['total']} register events")
        
        # Verify all returned logs have action='register'
        all_register = all(log['action'] == 'register' for log in register_logs['audit_logs'])
        if all_register:
            print_success("All filtered logs have action='register'")
        else:
            print_error("Some logs don't have action='register'")
            return False
        
        # Test filtering by date range
        print_test("Step 4: Testing filter by date range (last 24 hours)...")
        
        start_date = (datetime.now() - timedelta(hours=24)).isoformat() + "Z"
        
        response = requests.get(
            f"{BASE_URL}/admin/audit-logs",
            headers=headers,
            params={"start_date": start_date, "limit": 10}
        )
        
        if response.status_code != 200:
            print_error(f"Failed to filter by date: {response.status_code}")
            return False
        
        recent_logs = response.json()
        print_success(f"Found {recent_logs['total']} logs in last 24 hours")
        
        print_success("TEST 1 PASSED: Comprehensive audit logging works!")
        return True
        
    except Exception as e:
        print_error(f"Exception during test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_audit_export_csv():
    """Test CSV export with real admin."""
    print_section("TEST 2: AUDIT EXPORT - CSV FORMAT")
    
    # Create admin user
    admin_email, admin_password = create_admin_user()
    if not admin_email:
        print_error("Failed to create admin user")
        return False
    
    try:
        # Login as admin
        print_test("Step 1: Logging in as admin...")
        
        login_response = requests.post(
            f"{BASE_URL}/token",
            data={
                "username": admin_email,
                "password": admin_password
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if login_response.status_code != 200:
            print_error(f"Failed to login: {login_response.status_code}")
            return False
        
        tokens = login_response.json()
        access_token = tokens["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        print_success("Admin logged in")
        
        # Request CSV export
        print_test("Step 2: Requesting CSV export...")
        
        response = requests.get(
            f"{BASE_URL}/admin/audit-logs/export/csv",
            headers=headers,
            params={"action": "register"}
        )
        
        if response.status_code != 200:
            print_error(f"Failed to export CSV: {response.status_code} - {response.text}")
            return False
        
        # Verify CSV format
        print_test("Step 3: Verifying CSV format...")
        
        csv_content = response.text
        print_success(f"CSV downloaded ({len(csv_content)} bytes)")
        
        # Parse CSV
        reader = csv.DictReader(StringIO(csv_content))
        rows = list(reader)
        
        # Verify headers
        expected_headers = ['ID', 'User ID', 'User Email', 'Action', 'Resource Type', 
                           'Resource ID', 'IP Address', 'User Agent', 'Extra Data', 'Created At']
        
        if reader.fieldnames == expected_headers:
            print_success("CSV headers are correct")
        else:
            print_error(f"CSV headers incorrect: {reader.fieldnames}")
            return False
        
        print_success(f"CSV contains {len(rows)} records")
        
        # Verify content
        if rows:
            sample = rows[0]
            print_test(f"Sample CSV row:")
            print_test(f"  - ID: {sample['ID']}")
            print_test(f"  - Action: {sample['Action']}")
            print_test(f"  - User Email: {sample['User Email']}")
            print_success("CSV content format is valid")
        
        # Verify Content-Disposition header
        content_disp = response.headers.get('Content-Disposition', '')
        if 'attachment' in content_disp and 'audit_logs_' in content_disp:
            print_success(f"Content-Disposition header correct")
        else:
            print_error(f"Content-Disposition header missing or incorrect")
        
        print_success("TEST 2 PASSED: CSV export works correctly!")
        return True
        
    except Exception as e:
        print_error(f"Exception during test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_audit_export_json():
    """Test JSON export with real admin."""
    print_section("TEST 3: AUDIT EXPORT - JSON FORMAT")
    
    # Create admin user
    admin_email, admin_password = create_admin_user()
    if not admin_email:
        print_error("Failed to create admin user")
        return False
    
    try:
        # Login as admin
        print_test("Step 1: Logging in as admin...")
        
        login_response = requests.post(
            f"{BASE_URL}/token",
            data={
                "username": admin_email,
                "password": admin_password
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if login_response.status_code != 200:
            print_error(f"Failed to login: {login_response.status_code}")
            return False
        
        tokens = login_response.json()
        access_token = tokens["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        print_success("Admin logged in")
        
        # Request JSON export
        print_test("Step 2: Requesting JSON export...")
        
        start_date = (datetime.now() - timedelta(days=7)).isoformat() + "Z"
        
        response = requests.get(
            f"{BASE_URL}/admin/audit-logs/export/json",
            headers=headers,
            params={"start_date": start_date, "action": "login"}
        )
        
        if response.status_code != 200:
            print_error(f"Failed to export JSON: {response.status_code} - {response.text}")
            return False
        
        # Verify JSON structure
        print_test("Step 3: Verifying JSON structure...")
        
        json_data = response.json()
        print_success(f"JSON downloaded and parsed successfully")
        
        # Verify structure
        required_keys = ['export_date', 'total_records', 'filters', 'audit_logs']
        if all(key in json_data for key in required_keys):
            print_success("JSON structure is correct (all required keys present)")
        else:
            print_error(f"JSON structure incorrect. Keys: {json_data.keys()}")
            return False
        
        print_success(f"Total records in export: {json_data['total_records']}")
        print_success(f"Export date: {json_data['export_date']}")
        
        # Verify audit logs array
        audit_logs = json_data['audit_logs']
        print_success(f"Audit logs array contains {len(audit_logs)} records")
        
        if audit_logs:
            sample = audit_logs[0]
            required_log_keys = ['id', 'user_id', 'action', 'created_at']
            
            if all(key in sample for key in required_log_keys):
                print_success("Audit log object structure is correct")
            else:
                print_error(f"Audit log object incomplete. Keys: {sample.keys()}")
                return False
            
            print_test(f"Sample audit log:")
            print_test(f"  - ID: {sample['id']}")
            print_test(f"  - Action: {sample['action']}")
            print_test(f"  - User: {sample.get('user_email', 'N/A')}")
        
        # Verify Content-Disposition header
        content_disp = response.headers.get('Content-Disposition', '')
        if 'attachment' in content_disp and 'audit_logs_' in content_disp:
            print_success(f"Content-Disposition header correct")
        else:
            print_error(f"Content-Disposition header missing or incorrect")
        
        print_success("TEST 3 PASSED: JSON export works correctly!")
        return True
        
    except Exception as e:
        print_error(f"Exception during test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}AUDIT LOGGING FEATURES TEST SUITE (WITH REAL ADMIN){RESET}")
    print(f"{BLUE}Testing Features #23-25{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")
    
    results = []
    
    # Test 1: Comprehensive Audit Logging
    results.append(("Feature #23: Comprehensive Audit Logging", test_comprehensive_audit_logging()))
    
    # Test 2: CSV Export
    results.append(("Feature #24: CSV Export", test_audit_export_csv()))
    
    # Test 3: JSON Export
    results.append(("Feature #25: JSON Export", test_audit_export_json()))
    
    # Print summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        if result:
            print_success(f"{name}: PASSED")
        else:
            print_error(f"{name}: FAILED")
    
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}Total: {passed}/{total} tests passed{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")
    
    if passed == total:
        print_success("🎉 All audit logging features are fully functional!")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
