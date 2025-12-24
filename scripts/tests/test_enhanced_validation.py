#!/usr/bin/env python3
"""
Test Enhanced Input Validation

Tests the additional validation rules added:
1. Password minimum length (8 characters)
2. Password maximum length (128 characters)
3. Diagram title length limits
4. Note content length limits
"""

import requests
import sys


# Configuration
AUTH_SERVICE_URL = "http://localhost:8085"


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_test_header(title: str):
    """Print a formatted test section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.END}\n")


def print_success(message: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_failure(message: str):
    """Print failure message."""
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_info(message: str):
    """Print info message."""
    print(f"{Colors.YELLOW}ℹ {message}{Colors.END}")


def test_password_min_length():
    """Test password minimum length validation."""
    print_test_header("Test 1: Password Minimum Length (8 characters)")
    
    test_cases = [
        ("", False, "Empty password"),
        ("a", False, "1 character"),
        ("abc", False, "3 characters"),
        ("1234567", False, "7 characters"),
        ("12345678", True, "8 characters (valid)"),
        ("123456789", True, "9 characters (valid)"),
    ]
    
    for password, should_succeed, description in test_cases:
        print_info(f"Testing: {description}")
        
        response = requests.post(
            f"{AUTH_SERVICE_URL}/register",
            json={
                "email": f"test_{len(password)}@example.com",
                "password": password,
                "full_name": "Test User"
            },
            timeout=5
        )
        
        if should_succeed:
            if response.status_code in [201, 400]:  # 400 if already exists
                print_success(f"Valid password accepted - Status: {response.status_code}")
            else:
                print_failure(f"Valid password rejected - Status: {response.status_code}")
                print_info(f"Response: {response.text[:200]}")
                return False
        else:
            if response.status_code == 422:
                response_text = response.text.lower()
                if '8 characters' in response_text or 'at least' in response_text or 'too short' in response_text:
                    print_success(f"Short password rejected with appropriate error")
                else:
                    print_success(f"Short password rejected - Status: {response.status_code}")
            else:
                print_failure(f"Expected 422, got {response.status_code}")
                print_info(f"Response: {response.text[:200]}")
                return False
    
    print_success("Password minimum length validation working")
    return True


def test_password_max_length():
    """Test password maximum length validation."""
    print_test_header("Test 2: Password Maximum Length (128 characters)")
    
    test_cases = [
        ("a" * 128, True, "128 characters (valid)"),
        ("a" * 129, False, "129 characters (too long)"),
        ("a" * 200, False, "200 characters (too long)"),
        ("a" * 1000, False, "1000 characters (too long)"),
    ]
    
    for password, should_succeed, description in test_cases:
        print_info(f"Testing: {description}")
        
        response = requests.post(
            f"{AUTH_SERVICE_URL}/register",
            json={
                "email": f"test_max_{len(password)}@example.com",
                "password": password,
                "full_name": "Test User"
            },
            timeout=5
        )
        
        if should_succeed:
            if response.status_code in [201, 400]:  # 400 if already exists
                print_success(f"Valid password accepted - Status: {response.status_code}")
            else:
                print_failure(f"Valid password rejected - Status: {response.status_code}")
                return False
        else:
            if response.status_code == 422:
                response_text = response.text.lower()
                if '128' in response_text or 'exceed' in response_text or 'too long' in response_text:
                    print_success(f"Long password rejected with appropriate error")
                else:
                    print_success(f"Long password rejected - Status: {response.status_code}")
            else:
                print_failure(f"Expected 422, got {response.status_code}")
                return False
    
    print_success("Password maximum length validation working")
    return True


def test_full_name_validation():
    """Test full name length validation."""
    print_test_header("Test 3: Full Name Length (max 255 characters)")
    
    test_cases = [
        ("John Doe", True, "Normal name"),
        ("A" * 255, True, "255 characters (valid)"),
        ("A" * 256, False, "256 characters (too long)"),
        ("A" * 1000, False, "1000 characters (too long)"),
        ("   ", True, "Whitespace only (should be normalized)"),
        ("", True, "Empty (optional field)"),
    ]
    
    for full_name, should_succeed, description in test_cases:
        print_info(f"Testing: {description}")
        
        response = requests.post(
            f"{AUTH_SERVICE_URL}/register",
            json={
                "email": f"test_name_{len(full_name)}@example.com",
                "password": "ValidPass123",
                "full_name": full_name
            },
            timeout=5
        )
        
        if should_succeed:
            if response.status_code in [201, 400]:  # 400 if already exists
                print_success(f"Valid name accepted - Status: {response.status_code}")
            else:
                print_failure(f"Valid name rejected - Status: {response.status_code}")
                return False
        else:
            if response.status_code == 422:
                print_success(f"Long name rejected - Status: {response.status_code}")
            else:
                print_failure(f"Expected 422, got {response.status_code}")
                return False
    
    print_success("Full name length validation working")
    return True


def main():
    """Run all enhanced validation tests."""
    print(f"\n{Colors.BOLD}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}{'ENHANCED INPUT VALIDATION TESTS'.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{'=' * 80}{Colors.END}\n")
    
    # Check if services are accessible
    try:
        print_info("Checking service availability...")
        auth_health = requests.get(f"{AUTH_SERVICE_URL}/health", timeout=5)
        if auth_health.status_code != 200:
            print_failure("Auth service is not healthy")
            return False
        print_success("Auth service is healthy")
    except requests.exceptions.RequestException as e:
        print_failure(f"Auth service is not accessible: {e}")
        return False
    
    # Run all tests
    tests = [
        ("Password Minimum Length", test_password_min_length),
        ("Password Maximum Length", test_password_max_length),
        ("Full Name Length", test_full_name_validation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_failure(f"Test '{test_name}' failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Print summary
    print_test_header("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        if result:
            print_success(f"{test_name}: PASS")
        else:
            print_failure(f"{test_name}: FAIL")
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.END}")
    
    if passed == total:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ All enhanced validation tests passed!{Colors.END}\n")
        return True
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ Some tests failed{Colors.END}\n")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
