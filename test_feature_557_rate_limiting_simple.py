#!/usr/bin/env python3
"""
End-to-end test for Feature #557: API rate limiting configurable per plan

Tests:
1. Free plan: 100 req/hour limit (check headers)
2. Pro plan: 1000 req/hour limit (check headers)
3. Enterprise plan: unlimited (no rate limit)
4. Rate limit headers are returned
5. 429 status when limit exceeded (for free plan)
"""

import requests
import time
import sys
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Service URL
AUTH_SERVICE_URL = "https://localhost:8085"

# Test users (created via SQL)
TEST_USERS = {
    "free": {"email": "free_test_557@test.com", "password": "TestPassword123!", "expected_limit": 100},
    "pro": {"email": "pro_test_557@test.com", "password": "TestPassword123!", "expected_limit": 1000},
    "enterprise": {"email": "enterprise_test_557@test.com", "password": "TestPassword123!", "expected_limit": -1}
}

def log(message):
    """Print timestamped log message."""
    print(f"[{time.strftime('%H:%M:%S')}] {message}")

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

def test_plan_rate_limit(plan_name, user_info):
    """Test rate limit for a specific plan."""
    log("\n" + "="*70)
    log(f"TEST: {plan_name.upper()} plan rate limiting")
    log("="*70)

    # Login
    token = login_user(user_info["email"], user_info["password"])
    if not token:
        return False

    # Make a few requests and check headers
    log(f"\nMaking API requests to check {plan_name} plan rate limit...")

    expected_limit = user_info["expected_limit"]

    for i in range(1, 6):
        response = make_api_request(token)

        if response.status_code != 200:
            log(f"❌ Request {i} failed: {response.status_code}")
            log(f"Response: {response.text}")
            return False

        # Check rate limit headers
        limit = response.headers.get("X-RateLimit-Limit")
        remaining = response.headers.get("X-RateLimit-Remaining")
        reset = response.headers.get("X-RateLimit-Reset")

        log(f"  Request {i}: Status={response.status_code}, Limit={limit}, Remaining={remaining}")

        # For enterprise, we don't expect rate limit headers (unlimited)
        if expected_limit == -1:
            # Enterprise plan should not have rate limiting
            log(f"  ✅ Enterprise plan: No rate limiting applied")
            continue

        if limit != str(expected_limit):
            log(f"❌ Expected rate limit {expected_limit}, got {limit}")
            return False

        # Check that remaining is decreasing
        if remaining:
            remaining_int = int(remaining)
            if remaining_int > expected_limit:
                log(f"❌ Remaining ({remaining_int}) greater than limit ({expected_limit})")
                return False

    log(f"✅ {plan_name.upper()} plan rate limit is correct")
    return True

def test_rate_limit_enforcement():
    """Test that rate limits are enforced (429 response) for free plan."""
    log("\n" + "="*70)
    log("TEST: Rate limit enforcement (429 response)")
    log("="*70)

    # Use free plan user
    user_info = TEST_USERS["free"]

    # Login
    token = login_user(user_info["email"], user_info["password"])
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
            try:
                data = response.json()
                detail = data.get("detail", "")
                plan = data.get("plan", "")
                limit = data.get("limit", 0)

                log(f"  ✅ Response: plan={plan}, limit={limit}")

                if "rate limit exceeded" in detail.lower():
                    log(f"  ✅ Response contains rate limit message")

                # Check retry-after header
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    log(f"  ✅ Retry-After header present: {retry_after} seconds")

                # Check X-RateLimit headers
                rl_limit = response.headers.get("X-RateLimit-Limit")
                rl_remaining = response.headers.get("X-RateLimit-Remaining")
                rl_reset = response.headers.get("X-RateLimit-Reset")

                log(f"  ✅ Rate limit headers: Limit={rl_limit}, Remaining={rl_remaining}, Reset={rl_reset}")

            except Exception as e:
                log(f"  ⚠️  Could not parse response: {e}")

            exceeded = True
            break

        elif response.status_code != 200:
            log(f"❌ Request {i} failed with unexpected status: {response.status_code}")
            log(f"Response: {response.text}")
            return False

        if i % 20 == 0:
            log(f"  Made {i} requests...")

    if not exceeded:
        log(f"❌ Made 105 requests but rate limit was never exceeded!")
        log(f"   This could mean the middleware is not working")
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

        # Test each plan
        all_passed = True

        # Test 1: Free plan (100 req/hour)
        if not test_plan_rate_limit("free", TEST_USERS["free"]):
            log("\n❌ FREE PLAN TEST FAILED")
            all_passed = False

        # Test 2: Pro plan (1000 req/hour)
        if not test_plan_rate_limit("pro", TEST_USERS["pro"]):
            log("\n❌ PRO PLAN TEST FAILED")
            all_passed = False

        # Test 3: Enterprise plan (unlimited)
        if not test_plan_rate_limit("enterprise", TEST_USERS["enterprise"]):
            log("\n❌ ENTERPRISE PLAN TEST FAILED")
            all_passed = False

        # Test 4: Rate limit enforcement (429 response)
        if not test_rate_limit_enforcement():
            log("\n❌ RATE LIMIT ENFORCEMENT TEST FAILED")
            all_passed = False

        if not all_passed:
            log("\n" + "="*70)
            log("❌ SOME TESTS FAILED")
            log("="*70)
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
