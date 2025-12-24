#!/usr/bin/env python3
"""
Test Feature #134: Star/favorite diagram for quick access

This test verifies that users can star/favorite diagrams.
"""

import requests
import json
import time
import base64

BASE_URL = "http://localhost:8085"  # Auth service
DIAGRAM_URL = "http://localhost:8082"  # Diagram service

def print_test(test_name, status, details=""):
    """Print test result."""
    symbol = "✅" if status else "❌"
    print(f"{symbol} {test_name}")
    if details:
        print(f"   {details}")

def register_user(email, password, full_name):
    """Register a new user."""
    response = requests.post(
        f"{BASE_URL}/register",
        json={
            "email": email,
            "password": password,
            "full_name": full_name
        }
    )
    return response

def login_user(email, password):
    """Login and get access token."""
    response = requests.post(
        f"{BASE_URL}/login",
        json={
            "email": email,
            "password": password
        }
    )
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        
        # Decode JWT to get user_id (from 'sub' claim)
        if token:
            # JWT format: header.payload.signature
            parts = token.split('.')
            if len(parts) >= 2:
                # Decode payload (add padding if needed)
                payload = parts[1]
                padding = 4 - len(payload) % 4
                if padding != 4:
                    payload += '=' * padding
                
                decoded = base64.urlsafe_b64decode(payload)
                payload_data = json.loads(decoded)
                user_id = payload_data.get("sub")  # 'sub' is the user ID
                return token, user_id
        
        return token, None
    return None, None

def create_diagram(token, user_id, title, file_type="canvas"):
    """Create a new diagram."""
    response = requests.post(
        f"{DIAGRAM_URL}/",
        headers={
            "Authorization": f"Bearer {token}",
            "X-User-ID": user_id
        },
        json={
            "title": title,
            "file_type": file_type,
            "canvas_data": {"shapes": []},
            "note_content": "Test note"
        }
    )
    return response

def star_diagram(token, user_id, diagram_id):
    """Toggle star status for a diagram."""
    response = requests.put(
        f"{DIAGRAM_URL}/{diagram_id}/star",
        headers={
            "Authorization": f"Bearer {token}",
            "X-User-ID": user_id
        }
    )
    return response

def get_diagram(token, user_id, diagram_id):
    """Get diagram by ID."""
    response = requests.get(
        f"{DIAGRAM_URL}/{diagram_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "X-User-ID": user_id
        }
    )
    return response

def list_diagrams(token, user_id):
    """List all diagrams."""
    response = requests.get(
        f"{DIAGRAM_URL}/",
        headers={
            "Authorization": f"Bearer {token}",
            "X-User-ID": user_id
        }
    )
    return response

