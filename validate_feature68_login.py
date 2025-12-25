#!/usr/bin/env python3
"""
Feature 68: User Login with JWT Tokens
Tests user login functionality with email and password that returns JWT tokens.
"""
import requests
import json
import time
from datetime import datetime, timedelta
import jwt
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Configuration
AUTH_SERVICE_URL = "https://localhost:8085"
FRONTEND_URL = "http://localhost:3000"

# Disable SSL warnings for local testing
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Test user credentials
TEST_EMAIL = f"test_login_{int(time.time())}@example.com"
TEST_PASSWORD = "SecurePass123!"

# JWT secret for token validation
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
ALGORITHM = "HS256"

def print_test_result(test_name: str, passed: bool, details: str = ""):
    """Print formatted test result."""
    status = "✓" if passed else "✗"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{status} Test {test_name}: {'PASS' if passed else 'FAIL'}{reset}")
    if details:
        print(f"  {details}")

def main():
    """Run Feature 68 validation tests."""
    print("\n" + "="*80)
    print("Feature 68: User Login with JWT Tokens")
    print("="*80 + "\n")

    test_results = []

    # Step 1: Register user
    print("Step 1: Registering test user...")
    register_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "full_name": "Test User"
    }

    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/register",
            json=register_data,
            timeout=10,
            verify=False
        )

        if response.status_code == 201:
            print(f"✓ User registered successfully")
            user_data = response.json()
            user_id = user_data.get("id")  # UserResponse returns 'id' field
            print(f"  User ID: {user_id}")
            test_results.append(("User Registration", True, ""))
        else:
            print(f"✗ Registration failed: {response.status_code}")
            print(f"  Response: {response.text}")
            test_results.append(("User Registration", False, f"HTTP {response.status_code}"))
            return
    except Exception as e:
        print(f"✗ Registration failed: {str(e)}")
        test_results.append(("User Registration", False, str(e)))
        return

    # Step 2: Verify email (required before login)
    print("\nStep 2: Verifying email...")
    # Get verification token from database
    try:
        # Connect to database (use localhost since we're running outside Docker)
        db_host = "localhost"
        db_port = "5432"
        db_name = os.getenv("POSTGRES_DB", "autograph")
        db_user = os.getenv("POSTGRES_USER", "postgres")
        db_password = os.getenv("POSTGRES_PASSWORD", "postgres")

        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        cursor = conn.cursor()

        # Get verification token for the user
        cursor.execute(
            "SELECT token FROM email_verification_tokens WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        )
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result:
            verification_token = result[0]
            print(f"✓ Found verification token in database")

            # Call email/verify endpoint (POST)
            verify_response = requests.post(
                f"{AUTH_SERVICE_URL}/email/verify",
                json={"token": verification_token},
                timeout=10,
                verify=False
            )

            if verify_response.status_code in [200, 302]:
                print(f"✓ Email verified successfully")
                test_results.append(("Email Verification", True, ""))
            else:
                print(f"✗ Verification failed: {verify_response.status_code}")
                print(f"  Response: {verify_response.text}")
                test_results.append(("Email Verification", False, f"HTTP {verify_response.status_code}"))
                return
        else:
            print(f"✗ No verification token found in database")
            test_results.append(("Email Verification", False, "Token not found"))
            return

    except Exception as e:
        print(f"✗ Database error: {str(e)}")
        test_results.append(("Email Verification", False, str(e)))
        return

    # Step 3: Attempt login
    print("\nStep 3: Testing login endpoint...")
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "remember_me": True
    }

    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/login",
            json=login_data,
            timeout=10,
            verify=False
        )

        passed = response.status_code == 200
        details = f"HTTP {response.status_code}"

        if passed:
            print(f"✓ Login successful (HTTP 200)")
        else:
            print(f"✗ Login failed: HTTP {response.status_code}")
            print(f"  Response: {response.text}")

        test_results.append(("Login Returns 200 OK", passed, details))

        if not passed:
            # If login failed, we can't continue
            print("\n" + "="*80)
            print("TEST SUMMARY")
            print("="*80)
            for test_name, passed, details in test_results:
                print_test_result(test_name, passed, details)
            return

        # Parse response
        login_response = response.json()

    except Exception as e:
        print(f"✗ Login request failed: {str(e)}")
        test_results.append(("Login Returns 200 OK", False, str(e)))
        return

    # Step 4: Verify response contains access_token
    print("\nStep 4: Verifying access_token in response...")
    access_token = login_response.get("access_token")
    passed = access_token is not None and len(access_token) > 0
    details = "Access token present" if passed else "Access token missing"
    print_test_result("Response contains access_token", passed, details)
    test_results.append(("Response contains access_token", passed, details))

    # Step 5: Verify response contains refresh_token
    print("\nStep 5: Verifying refresh_token in response...")
    refresh_token = login_response.get("refresh_token")
    passed = refresh_token is not None and len(refresh_token) > 0
    details = "Refresh token present" if passed else "Refresh token missing"
    print_test_result("Response contains refresh_token", passed, details)
    test_results.append(("Response contains refresh_token", passed, details))

    # Step 6: Verify access_token is valid JWT
    print("\nStep 6: Validating access_token JWT format...")
    try:
        # Decode without verification first to check structure
        decoded_access = jwt.decode(access_token, options={"verify_signature": False})
        passed = True
        details = "Valid JWT format"
        print_test_result("Access token is valid JWT", passed, details)
        test_results.append(("Access token is valid JWT", passed, details))
    except Exception as e:
        passed = False
        details = f"Invalid JWT: {str(e)}"
        print_test_result("Access token is valid JWT", passed, details)
        test_results.append(("Access token is valid JWT", passed, details))
        decoded_access = None

    # Step 7: Verify access_token expiry (should be 1 hour)
    if decoded_access:
        print("\nStep 7: Verifying access_token expiry time...")
        exp_timestamp = decoded_access.get("exp")
        iat_timestamp = decoded_access.get("iat")

        if exp_timestamp and iat_timestamp:
            expiry_delta = exp_timestamp - iat_timestamp
            # Should be 3600 seconds (1 hour), allow 1 second tolerance
            expected_expiry = 3600
            passed = abs(expiry_delta - expected_expiry) <= 1
            details = f"Expires in {expiry_delta} seconds (expected {expected_expiry})"
            print_test_result("Access token expires in 1 hour", passed, details)
            test_results.append(("Access token expires in 1 hour", passed, details))
        else:
            passed = False
            details = "Missing exp or iat claims"
            print_test_result("Access token expires in 1 hour", passed, details)
            test_results.append(("Access token expires in 1 hour", passed, details))
    else:
        test_results.append(("Access token expires in 1 hour", False, "Could not decode token"))

    # Step 8: Verify refresh_token is valid JWT
    print("\nStep 8: Validating refresh_token JWT format...")
    try:
        # Decode without verification first to check structure
        decoded_refresh = jwt.decode(refresh_token, options={"verify_signature": False})
        passed = True
        details = "Valid JWT format"
        print_test_result("Refresh token is valid JWT", passed, details)
        test_results.append(("Refresh token is valid JWT", passed, details))
    except Exception as e:
        passed = False
        details = f"Invalid JWT: {str(e)}"
        print_test_result("Refresh token is valid JWT", passed, details)
        test_results.append(("Refresh token is valid JWT", passed, details))
        decoded_refresh = None

    # Step 9: Verify refresh_token expiry (should be 30 days)
    if decoded_refresh:
        print("\nStep 9: Verifying refresh_token expiry time...")
        exp_timestamp = decoded_refresh.get("exp")
        iat_timestamp = decoded_refresh.get("iat")

        if exp_timestamp and iat_timestamp:
            expiry_delta = exp_timestamp - iat_timestamp
            # Should be 2592000 seconds (30 days), allow 1 second tolerance
            expected_expiry = 30 * 24 * 60 * 60  # 30 days in seconds
            passed = abs(expiry_delta - expected_expiry) <= 1
            details = f"Expires in {expiry_delta} seconds (expected {expected_expiry}, {expiry_delta / 86400:.1f} days)"
            print_test_result("Refresh token expires in 30 days", passed, details)
            test_results.append(("Refresh token expires in 30 days", passed, details))
        else:
            passed = False
            details = "Missing exp or iat claims"
            print_test_result("Refresh token expires in 30 days", passed, details)
            test_results.append(("Refresh token expires in 30 days", passed, details))
    else:
        test_results.append(("Refresh token expires in 30 days", False, "Could not decode token"))

    # Step 10: Verify token_type is bearer
    print("\nStep 10: Verifying token_type...")
    token_type = login_response.get("token_type")
    passed = token_type == "bearer"
    details = f"Token type: {token_type}" if token_type else "Token type missing"
    print_test_result("Token type is 'bearer'", passed, details)
    test_results.append(("Token type is 'bearer'", passed, details))

    # Step 11: Verify access token contains user claims
    if decoded_access:
        print("\nStep 11: Verifying access token claims...")
        has_sub = "sub" in decoded_access
        has_email = "email" in decoded_access
        passed = has_sub and has_email
        details = f"Claims: sub={'✓' if has_sub else '✗'}, email={'✓' if has_email else '✗'}"
        print_test_result("Access token contains user claims", passed, details)
        test_results.append(("Access token contains user claims", passed, details))
    else:
        test_results.append(("Access token contains user claims", False, "Could not decode token"))

    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    total_tests = len(test_results)
    passed_tests = sum(1 for _, passed, _ in test_results if passed)

    for test_name, passed, details in test_results:
        print_test_result(test_name, passed, details)

    print("\n" + "-"*80)
    print(f"Total: {passed_tests}/{total_tests} tests passed ({passed_tests*100//total_tests}%)")
    print("-"*80)

    # Feature passes if all tests pass
    feature_passes = passed_tests == total_tests

    if feature_passes:
        print("\n✅ Feature 68: PASSING - User login with JWT tokens works correctly")
        return 0
    else:
        print(f"\n❌ Feature 68: FAILING - {total_tests - passed_tests} test(s) failed")
        return 1

if __name__ == "__main__":
    exit(main())
