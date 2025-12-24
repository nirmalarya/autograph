#!/usr/bin/env python3
"""
Quick verification tests for Features #65-67
These features are already implemented as part of Feature #64
"""

import requests
import sys
import time

def test_feature_65_email_validation():
    """Feature #65: User registration validates email format."""
    print("\n=== Feature #65: Email Format Validation ===\n")
    
    # Test invalid email
    response = requests.post(
        "http://localhost:8085/register",
        json={"email": "notanemail", "password": "SecurePass123!"},
        timeout=5
    )
    
    if response.status_code == 422:
        print("✓ Invalid email rejected (422)")
        print("✓ Email format validation working")
        return True
    else:
        print(f"✗ Invalid email not rejected (status: {response.status_code})")
        return False

def test_feature_66_password_strength():
    """Feature #66: Password strength requirements."""
    print("\n=== Feature #66: Password Strength Requirements ===\n")
    
    all_passed = True
    
    # Test weak password (< 8 chars)
    response = requests.post(
        "http://localhost:8085/register",
        json={"email": f"weak{time.time()}@example.com", "password": "123"},
        timeout=5
    )
    
    if response.status_code == 422 and "8 characters" in response.text:
        print("✓ Weak password rejected (< 8 chars)")
    else:
        print(f"✗ Weak password not rejected properly (status: {response.status_code})")
        all_passed = False
    
    # Test strong password (valid)
    response = requests.post(
        "http://localhost:8085/register",
        json={"email": f"strong{time.time()}@example.com", "password": "StrongPass123!"},
        timeout=5
    )
    
    if response.status_code in [200, 201]:
        print("✓ Strong password accepted")
    else:
        print(f"✗ Strong password rejected (status: {response.status_code})")
        all_passed = False
    
    # Test too long password (> 128 chars)
    response = requests.post(
        "http://localhost:8085/register",
        json={"email": f"long{time.time()}@example.com", "password": "a" * 129},
        timeout=5
    )
    
    if response.status_code == 422 and "128" in response.text:
        print("✓ Too long password rejected (> 128 chars)")
    else:
        print(f"✗ Too long password not rejected properly (status: {response.status_code})")
        all_passed = False
    
    if all_passed:
        print("✓ Password strength requirements enforced")
    
    return all_passed

def test_feature_67_duplicate_prevention():
    """Feature #67: Duplicate email prevention."""
    print("\n=== Feature #67: Duplicate Email Prevention ===\n")
    
    email = f"duplicate{time.time()}@example.com"
    password = "SecurePass123!"
    
    # Register first time
    response1 = requests.post(
        "http://localhost:8085/register",
        json={"email": email, "password": password},
        timeout=5
    )
    
    if response1.status_code not in [200, 201]:
        print(f"✗ First registration failed (status: {response1.status_code})")
        return False
    
    print(f"✓ First registration succeeded")
    
    # Try to register again with same email
    response2 = requests.post(
        "http://localhost:8085/register",
        json={"email": email, "password": password},
        timeout=5
    )
    
    if response2.status_code == 400 and "already registered" in response2.text.lower():
        print("✓ Duplicate email rejected (400)")
        print("✓ Error message: Email already registered")
        return True
    else:
        print(f"✗ Duplicate email not rejected properly (status: {response2.status_code})")
        return False

def main():
    """Run all tests."""
    print("=" * 80)
    print("FEATURES #65-67 VERIFICATION TESTS")
    print("=" * 80)
    
    results = {
        "Feature #65: Email Validation": test_feature_65_email_validation(),
        "Feature #66: Password Strength": test_feature_66_password_strength(),
        "Feature #67: Duplicate Prevention": test_feature_67_duplicate_prevention(),
    }
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(results.values())
    percentage = (passed / total * 100) if total > 0 else 0
    
    print("-" * 80)
    print(f"Total: {passed}/{total} tests passed ({percentage:.1f}%)")
    print("=" * 80)
    
    if passed == total:
        print("\n✓ All features verified!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
