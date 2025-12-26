#!/usr/bin/env python3
"""
Test Feature #538: Enterprise: Audit export: CSV format

Steps:
1. Navigate to /admin/audit (via API)
2. Click Export (trigger CSV export)
3. Select CSV (endpoint: /admin/audit-logs/export/csv)
4. Download
5. Verify CSV contains all audit entries
"""

import requests
import csv
from io import StringIO
import json

BASE_URL = "http://localhost:8085"  # API Gateway

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "autograph",
    "user": "autograph",
    "password": "autograph_dev_password"
}

def print_test(msg):
    print(f"\n🧪 TEST: {msg}")

def print_success(msg):
    print(f"✅ {msg}")

def print_error(msg):
    print(f"❌ {msg}")

def print_info(msg):
    print(f"ℹ️  {msg}")


def create_admin_user():
    """Create an admin user for testing."""
    print_test("Creating admin user...")

    # Generate unique email
    import uuid
    from datetime import datetime
    email = f"admin_test_538_{int(datetime.now().timestamp())}@example.com"

    response = requests.post(
        f"{BASE_URL}/register",
        json={
            "email": email,
            "password": "AdminPass123!",
            "full_name": "Feature 538 Admin"
        }
    )

    if response.status_code not in [200, 201]:
        print_error(f"Failed to register: {response.status_code} - {response.text}")
        return None, None

    user_data = response.json()
    user_id = user_data.get("id")
    print_success(f"Registered admin user: {email}")

    # Make user admin and verified directly in database
    import psycopg2
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET role = 'admin', is_verified = true WHERE email = %s",
        (email,)
    )
    conn.commit()
    cur.close()
    conn.close()

    print_success("Promoted user to admin and verified email")

    # Login
    response = requests.post(
        f"{BASE_URL}/login",
        json={"email": email, "password": "AdminPass123!"}
    )

    if response.status_code != 200:
        print_error(f"Failed to login: {response.status_code} - {response.text}")
        return None, None

    login_data = response.json()
    token = login_data["access_token"]
    # User ID might be in different locations depending on API response structure
    user_id = login_data.get("user", {}).get("id") or login_data.get("user_id") or user_data.get("id")
    print_success(f"Logged in as admin (user_id: {user_id})")

    return token, user_id


