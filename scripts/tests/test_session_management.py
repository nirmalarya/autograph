#!/usr/bin/env python3
"""
Test script for Feature #90: Session management with Redis

Tests:
1. Session creation on login
2. Session validation on protected endpoints
3. Session TTL (24 hours = 86400 seconds)
4. Session deletion on logout
5. Session expiry after TTL
"""

import requests
import time
import json
import redis
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8085"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

# Test user credentials
TEST_EMAIL = f"session_test_{int(time.time())}@example.com"
TEST_PASSWORD = "SecurePass123!@#"
TEST_NAME = "Session Test User"

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test(message):
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}{message}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")

def print_success(message):
    print(f"{GREEN}✓ {message}{RESET}")

def print_error(message):
    print(f"{RED}✗ {message}{RESET}")

def print_info(message):
    print(f"{YELLOW}ℹ {message}{RESET}")


def register_user(email, password, name):
    """Register a new user."""
    response = requests.post(
        f"{BASE_URL}/register",
        json={
            "email": email,
            "password": password,
            "full_name": name
        }
    )
    return response


def login_user(email, password):
    """Login and get tokens."""
    response = requests.post(
        f"{BASE_URL}/login",
        json={
            "email": email,
            "password": password
        }
    )
    return response


def get_user_info(access_token):
    """Get current user info (protected endpoint)."""
    response = requests.get(
        f"{BASE_URL}/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    return response


def logout_user(access_token):
    """Logout current session."""
    response = requests.post(
        f"{BASE_URL}/logout",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    return response


def check_redis_session(access_token):
    """Check if session exists in Redis."""
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
        key = f"session:{access_token}"
        
        # Check if key exists
        exists = r.exists(key)
        
        if exists:
            # Get session data
            data = r.get(key)
            session_data = json.loads(data) if data else None
            
            # Get TTL
            ttl = r.ttl(key)
            
            return {
                "exists": True,
                "data": session_data,
                "ttl": ttl
            }
        else:
            return {
                "exists": False,
                "data": None,
                "ttl": -1
            }
    except Exception as e:
        print_error(f"Redis error: {e}")
        return None


def test_session_creation():
    """Test 1: Session creation on login."""
    print_test("TEST 1: Session Creation on Login")
    
    # Register user
    print_info(f"Registering user: {TEST_EMAIL}")
    response = register_user(TEST_EMAIL, TEST_PASSWORD, TEST_NAME)
    if response.status_code != 201:
        print_error(f"Registration failed: {response.status_code} - {response.text}")
        return False
    print_success("User registered successfully")
    
    # Login
    print_info("Logging in...")
    response = login_user(TEST_EMAIL, TEST_PASSWORD)
    if response.status_code != 200:
        print_error(f"Login failed: {response.status_code} - {response.text}")
        return False
    
    tokens = response.json()
    access_token = tokens["access_token"]
    print_success("Login successful")
    print_info(f"Access token: {access_token[:50]}...")
    
    # Check Redis for session
    print_info("Checking Redis for session...")
    session_info = check_redis_session(access_token)
    
    if not session_info:
        print_error("Failed to check Redis")
        return False
    
    if not session_info["exists"]:
        print_error("Session not found in Redis!")
        return False
    
    print_success("Session found in Redis")
    print_info(f"Session data: {json.dumps(session_info['data'], indent=2)}")
    print_info(f"Session TTL: {session_info['ttl']} seconds (~{session_info['ttl']//3600} hours)")
    
    # Verify TTL is approximately 24 hours (86400 seconds)
    # Allow some margin for processing time (within 60 seconds)
    expected_ttl = 86400
    if abs(session_info['ttl'] - expected_ttl) > 60:
        print_error(f"Session TTL is {session_info['ttl']}s, expected ~{expected_ttl}s (24 hours)")
        return False
    
    print_success(f"Session TTL is correct: {session_info['ttl']}s (~24 hours)")
    
    return access_token


def test_session_validation(access_token):
    """Test 2: Session validation on protected endpoints."""
    print_test("TEST 2: Session Validation on Protected Endpoints")
    
    # Access protected endpoint
    print_info("Accessing protected endpoint /me...")
    response = get_user_info(access_token)
    
    if response.status_code != 200:
        print_error(f"Failed to access protected endpoint: {response.status_code} - {response.text}")
        return False
    
    user_info = response.json()
    print_success("Successfully accessed protected endpoint")
    print_info(f"User info: {json.dumps(user_info, indent=2)}")
    
    return True


def test_session_deletion(access_token):
    """Test 3: Session deletion on logout."""
    print_test("TEST 3: Session Deletion on Logout")
    
    # Verify session exists before logout
    print_info("Checking session exists before logout...")
    session_info = check_redis_session(access_token)
    if not session_info or not session_info["exists"]:
        print_error("Session not found before logout!")
        return False
    print_success("Session exists before logout")
    
    # Logout
    print_info("Logging out...")
    response = logout_user(access_token)
    if response.status_code != 200:
        print_error(f"Logout failed: {response.status_code} - {response.text}")
        return False
    print_success("Logout successful")
    
    # Verify session is deleted from Redis
    print_info("Checking session is deleted from Redis...")
    session_info = check_redis_session(access_token)
    if not session_info:
        print_error("Failed to check Redis")
        return False
    
    if session_info["exists"]:
        print_error("Session still exists in Redis after logout!")
        return False
    
    print_success("Session deleted from Redis")
    
    # Try to access protected endpoint with logged out token
    print_info("Trying to access protected endpoint with logged out token...")
    response = get_user_info(access_token)
    if response.status_code == 200:
        print_error("Protected endpoint still accessible after logout!")
        return False
    
    if response.status_code != 401:
        print_error(f"Expected 401 Unauthorized, got {response.status_code}")
        return False
    
    print_success("Protected endpoint correctly returns 401 Unauthorized")
    
    return True


def test_session_expiry():
    """Test 4: Session expiry after TTL."""
    print_test("TEST 4: Session Expiry After TTL")
    
    print_info("Note: This test would require waiting 24 hours or mocking time.")
    print_info("For now, we'll verify the TTL is set correctly and trust Redis expiry.")
    
    # Register and login a new user
    test_email = f"session_expiry_test_{int(time.time())}@example.com"
    print_info(f"Registering user: {test_email}")
    response = register_user(test_email, TEST_PASSWORD, "Expiry Test User")
    if response.status_code != 201:
        print_error(f"Registration failed: {response.status_code}")
        return False
    
    print_info("Logging in...")
    response = login_user(test_email, TEST_PASSWORD)
    if response.status_code != 200:
        print_error(f"Login failed: {response.status_code}")
        return False
    
    access_token = response.json()["access_token"]
    
    # Check session TTL
    print_info("Checking session TTL...")
    session_info = check_redis_session(access_token)
    if not session_info or not session_info["exists"]:
        print_error("Session not found!")
        return False
    
    ttl = session_info["ttl"]
    print_success(f"Session TTL: {ttl} seconds (~{ttl//3600} hours)")
    
    # Wait a few seconds and verify TTL decreases
    print_info("Waiting 5 seconds to verify TTL decreases...")
    time.sleep(5)
    
    session_info_after = check_redis_session(access_token)
    if not session_info_after or not session_info_after["exists"]:
        print_error("Session disappeared!")
        return False
    
    ttl_after = session_info_after["ttl"]
    print_info(f"Session TTL after 5 seconds: {ttl_after} seconds")
    
    # TTL should have decreased by approximately 5 seconds
    ttl_decrease = ttl - ttl_after
    if ttl_decrease < 3 or ttl_decrease > 7:
        print_error(f"TTL decrease is {ttl_decrease}s, expected ~5s")
        return False
    
    print_success(f"TTL correctly decreased by {ttl_decrease} seconds")
    print_success("Session will expire after 24 hours as configured")
    
    return True


def test_multiple_sessions():
    """Test 5: Multiple sessions for same user."""
    print_test("TEST 5: Multiple Sessions for Same User")
    
    # Create a new user
    test_email = f"multi_session_test_{int(time.time())}@example.com"
    print_info(f"Registering user: {test_email}")
    response = register_user(test_email, TEST_PASSWORD, "Multi Session Test")
    if response.status_code != 201:
        print_error(f"Registration failed: {response.status_code}")
        return False
    
    # Login twice to create two sessions
    print_info("Creating first session...")
    response1 = login_user(test_email, TEST_PASSWORD)
    if response1.status_code != 200:
        print_error("First login failed")
        return False
    token1 = response1.json()["access_token"]
    print_success("First session created")
    
    print_info("Creating second session...")
    time.sleep(1)  # Small delay to ensure different tokens
    response2 = login_user(test_email, TEST_PASSWORD)
    if response2.status_code != 200:
        print_error("Second login failed")
        return False
    token2 = response2.json()["access_token"]
    print_success("Second session created")
    
    # Verify both sessions exist in Redis
    print_info("Verifying both sessions exist...")
    session1 = check_redis_session(token1)
    session2 = check_redis_session(token2)
    
    if not session1 or not session1["exists"]:
        print_error("First session not found!")
        return False
    if not session2 or not session2["exists"]:
        print_error("Second session not found!")
        return False
    
    print_success("Both sessions exist in Redis")
    
    # Both tokens should work
    print_info("Testing first token...")
    response = get_user_info(token1)
    if response.status_code != 200:
        print_error("First token doesn't work!")
        return False
    print_success("First token works")
    
    print_info("Testing second token...")
    response = get_user_info(token2)
    if response.status_code != 200:
        print_error("Second token doesn't work!")
        return False
    print_success("Second token works")
    
    # Logout first session
    print_info("Logging out first session...")
    response = logout_user(token1)
    if response.status_code != 200:
        print_error("Logout failed")
        return False
    
    # First token should not work, second should still work
    print_info("Verifying first token is invalid...")
    response = get_user_info(token1)
    if response.status_code != 401:
        print_error("First token still works after logout!")
        return False
    print_success("First token correctly invalidated")
    
    print_info("Verifying second token still works...")
    response = get_user_info(token2)
    if response.status_code != 200:
        print_error("Second token stopped working!")
        return False
    print_success("Second token still works")
    
    return True


def main():
    """Run all tests."""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}Feature #90: Session Management with Redis - Test Suite{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")
    
    results = []
    
    # Test 1: Session creation
    access_token = test_session_creation()
    if access_token:
        results.append(("Session Creation", True))
    else:
        results.append(("Session Creation", False))
        print_error("Test 1 failed, cannot continue with remaining tests")
        print_summary(results)
        return
    
    # Test 2: Session validation
    result = test_session_validation(access_token)
    results.append(("Session Validation", result))
    
    # Test 3: Session deletion
    result = test_session_deletion(access_token)
    results.append(("Session Deletion", result))
    
    # Test 4: Session expiry
    result = test_session_expiry()
    results.append(("Session Expiry", result))
    
    # Test 5: Multiple sessions
    result = test_multiple_sessions()
    results.append(("Multiple Sessions", result))
    
    # Print summary
    print_summary(results)


def print_summary(results):
    """Print test summary."""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}TEST SUMMARY{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")
    
    total = len(results)
    passed = sum(1 for _, result in results if result)
    failed = total - passed
    
    for test_name, result in results:
        if result:
            print_success(f"{test_name}: PASS")
        else:
            print_error(f"{test_name}: FAIL")
    
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}Total: {total} | Passed: {passed} | Failed: {failed}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")
    
    if failed == 0:
        print_success("All tests passed! Feature #90 is working correctly.")
        sys.exit(0)
    else:
        print_error(f"{failed} test(s) failed. Please review the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
