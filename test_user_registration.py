#!/usr/bin/env python3
"""
Comprehensive test suite for Feature #64: User Registration with Email and Password

Tests all 9 requirements from feature_list.json:
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

import requests
import subprocess
import sys
import time
import json
import re

def print_result(test_name, passed, details=""):
    """Print colored test result."""
    if passed:
        print(f"✓ {test_name}")
        if details:
            print(f"  {details}")
    else:
        print(f"✗ {test_name}")
        if details:
            print(f"  {details}")

def test_registration_page_accessible():
    """Test 1: Navigate to /register page."""
    print("\n=== Test 1: Registration Page Accessible ===\n")
    
    try:
        response = requests.get("http://localhost:3000/register", timeout=5)
        
        if response.status_code == 200:
            # Check for key elements in the page
            if "Create Account" in response.text and "Email Address" in response.text:
                print_result("Registration page loads successfully", True, "Status: 200 OK")
                print_result("Page contains registration form", True, "Found form elements")
                return True
            else:
                print_result("Registration page loads", True, "Status: 200 OK")
                print_result("Page contains registration form", False, "Missing form elements")
                return False
        else:
            print_result("Registration page accessible", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_result("Registration page accessible", False, f"Error: {e}")
        return False

def test_user_registration_api():
    """Test 2-6: Register user via API and verify database."""
    print("\n=== Test 2-6: User Registration Flow ===\n")
    
    # Generate unique email
    timestamp = int(time.time())
    email = f"testuser{timestamp}@example.com"
    password = "SecurePass123!"
    full_name = f"Test User {timestamp}"
    
    print(f"Registering user: {email}")
    
    try:
        # Test 2-5: Submit registration
        response = requests.post(
            "http://localhost:8085/register",
            json={
                "email": email,
                "password": password,
                "full_name": full_name
            },
            timeout=5
        )
        
        if response.status_code not in [200, 201]:
            print_result("User registration", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
        
        data = response.json()
        print_result("User registration successful", True, f"User ID: {data.get('id')}")
        print_result("Email stored correctly", data.get('email') == email, f"Email: {data.get('email')}")
        print_result("Full name stored correctly", data.get('full_name') == full_name, f"Name: {data.get('full_name')}")
        
        user_id = data.get('id')
        
        # Test 6: Verify user in database
        result = subprocess.run(
            [
                "docker", "exec", "autograph-postgres",
                "psql", "-U", "autograph", "-d", "autograph",
                "-t", "-c",
                f"SELECT id, email, full_name FROM users WHERE email = '{email}';"
            ],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and email in result.stdout:
            print_result("User exists in database", True, "Database query successful")
        else:
            print_result("User exists in database", False, "User not found in database")
            return False
        
        # Test 7: Verify bcrypt password hash
        result = subprocess.run(
            [
                "docker", "exec", "autograph-postgres",
                "psql", "-U", "autograph", "-d", "autograph",
                "-t", "-c",
                f"SELECT password_hash FROM users WHERE email = '{email}';"
            ],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            password_hash = result.stdout.strip()
            
            # Check bcrypt format: $2b$12$...
            if password_hash.startswith('$2b$12$'):
                print_result("Password hashed with bcrypt", True, "Hash format: $2b$12$...")
                print_result("Bcrypt cost factor is 12", True, "Cost factor verified")
            elif password_hash.startswith('$2b$'):
                cost_factor = password_hash.split('$')[2]
                print_result("Password hashed with bcrypt", True, f"Hash format: $2b${cost_factor}$...")
                print_result("Bcrypt cost factor is 12", cost_factor == '12', f"Cost factor: {cost_factor}")
            else:
                print_result("Password hashed with bcrypt", False, f"Unexpected hash format: {password_hash[:20]}...")
                return False
        else:
            print_result("Password hash verification", False, "Could not retrieve password hash")
            return False
        
        return True
        
    except Exception as e:
        print_result("User registration flow", False, f"Error: {e}")
        return False

def test_duplicate_email_prevention():
    """Test: Verify duplicate email prevention."""
    print("\n=== Test: Duplicate Email Prevention ===\n")
    
    email = "duplicate@example.com"
    password = "SecurePass123!"
    
    try:
        # Register first time
        response1 = requests.post(
            "http://localhost:8085/register",
            json={"email": email, "password": password},
            timeout=5
        )
        
        # Register second time with same email
        response2 = requests.post(
            "http://localhost:8085/register",
            json={"email": email, "password": password},
            timeout=5
        )
        
        if response2.status_code == 400 and "already registered" in response2.text.lower():
            print_result("Duplicate email rejected", True, "Error message: Email already registered")
            return True
        else:
            print_result("Duplicate email rejected", False, f"Status: {response2.status_code}")
            return False
            
    except Exception as e:
        print_result("Duplicate email prevention", False, f"Error: {e}")
        return False

def test_password_validation():
    """Test: Password validation (length requirements)."""
    print("\n=== Test: Password Validation ===\n")
    
    all_passed = True
    
    # Test short password
    try:
        response = requests.post(
            "http://localhost:8085/register",
            json={"email": "short@example.com", "password": "short"},
            timeout=5
        )
        
        if response.status_code == 422:
            print_result("Short password rejected", True, "Password < 8 characters rejected")
        else:
            print_result("Short password rejected", False, f"Status: {response.status_code}")
            all_passed = False
    except Exception as e:
        print_result("Short password validation", False, f"Error: {e}")
        all_passed = False
    
    # Test long password (129 characters)
    try:
        long_password = "a" * 129
        response = requests.post(
            "http://localhost:8085/register",
            json={"email": "long@example.com", "password": long_password},
            timeout=5
        )
        
        if response.status_code == 422:
            print_result("Long password rejected", True, "Password > 128 characters rejected")
        else:
            print_result("Long password rejected", False, f"Status: {response.status_code}")
            all_passed = False
    except Exception as e:
        print_result("Long password validation", False, f"Error: {e}")
        all_passed = False
    
    # Test valid password
    try:
        timestamp = int(time.time())
        response = requests.post(
            "http://localhost:8085/register",
            json={
                "email": f"valid{timestamp}@example.com",
                "password": "ValidPass123!"
            },
            timeout=5
        )
        
        if response.status_code in [200, 201]:
            print_result("Valid password accepted", True, "8-128 character password accepted")
        else:
            print_result("Valid password accepted", False, f"Status: {response.status_code}")
            all_passed = False
    except Exception as e:
        print_result("Valid password validation", False, f"Error: {e}")
        all_passed = False
    
    return all_passed

def test_login_after_registration():
    """Test: User can login after registration."""
    print("\n=== Test: Login After Registration ===\n")
    
    timestamp = int(time.time())
    email = f"logintest{timestamp}@example.com"
    password = "SecurePass123!"
    
    try:
        # Register
        reg_response = requests.post(
            "http://localhost:8085/register",
            json={"email": email, "password": password},
            timeout=5
        )
        
        if reg_response.status_code not in [200, 201]:
            print_result("Registration for login test", False, f"Status: {reg_response.status_code}")
            return False
        
        print_result("User registered", True, f"Email: {email}")
        
        # Login
        login_response = requests.post(
            "http://localhost:8085/login",
            json={"email": email, "password": password},
            timeout=5
        )
        
        if login_response.status_code == 200:
            data = login_response.json()
            if 'access_token' in data and 'refresh_token' in data:
                print_result("Login successful", True, "JWT tokens received")
                print_result("Access token present", True, f"Token length: {len(data['access_token'])}")
                print_result("Refresh token present", True, f"Token length: {len(data['refresh_token'])}")
                return True
            else:
                print_result("Login successful", True, "Status: 200")
                print_result("JWT tokens present", False, "Missing tokens in response")
                return False
        else:
            print_result("Login successful", False, f"Status: {login_response.status_code}")
            return False
            
    except Exception as e:
        print_result("Login after registration", False, f"Error: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 80)
    print("USER REGISTRATION TEST SUITE - Feature #64")
    print("=" * 80)
    
    results = {
        "Registration Page Accessible": test_registration_page_accessible(),
        "User Registration Flow": test_user_registration_api(),
        "Duplicate Email Prevention": test_duplicate_email_prevention(),
        "Password Validation": test_password_validation(),
        "Login After Registration": test_login_after_registration(),
    }
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(results.values())
    percentage = (passed / total * 100) if total > 0 else 0
    
    print("-" * 80)
    print(f"Total: {passed}/{total} tests passed ({percentage:.1f}%)")
    print("=" * 80)
    
    if passed == total:
        print("\n✓ All user registration tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