def main():
    print("\n" + "="*80)
    print("TEST FEATURE #134: STAR/FAVORITE DIAGRAM FOR QUICK ACCESS")
    print("="*80 + "\n")
    
    # Generate unique email
    timestamp = int(time.time())
    email = f"test-star-{timestamp}@example.com"
    password = "TestPass123!"
    
    # Test 1: Register user
    print("Test 1: Register user")
    response = register_user(email, password, "Test User")
    if response.status_code in [200, 201]:
        user_data = response.json()
        user_id = user_data.get("id")
        print_test("User registered", True, f"User ID: {user_id}")
    else:
        print_test("User registered", False, f"Status: {response.status_code}")
        return
    
    # Test 2: Login
    print("\nTest 2: Login user")
    token, user_id = login_user(email, password)
    if token:
        print_test("User logged in", True, f"Token received")
    else:
        print_test("User logged in", False)
        return
    
    # Test 3: Create diagram
    print("\nTest 3: Create diagram")
    response = create_diagram(token, user_id, "Test Diagram for Star")
    if response.status_code == 200:
        diagram_data = response.json()
        diagram_id = diagram_data.get("id")
        is_starred = diagram_data.get("is_starred", False)
        print_test("Diagram created", True, f"Diagram ID: {diagram_id}")
        print(f"   Initial is_starred: {is_starred}")
    else:
        print_test("Diagram created", False, f"Status: {response.status_code}")
        return
    
    # Test 4: Star the diagram
    print("\nTest 4: Star the diagram")
    response = star_diagram(token, user_id, diagram_id)
    if response.status_code == 200:
        star_data = response.json()
        print_test("Diagram starred", True)
        print(f"   Message: {star_data.get('message')}")
        print(f"   is_starred: {star_data.get('is_starred')}")
    else:
        print_test("Diagram starred", False, f"Status: {response.status_code}, Error: {response.text}")
        return
    
    # Test 5: Verify diagram is starred
    print("\nTest 5: Verify diagram is starred")
    response = get_diagram(token, user_id, diagram_id)
    if response.status_code == 200:
        diagram_data = response.json()
        if diagram_data.get("is_starred") == True:
            print_test("Diagram is_starred = True", True)
        else:
            print_test("Diagram is_starred = True", False, f"Got: {diagram_data.get('is_starred')}")
    else:
        print_test("Diagram is_starred = True", False, f"Status: {response.status_code}")
    
    # Test 6: Unstar the diagram (toggle again)
    print("\nTest 6: Unstar the diagram")
    response = star_diagram(token, user_id, diagram_id)
    if response.status_code == 200:
        star_data = response.json()
        print_test("Diagram unstarred", True)
        print(f"   Message: {star_data.get('message')}")
        print(f"   is_starred: {star_data.get('is_starred')}")
    else:
        print_test("Diagram unstarred", False, f"Status: {response.status_code}")
    
    # Test 7: Verify diagram is unstarred
    print("\nTest 7: Verify diagram is unstarred")
    response = get_diagram(token, user_id, diagram_id)
    if response.status_code == 200:
        diagram_data = response.json()
        if diagram_data.get("is_starred") == False:
            print_test("Diagram is_starred = False", True)
        else:
            print_test("Diagram is_starred = False", False, f"Got: {diagram_data.get('is_starred')}")
    else:
        print_test("Diagram is_starred = False", False, f"Status: {response.status_code}")
    
    # Test 8: Star again
    print("\nTest 8: Star again")
    response = star_diagram(token, user_id, diagram_id)
    if response.status_code == 200:
        star_data = response.json()
        if star_data.get("is_starred") == True:
            print_test("Diagram starred again", True)
        else:
            print_test("Diagram starred again", False, f"is_starred should be True")
    else:
        print_test("Diagram starred again", False, f"Status: {response.status_code}")
    
    # Test 9: Try to star non-existent diagram
    print("\nTest 9: Try to star non-existent diagram")
    fake_diagram_id = "00000000-0000-0000-0000-000000000000"
    response = star_diagram(token, user_id, fake_diagram_id)
    if response.status_code == 404:
        print_test("Non-existent diagram rejected", True, "404 returned")
    else:
        print_test("Non-existent diagram rejected", False, f"Expected 404, got {response.status_code}")
    
    # Test 10: Create second user and try to star first user's diagram
    print("\nTest 10: Unauthorized star attempt")
    email2 = f"test-star-2-{timestamp}@example.com"
    response = register_user(email2, password, "Test User 2")
    if response.status_code in [200, 201]:
        token2, user_id2 = login_user(email2, password)
        if token2:
            response = star_diagram(token2, user_id2, diagram_id)
            if response.status_code == 403:
                print_test("Unauthorized star rejected", True, "403 returned")
            else:
                print_test("Unauthorized star rejected", False, f"Expected 403, got {response.status_code}")
        else:
            print_test("Unauthorized star rejected", False, "Failed to login second user")
    else:
        print_test("Unauthorized star rejected", False, "Failed to create second user")
    
    # Test 11: Create multiple diagrams and star some
    print("\nTest 11: Create multiple diagrams and star some")
    diagram_ids = []
    for i in range(3):
        response = create_diagram(token, user_id, f"Diagram {i+1}")
        if response.status_code == 200:
            diagram_ids.append(response.json().get("id"))
    
    # Star diagram 1 and 3
    if len(diagram_ids) == 3:
        star_diagram(token, user_id, diagram_ids[0])
        star_diagram(token, user_id, diagram_ids[2])
        
        # Verify starred status
        starred_count = 0
        for did in diagram_ids:
            response = get_diagram(token, user_id, did)
            if response.status_code == 200:
                if response.json().get("is_starred"):
                    starred_count += 1
        
        # Plus the original diagram we starred earlier
        if starred_count == 2:
            print_test("Multiple diagrams starred", True, f"2 out of 3 starred")
        else:
            print_test("Multiple diagrams starred", False, f"Expected 2 starred, got {starred_count}")
    else:
        print_test("Multiple diagrams starred", False, "Failed to create diagrams")
    
    # Test 12: Toggle star multiple times
    print("\nTest 12: Toggle star multiple times")
    response = create_diagram(token, user_id, "Toggle Test Diagram")
    if response.status_code == 200:
        toggle_diagram_id = response.json().get("id")
        
        # Toggle 5 times
        expected_states = [True, False, True, False, True]
        all_correct = True
        
        for i, expected in enumerate(expected_states):
            response = star_diagram(token, user_id, toggle_diagram_id)
            if response.status_code == 200:
                actual = response.json().get("is_starred")
                if actual != expected:
                    all_correct = False
                    print(f"   Toggle {i+1}: Expected {expected}, got {actual}")
            else:
                all_correct = False
                break
        
        if all_correct:
            print_test("Toggle star multiple times", True, "All 5 toggles correct")
        else:
            print_test("Toggle star multiple times", False)
    else:
        print_test("Toggle star multiple times", False, "Failed to create diagram")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
