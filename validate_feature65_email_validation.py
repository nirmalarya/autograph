#!/usr/bin/env python3
"""
Feature 65: Email Format Validation
Tests that user registration validates email format correctly.
"""

import requests
import sys
import json
from datetime import datetime
import urllib3

# Disable SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
AUTH_SERVICE_URL = "https://localhost:8085"
TEST_PASSWORD = "ValidPass123!"

def test_invalid_email_no_at_sign():
    """Test 1: Verify error message for email without @ sign"""
    print("\nTest 1: Invalid email - no @ sign (notanemail)")
    print("-" * 60)

    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/register",
            json={
                "email": "notanemail",
                "password": TEST_PASSWORD,
                "full_name": "Test User"
            },
            verify=False,
            timeout=10
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 422:
            data = response.json()
            detail = data.get("detail", [])
            if detail and len(detail) > 0:
                error = detail[0]
                msg = error.get("msg", "")
                if "@-sign" in msg or "email" in msg.lower():
                    print(f"✓ Validation error detected: {msg}")
                    return True
                else:
                    print(f"✗ Unexpected error message: {msg}")
                    return False

        print(f"✗ Expected 422 status code, got {response.status_code}")
        return False

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_edge_case_no_tld():
    """Test 2: Verify error for email@domain (no TLD)"""
    print("\nTest 2: Edge case - no TLD (email@domain)")
    print("-" * 60)

    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/register",
            json={
                "email": "email@domain",
                "password": TEST_PASSWORD,
                "full_name": "Test User"
            },
            verify=False,
            timeout=10
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 422:
            data = response.json()
            detail = data.get("detail", [])
            if detail and len(detail) > 0:
                error = detail[0]
                msg = error.get("msg", "")
                print(f"✓ Validation error detected: {msg}")
                return True

        print(f"✗ Expected 422 status code, got {response.status_code}")
        return False

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_edge_case_no_local_part():
    """Test 3: Verify error for @domain.com (no local part)"""
    print("\nTest 3: Edge case - no local part (@domain.com)")
    print("-" * 60)

    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/register",
            json={
                "email": "@domain.com",
                "password": TEST_PASSWORD,
                "full_name": "Test User"
            },
            verify=False,
            timeout=10
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 422:
            data = response.json()
            detail = data.get("detail", [])
            if detail and len(detail) > 0:
                error = detail[0]
                msg = error.get("msg", "")
                if "before the @-sign" in msg or "email" in msg.lower():
                    print(f"✓ Validation error detected: {msg}")
                    return True
                else:
                    print(f"Validation error: {msg}")
                    return True

        print(f"✗ Expected 422 status code, got {response.status_code}")
        return False

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_edge_case_double_at():
    """Test 4: Verify error for email with double @ signs"""
    print("\nTest 4: Edge case - double @ signs (test@@example.com)")
    print("-" * 60)

    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/register",
            json={
                "email": "test@@example.com",
                "password": TEST_PASSWORD,
                "full_name": "Test User"
            },
            verify=False,
            timeout=10
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 422:
            data = response.json()
            print(f"✓ Validation error detected")
            return True

        print(f"✗ Expected 422 status code, got {response.status_code}")
        return False

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_edge_case_spaces():
    """Test 5: Verify error for email with spaces"""
    print("\nTest 5: Edge case - email with spaces (test @example.com)")
    print("-" * 60)

    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/register",
            json={
                "email": "test @example.com",
                "password": TEST_PASSWORD,
                "full_name": "Test User"
            },
            verify=False,
            timeout=10
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 422:
            data = response.json()
            print(f"✓ Validation error detected")
            return True

        print(f"✗ Expected 422 status code, got {response.status_code}")
        return False

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_valid_email_basic():
    """Test 6: Verify valid email passes (test@example.com)"""
    print("\nTest 6: Valid email - basic format (test@example.com)")
    print("-" * 60)

    # Generate unique email
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    email = f"test{timestamp}@example.com"

    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/register",
            json={
                "email": email,
                "password": TEST_PASSWORD,
                "full_name": "Test User"
            },
            verify=False,
            timeout=10
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 201:
            data = response.json()
            if data.get("email") == email:
                print(f"✓ Valid email accepted: {email}")
                return True
            else:
                print(f"✗ Email mismatch in response")
                return False

        print(f"✗ Expected 201 status code, got {response.status_code}")
        print(f"Response: {response.text}")
        return False

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_valid_email_subdomain():
    """Test 7: Verify valid email with subdomain passes"""
    print("\nTest 7: Valid email - with subdomain (user@mail.example.com)")
    print("-" * 60)

    # Generate unique email
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    email = f"user{timestamp}@mail.example.com"

    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/register",
            json={
                "email": email,
                "password": TEST_PASSWORD,
                "full_name": "Test User"
            },
            verify=False,
            timeout=10
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 201:
            data = response.json()
            if data.get("email") == email:
                print(f"✓ Valid email with subdomain accepted: {email}")
                return True
            else:
                print(f"✗ Email mismatch in response")
                return False

        print(f"✗ Expected 201 status code, got {response.status_code}")
        print(f"Response: {response.text}")
        return False

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_valid_email_with_plus():
    """Test 8: Verify valid email with + sign passes"""
    print("\nTest 8: Valid email - with + sign (user+tag@example.com)")
    print("-" * 60)

    # Generate unique email
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    email = f"user+tag{timestamp}@example.com"

    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/register",
            json={
                "email": email,
                "password": TEST_PASSWORD,
                "full_name": "Test User"
            },
            verify=False,
            timeout=10
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 201:
            data = response.json()
            if data.get("email") == email:
                print(f"✓ Valid email with + sign accepted: {email}")
                return True
            else:
                print(f"✗ Email mismatch in response")
                return False

        print(f"✗ Expected 201 status code, got {response.status_code}")
        print(f"Response: {response.text}")
        return False

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_auth_service_health():
    """Test 0: Verify auth service is accessible"""
    print("\nTest 0: Auth Service Health Check")
    print("-" * 60)

    try:
        response = requests.get(f"{AUTH_SERVICE_URL}/health", verify=False, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Auth service is healthy: {data.get('status')}")
            return True
        else:
            print(f"✗ Auth service returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Cannot connect to auth service: {str(e)}")
        return False


def main():
    """Run all tests for Feature 65"""
    print("=" * 60)
    print("Feature 65: Email Format Validation")
    print("=" * 60)

    tests = [
        ("Health Check", test_auth_service_health),
        ("Invalid Email - No @ Sign", test_invalid_email_no_at_sign),
        ("Edge Case - No TLD", test_edge_case_no_tld),
        ("Edge Case - No Local Part", test_edge_case_no_local_part),
        ("Edge Case - Double @ Signs", test_edge_case_double_at),
        ("Edge Case - Spaces in Email", test_edge_case_spaces),
        ("Valid Email - Basic", test_valid_email_basic),
        ("Valid Email - Subdomain", test_valid_email_subdomain),
        ("Valid Email - Plus Sign", test_valid_email_with_plus),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' failed with exception: {str(e)}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("=" * 60)

    if passed == total:
        print("\n✅ Feature 65: Email Format Validation - PASSING")
        return 0
    else:
        print(f"\n❌ Feature 65: Email Format Validation - FAILING ({total - passed} tests failed)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
