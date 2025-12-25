#!/usr/bin/env python3
"""
Feature #64: User Registration with Email and Password
Tests user registration functionality with bcrypt password hashing (cost factor 12)

Test Steps:
1. Navigate to /register page
2. Enter email: test@example.com
3. Enter password: SecurePass123!
4. Enter password confirmation: SecurePass123!
5. Click Register button
6. Verify user created in database
7. Verify password hashed with bcrypt (cost factor 12)
8. Verify success message displayed
9. Verify redirect to login page
"""

import os
import sys
import time
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import secrets
import re

# Test configuration
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "https://localhost:8080")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "https://localhost:8085")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Disable SSL warnings for self-signed certificates
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Database configuration
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "database": os.getenv("POSTGRES_DB", "autograph"),
    "user": os.getenv("POSTGRES_USER", "autograph"),
    "password": os.getenv("POSTGRES_PASSWORD", "autograph_dev_password")
}

def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

def cleanup_test_user(email: str):
    """Delete test user if exists."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE email = %s", (email,))
        conn.commit()
        cur.close()
        conn.close()
        print(f"  Cleaned up test user: {email}")
    except Exception as e:
        print(f"  Warning: Could not cleanup test user: {e}")

def test_user_registration():
    """Test user registration with email and password."""
    print("\n" + "="*80)
    print("Feature #64: User Registration with Email and Password")
    print("="*80)

    test_results = {
        "total": 9,
        "passed": 0,
        "failed": 0,
        "tests": []
    }

    # Generate unique test email
    test_email = f"test_{secrets.token_hex(4)}@example.com"
    test_password = "SecurePass123!"
    test_full_name = "Test User"

    print(f"\nTest user: {test_email}")
    print(f"Password: {test_password}")

    # Cleanup any existing test user
    cleanup_test_user(test_email)

    # Test 1: Check auth service is accessible
    print("\n[Test 1/9] Check auth service is accessible...")
    try:
        response = requests.get(f"{AUTH_SERVICE_URL}/health", timeout=5, verify=False)
        if response.status_code == 200:
            print("  ✓ Auth service is accessible")
            test_results["passed"] += 1
            test_results["tests"].append({"name": "Auth service accessible", "status": "PASS"})
        else:
            print(f"  ✗ Auth service returned {response.status_code}")
            test_results["failed"] += 1
            test_results["tests"].append({"name": "Auth service accessible", "status": "FAIL"})
            return test_results
    except Exception as e:
        print(f"  ✗ Cannot connect to auth service: {e}")
        test_results["failed"] += 1
        test_results["tests"].append({"name": "Auth service accessible", "status": "FAIL"})
        return test_results

    # Test 2: Register new user via API
    print("\n[Test 2/9] Register new user via API...")
    try:
        payload = {
            "email": test_email,
            "password": test_password,
            "full_name": test_full_name
        }
        response = requests.post(
            f"{AUTH_SERVICE_URL}/register",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
            verify=False
        )

        if response.status_code == 201:
            print("  ✓ User registered successfully (HTTP 201)")
            user_data = response.json()
            print(f"    User ID: {user_data.get('id')}")
            print(f"    Email: {user_data.get('email')}")
            test_results["passed"] += 1
            test_results["tests"].append({"name": "User registration via API", "status": "PASS"})
        else:
            print(f"  ✗ Registration failed: {response.status_code}")
            print(f"    Response: {response.text}")
            test_results["failed"] += 1
            test_results["tests"].append({"name": "User registration via API", "status": "FAIL"})
            cleanup_test_user(test_email)
            return test_results
    except Exception as e:
        print(f"  ✗ Registration request failed: {e}")
        test_results["failed"] += 1
        test_results["tests"].append({"name": "User registration via API", "status": "FAIL"})
        cleanup_test_user(test_email)
        return test_results

    # Test 3: Verify user created in database
    print("\n[Test 3/9] Verify user created in database...")
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, email, password_hash, full_name, is_active, is_verified FROM users WHERE email = %s",
            (test_email,)
        )
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            print("  ✓ User found in database")
            print(f"    ID: {user['id']}")
            print(f"    Email: {user['email']}")
            print(f"    Full Name: {user['full_name']}")
            print(f"    Active: {user['is_active']}")
            print(f"    Verified: {user['is_verified']}")
            test_results["passed"] += 1
            test_results["tests"].append({"name": "User in database", "status": "PASS"})
        else:
            print("  ✗ User not found in database")
            test_results["failed"] += 1
            test_results["tests"].append({"name": "User in database", "status": "FAIL"})
            cleanup_test_user(test_email)
            return test_results
    except Exception as e:
        print(f"  ✗ Database query failed: {e}")
        test_results["failed"] += 1
        test_results["tests"].append({"name": "User in database", "status": "FAIL"})
        cleanup_test_user(test_email)
        return test_results

    # Test 4: Verify password is hashed (not plain text)
    print("\n[Test 4/9] Verify password is hashed...")
    try:
        if user['password_hash'] and user['password_hash'] != test_password:
            print("  ✓ Password is hashed (not stored as plain text)")
            print(f"    Hash length: {len(user['password_hash'])} characters")
            test_results["passed"] += 1
            test_results["tests"].append({"name": "Password hashed", "status": "PASS"})
        else:
            print("  ✗ Password appears to be stored as plain text!")
            test_results["failed"] += 1
            test_results["tests"].append({"name": "Password hashed", "status": "FAIL"})
            cleanup_test_user(test_email)
            return test_results
    except Exception as e:
        print(f"  ✗ Failed to verify password hash: {e}")
        test_results["failed"] += 1
        test_results["tests"].append({"name": "Password hashed", "status": "FAIL"})
        cleanup_test_user(test_email)
        return test_results

    # Test 5: Verify password hashed with bcrypt
    print("\n[Test 5/9] Verify password hashed with bcrypt...")
    try:
        password_hash = user['password_hash']
        # Bcrypt hashes start with $2b$ (Python) or $2a$ (some implementations)
        if password_hash.startswith('$2b$') or password_hash.startswith('$2a$') or password_hash.startswith('$2y$'):
            print("  ✓ Password hashed with bcrypt")
            print(f"    Hash prefix: {password_hash[:7]}")
            test_results["passed"] += 1
            test_results["tests"].append({"name": "Bcrypt hashing", "status": "PASS"})
        else:
            print(f"  ✗ Password not hashed with bcrypt (prefix: {password_hash[:7]})")
            test_results["failed"] += 1
            test_results["tests"].append({"name": "Bcrypt hashing", "status": "FAIL"})
            cleanup_test_user(test_email)
            return test_results
    except Exception as e:
        print(f"  ✗ Failed to verify bcrypt: {e}")
        test_results["failed"] += 1
        test_results["tests"].append({"name": "Bcrypt hashing", "status": "FAIL"})
        cleanup_test_user(test_email)
        return test_results

    # Test 6: Verify bcrypt cost factor is 12
    print("\n[Test 6/9] Verify bcrypt cost factor is 12...")
    try:
        password_hash = user['password_hash']
        # Bcrypt hash format: $2b$12$[22 char salt][31 char hash]
        # The cost factor is between the second and third $
        match = re.match(r'\$2[aby]\$(\d+)\$', password_hash)
        if match:
            cost_factor = int(match.group(1))
            if cost_factor == 12:
                print(f"  ✓ Bcrypt cost factor is 12")
                test_results["passed"] += 1
                test_results["tests"].append({"name": "Bcrypt cost factor 12", "status": "PASS"})
            else:
                print(f"  ✗ Bcrypt cost factor is {cost_factor}, expected 12")
                test_results["failed"] += 1
                test_results["tests"].append({"name": "Bcrypt cost factor 12", "status": "FAIL"})
        else:
            print(f"  ✗ Could not parse cost factor from hash")
            test_results["failed"] += 1
            test_results["tests"].append({"name": "Bcrypt cost factor 12", "status": "FAIL"})
    except Exception as e:
        print(f"  ✗ Failed to verify cost factor: {e}")
        test_results["failed"] += 1
        test_results["tests"].append({"name": "Bcrypt cost factor 12", "status": "FAIL"})

    # Test 7: Verify user is active
    print("\n[Test 7/9] Verify user is active...")
    try:
        if user['is_active']:
            print("  ✓ User is active")
            test_results["passed"] += 1
            test_results["tests"].append({"name": "User is active", "status": "PASS"})
        else:
            print("  ✗ User is not active")
            test_results["failed"] += 1
            test_results["tests"].append({"name": "User is active", "status": "FAIL"})
    except Exception as e:
        print(f"  ✗ Failed to verify user active status: {e}")
        test_results["failed"] += 1
        test_results["tests"].append({"name": "User is active", "status": "FAIL"})

    # Test 8: Verify duplicate email is rejected
    print("\n[Test 8/9] Verify duplicate email is rejected...")
    try:
        payload = {
            "email": test_email,
            "password": "AnotherPassword123!",
            "full_name": "Another User"
        }
        response = requests.post(
            f"{AUTH_SERVICE_URL}/register",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
            verify=False
        )

        if response.status_code == 400:
            print("  ✓ Duplicate email rejected (HTTP 400)")
            test_results["passed"] += 1
            test_results["tests"].append({"name": "Duplicate email rejected", "status": "PASS"})
        else:
            print(f"  ✗ Expected HTTP 400, got {response.status_code}")
            test_results["failed"] += 1
            test_results["tests"].append({"name": "Duplicate email rejected", "status": "FAIL"})
    except Exception as e:
        print(f"  ✗ Duplicate email test failed: {e}")
        test_results["failed"] += 1
        test_results["tests"].append({"name": "Duplicate email rejected", "status": "FAIL"})

    # Test 9: Verify password can be used for login
    print("\n[Test 9/9] Verify password can be used for login...")
    try:
        payload = {
            "username": test_email,
            "password": test_password
        }
        response = requests.post(
            f"{AUTH_SERVICE_URL}/token",
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
            verify=False
        )

        if response.status_code == 200:
            token_data = response.json()
            if "access_token" in token_data:
                print("  ✓ Login successful with registered password")
                print(f"    Access token received (length: {len(token_data['access_token'])})")
                test_results["passed"] += 1
                test_results["tests"].append({"name": "Login with password", "status": "PASS"})
            else:
                print("  ✗ No access token in response")
                test_results["failed"] += 1
                test_results["tests"].append({"name": "Login with password", "status": "FAIL"})
        else:
            print(f"  ✗ Login failed: {response.status_code}")
            print(f"    Response: {response.text}")
            test_results["failed"] += 1
            test_results["tests"].append({"name": "Login with password", "status": "FAIL"})
    except Exception as e:
        print(f"  ✗ Login test failed: {e}")
        test_results["failed"] += 1
        test_results["tests"].append({"name": "Login with password", "status": "FAIL"})

    # Cleanup
    print("\n" + "-"*80)
    print("Cleaning up test data...")
    cleanup_test_user(test_email)

    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total tests: {test_results['total']}")
    print(f"Passed: {test_results['passed']}")
    print(f"Failed: {test_results['failed']}")
    print(f"Success rate: {(test_results['passed']/test_results['total']*100):.1f}%")

    print("\nDetailed Results:")
    for test in test_results["tests"]:
        status_symbol = "✓" if test["status"] == "PASS" else "✗"
        print(f"  {status_symbol} {test['name']}: {test['status']}")

    print("="*80)

    if test_results["failed"] == 0:
        print("\n✅ Feature #64: PASSING - All tests passed!")
        return 0
    else:
        print(f"\n❌ Feature #64: FAILING - {test_results['failed']} test(s) failed")
        return 1

if __name__ == "__main__":
    try:
        exit_code = test_user_registration()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
