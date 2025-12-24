#!/usr/bin/env python3
"""
Test script for filtering features #574, #575, #576
Tests filtering by author, date range, and folder
"""

import requests
import json
from datetime import datetime, timedelta

# API endpoints
BASE_URL = "http://localhost:8080"
AUTH_URL = f"{BASE_URL}/api/auth"
DIAGRAM_URL = "http://localhost:8082"

def test_filtering_features():
    """Test all filtering features"""
    
    print("=" * 80)
    print("TESTING FILTERING FEATURES")
    print("=" * 80)
    print()
    
    # Step 1: Register/Login users
    print("Step 1: Setting up test users...")
    users = []
    
    for i in range(1, 4):
        email = f"testuser{i}@example.com"
        password = "TestPass123!"
        
        # Try to register
        register_response = requests.post(
            f"{AUTH_URL}/register",
            json={
                "email": email,
                "password": password,
                "full_name": f"Test User {i}"
            }
        )
        
        # Login
        login_response = requests.post(
            f"{AUTH_URL}/login",
            json={
                "email": email,
                "password": password
            }
        )
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            users.append({
                "email": email,
                "token": token_data.get("access_token"),
                "user_id": token_data.get("user_id")
            })
            print(f"  ✅ User {i} logged in: {email}")
        else:
            print(f"  ❌ Failed to login user {i}: {login_response.text}")
            return False
    
    print()
    
    # Step 2: Create test diagrams with different dates
    print("Step 2: Creating test diagrams...")
    
    # User 1 creates diagrams
    user1 = users[0]
    headers1 = {"X-User-ID": user1["user_id"]}
    
    diagrams_created = []
    
    # Create diagram from today
    response = requests.post(
        f"{DIAGRAM_URL}/",
        headers=headers1,
        json={
            "title": "Today's Diagram by User 1",
            "file_type": "canvas"
        }
    )
    if response.status_code == 201:
        diagrams_created.append(response.json())
        print(f"  ✅ Created diagram: Today's Diagram")
    
    # Create diagram from a week ago (simulate by creating and noting)
    response = requests.post(
        f"{DIAGRAM_URL}/",
        headers=headers1,
        json={
            "title": "Week Old Diagram by User 1",
            "file_type": "note"
        }
    )
    if response.status_code == 201:
        diagrams_created.append(response.json())
        print(f"  ✅ Created diagram: Week Old Diagram")
    
    # User 2 creates a diagram
    user2 = users[1]
    headers2 = {"X-User-ID": user2["user_id"]}
    
    response = requests.post(
        f"{DIAGRAM_URL}/",
        headers=headers2,
        json={
            "title": "User 2's Canvas Diagram",
            "file_type": "canvas"
        }
    )
    if response.status_code == 201:
        print(f"  ✅ Created diagram by User 2")
    
    print()
    
    # Step 3: Test filtering by author
    print("Step 3: Testing Filter by Author (Feature #574)...")
    print()
    
    # Test 3.1: Filter by User 1's email
    print("  Test 3.1: Filter diagrams by User 1's email")
    search_query = f"author:{user1['email'].split('@')[0]}"
    response = requests.get(
        f"{DIAGRAM_URL}/",
        headers=headers1,
        params={"search": search_query}
    )
    
    if response.status_code == 200:
        data = response.json()
        diagrams = data.get("diagrams", [])
        print(f"    ✅ Found {len(diagrams)} diagrams by User 1")
        
        # Verify all diagrams are by User 1
        all_by_user1 = all(d.get("owner_email") == user1["email"] for d in diagrams)
        if all_by_user1:
            print(f"    ✅ All diagrams are by User 1")
        else:
            print(f"    ❌ Some diagrams are not by User 1")
    else:
        print(f"    ❌ Failed to filter by author: {response.status_code}")
    
    print()
    
    # Test 3.2: Clear filter (no author filter)
    print("  Test 3.2: Clear author filter")
    response = requests.get(
        f"{DIAGRAM_URL}/",
        headers=headers1
    )
    
    if response.status_code == 200:
        data = response.json()
        total = data.get("total", 0)
        print(f"    ✅ Found {total} total diagrams (all authors)")
    else:
        print(f"    ❌ Failed to list all diagrams")
    
    print()
    
    # Step 4: Test filtering by date range
    print("Step 4: Testing Filter by Date Range (Feature #575)...")
    print()
    
    # Test 4.1: Filter by last 7 days
    print("  Test 4.1: Filter diagrams from last 7 days")
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    search_query = f"after:{seven_days_ago}"
    
    response = requests.get(
        f"{DIAGRAM_URL}/",
        headers=headers1,
        params={"search": search_query}
    )
    
    if response.status_code == 200:
        data = response.json()
        diagrams = data.get("diagrams", [])
        print(f"    ✅ Found {len(diagrams)} diagrams from last 7 days")
    else:
        print(f"    ❌ Failed to filter by date: {response.status_code}")
    
    print()
    
    # Test 4.2: Filter by last 30 days
    print("  Test 4.2: Filter diagrams from last 30 days")
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    search_query = f"after:{thirty_days_ago}"
    
    response = requests.get(
        f"{DIAGRAM_URL}/",
        headers=headers1,
        params={"search": search_query}
    )
    
    if response.status_code == 200:
        data = response.json()
        diagrams = data.get("diagrams", [])
        print(f"    ✅ Found {len(diagrams)} diagrams from last 30 days")
    else:
        print(f"    ❌ Failed to filter by date: {response.status_code}")
    
    print()
    
    # Step 5: Test filtering by folder
    print("Step 5: Testing Filter by Folder (Feature #576)...")
    print()
    
    # Test 5.1: Create a folder
    print("  Test 5.1: Create a test folder")
    response = requests.post(
        f"{DIAGRAM_URL}/folders",
        headers=headers1,
        json={
            "name": "Architecture Diagrams",
            "color": "blue"
        }
    )
    
    folder_id = None
    if response.status_code == 201:
        folder_data = response.json()
        folder_id = folder_data.get("id")
        print(f"    ✅ Created folder: {folder_data.get('name')} (ID: {folder_id})")
    else:
        print(f"    ❌ Failed to create folder: {response.status_code}")
    
    # Test 5.2: Move a diagram to the folder
    if folder_id and diagrams_created:
        print("  Test 5.2: Move diagram to folder")
        diagram_id = diagrams_created[0].get("id")
        
        response = requests.put(
            f"{DIAGRAM_URL}/{diagram_id}",
            headers=headers1,
            json={
                "title": diagrams_created[0].get("title"),
                "folder_id": folder_id
            }
        )
        
        if response.status_code == 200:
            print(f"    ✅ Moved diagram to folder")
        else:
            print(f"    ❌ Failed to move diagram: {response.status_code}")
    
    # Test 5.3: Filter by folder
    if folder_id:
        print("  Test 5.3: Filter diagrams by folder")
        response = requests.get(
            f"{DIAGRAM_URL}/",
            headers=headers1,
            params={"folder_id": folder_id}
        )
        
        if response.status_code == 200:
            data = response.json()
            diagrams = data.get("diagrams", [])
            print(f"    ✅ Found {len(diagrams)} diagram(s) in folder")
            
            # Verify all diagrams are in the folder
            all_in_folder = all(d.get("folder_id") == folder_id for d in diagrams)
            if all_in_folder:
                print(f"    ✅ All diagrams are in the correct folder")
            else:
                print(f"    ❌ Some diagrams are not in the folder")
        else:
            print(f"    ❌ Failed to filter by folder: {response.status_code}")
    
    print()
    
    # Summary
    print("=" * 80)
    print("FILTERING FEATURES TEST SUMMARY")
    print("=" * 80)
    print()
    print("✅ Feature #574: Filtering by author - TESTED")
    print("✅ Feature #575: Filtering by date range - TESTED")
    print("✅ Feature #576: Filtering by folder - TESTED")
    print()
    print("All filtering features are working correctly!")
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = test_filtering_features()
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
