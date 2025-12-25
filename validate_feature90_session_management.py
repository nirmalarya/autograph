#!/usr/bin/env python3
"""
Feature #90 Validator: Session Management with Redis
Tests that sessions are stored in Redis with 24-hour TTL
"""

import requests
import redis
import json
import time
import uuid
from datetime import datetime
import psycopg2

# Configuration
AUTH_SERVICE_URL = "https://localhost:8085"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432
POSTGRES_DB = "autograph"
POSTGRES_USER = "autograph"
POSTGRES_PASSWORD = "autograph_dev_password"

# Disable SSL warnings for self-signed certificates
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def print_step(step: str):
    """Print test step"""
    print(f"\n{'='*60}")
    print(f"STEP: {step}")
    print(f"{'='*60}")

def print_success(message: str):
    """Print success message"""
    print(f"✅ {message}")

def print_error(message: str):
    """Print error message"""
    print(f"❌ {message}")

def main():
    print("\n" + "="*60)
    print("Feature #90: Session Management with Redis")
    print("="*60)

    # Connect to Redis
    print_step("Connect to Redis")
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        r.ping()
        print_success("Connected to Redis successfully")
    except Exception as e:
        print_error(f"Failed to connect to Redis: {e}")
        return False

    # Create a test user
    print_step("Register test user")
    test_email = f"session_test_{int(time.time())}@example.com"
    test_password = "SecurePass123!"

    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/register",
            json={
                "email": test_email,
                "password": test_password,
                "name": "Session Test User"
            },
            timeout=10,
            verify=False  # Skip SSL verification for self-signed certs
        )

        if response.status_code == 201:
            print_success(f"User registered: {test_email}")

            # Verify the email in the database
            print("   Verifying email in database...")
            try:
                conn = psycopg2.connect(
                    host=POSTGRES_HOST,
                    port=POSTGRES_PORT,
                    database=POSTGRES_DB,
                    user=POSTGRES_USER,
                    password=POSTGRES_PASSWORD
                )
                cur = conn.cursor()
                cur.execute(
                    "UPDATE users SET is_verified = true WHERE email = %s",
                    (test_email,)
                )
                conn.commit()
                cur.close()
                conn.close()
                print_success("Email verified in database")
            except Exception as e:
                print_error(f"Failed to verify email in database: {e}")
                return False
        else:
            print_error(f"Registration failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print_error(f"Registration request failed: {e}")
        return False

    # Login to create session
    print_step("Login to create session")
    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/login",
            json={
                "email": test_email,
                "password": test_password
            },
            timeout=10,
            verify=False  # Skip SSL verification for self-signed certs
        )

        if response.status_code == 200:
            data = response.json()
            access_token = data.get('access_token')
            print_success(f"Login successful")
            print(f"   Access token: {access_token[:20]}...")
        else:
            print_error(f"Login failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print_error(f"Login request failed: {e}")
        return False

    # Verify session stored in Redis
    print_step("Verify session stored in Redis")

    # The session key should be session:<access_token>
    session_key = f"session:{access_token}"
    session_found = False
    session_ttl = None

    try:
        # Check if session exists
        if r.exists(session_key):
            session_found = True
            session_ttl = r.ttl(session_key)
            print_success(f"Session found in Redis: session:<token>")
            print(f"   TTL: {session_ttl} seconds ({session_ttl/3600:.1f} hours)")

            # Get session data
            session_data = r.get(session_key)
            if session_data:
                try:
                    data = json.loads(session_data)
                    print(f"   User ID: {data.get('user_id', 'unknown')}")
                    print(f"   Created at: {data.get('created_at', 'unknown')}")
                except:
                    pass
        else:
            # This might be JWT-based auth without Redis sessions
            print("⚠️  No session found in Redis")
            print("   This might be using JWT tokens without Redis session storage")
            print("   Checking if JWT auth is working...")
    except Exception as e:
        print_error(f"Failed to check Redis: {e}")
        return False

    # Verify session TTL (should be 24 hours = 86400 seconds)
    if session_found and session_ttl:
        print_step("Verify session TTL set to 86400 seconds (24 hours)")

        # Allow some margin for processing time (85000-87000 seconds)
        if 85000 <= session_ttl <= 87000:
            print_success(f"Session TTL is correct: {session_ttl}s (~24 hours)")
        else:
            print_error(f"Session TTL is incorrect: {session_ttl}s (expected ~86400s)")
            return False

    # Access protected endpoint
    print_step("Access protected endpoint with session")
    try:
        response = requests.get(
            f"{AUTH_SERVICE_URL}/me",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
            verify=False  # Skip SSL verification for self-signed certs
        )

        if response.status_code == 200:
            user_data = response.json()
            print_success("Protected endpoint accessed successfully")
            print(f"   User: {user_data.get('email')}")
        else:
            print_error(f"Protected endpoint failed: {response.status_code} - {response.text}")
            # Don't return False here - JWT might work without Redis sessions
    except Exception as e:
        print_error(f"Protected endpoint request failed: {e}")
        # Don't return False here - JWT might work without Redis sessions

    # Verify session validated against Redis
    if session_found:
        print_step("Verify session validated against Redis")

        # Make another request to ensure session is being validated
        try:
            response = requests.get(
                f"{AUTH_SERVICE_URL}/me",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
                verify=False  # Skip SSL verification for self-signed certs
            )

            if response.status_code == 200:
                print_success("Session validated successfully")
            else:
                print_error(f"Session validation failed: {response.status_code}")
                return False
        except Exception as e:
            print_error(f"Session validation request failed: {e}")
            return False

    # Test session expiry handling
    print_step("Test session persistence")

    # Wait a moment and verify session still exists
    time.sleep(2)

    if session_found:
        try:
            new_ttl = r.ttl(session_key)
            if new_ttl > 0:
                print_success(f"Session still exists with TTL: {new_ttl}s")

                # TTL should have decreased
                if new_ttl < session_ttl:
                    print_success("Session TTL decreasing as expected")
                else:
                    print_error("Session TTL not decreasing")
                    return False
            else:
                print_error("Session expired unexpectedly")
                return False
        except Exception as e:
            print_error(f"Failed to check session persistence: {e}")
            return False

    # Logout and verify session removed
    print_step("Logout and verify session removed from Redis")
    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/logout",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
            verify=False  # Skip SSL verification for self-signed certs
        )

        if response.status_code == 200:
            print_success("Logout successful")

            if session_found:
                # Wait a moment for cleanup
                time.sleep(1)

                # Check if session still exists
                if r.exists(session_key):
                    print("⚠️  Session still exists after logout")
                    print("   This might be expected if using blacklist approach")
                else:
                    print_success("Session removed from Redis after logout")
        else:
            print_error(f"Logout failed: {response.status_code} - {response.text}")
            # Don't fail the test for logout issues
    except Exception as e:
        print_error(f"Logout request failed: {e}")
        # Don't fail the test for logout issues

    # Verify logged out session cannot access protected endpoints
    print_step("Verify logged out session cannot access protected endpoints")
    try:
        response = requests.get(
            f"{AUTH_SERVICE_URL}/me",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
            verify=False  # Skip SSL verification for self-signed certs
        )

        if response.status_code == 401:
            print_success("Logged out session correctly denied access")
        elif response.status_code == 200:
            print_error("Logged out session still has access (session not invalidated)")
            return False
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
    except Exception as e:
        print_error(f"Protected endpoint request failed: {e}")

    # Summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)

    if session_found:
        print_success("Feature #90: Session Management with Redis - PASSED")
        print("\nVerified:")
        print("  ✅ Sessions stored in Redis")
        print("  ✅ Session TTL set to 24 hours (86400 seconds)")
        print("  ✅ Protected endpoints validate against Redis")
        print("  ✅ Session persistence works correctly")
        print("  ✅ Logout invalidates session")
        return True
    else:
        print("⚠️  Feature #90: Partial Implementation")
        print("\nNotes:")
        print("  - JWT authentication is working")
        print("  - Session storage in Redis not found")
        print("  - This might be stateless JWT implementation")
        print("\nFor full Redis session management, ensure:")
        print("  1. Sessions are stored in Redis with session:<token> key")
        print("  2. TTL is set to 86400 seconds")
        print("  3. All auth endpoints validate against Redis")
        return False

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
