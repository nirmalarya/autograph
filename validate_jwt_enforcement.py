#!/usr/bin/env python3
"""
Validate Feature #8: API Gateway enforces JWT authentication on protected routes

This script validates that:
1. Protected routes reject requests without tokens (401)
2. Protected routes reject requests with invalid tokens (401)
3. Protected routes reject requests with malformed auth headers (401)
4. JWT token validation is being performed (signature verification)
"""

import requests
import sys

GATEWAY_URL = "http://localhost:8080"

def test_auth_enforcement():
    """Test that JWT authentication is enforced on protected routes."""

    print("=" * 80)
    print("FEATURE #8 VALIDATION: JWT Authentication Enforcement")
    print("=" * 80)
    print()

    tests_passed = 0
    tests_total = 0

    # List of protected routes to test
    protected_routes = [
        "/api/diagrams/",
        "/api/diagrams",
        "/api/ai/health",
        "/api/collaboration/health",
        "/api/git/health",
        "/api/export/health",
        "/api/integrations/health",
    ]

    # Test 1: No token should be rejected
    print("Test 1: Protected routes WITHOUT token")
    print("-" * 80)
    for route in protected_routes:
        tests_total += 1
        response = requests.get(f"{GATEWAY_URL}{route}")
        if response.status_code == 401:
            print(f"  ✓ {route} - Rejected without token (HTTP 401)")
            tests_passed += 1
        else:
            print(f"  ✗ {route} - Expected 401, got {response.status_code}")
    print()

    # Test 2: Invalid token should be rejected
    print("Test 2: Protected routes with INVALID token")
    print("-" * 80)
    invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"
    headers = {"Authorization": f"Bearer {invalid_token}"}

    for route in protected_routes[:3]:  # Test first 3 routes
        tests_total += 1
        response = requests.get(f"{GATEWAY_URL}{route}", headers=headers)
        if response.status_code == 401:
            print(f"  ✓ {route} - Rejected invalid token (HTTP 401)")
            tests_passed += 1
        else:
            print(f"  ✗ {route} - Expected 401, got {response.status_code}")
    print()

    # Test 3: Malformed Authorization header should be rejected
    print("Test 3: Protected routes with MALFORMED Authorization header")
    print("-" * 80)
    malformed_headers = [
        {"Authorization": "InvalidFormat"},
        {"Authorization": "Bearer"},  # Missing token
        {"Authorization": ""},  # Empty
    ]

    for i, headers in enumerate(malformed_headers):
        tests_total += 1
        response = requests.get(f"{GATEWAY_URL}/api/diagrams/", headers=headers)
        if response.status_code == 401:
            print(f"  ✓ Malformed header #{i+1} - Rejected (HTTP 401)")
            tests_passed += 1
        else:
            print(f"  ✗ Malformed header #{i+1} - Expected 401, got {response.status_code}")
    print()

    # Test 4: Verify JWT validation is actually happening
    print("Test 4: JWT signature verification is active")
    print("-" * 80)
    tests_total += 1

    # Try with a token that has valid structure but wrong signature
    # This proves the system is actually validating signatures, not just checking for presence
    fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiZXhwIjo5OTk5OTk5OTk5fQ.fakesignature"
    headers = {"Authorization": f"Bearer {fake_token}"}
    response = requests.get(f"{GATEWAY_URL}/api/diagrams/", headers=headers)

    if response.status_code == 401 and "Invalid token" in response.text:
        print(f"  ✓ JWT signature verification is active")
        print(f"    Response: {response.json().get('detail', 'N/A')[:100]}")
        tests_passed += 1
    else:
        print(f"  ✗ JWT validation may not be working properly")
        print(f"    Status: {response.status_code}, Response: {response.text[:100]}")
    print()

    # Summary
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Tests passed: {tests_passed}/{tests_total}")
    print()

    if tests_passed == tests_total:
        print("✅ FEATURE #8 VALIDATION: PASS")
        print()
        print("JWT Authentication Enforcement is working correctly:")
        print("  ✓ Protected routes require Authorization header")
        print("  ✓ Invalid tokens are rejected")
        print("  ✓ Malformed auth headers are rejected")
        print("  ✓ JWT signature verification is active")
        print()
        return True
    else:
        print("❌ FEATURE #8 VALIDATION: FAIL")
        print(f"   {tests_total - tests_passed} test(s) failed")
        print()
        return False

if __name__ == "__main__":
    success = test_auth_enforcement()
    sys.exit(0 if success else 1)
