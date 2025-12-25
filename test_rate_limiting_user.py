#!/usr/bin/env python3
"""
Test API Gateway User-Based Rate Limiting (Feature #9)
Tests: 100 requests/min per user
"""

import requests
import time
import json
import sys

BASE_URL = "http://localhost:8080"
AUTH_URL = f"{BASE_URL}/api/auth"

def register_and_login():
    """Register a new test user and get JWT token."""
    timestamp = int(time.time())
    email = f"ratelimit_test_{timestamp}@example.com"
    password = "RateLimit123!@#"

    # Register
    print(f"Registering user: {email}")
    register_response = requests.post(
        f"{AUTH_URL}/register",
        json={
            "email": email,
            "password": password,
            "username": f"ratelimit_user_{timestamp}"
        }
    )

    if register_response.status_code != 201:
        print(f"❌ Registration failed: {register_response.status_code}")
        print(f"Response: {register_response.text}")
        return None

    print(f"✅ User registered successfully")

    # Verify user in database (bypass email verification for testing)
    import subprocess
    verify_cmd = f"docker exec autograph-postgres psql -U autograph -d autograph -c \"UPDATE users SET is_verified = true WHERE email = '{email}';\""
    result = subprocess.run(verify_cmd, shell=True, capture_output=True)

    if result.returncode == 0:
        print(f"✅ User verified in database")
    else:
        print(f"⚠️  Could not verify user (this may cause login to fail)")

    # Login
    print(f"Logging in as {email}")
    login_response = requests.post(
        f"{AUTH_URL}/login",
        json={
            "email": email,
            "password": password
        }
    )

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return None

    data = login_response.json()
    token = data.get("access_token")

    if not token:
        print(f"❌ No access token in response")
        return None

    print(f"✅ Login successful, got JWT token")
    return token

def test_rate_limit(token):
    """Test the 100 requests/minute user-based rate limit."""

    print("\n" + "="*80)
    print("Testing User-Based Rate Limiting: 100 requests/min")
    print("="*80)

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Test endpoint - use a protected route with 100/min user-based limit
    # Use diagrams endpoint which has @limiter.limit("100/minute")
    test_url = f"{BASE_URL}/api/diagrams"

    # Step 1-3: Send 100 requests and verify they all succeed
    print("\n[Step 1-3] Sending 100 requests within 1 minute...")
    success_count = 0
    failed_count = 0
    rate_limited_count = 0

    start_time = time.time()

    for i in range(100):
        try:
            response = requests.get(test_url, headers=headers, timeout=5)

            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited_count += 1
                print(f"Request {i+1}: Rate limited (429)")
            else:
                failed_count += 1
                print(f"Request {i+1}: Failed with {response.status_code}")

            # Show progress every 10 requests
            if (i + 1) % 10 == 0:
                print(f"Progress: {i+1}/100 requests sent ({success_count} succeeded)")

        except Exception as e:
            failed_count += 1
            print(f"Request {i+1}: Exception - {e}")

        # Small delay to avoid overwhelming the server
        time.sleep(0.05)

    elapsed = time.time() - start_time

    print(f"\n✅ Sent 100 requests in {elapsed:.2f} seconds")
    print(f"   Succeeded: {success_count}")
    print(f"   Rate limited: {rate_limited_count}")
    print(f"   Failed: {failed_count}")

    if success_count == 100:
        print("✅ Step 1-3 PASSED: All 100 requests succeeded")
    else:
        print(f"❌ Step 1-3 FAILED: Expected 100 successful, got {success_count}")
        return False

    # Step 4-5: Send 101st request and verify it gets rate limited
    print("\n[Step 4-5] Sending 101st request...")

    try:
        response = requests.get(test_url, headers=headers, timeout=5)

        if response.status_code == 429:
            print(f"✅ Request 101: Rate limited (429 Too Many Requests)")
            print(f"✅ Step 4-5 PASSED: 101st request correctly rate limited")

            # Check for rate limit headers
            if 'X-RateLimit-Limit' in response.headers:
                print(f"   Rate limit: {response.headers.get('X-RateLimit-Limit')}")
            if 'X-RateLimit-Remaining' in response.headers:
                print(f"   Remaining: {response.headers.get('X-RateLimit-Remaining')}")
            if 'X-RateLimit-Reset' in response.headers:
                print(f"   Reset: {response.headers.get('X-RateLimit-Reset')}")
        else:
            print(f"❌ Step 4-5 FAILED: Expected 429, got {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Step 4-5 FAILED: Exception - {e}")
        return False

    # Step 6-7: Wait 1 minute and verify rate limit resets
    print("\n[Step 6-7] Waiting 61 seconds for rate limit to reset...")

    for remaining in range(61, 0, -5):
        print(f"   {remaining} seconds remaining...", end='\r')
        time.sleep(5)

    print("\n   Rate limit window should have reset")

    # Try a new request
    print("\n[Step 7] Sending request after reset...")

    try:
        response = requests.get(test_url, headers=headers, timeout=5)

        if response.status_code == 200:
            print(f"✅ Request succeeded after reset (200 OK)")
            print(f"✅ Step 6-7 PASSED: Rate limit correctly reset")
        else:
            print(f"❌ Step 6-7 FAILED: Expected 200, got {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Step 6-7 FAILED: Exception - {e}")
        return False

    return True

def main():
    """Main test execution."""

    print("="*80)
    print("Feature #9: API Gateway User-Based Rate Limiting Test")
    print("Testing: 100 requests/min per user")
    print("="*80)

    # Step 1: Register and login to get JWT token
    token = register_and_login()

    if not token:
        print("\n❌ FAILED: Could not obtain JWT token")
        sys.exit(1)

    # Run rate limit tests
    if test_rate_limit(token):
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED")
        print("="*80)
        print("\nFeature #9 Status: PASSING")
        print("- User-based rate limiting works correctly")
        print("- 100 requests/min enforced per user")
        print("- Rate limit resets after 1 minute")
        sys.exit(0)
    else:
        print("\n" + "="*80)
        print("❌ TESTS FAILED")
        print("="*80)
        sys.exit(1)

if __name__ == "__main__":
    main()
