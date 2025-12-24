#!/usr/bin/env python3
"""
Test Feature #133: Move diagram to folder

This test verifies that users can move diagrams to folders.
"""

import requests
import json
import time
from datetime import datetime

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
            import base64
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

def create_folder(token, user_id, name):
    """Create a folder (we'll use the database directly for now)."""
    import uuid
    import psycopg2
    from datetime import datetime
    
    folder_id = str(uuid.uuid4())
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="autograph",
            user="autograph",
            password="autograph_dev_password"
        )
        
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO folders (id, name, owner_id, created_at, updated_at) 
            VALUES (%s, %s, %s, %s, %s)
            """,
            (folder_id, name, user_id, datetime.utcnow(), datetime.utcnow())
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return folder_id
    except Exception as e:
        print(f"Failed to create folder: {e}")
        return None

def move_diagram(token, user_id, diagram_id, folder_id):
    """Move diagram to folder."""
    response = requests.put(
        f"{DIAGRAM_URL}/{diagram_id}/move",
        headers={
            "Authorization": f"Bearer {token}",
            "X-User-ID": user_id
        },
        json={
            "folder_id": folder_id
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

def main():
    print("\n" + "="*80)
    print("TEST FEATURE #133: MOVE DIAGRAM TO FOLDER")
    print("="*80 + "\n")
    
    # Generate unique email
    timestamp = int(time.time())
    email = f"test-move-{timestamp}@example.com"
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
    response = create_diagram(token, user_id, "Test Diagram for Move")
    if response.status_code == 200:
        diagram_data = response.json()
        diagram_id = diagram_data.get("id")
        print_test("Diagram created", True, f"Diagram ID: {diagram_id}")
        print(f"   Initial folder_id: {diagram_data.get('folder_id')}")
    else:
        print_test("Diagram created", False, f"Status: {response.status_code}")
        return
    
    # Test 4: Create folder
    print("\nTest 4: Create folder")
    folder_id = create_folder(token, user_id, "Test Folder")
    if folder_id:
        print_test("Folder created", True, f"Folder ID: {folder_id}")
    else:
        print_test("Folder created", False)
        return
    
    # Test 5: Move diagram to folder
    print("\nTest 5: Move diagram to folder")
    response = move_diagram(token, user_id, diagram_id, folder_id)
    if response.status_code == 200:
        move_data = response.json()
        print_test("Diagram moved to folder", True)
        print(f"   Message: {move_data.get('message')}")
        print(f"   New folder_id: {move_data.get('folder_id')}")
    else:
        print_test("Diagram moved to folder", False, f"Status: {response.status_code}, Error: {response.text}")
        return
    
    # Test 6: Verify diagram is in folder
    print("\nTest 6: Verify diagram is in folder")
    response = get_diagram(token, user_id, diagram_id)
    if response.status_code == 200:
        diagram_data = response.json()
        if diagram_data.get("folder_id") == folder_id:
            print_test("Diagram folder_id updated", True, f"folder_id: {folder_id}")
        else:
            print_test("Diagram folder_id updated", False, f"Expected: {folder_id}, Got: {diagram_data.get('folder_id')}")
    else:
        print_test("Diagram folder_id updated", False, f"Status: {response.status_code}")
    
    # Test 7: Move diagram to root (folder_id = null)
    print("\nTest 7: Move diagram to root (folder_id = null)")
    response = move_diagram(token, user_id, diagram_id, None)
    if response.status_code == 200:
        move_data = response.json()
        print_test("Diagram moved to root", True)
        print(f"   Message: {move_data.get('message')}")
        print(f"   New folder_id: {move_data.get('folder_id')}")
    else:
        print_test("Diagram moved to root", False, f"Status: {response.status_code}")
    
    # Test 8: Verify diagram is at root
    print("\nTest 8: Verify diagram is at root")
    response = get_diagram(token, user_id, diagram_id)
    if response.status_code == 200:
        diagram_data = response.json()
        if diagram_data.get("folder_id") is None:
            print_test("Diagram at root", True, "folder_id is null")
        else:
            print_test("Diagram at root", False, f"folder_id should be null, got: {diagram_data.get('folder_id')}")
    else:
        print_test("Diagram at root", False, f"Status: {response.status_code}")
    
    # Test 9: Try to move to non-existent folder
    print("\nTest 9: Try to move to non-existent folder")
    fake_folder_id = "00000000-0000-0000-0000-000000000000"
    response = move_diagram(token, user_id, diagram_id, fake_folder_id)
    if response.status_code == 404:
        print_test("Non-existent folder rejected", True, "404 returned")
    else:
        print_test("Non-existent folder rejected", False, f"Expected 404, got {response.status_code}")
    
    # Test 10: Try to move non-existent diagram
    print("\nTest 10: Try to move non-existent diagram")
    fake_diagram_id = "00000000-0000-0000-0000-000000000000"
    response = move_diagram(token, user_id, fake_diagram_id, folder_id)
    if response.status_code == 404:
        print_test("Non-existent diagram rejected", True, "404 returned")
    else:
        print_test("Non-existent diagram rejected", False, f"Expected 404, got {response.status_code}")
    
    # Test 11: Create second user and try to move first user's diagram
    print("\nTest 11: Unauthorized move attempt")
    email2 = f"test-move-2-{timestamp}@example.com"
    response = register_user(email2, password, "Test User 2")
    if response.status_code in [200, 201]:
        token2, user_id2 = login_user(email2, password)
        if token2:
            response = move_diagram(token2, user_id2, diagram_id, folder_id)
            if response.status_code == 403:
                print_test("Unauthorized move rejected", True, "403 returned")
            else:
                print_test("Unauthorized move rejected", False, f"Expected 403, got {response.status_code}")
        else:
            print_test("Unauthorized move rejected", False, "Failed to login second user")
    else:
        print_test("Unauthorized move rejected", False, "Failed to create second user")
    
    # Test 12: Create second folder and move diagram there
    print("\nTest 12: Move diagram between folders")
    folder_id2 = create_folder(token, user_id, "Test Folder 2")
    if folder_id2:
        # First move to folder 1
        response = move_diagram(token, user_id, diagram_id, folder_id)
        if response.status_code == 200:
            # Then move to folder 2
            response = move_diagram(token, user_id, diagram_id, folder_id2)
            if response.status_code == 200:
                # Verify it's in folder 2
                response = get_diagram(token, user_id, diagram_id)
                if response.status_code == 200:
                    diagram_data = response.json()
                    if diagram_data.get("folder_id") == folder_id2:
                        print_test("Move between folders", True, f"Now in folder 2: {folder_id2}")
                    else:
                        print_test("Move between folders", False, f"Expected folder 2, got: {diagram_data.get('folder_id')}")
                else:
                    print_test("Move between folders", False, "Failed to get diagram")
            else:
                print_test("Move between folders", False, "Failed to move to folder 2")
        else:
            print_test("Move between folders", False, "Failed to move to folder 1")
    else:
        print_test("Move between folders", False, "Failed to create folder 2")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
