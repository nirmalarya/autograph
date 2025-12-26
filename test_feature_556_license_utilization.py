#!/usr/bin/env python3
"""
Feature #556: License Management - Utilization Tracking
Test the license utilization tracking endpoint.

This test validates:
1. View license utilization
2. Verify seat usage calculation (e.g., 75 of 100 seats used)
3. Verify utilization percentage (e.g., 75%)
4. Verify alerts at 90% threshold
"""

import requests
import subprocess
import json
import sys
import time
from datetime import datetime

# Configuration
BASE_URL = "https://localhost:8085"
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "SecureAdminPass123!"

def run_docker_exec(command):
    """Execute command in postgres container."""
    full_command = f'docker exec autograph-postgres psql -U autograph -d autograph -c "{command}"'
    result = subprocess.run(full_command, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode

def get_user_count():
    """Get current user count from database."""
    stdout, stderr, returncode = run_docker_exec("SELECT COUNT(*) FROM users;")
    if returncode != 0:
        print(f"Error getting user count: {stderr}")
        return None

    # Parse count from psql output
    lines = stdout.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line.isdigit():
            return int(line)
    return None

def create_test_users(count, start_index=1):
    """Create test users in database."""
    print(f"\n📝 Creating {count} test users...")

    for i in range(count):
        user_num = start_index + i
        email = f"utilization_test_{user_num}@test.com"
        username = f"util_user_{user_num}"

        # Hash: testpass123
        password_hash = "$2b$12$LqGDTGgPdRHqxFdvqQMSGO4XlOq9LqV.VLHZpJLMB0nEwdQxqHXPm"

        insert_cmd = f"""
        INSERT INTO users (email, username, password_hash, is_active, is_verified, created_at)
        VALUES ('{email}', '{username}', '{password_hash}', true, true, NOW())
        ON CONFLICT (email) DO NOTHING;
        """

        stdout, stderr, returncode = run_docker_exec(insert_cmd)
        if returncode != 0:
            print(f"Warning: Failed to create user {email}: {stderr}")

def delete_test_users():
    """Delete test users created for this test."""
    print("\n🧹 Cleaning up test users...")
    delete_cmd = "DELETE FROM users WHERE email LIKE 'utilization_test_%@test.com';"
    run_docker_exec(delete_cmd)

def get_admin_token():
    """Get admin authentication token."""
    print("\n🔐 Authenticating as admin...")

    response = requests.post(
        f"{BASE_URL}/login",
        json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        },
        verify=False
    )

    if response.status_code != 200:
        print(f"❌ Admin login failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None

    data = response.json()
    token = data.get("access_token")

    if not token:
        print("❌ No access token in response")
        return None

    print(f"✅ Admin authenticated")
    return token

def set_license_limit(token, max_seats):
    """Set license seat limit."""
    print(f"\n⚙️ Setting license limit to {max_seats} seats...")

    response = requests.post(
        f"{BASE_URL}/admin/config/license",
        json={"max_seats": max_seats},
        headers={"Authorization": f"Bearer {token}"},
        verify=False
    )

    if response.status_code != 200:
        print(f"❌ Failed to set license limit: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    print(f"✅ License limit set to {max_seats} seats")
    return True

def get_utilization(token):
    """Get license seat utilization."""
    response = requests.get(
        f"{BASE_URL}/admin/license/seat-utilization",
        headers={"Authorization": f"Bearer {token}"},
        verify=False
    )

    if response.status_code != 200:
        print(f"❌ Failed to get utilization: {response.status_code}")
        print(f"Response: {response.text}")
        return None

    return response.json()

def test_utilization_tracking():
    """Test license utilization tracking."""
    print("="*80)
    print("🧪 Testing Feature #556: License Utilization Tracking")
    print("="*80)

    try:
        # Clean up any existing test users
        delete_test_users()

        # Get admin token
        token = get_admin_token()
        if not token:
            return False

        # Get initial user count
        initial_count = get_user_count()
        if initial_count is None:
            print("❌ Failed to get initial user count")
            return False

        print(f"\n📊 Initial user count: {initial_count}")

        # Test 1: No license limit configured (unlimited)
        print("\n" + "="*80)
        print("Test 1: Unlimited seats (no license configured)")
        print("="*80)

        # Clear license config
        set_license_limit(token, 0)

        utilization = get_utilization(token)
        if not utilization:
            return False

        print(f"\n📊 Utilization data:")
        print(json.dumps(utilization, indent=2))

        if utilization["enabled"]:
            print("❌ License should not be enabled with 0 max_seats")
            return False

        if utilization["total_seats"] != 0:
            print("❌ Total seats should be 0 (unlimited)")
            return False

        if utilization["alert_triggered"]:
            print("❌ Alert should not be triggered with unlimited seats")
            return False

        print("✅ Unlimited seats configuration works correctly")

        # Test 2: 75% utilization (set limit based on current users)
        print("\n" + "="*80)
        print("Test 2: 75% utilization")
        print("="*80)

        # We have initial_count users, so set max_seats to make it 75%
        # initial_count = 0.75 * max_seats
        # max_seats = initial_count / 0.75
        max_seats_for_75 = int(initial_count / 0.75)

        print(f"Setting license to {max_seats_for_75} seats for 75% utilization...")

        if not set_license_limit(token, max_seats_for_75):
            return False

        # Verify user count
        actual_count = get_user_count()
        print(f"\n📊 Current user count: {actual_count}")

        # Get utilization
        utilization = get_utilization(token)
        if not utilization:
            return False

        print(f"\n📊 Utilization data:")
        print(json.dumps(utilization, indent=2))

        if not utilization["enabled"]:
            print("❌ License should be enabled with max_seats > 0")
            return False

        if utilization["total_seats"] != max_seats_for_75:
            print(f"❌ Total seats should be {max_seats_for_75}, got {utilization['total_seats']}")
            return False

        if utilization["used_seats"] != actual_count:
            print(f"❌ Used seats should be {actual_count}, got {utilization['used_seats']}")
            return False

        expected_percentage = (actual_count / max_seats_for_75) * 100
        if abs(utilization["utilization_percentage"] - expected_percentage) > 1.0:
            print(f"❌ Utilization should be ~{expected_percentage:.2f}%, got {utilization['utilization_percentage']}%")
            return False

        # Allow some tolerance since we're rounding
        if utilization["utilization_percentage"] < 74.0 or utilization["utilization_percentage"] > 76.0:
            print(f"❌ Utilization should be ~75%, got {utilization['utilization_percentage']}%")
            return False

        if utilization["alert_triggered"]:
            print("❌ Alert should not be triggered at ~75% utilization")
            return False

        print(f"✅ ~75% utilization calculated correctly")
        print(f"   - Total seats: {utilization['total_seats']}")
        print(f"   - Used seats: {utilization['used_seats']}")
        print(f"   - Available seats: {utilization['available_seats']}")
        print(f"   - Utilization: {utilization['utilization_percentage']:.2f}%")

        # Test 3: 90% utilization threshold (alert should trigger)
        print("\n" + "="*80)
        print("Test 3: 90% utilization (alert threshold)")
        print("="*80)

        # Adjust license to trigger 90% alert
        # We have actual_count users, so set max_seats such that we're at 90%
        # actual_count = 0.90 * max_seats
        # max_seats = actual_count / 0.90

        max_seats_for_90 = int(actual_count / 0.90)

        if not set_license_limit(token, max_seats_for_90):
            return False

        utilization = get_utilization(token)
        if not utilization:
            return False

        print(f"\n📊 Utilization data:")
        print(json.dumps(utilization, indent=2))

        if utilization["utilization_percentage"] < 90.0:
            print(f"❌ Utilization should be >= 90%, got {utilization['utilization_percentage']}%")
            return False

        if not utilization["alert_triggered"]:
            print("❌ Alert should be triggered at 90%+ utilization")
            return False

        if utilization["alert_threshold"] != 90.0:
            print(f"❌ Alert threshold should be 90.0, got {utilization['alert_threshold']}")
            return False

        print(f"✅ 90% threshold alert triggered correctly")
        print(f"   - Total seats: {utilization['total_seats']}")
        print(f"   - Used seats: {utilization['used_seats']}")
        print(f"   - Utilization: {utilization['utilization_percentage']:.2f}%")
        print(f"   - Alert triggered: {utilization['alert_triggered']}")

        # Test 4: 95% utilization (well above threshold)
        print("\n" + "="*80)
        print("Test 4: 95% utilization (above threshold)")
        print("="*80)

        max_seats_for_95 = int(actual_count / 0.95)

        if not set_license_limit(token, max_seats_for_95):
            return False

        utilization = get_utilization(token)
        if not utilization:
            return False

        print(f"\n📊 Utilization data:")
        print(json.dumps(utilization, indent=2))

        if utilization["utilization_percentage"] < 90.0:
            print(f"❌ Utilization should be >= 90%, got {utilization['utilization_percentage']}%")
            return False

        if not utilization["alert_triggered"]:
            print("❌ Alert should be triggered at 95% utilization")
            return False

        print(f"✅ High utilization alert working correctly")
        print(f"   - Utilization: {utilization['utilization_percentage']:.2f}%")
        print(f"   - Alert triggered: {utilization['alert_triggered']}")

        # All tests passed
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED!")
        print("="*80)
        print("\n📊 Feature #556 Validation Summary:")
        print("   ✅ View license utilization endpoint working")
        print("   ✅ Seat usage calculation accurate")
        print("   ✅ Utilization percentage correct")
        print("   ✅ 90% threshold alert functioning")
        print("   ✅ Unlimited seats configuration working")

        return True

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        delete_test_users()
        print("\n✅ Cleanup completed")

if __name__ == "__main__":
    # Disable SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    success = test_utilization_tracking()
    sys.exit(0 if success else 1)
