#!/usr/bin/env python3
"""
Feature #100: Email verification required for new accounts

Tests:
1. Register new user: test@example.com
2. Verify account created but email_verified=false
3. Attempt to login
4. Verify error: 'Please verify your email before logging in'
5. Check email inbox (retrieve verification token from logs)
6. Click verification link (call /email/verify endpoint)
7. Verify email_verified=true in database
8. Login successfully
9. Verify access granted
"""

import requests
import os
import time
import sys
import secrets
import subprocess
import json
from datetime import datetime

# Configuration
API_GATEWAY = os.getenv("API_GATEWAY", "http://localhost:8080")
AUTH_SERVICE = os.getenv("AUTH_SERVICE", "http://localhost:8085")
POSTGRES_CONTAINER = "autograph-postgres"
POSTGRES_DB = "autograph"
POSTGRES_USER = "autograph"

def run_psql_query(query: str):
    """Execute a PostgreSQL query using docker exec."""
    try:
        result = subprocess.run(
            ["docker", "exec", "-i", POSTGRES_CONTAINER, "psql", "-U", POSTGRES_USER, "-d", POSTGRES_DB, "-t", "-c", query],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Database query failed: {e.stderr}")
        return None

def cleanup_test_user(email: str):
    """Clean up test user and related data."""
    try:
        query = f"DELETE FROM users WHERE email = '{email}';"
        run_psql_query(query)
        print(f"✓ Cleaned up test user: {email}")
    except Exception as e:
        print(f"Warning: Could not clean up test user: {e}")

def get_user_from_db(email: str):
    """Get user details from database."""
    try:
        query = f"""
            SELECT id, email, is_verified, is_active, created_at
            FROM users
            WHERE email = '{email}';
        """
        result = run_psql_query(query)

        if result and result.strip():
            # Parse the result
            parts = [p.strip() for p in result.split('|')]
            if len(parts) >= 5:
                return {
                    "id": parts[0],
                    "email": parts[1],
                    "is_verified": parts[2].lower() == 't',
                    "is_active": parts[3].lower() == 't',
                    "created_at": parts[4]
                }
        return None
    except Exception as e:
        print(f"❌ Error getting user from database: {e}")
        return None

def get_verification_token_from_db(user_id: str):
    """Get verification token from database."""
    try:
        query = f"""
            SELECT token, is_used, expires_at
            FROM email_verification_tokens
            WHERE user_id = '{user_id}'
            ORDER BY created_at DESC
            LIMIT 1;
        """
        result = run_psql_query(query)

        if result and result.strip():
            # Parse the result
            parts = [p.strip() for p in result.split('|')]
            if len(parts) >= 3:
                return {
                    "token": parts[0],
                    "is_used": parts[1].lower() == 't',
                    "expires_at": parts[2]
                }
        return None
    except Exception as e:
        print(f"❌ Error getting verification token from database: {e}")
        return None

def test_feature_100():
    """Test Feature #100: Email verification required for new accounts."""
    print("\n" + "="*80)
    print("Feature #100: Email verification required for new accounts")
    print("="*80 + "\n")

    # Generate unique test email
    test_email = f"test-verify-{secrets.token_hex(4)}@example.com"
    test_password = "Test123!@#"
    test_full_name = "Email Verification Test User"

    print(f"Test email: {test_email}\n")

    # Clean up any existing test user
    cleanup_test_user(test_email)

    try:
        # Step 1: Register new user
        print("STEP 1: Register new user")
        print("-" * 40)

        response = requests.post(
            f"{AUTH_SERVICE}/register",
            json={
                "email": test_email,
                "password": test_password,
                "full_name": test_full_name,
                "role": "viewer"
            }
        )

        if response.status_code != 201:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False

        user_data = response.json()
        user_id = user_data["id"]
        print(f"✓ User registered successfully: {user_id}")
        print(f"  Email: {user_data['email']}")
        print(f"  Is Verified: {user_data.get('is_verified', 'N/A')}\n")

        # Step 2: Verify account created but email_verified=false
        print("STEP 2: Verify account created but email_verified=false")
        print("-" * 40)

        db_user = get_user_from_db(test_email)
        if not db_user:
            print("❌ User not found in database")
            return False

        if db_user["is_verified"]:
            print("❌ User is already verified (expected: false)")
            return False

        print(f"✓ User account created with is_verified=false")
        print(f"  User ID: {db_user['id']}")
        print(f"  Email: {db_user['email']}")
        print(f"  Is Verified: {db_user['is_verified']}")
        print(f"  Is Active: {db_user['is_active']}\n")

        # Step 3: Attempt to login
        print("STEP 3: Attempt to login (should fail)")
        print("-" * 40)

        response = requests.post(
            f"{AUTH_SERVICE}/login",
            json={
                "email": test_email,
                "password": test_password,
                "remember_me": False
            }
        )

        # Step 4: Verify error: 'Please verify your email before logging in'
        print("STEP 4: Verify error message")
        print("-" * 40)

        if response.status_code == 200:
            print("❌ Login succeeded (expected: should fail)")
            print(f"Response: {response.json()}")
            return False

        if response.status_code != 403:
            print(f"❌ Unexpected status code: {response.status_code} (expected: 403)")
            print(f"Response: {response.text}")
            return False

        error_detail = response.json().get("detail", "")
        expected_message = "Please verify your email before logging in"

        if expected_message not in error_detail:
            print(f"❌ Unexpected error message: {error_detail}")
            print(f"Expected: {expected_message}")
            return False

        print(f"✓ Login blocked with correct error message")
        print(f"  Status: {response.status_code}")
        print(f"  Message: {error_detail}\n")

        # Step 5: Check email inbox (retrieve verification token from database)
        print("STEP 5: Retrieve verification token from database")
        print("-" * 40)

        token_data = get_verification_token_from_db(user_id)
        if not token_data:
            print("❌ Verification token not found in database")
            return False

        verification_token = token_data["token"]
        print(f"✓ Verification token retrieved")
        print(f"  Token: {verification_token[:20]}...")
        print(f"  Is Used: {token_data['is_used']}")
        print(f"  Expires At: {token_data['expires_at']}\n")

        # Step 6: Click verification link (call /email/verify endpoint)
        print("STEP 6: Verify email with token")
        print("-" * 40)

        response = requests.post(
            f"{AUTH_SERVICE}/email/verify",
            json={
                "token": verification_token
            }
        )

        if response.status_code != 200:
            print(f"❌ Email verification failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False

        verify_result = response.json()
        print(f"✓ Email verified successfully")
        print(f"  Message: {verify_result.get('message', 'N/A')}")
        print(f"  Email: {verify_result.get('email', 'N/A')}\n")

        # Step 7: Verify email_verified=true in database
        print("STEP 7: Verify is_verified=true in database")
        print("-" * 40)

        db_user = get_user_from_db(test_email)
        if not db_user:
            print("❌ User not found in database")
            return False

        if not db_user["is_verified"]:
            print("❌ User is still not verified (expected: true)")
            return False

        print(f"✓ User email verified in database")
        print(f"  Is Verified: {db_user['is_verified']}\n")

        # Step 8: Login successfully
        print("STEP 8: Login successfully")
        print("-" * 40)

        response = requests.post(
            f"{AUTH_SERVICE}/login",
            json={
                "email": test_email,
                "password": test_password,
                "remember_me": False
            }
        )

        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False

        token_data = response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            print("❌ No access token in response")
            return False

        print(f"✓ Login successful")
        print(f"  Access Token: {access_token[:30]}...")
        print(f"  Token Type: {token_data.get('token_type', 'N/A')}\n")

        # Step 9: Verify access granted (call authenticated endpoint)
        print("STEP 9: Verify access granted")
        print("-" * 40)

        response = requests.get(
            f"{AUTH_SERVICE}/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if response.status_code != 200:
            print(f"❌ Failed to access authenticated endpoint: {response.status_code}")
            print(f"Response: {response.text}")
            return False

        me_data = response.json()
        print(f"✓ Authenticated access granted")
        print(f"  Email: {me_data.get('email', 'N/A')}")
        print(f"  Role: {me_data.get('role', 'N/A')}")
        print(f"  Is Verified: {me_data.get('is_verified', 'N/A')}\n")

        # Clean up test user
        cleanup_test_user(test_email)

        print("="*80)
        print("✅ Feature #100: ALL TESTS PASSED")
        print("="*80)
        print("\nValidated behaviors:")
        print("  ✓ Registration creates account with is_verified=false")
        print("  ✓ Email verification token created")
        print("  ✓ Login blocked for unverified email")
        print("  ✓ Correct error message: 'Please verify your email before logging in'")
        print("  ✓ Email verification endpoint sets is_verified=true")
        print("  ✓ Login succeeds after verification")
        print("  ✓ Authenticated access granted")

        return True

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        cleanup_test_user(test_email)
        return False

if __name__ == "__main__":
    success = test_feature_100()
    sys.exit(0 if success else 1)
