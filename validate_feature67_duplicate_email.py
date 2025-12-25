#!/usr/bin/env python3
"""
Feature #67 Validation: Duplicate Email Prevention
Tests that registration prevents duplicate emails with case-insensitive matching
"""
import sys
import time
import requests
import secrets
import psycopg2
from datetime import datetime
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
API_GATEWAY = "http://localhost:8080"
AUTH_SERVICE = "https://localhost:8085"
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432
POSTGRES_DB = "autograph"
POSTGRES_USER = "autograph"
POSTGRES_PASSWORD = "autograph_dev_password"

def print_step(step_num, description):
    """Print test step."""
    print(f"\n{'='*60}")
    print(f"Step {step_num}: {description}")
    print(f"{'='*60}")

def cleanup_test_user(email):
    """Delete test user from database."""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        cur = conn.cursor()
        # Delete user with this email (case-insensitive)
        cur.execute("DELETE FROM users WHERE LOWER(email) = LOWER(%s)", (email,))
        conn.commit()
        count = cur.rowcount
        cur.close()
        conn.close()
        if count > 0:
            print(f"✓ Cleaned up {count} test user(s) with email: {email}")
        return True
    except Exception as e:
        print(f"✗ Cleanup failed: {e}")
        return False

def register_user(email, password="StrongPass123!", full_name="Test User"):
    """Register a new user."""
    # Use AUTH_SERVICE directly since API Gateway isn't responding
    url = f"{AUTH_SERVICE}/register"
    payload = {
        "email": email,
        "password": password,
        "full_name": full_name,
        "role": "viewer"
    }

    # Disable SSL verification for self-signed certs
    response = requests.post(url, json=payload, verify=False)
    return response

def main():
    """Run all validation tests for Feature #67."""
    print("\n" + "="*60)
    print("Feature #67 Validation: Duplicate Email Prevention")
    print("="*60)

    # Generate unique test email
    test_email = f"test-{secrets.token_hex(8)}@example.com"
    test_password = "StrongPass123!"

    passed_tests = 0
    total_tests = 6  # 6 actual test assertions (Step 1 is cleanup, not a test)

    try:
        # Step 1: Clean up any existing test users
        print_step(1, "Clean up existing test users")
        cleanup_test_user(test_email)
        time.sleep(1)

        # Step 2: Register user with test email
        print_step(2, "Register user with test email")
        print(f"Email: {test_email}")
        response = register_user(test_email, test_password)

        if response.status_code == 201:
            print(f"✓ Registration succeeded (HTTP {response.status_code})")
            data = response.json()
            print(f"  User ID: {data.get('id')}")
            print(f"  Email: {data.get('email')}")
            passed_tests += 1
        else:
            print(f"✗ Registration failed (HTTP {response.status_code})")
            print(f"  Response: {response.text}")
            raise Exception("Initial registration should succeed")

        time.sleep(1)

        # Step 3: Verify registration succeeded
        print_step(3, "Verify registration succeeded")
        if response.status_code == 201:
            print("✓ User registered successfully")
            passed_tests += 1
        else:
            print("✗ Verification failed")
            raise Exception("Registration verification failed")

        time.sleep(1)

        # Step 4: Attempt to register again with same email (exact match)
        print_step(4, "Attempt duplicate registration (exact match)")
        print(f"Email: {test_email}")
        response2 = register_user(test_email, test_password)

        if response2.status_code == 409:
            print(f"✓ Duplicate registration rejected (HTTP {response2.status_code})")
            passed_tests += 1
        else:
            print(f"✗ Wrong status code (HTTP {response2.status_code}, expected 409)")
            print(f"  Response: {response2.text}")

        time.sleep(1)

        # Step 5: Verify error message
        print_step(5, "Verify error message")
        if response2.status_code == 409:
            error_data = response2.json()
            error_msg = error_data.get("detail", "")
            if "Email already registered" in error_msg or "already registered" in error_msg.lower():
                print(f"✓ Correct error message: '{error_msg}'")
                passed_tests += 1
            else:
                print(f"✗ Unexpected error message: '{error_msg}'")
        else:
            print("✗ Cannot verify error message (wrong status code)")

        time.sleep(1)

        # Step 6: Verify HTTP 409 Conflict status
        print_step(6, "Verify HTTP 409 Conflict status")
        if response2.status_code == 409:
            print("✓ HTTP 409 Conflict status confirmed")
            passed_tests += 1
        else:
            print(f"✗ Wrong status code: {response2.status_code} (expected 409)")

        time.sleep(1)

        # Step 7: Test case-insensitive email matching
        print_step(7, "Test case-insensitive matching")

        # Test uppercase email
        uppercase_email = test_email.upper()
        print(f"Testing uppercase: {uppercase_email}")
        response3 = register_user(uppercase_email, test_password)

        if response3.status_code == 409:
            print(f"✓ Uppercase email rejected (HTTP {response3.status_code})")
        else:
            print(f"✗ Uppercase email not rejected (HTTP {response3.status_code})")
            print(f"  Response: {response3.text}")

        time.sleep(0.5)

        # Test mixed case email
        mixed_case_email = test_email[:5].upper() + test_email[5:]
        print(f"Testing mixed case: {mixed_case_email}")
        response4 = register_user(mixed_case_email, test_password)

        if response4.status_code == 409:
            print(f"✓ Mixed case email rejected (HTTP {response4.status_code})")
        else:
            print(f"✗ Mixed case email not rejected (HTTP {response4.status_code})")
            print(f"  Response: {response4.text}")

        # Overall case-insensitive test
        if response3.status_code == 409 and response4.status_code == 409:
            print("✓ Case-insensitive email matching working correctly")
            passed_tests += 1
        else:
            print("✗ Case-insensitive matching failed")

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")

    finally:
        # Cleanup
        print_step("Cleanup", "Remove test users")
        cleanup_test_user(test_email)

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    print(f"Tests Failed: {total_tests - passed_tests}/{total_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

    if passed_tests == total_tests:
        print("\n✅ Feature #67 PASSED - All tests successful!")
        return 0
    else:
        print(f"\n❌ Feature #67 FAILED - {total_tests - passed_tests} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
