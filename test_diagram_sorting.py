#!/usr/bin/env python3
"""
Test script for Features #147-149: Diagram sorting
- Feature #147: Sort by name (A-Z, Z-A)
- Feature #148: Sort by date created
- Feature #149: Sort by date updated
"""

import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8080"
DIAGRAM_SERVICE_URL = "http://localhost:8082"
TEST_USER_EMAIL = f"sort_test_{int(time.time())}@example.com"
TEST_USER_PASSWORD = "SecurePassword123!"

def print_test(test_name, passed, details=""):
    """Print test result with formatting"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"    {details}")
    print()

def register_and_login():
    """Register a test user and get access token"""
    print("=" * 80)
    print("SETUP: Register and Login")
    print("=" * 80)
    
    # Register
    response = requests.post(
        f"{API_BASE_URL}/api/auth/register",
        json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "full_name": "Sort Test User"
        },
        timeout=10
    )
    
    if response.status_code != 201:
        print(f"❌ Registration failed: {response.status_code}")
        return None, None
    
    data = response.json()
    user_id = data.get('id')
    print(f"✅ User registered: {TEST_USER_EMAIL}")
    
    # Login
    response = requests.post(
        f"{API_BASE_URL}/api/auth/login",
        json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        },
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return None, None
    
    data = response.json()
    token = data.get('access_token')
    print(f"✅ User logged in, token received\n")
    
    return user_id, token

def create_test_diagrams(user_id, token):
    """Create multiple test diagrams with different names and timestamps"""
    print("=" * 80)
    print("SETUP: Create Test Diagrams")
    print("=" * 80)
    
    diagrams = [
        {"title": "Alpha Diagram", "type": "canvas"},
        {"title": "Zeta Diagram", "type": "note"},
        {"title": "Beta Diagram", "type": "mixed"},
        {"title": "Gamma Diagram", "type": "canvas"},
        {"title": "Delta Diagram", "type": "note"},
    ]
    
    created_ids = []
    
    for i, diagram in enumerate(diagrams):
        # Add small delay to ensure different timestamps
        if i > 0:
            time.sleep(0.5)
        
        response = requests.post(
            f"{DIAGRAM_SERVICE_URL}/",
            headers={"X-User-ID": user_id},
            json={
                "title": diagram["title"],
                "file_type": diagram["type"],
                "canvas_data": {"shapes": []} if diagram["type"] in ["canvas", "mixed"] else None,
                "note_content": f"Content for {diagram['title']}" if diagram["type"] in ["note", "mixed"] else None,
            },
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            created_ids.append(data['id'])
            print(f"✅ Created: {diagram['title']}")
        else:
            print(f"❌ Failed to create: {diagram['title']}")
            return []
    
    print(f"\n✅ Created {len(created_ids)} test diagrams\n")
    return created_ids

def test_sort_by_name_asc(user_id):
    """Test Feature #147: Sort by name A-Z"""
    print("=" * 80)
    print("TEST 1: Sort by Name (A-Z)")
    print("=" * 80)
    
    try:
        response = requests.get(
            f"{DIAGRAM_SERVICE_URL}/",
            headers={"X-User-ID": user_id},
            params={
                "sort_by": "title",
                "sort_order": "asc",
                "page_size": 20
            },
            timeout=10
        )
        
        if response.status_code != 200:
            print_test("Sort by Name A-Z", False, f"Status: {response.status_code}")
            return False
        
        data = response.json()
        diagrams = data.get('diagrams', [])
        
        if len(diagrams) < 2:
            print_test("Sort by Name A-Z", False, "Not enough diagrams to test sorting")
            return False
        
        # Check if sorted alphabetically
        titles = [d['title'] for d in diagrams]
        sorted_titles = sorted(titles)
        
        if titles == sorted_titles:
            print_test(
                "Sort by Name A-Z", 
                True, 
                f"Diagrams sorted correctly: {', '.join(titles[:3])}..."
            )
            return True
        else:
            print_test(
                "Sort by Name A-Z", 
                False, 
                f"Expected: {sorted_titles}, Got: {titles}"
            )
            return False
            
    except Exception as e:
        print_test("Sort by Name A-Z", False, f"Error: {str(e)}")
        return False

