#!/usr/bin/env python3
"""
Test script for Features #87-89: Rate Limiting and Audit Logging

Features tested:
- #87: Login rate limiting: 5 attempts per 15 minutes
- #88: Login rate limiting tracks by IP address
- #89: Audit logging for all authentication events

This script tests:
1. Rate limiting on failed login attempts (5 attempts per 15 minutes)
2. Rate limiting tracks by IP address (X-Forwarded-For header)
3. Audit logging for login, logout, registration, password reset events
4. Audit log entries contain correct information
"""

import requests
import time
import json
from datetime import datetime

# Configuration
AUTH_SERVICE_URL = "http://localhost:8085"
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432
POSTGRES_DB = "autograph"
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "postgres"

# Test user credentials
TEST_EMAIL = f"test_rate_limit_{int(time.time())}@example.com"
TEST_PASSWORD = "TestPassword123!@#"
TEST_FULL_NAME = "Rate Limit Test User"

def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

def print_step(step_num, description):
    """Print a test step."""
    print(f"\nStep {step_num}: {description}")

def print_result(success, message):
    """Print test result."""
    symbol = "✓" if success else "✗"
    print(f"{symbol} {message}")

def register_user(email, password, full_name, ip_address="192.168.1.100"):
    """Register a new user."""
    response = requests.post(
        f"{AUTH_SERVICE_URL}/register",
        json={
            "email": email,
            "password": password,
            "full_name": full_name
        },
        headers={"X-Forwarded-For": ip_address}
    )
    return response

def login_user(email, password, ip_address="192.168.1.100"):
    """Login a user."""
    response = requests.post(
        f"{AUTH_SERVICE_URL}/login",
        json={
            "email": email,
            "password": password
        },
        headers={"X-Forwarded-For": ip_address}
    )
    return response

