#!/usr/bin/env python3
"""
Feature 66: User registration enforces password strength requirements
Tests password validation for:
- Minimum length (8 characters)
- Maximum length (128 characters)
- Complexity requirements (uppercase, lowercase, digit, special char)
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
AUTH_SERVICE_URL = "https://localhost:8085"
REGISTER_ENDPOINT = f"{AUTH_SERVICE_URL}/register"

# Test counter
tests_passed = 0
tests_failed = 0

def test_password(password, email_suffix, should_pass, reason):
    """Test a password against the registration endpoint."""
    global tests_passed, tests_failed

    email = f"test_{email_suffix}_{datetime.now().timestamp()}@example.com"
    payload = {
        "email": email,
        "password": password,
        "full_name": "Test User"
    }

    try:
        response = requests.post(REGISTER_ENDPOINT, json=payload, verify=False, timeout=5)

        if should_pass:
            # Password should be accepted
            if response.status_code == 201:
                print(f"✓ PASS: {reason}")
                print(f"  Password: {password[:3]}... (length: {len(password)})")
                tests_passed += 1
                return True
            else:
                print(f"✗ FAIL: {reason}")
                print(f"  Expected: 201, Got: {response.status_code}")
                print(f"  Response: {response.text[:200]}")
                tests_failed += 1
                return False
        else:
            # Password should be rejected
            if response.status_code == 422 or response.status_code == 400:
                print(f"✓ PASS: {reason}")
                print(f"  Password rejected: {password[:3]}... (length: {len(password)})")
                if response.status_code == 422:
                    try:
                        error_detail = response.json()
                        print(f"  Error message: {error_detail}")
                    except:
                        pass
                tests_passed += 1
                return True
            else:
                print(f"✗ FAIL: {reason}")
                print(f"  Expected rejection (422/400), Got: {response.status_code}")
                tests_failed += 1
                return False

    except Exception as e:
        print(f"✗ ERROR: {reason}")
        print(f"  Exception: {str(e)}")
        tests_failed += 1
        return False

def main():
    print("=" * 70)
    print("Feature 66: Password Strength Validation Tests")
    print("=" * 70)
    print()

    # Test 1: Service health check
    print("Test 1: Auth service health check")
    try:
        response = requests.get(f"{AUTH_SERVICE_URL}/health", verify=False, timeout=5)
        if response.status_code == 200:
            print("✓ PASS: Auth service is accessible")
            global tests_passed
            tests_passed += 1
        else:
            print(f"✗ FAIL: Auth service returned {response.status_code}")
            global tests_failed
            tests_failed += 1
    except Exception as e:
        print(f"✗ FAIL: Cannot reach auth service: {e}")
        tests_failed += 1
    print()

    # Test 2: Too short password (< 8 chars)
    print("Test 2: Reject password too short (< 8 characters)")
    test_password("abc123", "short", False, "Password with 6 characters should be rejected")
    print()

    # Test 3: Minimum length password (8 chars)
    print("Test 3: Accept minimum length password (8 characters)")
    test_password("Abcd123!", "min8", True, "Password with exactly 8 characters should be accepted")
    print()

    # Test 4: Too long password (> 128 chars)
    print("Test 4: Reject password too long (> 128 characters)")
    long_password = "A" * 129 + "a1!"
    test_password(long_password, "toolong", False, "Password with 129+ characters should be rejected")
    print()

    # Test 5: Missing uppercase letter
    print("Test 5: Check uppercase requirement")
    test_password("abcd1234!", "nouppercase", False, "Password without uppercase should be rejected (if complexity required)")
    print()

    # Test 6: Missing lowercase letter
    print("Test 6: Check lowercase requirement")
    test_password("ABCD1234!", "nolowercase", False, "Password without lowercase should be rejected (if complexity required)")
    print()

    # Test 7: Missing digit
    print("Test 7: Check digit requirement")
    test_password("Abcdefgh!", "nodigit", False, "Password without digit should be rejected (if complexity required)")
    print()

    # Test 8: Missing special character
    print("Test 8: Check special character requirement")
    test_password("Abcd1234", "nospecial", False, "Password without special char should be rejected (if complexity required)")
    print()

    # Test 9: Valid strong password
    print("Test 9: Accept strong password (all requirements)")
    test_password("StrongPass123!", "strong", True, "Strong password with all requirements should be accepted")
    print()

    # Test 10: Valid password with various special characters
    print("Test 10: Accept password with various special characters")
    test_password("P@ssw0rd#2024", "special_chars", True, "Password with multiple special chars should be accepted")
    print()

    # Test 11: Edge case - exactly 128 characters
    print("Test 11: Accept maximum length password (128 characters)")
    max_password = "A" * 63 + "a" * 63 + "1!"  # Total 128 chars
    test_password(max_password, "max128", True, "Password with exactly 128 characters should be accepted")
    print()

    # Summary
    print("=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print(f"Tests passed: {tests_passed}")
    print(f"Tests failed: {tests_failed}")
    print(f"Total tests: {tests_passed + tests_failed}")
    print()

    if tests_failed == 0:
        print("✅ ALL TESTS PASSED - Feature 66 is working correctly!")
        print()
        print("Password strength requirements enforced:")
        print("  • Minimum 8 characters")
        print("  • Maximum 128 characters")
        print("  • At least one uppercase letter")
        print("  • At least one lowercase letter")
        print("  • At least one digit")
        print("  • At least one special character")
        return 0
    else:
        print(f"❌ {tests_failed} TEST(S) FAILED - Feature 66 needs fixes")
        return 1

if __name__ == "__main__":
    sys.exit(main())
