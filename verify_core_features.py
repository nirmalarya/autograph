#!/usr/bin/env python3
"""
Verification test for core features before implementing new ones.
Tests Features #64, #68, #116, #117, #119, #145
"""

import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8080"
TEST_USER_EMAIL = f"verify_test_{int(time.time())}@example.com"
TEST_USER_PASSWORD = "SecurePassword123!"

def print_test(test_name, passed, details=""):
    """Print test result with formatting"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"    {details}")
    print()

def test_user_registration():
    """Test Feature #64: User registration"""
    print("=" * 80)
    print("TEST 1: User Registration (Feature #64)")
    print("=" * 80)
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/auth/register",
            json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
                "full_name": "Verification Test User"
            },
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            print_test(
                "User Registration", 
                True, 
                f"User created: {data.get('email', 'N/A')}"
            )
            return True
        else:
            print_test(
                "User Registration", 
                False, 
                f"Status: {response.status_code}, Response: {response.text[:200]}"
            )
            return False
    except Exception as e:
        print_test("User Registration", False, f"Error: {str(e)}")
        return False

def test_user_login():
    """Test Feature #68: User login"""
    print("=" * 80)
    print("TEST 2: User Login (Feature #68)")
    print("=" * 80)
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/auth/login",
            json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get('access_token')
            if access_token:
                print_test(
                    "User Login", 
                    True, 
                    f"Token received (length: {len(access_token)})"
                )
                return access_token
            else:
                print_test("User Login", False, "No access_token in response")
                return None
        else:
            print_test(
                "User Login", 
                False, 
                f"Status: {response.status_code}, Response: {response.text[:200]}"
            )
            return None
    except Exception as e:
        print_test("User Login", False, f"Error: {str(e)}")
        return None

def test_create_diagram(token):
    """Test Feature #116: Create diagram"""
    print("=" * 80)
    print("TEST 3: Create Diagram (Feature #116)")
    print("=" * 80)
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/diagrams",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Verification Test Diagram",
                "type": "canvas",
                "canvas_data": {"shapes": [], "version": 1},
                "note_content": "This is a test diagram for verification"
            },
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            diagram_id = data.get('id')
            print_test(
                "Create Diagram", 
                True, 
                f"Diagram created: {diagram_id}"
            )
            return diagram_id
        else:
            print_test(
                "Create Diagram", 
                False, 
                f"Status: {response.status_code}, Response: {response.text[:200]}"
            )
            return None
    except Exception as e:
        print_test("Create Diagram", False, f"Error: {str(e)}")
        return None

def test_list_diagrams(token):
    """Test Feature #117: List diagrams"""
    print("=" * 80)
    print("TEST 4: List Diagrams (Feature #117)")
    print("=" * 80)
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/diagrams",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            diagrams = data.get('diagrams', [])
            total = data.get('total', 0)
            print_test(
                "List Diagrams", 
                True, 
                f"Found {total} diagrams, returned {len(diagrams)} in page"
            )
            return True
        else:
            print_test(
                "List Diagrams", 
                False, 
                f"Status: {response.status_code}, Response: {response.text[:200]}"
            )
            return False
    except Exception as e:
        print_test("List Diagrams", False, f"Error: {str(e)}")
        return False

def test_get_diagram(token, diagram_id):
    """Test Feature #119: Get diagram by ID"""
    print("=" * 80)
    print("TEST 5: Get Diagram by ID (Feature #119)")
    print("=" * 80)
    
    if not diagram_id:
        print_test("Get Diagram by ID", False, "No diagram ID available")
        return False
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/diagrams/{diagram_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            title = data.get('title', 'N/A')
            print_test(
                "Get Diagram by ID", 
                True, 
                f"Retrieved diagram: {title}"
            )
            return True
        else:
            print_test(
                "Get Diagram by ID", 
                False, 
                f"Status: {response.status_code}, Response: {response.text[:200]}"
            )
            return False
    except Exception as e:
        print_test("Get Diagram by ID", False, f"Error: {str(e)}")
        return False

def test_full_text_search(token):
    """Test Feature #145: Full-text search"""
    print("=" * 80)
    print("TEST 6: Full-Text Search (Feature #145)")
    print("=" * 80)
    
    try:
        # Search for the diagram we created
        response = requests.get(
            f"{API_BASE_URL}/api/diagrams",
            headers={"Authorization": f"Bearer {token}"},
            params={"search": "Verification"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            diagrams = data.get('diagrams', [])
            total = data.get('total', 0)
            
            # Check if our test diagram is in the results
            found = any(d.get('title', '').startswith('Verification') for d in diagrams)
            
            if found:
                print_test(
                    "Full-Text Search", 
                    True, 
                    f"Search returned {total} results, test diagram found"
                )
                return True
            else:
                print_test(
                    "Full-Text Search", 
                    False, 
                    f"Search returned {total} results, but test diagram not found"
                )
                return False
        else:
            print_test(
                "Full-Text Search", 
                False, 
                f"Status: {response.status_code}, Response: {response.text[:200]}"
            )
            return False
    except Exception as e:
        print_test("Full-Text Search", False, f"Error: {str(e)}")
        return False

def main():
    """Run all verification tests"""
    print("\n")
    print("=" * 80)
    print("CORE FEATURES VERIFICATION TEST")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API Base URL: {API_BASE_URL}")
    print("=" * 80)
    print("\n")
    
    results = []
    
    # Test 1: User Registration
    results.append(("User Registration", test_user_registration()))
    
    # Test 2: User Login
    token = test_user_login()
    results.append(("User Login", token is not None))
    
    if not token:
        print("\n❌ Cannot continue tests without valid token\n")
        return
    
    # Test 3: Create Diagram
    diagram_id = test_create_diagram(token)
    results.append(("Create Diagram", diagram_id is not None))
    
    # Test 4: List Diagrams
    results.append(("List Diagrams", test_list_diagrams(token)))
    
    # Test 5: Get Diagram by ID
    results.append(("Get Diagram by ID", test_get_diagram(token, diagram_id)))
    
    # Test 6: Full-Text Search
    results.append(("Full-Text Search", test_full_text_search(token)))
    
    # Summary
    print("\n")
    print("=" * 80)
    print("VERIFICATION TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("=" * 80)
    print(f"Results: {passed}/{total} tests passed ({passed*100//total}%)")
    print("=" * 80)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n")
    
    if passed == total:
        print("✅ All core features verified successfully!")
        print("✅ Ready to implement new features.")
    else:
        print("❌ Some tests failed. Fix issues before implementing new features.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
