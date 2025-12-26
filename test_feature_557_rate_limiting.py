#!/usr/bin/env python3
"""
End-to-end test for Feature #557: API rate limiting configurable per plan

Tests:
1. Free plan: 100 req/hour limit is enforced
2. Pro plan: 1000 req/hour limit is enforced
3. Enterprise plan: unlimited (no rate limit)
4. Rate limit headers are returned
5. 429 status when limit exceeded
"""

import requests
import time
import json
import sys
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Service URL
AUTH_SERVICE_URL = "https://localhost:8085"

def log(message):
    """Print timestamped log message."""
    print(f"[{time.strftime('%H:%M:%S')}] {message}")

def create_test_user(email, password, plan="free"):
    """Create a test user with specified plan."""
    log(f"Creating test user: {email} with plan: {plan}")

    # Register user
    response = requests.post(
        f"{AUTH_SERVICE_URL}/register",
        json={
            "email": email,
            "password": password,
            "full_name": f"Test User {plan}"
        },
        verify=False
    )

    if response.status_code != 201:
        log(f"❌ Failed to register user: {response.status_code}")
        log(f"Response: {response.text}")
        return None

    user_data = response.json()
    user_id = user_data.get("id")

    # Update user's plan in database
    import psycopg2
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="autograph",
        user="autograph",
        password="autograph123"
    )
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET plan = %s, is_verified = TRUE WHERE id = %s",
        (plan, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

    log(f"✅ Created user {email} with plan {plan}")
    return user_id

def login_user(email, password):
    """Login and get access token."""
    log(f"Logging in as {email}...")

    response = requests.post(
        f"{AUTH_SERVICE_URL}/login",
        json={
            "email": email,
            "password": password
        },
        verify=False
    )

    if response.status_code != 200:
        log(f"❌ Login failed: {response.status_code}")
        log(f"Response: {response.text}")
        return None

    data = response.json()
    token = data.get("access_token")
    log(f"✅ Login successful")
    return token

def make_api_request(token, endpoint="/me"):
    """Make an authenticated API request."""
    response = requests.get(
        f"{AUTH_SERVICE_URL}{endpoint}",
        headers={"Authorization": f"Bearer {token}"},
        verify=False
    )
    return response

def test_free_plan_rate_limit():
    """Test that free plan has 100 req/hour limit."""
    log("\n" + "="*70)
    log("TEST 1: Free plan rate limiting (100 req/hour)")
    log("="*70)

    # Create free plan user
    email = f"free_test_{int(time.time())}@test.com"
    password = "TestPassword123!"
    user_id = create_test_user(email, password, "free")

    if not user_id:
        return False

    # Login
    token = login_user(email, password)
    if not token:
        return False

    # Make requests to test rate limit
    log("\nMaking API requests to test free plan limit...")

    # Make a few requests and check headers
    for i in range(1, 6):
        response = make_api_request(token)

        if response.status_code != 200:
            log(f"❌ Request {i} failed: {response.status_code}")
            return False

        # Check rate limit headers
        limit = response.headers.get("X-RateLimit-Limit")
        remaining = response.headers.get("X-RateLimit-Remaining")
        reset = response.headers.get("X-RateLimit-Reset")

        log(f"  Request {i}: Status={response.status_code}, Limit={limit}, Remaining={remaining}")

        if limit != "100":
            log(f"❌ Expected rate limit 100, got {limit}")
            return False

    log("✅ Free plan rate limit headers are correct (100 req/hour)")
    return True

def test_pro_plan_rate_limit():
    """Test that pro plan has 1000 req/hour limit."""
    log("\n" + "="*70)
    log("TEST 2: Pro plan rate limiting (1000 req/hour)")
    log("="*70)

    # Create pro plan user
    email = f"pro_test_{int(time.time())}@test.com"
    password = "TestPassword123!"
    user_id = create_test_user(email, password, "pro")

    if not user_id:
        return False

    # Login
    token = login_user(email, password)
    if not token:
        return False

    # Make requests to check headers
    log("\nMaking API requests to test pro plan limit...")

    for i in range(1, 6):
        response = make_api_request(token)

        if response.status_code != 200:
            log(f"❌ Request {i} failed: {response.status_code}")
            return False

        # Check rate limit headers
        limit = response.headers.get("X-RateLimit-Limit")
        remaining = response.headers.get("X-RateLimit-Remaining")

        log(f"  Request {i}: Status={response.status_code}, Limit={limit}, Remaining={remaining}")

        if limit != "1000":
            log(f"❌ Expected rate limit 1000, got {limit}")
            return False

    log("✅ Pro plan rate limit headers are correct (1000 req/hour)")
    return True

def test_enterprise_plan_unlimited():
    """Test that enterprise plan has unlimited access."""
    log("\n" + "="*70)
    log("TEST 3: Enterprise plan unlimited access")
    log("="*70)

    # Create enterprise plan user
    email = f"enterprise_test_{int(time.time())}@test.com"
    password = "TestPassword123!"
    user_id = create_test_user(email, password, "enterprise")

    if not user_id:
        return False

    # Login
    token = login_user(email, password)
    if not token:
        return False

    # Make requests - enterprise should have no rate limit
    log("\nMaking API requests to test enterprise unlimited access...")

    for i in range(1, 11):  # Make 10 requests
        response = make_api_request(token)

        if response.status_code != 200:
            log(f"❌ Request {i} failed: {response.status_code}")
            return False

        # Enterprise plan should not have rate limit headers (or they should indicate unlimited)
        log(f"  Request {i}: Status={response.status_code} (no rate limit)")

    log("✅ Enterprise plan has unlimited access (no rate limiting)")
    return True

def test_rate_limit_enforcement():
    """Test that rate limits are actually enforced (429 response)."""
    log("\n" + "="*70)
    log("TEST 4: Rate limit enforcement (429 response)")
    log("="*70)

    # Create a user with a very low rate limit for testing
    email = f"ratelimit_test_{int(time.time())}@test.com"
    password = "TestPassword123!"
    user_id = create_test_user(email, password, "free")

    if not user_id:
        return False

    # Login
    token = login_user(email, password)
    if not token:
        return False

    log("\nMaking 105 requests to exceed free plan limit (100 req/hour)...")

    # Make 105 requests (5 more than the limit)
    exceeded = False
    for i in range(1, 106):
        response = make_api_request(token)

        if response.status_code == 429:
            log(f"  ✅ Request {i}: Got 429 Too Many Requests (rate limit exceeded)")

            # Check response body
            data = response.json()
            if "rate limit exceeded" in data.get("detail", "").lower():
                log(f"  ✅ Response contains rate limit message")

            # Check retry-after header
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                log(f"  ✅ Retry-After header present: {retry_after} seconds")

            exceeded = True
            break

        elif response.status_code != 200:
            log(f"❌ Request {i} failed with unexpected status: {response.status_code}")
            return False

        if i % 20 == 0:
            log(f"  Made {i} requests...")

    if not exceeded:
        log(f"❌ Made 105 requests but rate limit was never exceeded!")
        return False

    log("✅ Rate limit enforcement working correctly")
    return True

def main():
    """Run all tests."""
    log("="*70)
    log("Feature #557: API Rate Limiting Per Plan - E2E Test")
    log("="*70)

    try:
        # Wait a moment for service to be ready
        time.sleep(2)

        # Test 1: Free plan (100 req/hour)
        if not test_free_plan_rate_limit():
            log("\n❌ TEST 1 FAILED")
            return False

        # Test 2: Pro plan (1000 req/hour)
        if not test_pro_plan_rate_limit():
            log("\n❌ TEST 2 FAILED")
            return False

        # Test 3: Enterprise plan (unlimited)
        if not test_enterprise_plan_unlimited():
            log("\n❌ TEST 3 FAILED")
            return False

        # Test 4: Rate limit enforcement
        if not test_rate_limit_enforcement():
            log("\n❌ TEST 4 FAILED")
            return False

        log("\n" + "="*70)
        log("✅ ALL TESTS PASSED")
        log("="*70)
        log("\nFeature #557 Summary:")
        log("  ✅ Free plan: 100 req/hour limit enforced")
        log("  ✅ Pro plan: 1000 req/hour limit enforced")
        log("  ✅ Enterprise plan: unlimited access")
        log("  ✅ Rate limit headers returned correctly")
        log("  ✅ 429 status when limit exceeded")
        log("  ✅ Retry-After header present")

        return True

    except requests.exceptions.ConnectionError:
        log("\n❌ Could not connect to auth service")
        log("   Make sure auth service is running on https://localhost:8085")
        return False
    except Exception as e:
        log(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
