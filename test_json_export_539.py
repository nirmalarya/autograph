#!/usr/bin/env python3
"""
Test script for Feature #539: JSON audit log export
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8085"

def test_json_export():
    """Test JSON export endpoint for audit logs."""

    # Step 1: Login as an existing admin
    print("Step 1: Logging in as admin...")
    login_response = requests.post(
        f"{BASE_URL}/login",
        json={"email": "test476@example.com", "password": "TestPass123!"}
    )

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        sys.exit(1)

    token = login_response.json()["access_token"]
    print(f"✅ Login successful, got token")

    headers = {"Authorization": f"Bearer {token}"}

    # Step 2: Test JSON export endpoint exists
    print("\nStep 2: Testing JSON export endpoint...")
    export_response = requests.get(
        f"{BASE_URL}/admin/audit-logs/export/json",
        headers=headers
    )

    if export_response.status_code != 200:
        print(f"❌ JSON export failed: {export_response.status_code}")
        print(f"Response: {export_response.text}")
        sys.exit(1)

    print(f"✅ JSON export endpoint exists and returns 200")

    # Step 3: Verify JSON structure
    print("\nStep 3: Verifying JSON structure...")

    # Check Content-Type header
    content_type = export_response.headers.get("Content-Type", "")
    if "application/json" not in content_type:
        print(f"❌ Wrong content type: {content_type}")
        sys.exit(1)
    print(f"✅ Content-Type is application/json")

    # Check Content-Disposition header
    content_disposition = export_response.headers.get("Content-Disposition", "")
    if "attachment" not in content_disposition or "audit_logs_" not in content_disposition:
        print(f"❌ Wrong Content-Disposition: {content_disposition}")
        sys.exit(1)
    print(f"✅ Content-Disposition header correct")

    # Step 4: Verify valid JSON
    print("\nStep 4: Verifying valid JSON...")
    try:
        data = export_response.json()
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        sys.exit(1)
    print(f"✅ Valid JSON received")

    # Step 5: Verify JSON has required fields
    print("\nStep 5: Verifying JSON structure has required fields...")
    required_top_level = ["export_date", "total_records", "filters", "audit_logs"]
    for field in required_top_level:
        if field not in data:
            print(f"❌ Missing top-level field: {field}")
            sys.exit(1)
    print(f"✅ All top-level fields present: {required_top_level}")

    # Step 6: Verify audit_logs is an array
    print("\nStep 6: Verifying audit_logs is an array...")
    if not isinstance(data["audit_logs"], list):
        print(f"❌ audit_logs is not an array")
        sys.exit(1)
    print(f"✅ audit_logs is an array with {len(data['audit_logs'])} entries")

    # Step 7: Verify each log entry has required fields
    print("\nStep 7: Verifying log entry structure...")
    if len(data["audit_logs"]) > 0:
        required_fields = [
            "id", "user_id", "user_email", "action", "resource_type",
            "resource_id", "ip_address", "user_agent", "extra_data", "created_at"
        ]
        first_log = data["audit_logs"][0]
        for field in required_fields:
            if field not in first_log:
                print(f"❌ Missing field in log entry: {field}")
                sys.exit(1)
        print(f"✅ All required fields present in log entries: {required_fields}")

    # Step 8: Test filtering by action
    print("\nStep 8: Testing filtering by action...")
    filter_response = requests.get(
        f"{BASE_URL}/admin/audit-logs/export/json?action=login",
        headers=headers
    )

    if filter_response.status_code != 200:
        print(f"❌ Filtered JSON export failed: {filter_response.status_code}")
        sys.exit(1)

    filtered_data = filter_response.json()
    if filtered_data["filters"]["action"] != "login":
        print(f"❌ Filter not reflected in response")
        sys.exit(1)

    print(f"✅ Filtering works, got {filtered_data['total_records']} records with action='login'")

    # Step 9: Verify all filtered records match the action
    if filtered_data["total_records"] > 0:
        for log in filtered_data["audit_logs"]:
            if log["action"] != "login":
                print(f"❌ Found non-login action in filtered results: {log['action']}")
                sys.exit(1)
        print(f"✅ All filtered records match action='login'")

    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED - Feature #539 is working!")
    print("="*60)
    print(f"\nSummary:")
    print(f"  - JSON export endpoint exists at /admin/audit-logs/export/json")
    print(f"  - Returns valid JSON with correct structure")
    print(f"  - Total records in export: {data['total_records']}")
    print(f"  - Content-Type: application/json")
    print(f"  - Content-Disposition: {content_disposition}")
    print(f"  - Filtering works correctly")
    print(f"  - All required fields present")

if __name__ == "__main__":
    test_json_export()