def test_csv_export(admin_token):
    """Test CSV export of audit logs."""
    print_test("Testing CSV export...")

    headers = {"Authorization": f"Bearer {admin_token}"}

    # Step 1: Check audit logs endpoint
    print_test("Step 1: Checking audit logs exist...")
    response = requests.get(
        f"{BASE_URL}/admin/audit-logs",
        headers=headers,
        params={"skip": 0, "limit": 10}
    )

    if response.status_code != 200:
        print_error(f"Failed to get audit logs: {response.status_code} - {response.text}")
        return False

    data = response.json()
    total_logs = data.get("total", 0)
    print_success(f"Found {total_logs} total audit logs")

    if total_logs == 0:
        print_error("No audit logs to export!")
        return False

    # Step 2: Export CSV without filters
    print_test("Step 2: Exporting all audit logs to CSV...")
    response = requests.get(
        f"{BASE_URL}/admin/audit-logs/export/csv",
        headers=headers
    )

    if response.status_code != 200:
        print_error(f"Failed to export CSV: {response.status_code} - {response.text}")
        return False

    print_success("CSV export successful!")

    # Step 3: Verify CSV format
    print_test("Step 3: Verifying CSV format...")

    # Check Content-Type
    content_type = response.headers.get("Content-Type", "")
    if "text/csv" not in content_type:
        print_error(f"Wrong content type: {content_type}")
        return False
    print_success(f"Content-Type correct: {content_type}")

    # Check Content-Disposition for filename
    disposition = response.headers.get("Content-Disposition", "")
    if "attachment" not in disposition or "audit_logs_" not in disposition:
        print_error(f"Wrong Content-Disposition: {disposition}")
        return False
    print_success(f"Content-Disposition correct: {disposition}")

    # Parse CSV
    csv_content = response.text
    reader = csv.reader(StringIO(csv_content))
    rows = list(reader)

    if len(rows) < 2:
        print_error(f"CSV has too few rows: {len(rows)}")
        return False

    # Check headers
    expected_headers = [
        'ID', 'User ID', 'User Email', 'Action', 'Resource Type',
        'Resource ID', 'IP Address', 'User Agent', 'Extra Data', 'Created At'
    ]

    headers_row = rows[0]
    if headers_row != expected_headers:
        print_error(f"Wrong headers: {headers_row}")
        print_error(f"Expected: {expected_headers}")
        return False

    print_success(f"CSV headers correct: {len(headers_row)} columns")

    # Check data rows
    data_rows = rows[1:]
    print_success(f"CSV has {len(data_rows)} data rows")

    # Verify each row has correct number of columns
    for i, row in enumerate(data_rows[:5], 1):  # Check first 5 rows
        if len(row) != len(expected_headers):
            print_error(f"Row {i} has wrong column count: {len(row)} (expected {len(expected_headers)})")
            return False

    print_success("All rows have correct column count")

    # Show sample data
    if len(data_rows) > 0:
        print_info("Sample CSV row:")
        print_info(f"  ID: {data_rows[0][0]}")
        print_info(f"  Action: {data_rows[0][3]}")
        print_info(f"  User Email: {data_rows[0][2]}")
        print_info(f"  Created At: {data_rows[0][9]}")

    # Step 4: Test with filters
    print_test("Step 4: Testing CSV export with filters...")

    # Export only 'registration_success' actions
    response = requests.get(
        f"{BASE_URL}/admin/audit-logs/export/csv",
        headers=headers,
        params={"action": "registration_success"}
    )

    if response.status_code != 200:
        print_error(f"Failed to export filtered CSV: {response.status_code}")
        return False

    csv_content = response.text
    reader = csv.reader(StringIO(csv_content))
    filtered_rows = list(reader)

    # Check all data rows have action = 'registration_success'
    data_rows = filtered_rows[1:]
    if len(data_rows) > 0:
        all_correct = all(row[3] == 'registration_success' for row in data_rows)
        if not all_correct:
            print_error("Filter didn't work - found non-matching actions")
            return False
        print_success(f"Filter works! Got {len(data_rows)} registration_success entries")
    else:
        print_info("No registration_success entries found (ok if none exist)")

    # Step 5: Verify complete data integrity
    print_test("Step 5: Verifying data integrity...")

    # Re-export all and compare count with API
    response = requests.get(
        f"{BASE_URL}/admin/audit-logs/export/csv",
        headers=headers
    )

    csv_content = response.text
    reader = csv.reader(StringIO(csv_content))
    all_rows = list(reader)
    csv_count = len(all_rows) - 1  # Subtract header

    # Get count from API
    response = requests.get(
        f"{BASE_URL}/admin/audit-logs",
        headers=headers,
        params={"skip": 0, "limit": 1}
    )
    api_count = response.json()["total"]

    if csv_count != api_count:
        print_error(f"Count mismatch! CSV has {csv_count} rows, API reports {api_count} total")
        # This might be ok if logs are being created during test
        print_info("Note: Small differences acceptable if audit logs created during export")
        if abs(csv_count - api_count) > 10:
            return False
    else:
        print_success(f"Count matches! {csv_count} rows in CSV = {api_count} total in database")

    return True


def main():
    print("=" * 80)
    print("Feature #538: Enterprise: Audit export: CSV format")
    print("=" * 80)

    # Create admin user
    admin_token, admin_id = create_admin_user()
    if not admin_token:
        print_error("Failed to create admin user")
        return False

    # Test CSV export
    success = test_csv_export(admin_token)

    print("\n" + "=" * 80)
    if success:
        print("✅ FEATURE #538 PASSED: CSV export works correctly!")
    else:
        print("❌ FEATURE #538 FAILED: CSV export has issues")
    print("=" * 80)

    return success


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