def test_sort_by_name_desc(user_id):
    """Test Feature #147: Sort by name Z-A"""
    print("=" * 80)
    print("TEST 2: Sort by Name (Z-A)")
    print("=" * 80)
    
    try:
        response = requests.get(
            f"{DIAGRAM_SERVICE_URL}/",
            headers={"X-User-ID": user_id},
            params={
                "sort_by": "title",
                "sort_order": "desc",
                "page_size": 20
            },
            timeout=10
        )
        
        if response.status_code != 200:
            print_test("Sort by Name Z-A", False, f"Status: {response.status_code}")
            return False
        
        data = response.json()
        diagrams = data.get('diagrams', [])
        
        if len(diagrams) < 2:
            print_test("Sort by Name Z-A", False, "Not enough diagrams to test sorting")
            return False
        
        # Check if sorted reverse alphabetically
        titles = [d['title'] for d in diagrams]
        sorted_titles = sorted(titles, reverse=True)
        
        if titles == sorted_titles:
            print_test(
                "Sort by Name Z-A", 
                True, 
                f"Diagrams sorted correctly: {', '.join(titles[:3])}..."
            )
            return True
        else:
            print_test(
                "Sort by Name Z-A", 
                False, 
                f"Expected: {sorted_titles}, Got: {titles}"
            )
            return False
            
    except Exception as e:
        print_test("Sort by Name Z-A", False, f"Error: {str(e)}")
        return False

def test_sort_by_created_newest(user_id):
    """Test Feature #148: Sort by date created (newest first)"""
    print("=" * 80)
    print("TEST 3: Sort by Created Date (Newest First)")
    print("=" * 80)
    
    try:
        response = requests.get(
            f"{DIAGRAM_SERVICE_URL}/",
            headers={"X-User-ID": user_id},
            params={
                "sort_by": "created_at",
                "sort_order": "desc",
                "page_size": 20
            },
            timeout=10
        )
        
        if response.status_code != 200:
            print_test("Sort by Created (Newest)", False, f"Status: {response.status_code}")
            return False
        
        data = response.json()
        diagrams = data.get('diagrams', [])
        
        if len(diagrams) < 2:
            print_test("Sort by Created (Newest)", False, "Not enough diagrams to test sorting")
            return False
        
        # Check if sorted by created_at descending
        created_dates = [d['created_at'] for d in diagrams]
        sorted_dates = sorted(created_dates, reverse=True)
        
        if created_dates == sorted_dates:
            print_test(
                "Sort by Created (Newest)", 
                True, 
                f"Diagrams sorted correctly by creation date"
            )
            return True
        else:
            print_test(
                "Sort by Created (Newest)", 
                False, 
                f"Dates not in descending order"
            )
            return False
            
    except Exception as e:
        print_test("Sort by Created (Newest)", False, f"Error: {str(e)}")
        return False

def test_sort_by_created_oldest(user_id):
    """Test Feature #148: Sort by date created (oldest first)"""
    print("=" * 80)
    print("TEST 4: Sort by Created Date (Oldest First)")
    print("=" * 80)
    
    try:
        response = requests.get(
            f"{DIAGRAM_SERVICE_URL}/",
            headers={"X-User-ID": user_id},
            params={
                "sort_by": "created_at",
                "sort_order": "asc",
                "page_size": 20
            },
            timeout=10
        )
        
        if response.status_code != 200:
            print_test("Sort by Created (Oldest)", False, f"Status: {response.status_code}")
            return False
        
        data = response.json()
        diagrams = data.get('diagrams', [])
        
        if len(diagrams) < 2:
            print_test("Sort by Created (Oldest)", False, "Not enough diagrams to test sorting")
            return False
        
        # Check if sorted by created_at ascending
        created_dates = [d['created_at'] for d in diagrams]
        sorted_dates = sorted(created_dates)
        
        if created_dates == sorted_dates:
            print_test(
                "Sort by Created (Oldest)", 
                True, 
                f"Diagrams sorted correctly by creation date"
            )
            return True
        else:
            print_test(
                "Sort by Created (Oldest)", 
                False, 
                f"Dates not in ascending order"
            )
            return False
            
    except Exception as e:
        print_test("Sort by Created (Oldest)", False, f"Error: {str(e)}")
        return False