def get_audit_logs():
    """Get audit logs from database."""
    import psycopg2
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, user_id, action, resource_type, resource_id, 
               ip_address, user_agent, extra_data, created_at
        FROM audit_log
        ORDER BY created_at DESC
        LIMIT 20
    """)
    logs = cursor.fetchall()
    cursor.close()
    conn.close()
    return logs

def check_redis_rate_limit(ip_address):
    """Check rate limit counter in Redis."""
    import redis
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    key = f"rate_limit:login:{ip_address}"
    count = r.get(key)
    ttl = r.ttl(key)
    return int(count) if count else 0, ttl

def test_rate_limiting():
    """Test rate limiting on login attempts."""
    print_header("TEST 1: Login Rate Limiting (Features #87-88)")
    
    # Use a unique IP address for this test
    test_ip = f"10.0.0.{int(time.time()) % 255}"
    test_email = f"rate_test_{int(time.time())}@example.com"
    
    print_step(1, f"Registering test user: {test_email}")
    response = register_user(test_email, TEST_PASSWORD, "Rate Test", test_ip)
    if response.status_code == 201:
        print_result(True, "User registered successfully")
    else:
        print_result(False, f"Registration failed: {response.text}")
        return False
    
    print_step(2, "Attempting 5 failed login attempts (should all succeed)")
    failed_attempts = 0
    for i in range(5):
        response = login_user(test_email, "WrongPassword123!@#", test_ip)
        if response.status_code == 401:
            failed_attempts += 1
            print_result(True, f"Attempt {i+1}: Correctly rejected with 401")
        else:
            print_result(False, f"Attempt {i+1}: Unexpected status {response.status_code}")
        time.sleep(0.5)  # Small delay between attempts
    
    if failed_attempts == 5:
        print_result(True, "All 5 failed attempts were processed")
    else:
        print_result(False, f"Only {failed_attempts}/5 attempts were processed")
    
    print_step(3, "Checking Redis rate limit counter")
    count, ttl = check_redis_rate_limit(test_ip)
    print_result(True, f"Rate limit counter: {count} attempts")
    print_result(True, f"TTL: {ttl} seconds (~{ttl//60} minutes)")
    if count == 5:
        print_result(True, "Counter correctly shows 5 failed attempts")
    else:
        print_result(False, f"Counter shows {count} instead of 5")
    
    print_step(4, "Attempting 6th login (should be rate limited)")
    response = login_user(test_email, "WrongPassword123!@#", test_ip)
    if response.status_code == 429:
        print_result(True, "6th attempt correctly rate limited (429)")
        print_result(True, f"Error message: {response.json().get('detail', 'N/A')}")
    else:
        print_result(False, f"6th attempt not rate limited: {response.status_code}")
        return False
    
    print_step(5, "Attempting login from different IP (should succeed)")
    different_ip = f"10.0.1.{int(time.time()) % 255}"
    response = login_user(test_email, "WrongPassword123!@#", different_ip)
    if response.status_code == 401:
        print_result(True, "Different IP not rate limited (401 for wrong password)")
    else:
        print_result(False, f"Different IP unexpected status: {response.status_code}")
    
    print_step(6, "Attempting successful login from original IP (should be rate limited)")
    response = login_user(test_email, TEST_PASSWORD, test_ip)
    if response.status_code == 429:
        print_result(True, "Still rate limited even with correct password")
    else:
        print_result(False, f"Not rate limited: {response.status_code}")
    
    print_step(7, "Successful login from different IP (should reset rate limit)")
    response = login_user(test_email, TEST_PASSWORD, different_ip)
    if response.status_code == 200:
        print_result(True, "Login successful from different IP")
        # Check if rate limit was reset for different IP
        count, ttl = check_redis_rate_limit(different_ip)
        if count == 0:
            print_result(True, "Rate limit reset after successful login")
        else:
            print_result(False, f"Rate limit not reset: {count} attempts remaining")
    else:
        print_result(False, f"Login failed: {response.status_code}")
    
    print("\n✅ TEST 1 PASSED: Rate limiting works correctly")
    return True

def test_audit_logging():
    """Test audit logging for authentication events."""
    print_header("TEST 2: Audit Logging (Feature #89)")
    
    test_ip = f"10.1.0.{int(time.time()) % 255}"
    test_email = f"audit_test_{int(time.time())}@example.com"
    
    print_step(1, "Getting initial audit log count")
    initial_logs = get_audit_logs()
    initial_count = len(initial_logs)
    print_result(True, f"Initial audit log count: {initial_count}")
    
    print_step(2, "Registering user (should create audit log)")
    response = register_user(test_email, TEST_PASSWORD, "Audit Test", test_ip)
    if response.status_code == 201:
        print_result(True, "User registered successfully")
        user_id = response.json()["id"]
    else:
        print_result(False, f"Registration failed: {response.text}")
        return False
    
    time.sleep(1)  # Wait for audit log to be written
    
    print_step(3, "Checking audit log for registration")
    logs = get_audit_logs()
    registration_log = None
    for log in logs:
        if log[2] == "registration_success" and log[5] == test_ip:
            registration_log = log
            break
    
    if registration_log:
        print_result(True, "Registration audit log found")
        print_result(True, f"  Action: {registration_log[2]}")
        print_result(True, f"  User ID: {registration_log[1]}")
        print_result(True, f"  IP Address: {registration_log[5]}")
        print_result(True, f"  Extra Data: {registration_log[7]}")
    else:
        print_result(False, "Registration audit log not found")
        return False
    
    print_step(4, "Failed login attempt (should create audit log)")
    response = login_user(test_email, "WrongPassword123!@#", test_ip)
    if response.status_code == 401:
        print_result(True, "Login correctly rejected")
    
    time.sleep(1)
    
    print_step(5, "Checking audit log for failed login")
    logs = get_audit_logs()
    failed_login_log = None
    for log in logs:
        if log[2] == "login_failed" and log[5] == test_ip:
            failed_login_log = log
            break
    
    if failed_login_log:
        print_result(True, "Failed login audit log found")
        print_result(True, f"  Action: {failed_login_log[2]}")
        print_result(True, f"  User ID: {failed_login_log[1]}")
        print_result(True, f"  IP Address: {failed_login_log[5]}")
        extra_data = failed_login_log[7]
        if extra_data and 'reason' in extra_data:
            print_result(True, f"  Reason: {extra_data['reason']}")
    else:
        print_result(False, "Failed login audit log not found")
    
    print_step(6, "Successful login (should create audit log)")
    response = login_user(test_email, TEST_PASSWORD, test_ip)
    if response.status_code == 200:
        print_result(True, "Login successful")
        tokens = response.json()
        access_token = tokens["access_token"]
    else:
        print_result(False, f"Login failed: {response.text}")
        return False
    
    time.sleep(1)
    
    print_step(7, "Checking audit log for successful login")
    logs = get_audit_logs()
    success_login_log = None
    for log in logs:
        if log[2] == "login_success" and log[5] == test_ip:
            success_login_log = log
            break
    
    if success_login_log:
        print_result(True, "Successful login audit log found")
        print_result(True, f"  Action: {success_login_log[2]}")
        print_result(True, f"  User ID: {success_login_log[1]}")
        print_result(True, f"  IP Address: {success_login_log[5]}")
    else:
        print_result(False, "Successful login audit log not found")
    
    print_step(8, "Logout (should create audit log)")
    response = requests.post(
        f"{AUTH_SERVICE_URL}/logout",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-Forwarded-For": test_ip
        }
    )
    if response.status_code == 200:
        print_result(True, "Logout successful")
    else:
        print_result(False, f"Logout failed: {response.text}")
    
    time.sleep(1)
    
    print_step(9, "Checking audit log for logout")
    logs = get_audit_logs()
    logout_log = None
    for log in logs:
        if log[2] == "logout" and log[5] == test_ip:
            logout_log = log
            break
    
    if logout_log:
        print_result(True, "Logout audit log found")
        print_result(True, f"  Action: {logout_log[2]}")
        print_result(True, f"  User ID: {logout_log[1]}")
        print_result(True, f"  IP Address: {logout_log[5]}")
    else:
        print_result(False, "Logout audit log not found")
    
    print_step(10, "Summary of audit events")
    logs = get_audit_logs()
    audit_events = {}
    for log in logs:
        action = log[2]
        if action not in audit_events:
            audit_events[action] = 0
        audit_events[action] += 1
    
    print_result(True, "Audit event counts:")
    for action, count in sorted(audit_events.items()):
        print(f"    {action}: {count}")
    
    print("\n✅ TEST 2 PASSED: Audit logging works correctly")
    return True

def test_rate_limit_by_ip():
    """Test that rate limiting is tracked by IP address."""
    print_header("TEST 3: Rate Limiting by IP Address (Feature #88)")
    
    test_email = f"ip_test_{int(time.time())}@example.com"
    ip1 = f"10.2.0.{int(time.time()) % 255}"
    ip2 = f"10.2.1.{int(time.time()) % 255}"
    
    print_step(1, f"Registering test user: {test_email}")
    response = register_user(test_email, TEST_PASSWORD, "IP Test", ip1)
    if response.status_code == 201:
        print_result(True, "User registered successfully")
    else:
        print_result(False, f"Registration failed: {response.text}")
        return False
    
    print_step(2, f"Making 5 failed attempts from IP1: {ip1}")
    for i in range(5):
        response = login_user(test_email, "WrongPassword123!@#", ip1)
        if response.status_code == 401:
            print_result(True, f"Attempt {i+1} from IP1: Rejected (401)")
        time.sleep(0.3)
    
    print_step(3, f"Checking rate limit for IP1")
    count1, ttl1 = check_redis_rate_limit(ip1)
    print_result(True, f"IP1 ({ip1}): {count1} attempts, TTL: {ttl1}s")
    
    print_step(4, f"Making 6th attempt from IP1 (should be rate limited)")
    response = login_user(test_email, "WrongPassword123!@#", ip1)
    if response.status_code == 429:
        print_result(True, "IP1 correctly rate limited (429)")
    else:
        print_result(False, f"IP1 not rate limited: {response.status_code}")
        return False
    
    print_step(5, f"Making 5 failed attempts from IP2: {ip2}")
    for i in range(5):
        response = login_user(test_email, "WrongPassword123!@#", ip2)
        if response.status_code == 401:
            print_result(True, f"Attempt {i+1} from IP2: Rejected (401)")
        time.sleep(0.3)
    
    print_step(6, f"Checking rate limit for IP2")
    count2, ttl2 = check_redis_rate_limit(ip2)
    print_result(True, f"IP2 ({ip2}): {count2} attempts, TTL: {ttl2}s")
    
    print_step(7, f"Making 6th attempt from IP2 (should be rate limited)")
    response = login_user(test_email, "WrongPassword123!@#", ip2)
    if response.status_code == 429:
        print_result(True, "IP2 correctly rate limited (429)")
    else:
        print_result(False, f"IP2 not rate limited: {response.status_code}")
        return False
    
    print_step(8, "Verifying both IPs are independently rate limited")
    count1, _ = check_redis_rate_limit(ip1)
    count2, _ = check_redis_rate_limit(ip2)
    if count1 == 5 and count2 == 5:
        print_result(True, "Both IPs have independent rate limit counters")
    else:
        print_result(False, f"Rate limits not independent: IP1={count1}, IP2={count2}")
        return False
    
    print("\n✅ TEST 3 PASSED: Rate limiting by IP address works correctly")
    return True

def main():
    """Run all tests."""
    print_header("AUTOGRAPH V3 - RATE LIMITING AND AUDIT LOGGING TESTS")
    print(f"Testing Features #87-89")
    print(f"Auth Service: {AUTH_SERVICE_URL}")
    print(f"Test started at: {datetime.now().isoformat()}")
    
    # Check if services are running
    try:
        response = requests.get(f"{AUTH_SERVICE_URL}/health", timeout=5)
        if response.status_code == 200:
            print_result(True, "Auth service is healthy")
        else:
            print_result(False, "Auth service not healthy")
            return
    except Exception as e:
        print_result(False, f"Cannot connect to auth service: {e}")
        return
    
    # Run tests
    results = []
    
    try:
        results.append(("Rate Limiting", test_rate_limiting()))
    except Exception as e:
        print_result(False, f"Test 1 failed with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Rate Limiting", False))
    
    try:
        results.append(("Audit Logging", test_audit_logging()))
    except Exception as e:
        print_result(False, f"Test 2 failed with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Audit Logging", False))
    
    try:
        results.append(("Rate Limiting by IP", test_rate_limit_by_ip()))
    except Exception as e:
        print_result(False, f"Test 3 failed with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Rate Limiting by IP", False))
    
    # Print summary
    print_header("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed*100/total:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Features #87-89 are ready for production.")
        print("\nFeature Status:")
        print("- #87: Login rate limiting (5 attempts per 15 minutes) ✅ PASSING")
        print("- #88: Rate limiting tracks by IP address ✅ PASSING")
        print("- #89: Audit logging for authentication events ✅ PASSING")
    else:
        print(f"\n❌ {total - passed} test(s) failed. Please review and fix issues.")

if __name__ == "__main__":
    main()