def test_sort_by_updated_recent(user_id):
    """Test Feature #149: Sort by date updated (most recent first)"""
    print("=" * 80)
    print("TEST 5: Sort by Updated Date (Most Recent)")
    print("=" * 80)
    
    try:
        response = requests.get(
            f"{DIAGRAM_SERVICE_URL}/",
            headers={"X-User-ID": user_id},
            params={
                "sort_by": "updated_at",
                "sort_order": "desc",
                "page_size": 20
            },
            timeout=10
        )
        
        if response.status_code != 200:
            print_test("Sort by Updated (Recent)", False, f"Status: {response.status_code}")
            return False
        
        data = response.json()
        diagrams = data.get('diagrams', [])
        
        if len(diagrams) < 2:
            print_test("Sort by Updated (Recent)", False, "Not enough diagrams to test sorting")
            return False
        
        # Check if sorted by updated_at descending
        updated_dates = [d['updated_at'] for d in diagrams]
        sorted_dates = sorted(updated_dates, reverse=True)
        
        if updated_dates == sorted_dates:
            print_test(
                "Sort by Updated (Recent)", 
                True, 
                f"Diagrams sorted correctly by update date"
            )
            return True
        else:
            print_test(
                "Sort by Updated (Recent)", 
                False, 
                f"Dates not in descending order"
            )
            return False
            
    except Exception as e:
        print_test("Sort by Updated (Recent)", False, f"Error: {str(e)}")
        return False

def test_sort_by_updated_oldest(user_id):
    """Test Feature #149: Sort by date updated (oldest first)"""
    print("=" * 80)
    print("TEST 6: Sort by Updated Date (Oldest First)")
    print("=" * 80)
    
    try:
        response = requests.get(
            f"{DIAGRAM_SERVICE_URL}/",
            headers={"X-User-ID": user_id},
            params={
                "sort_by": "updated_at",
                "sort_order": "asc",
                "page_size": 20
            },
            timeout=10
        )
        
        if response.status_code != 200:
            print_test("Sort by Updated (Oldest)", False, f"Status: {response.status_code}")
            return False
        
        data = response.json()
        diagrams = data.get('diagrams', [])
        
        if len(diagrams) < 2:
            print_test("Sort by Updated (Oldest)", False, "Not enough diagrams to test sorting")
            return False
        
        # Check if sorted by updated_at ascending
        updated_dates = [d['updated_at'] for d in diagrams]
        sorted_dates = sorted(updated_dates)
        
        if updated_dates == sorted_dates:
            print_test(
                "Sort by Updated (Oldest)", 
                True, 
                f"Diagrams sorted correctly by update date"
            )
            return True
        else:
            print_test(
                "Sort by Updated (Oldest)", 
                False, 
                f"Dates not in ascending order"
            )
            return False
            
    except Exception as e:
        print_test("Sort by Updated (Oldest)", False, f"Error: {str(e)}")
        return False

def main():
    """Run all sorting tests"""
    print("\n")
    print("=" * 80)
    print("DIAGRAM SORTING TEST SUITE")
    print("Features #147-149: Sort by Name, Created Date, Updated Date")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print("\n")
    
    # Setup: Register and login
    user_id, token = register_and_login()
    if not user_id or not token:
        print("\n❌ Setup failed. Cannot continue tests.\n")
        return 1
    
    # Setup: Create test diagrams
    diagram_ids = create_test_diagrams(user_id, token)
    if len(diagram_ids) < 5:
        print("\n❌ Failed to create enough test diagrams. Cannot continue tests.\n")
        return 1
    
    # Run tests
    results = []
    
    results.append(("Sort by Name A-Z", test_sort_by_name_asc(user_id)))
    results.append(("Sort by Name Z-A", test_sort_by_name_desc(user_id)))
    results.append(("Sort by Created (Newest)", test_sort_by_created_newest(user_id)))
    results.append(("Sort by Created (Oldest)", test_sort_by_created_oldest(user_id)))
    results.append(("Sort by Updated (Recent)", test_sort_by_updated_recent(user_id)))
    results.append(("Sort by Updated (Oldest)", test_sort_by_updated_oldest(user_id)))
    
    # Summary
    print("\n")
    print("=" * 80)
    print("TEST SUMMARY")
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
        print("✅ All sorting tests passed!")
        print("✅ Features #147-149 verified successfully!")
        return 0
    else:
        print("❌ Some tests failed. Review and fix issues.")
        return 1

if __name__ == "__main__":
    exit(main())
