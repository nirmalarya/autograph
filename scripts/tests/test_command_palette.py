#!/usr/bin/env python3
"""
Test script for Command Palette Feature #679
Tests: Cmd+K shortcut, search, navigation, and quick actions
"""

import time
import requests
import json

# Base URLs
AUTH_URL = "http://localhost:8085"
DIAGRAM_URL = "http://localhost:8082"

def test_command_palette():
    print("=" * 80)
    print("COMMAND PALETTE TEST - Feature #679")
    print("=" * 80)
    
    # Step 1: Register or login test user
    print("\n[1] Creating test user...")
    test_email = "cmdpalette_test@test.com"
    test_password = "Test123!"
    
    # Try to register
    register_response = requests.post(
        f"{AUTH_URL}/register",
        json={"email": test_email, "password": test_password, "name": "Command Palette Test"}
    )
    
    if register_response.status_code == 201:
        print(f"✅ User created: {test_email}")
        user_data = register_response.json()
        user_id = user_data['id']
    elif register_response.status_code == 400:
        print(f"ℹ️  User already exists, logging in...")
        # Login instead
        login_response = requests.post(
            f"{AUTH_URL}/login",
            json={"email": test_email, "password": test_password}
        )
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return False
        
        tokens = login_response.json()
        access_token = tokens['access_token']
        
        # Decode JWT to get user_id
        import base64
        payload = access_token.split('.')[1]
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4)
        decoded = json.loads(base64.b64decode(payload))
        user_id = decoded['sub']
        print(f"✅ Logged in as: {test_email}")
    else:
        print(f"❌ Registration failed: {register_response.text}")
        return False
    
    # Step 2: Create some test diagrams for the command palette to find
    print("\n[2] Creating test diagrams...")
    headers = {"X-User-ID": user_id}
    
    test_diagrams = [
        {"title": "AWS Architecture", "file_type": "canvas"},
        {"title": "Database Schema", "file_type": "note"},
        {"title": "System Flowchart", "file_type": "canvas"},
    ]
    
    created_diagrams = []
    for diagram in test_diagrams:
        response = requests.post(
            f"{DIAGRAM_URL}/",
            headers=headers,
            json={
                **diagram,
                "canvas_data": {"shapes": []} if diagram['file_type'] == 'canvas' else None,
                "note_content": "" if diagram['file_type'] == 'note' else None,
            }
        )
        if response.status_code == 201:
            created_diagrams.append(response.json())
            print(f"  ✅ Created: {diagram['title']}")
        else:
            print(f"  ⚠️  Failed to create {diagram['title']}: {response.text}")
    
    if len(created_diagrams) < 2:
        print("❌ Not enough diagrams created for testing")
        return False
    
    print(f"\n✅ Test data setup complete!")
    print(f"   User ID: {user_id}")
    print(f"   Diagrams created: {len(created_diagrams)}")
    
    # Step 3: Instructions for manual UI testing
    print("\n" + "=" * 80)
    print("MANUAL UI TESTING INSTRUCTIONS")
    print("=" * 80)
    print(f"""
To complete the verification of Feature #679 (Command Palette), perform these tests:

1. OPEN THE DASHBOARD:
   - Navigate to http://localhost:3000/dashboard
   - Log in with: {test_email} / {test_password}

2. TEST KEYBOARD SHORTCUT:
   ✓ Press Cmd+K (Mac) or Ctrl+K (Windows/Linux)
   ✓ Verify: Command palette modal opens
   ✓ Verify: Input field is focused and ready for typing
   ✓ Press Escape
   ✓ Verify: Command palette closes

3. TEST COMMAND SEARCH:
   ✓ Press Cmd+K to open palette
   ✓ Type "new" 
   ✓ Verify: Commands like "New Canvas Diagram", "New Note", "New Mermaid Diagram" appear
   ✓ Verify: Commands are highlighted/filtered as you type
   
4. TEST NAVIGATION COMMANDS:
   ✓ Press Cmd+K
   ✓ Type "dashboard"
   ✓ Verify: "Go to Dashboard" command appears
   ✓ Type "starred"
   ✓ Verify: "Go to Starred" command appears
   ✓ Clear search
   ✓ Verify: All navigation commands visible (Dashboard, Starred, Recent, Shared, Trash)

5. TEST FILE SEARCH:
   ✓ Press Cmd+K
   ✓ Type "aws"
   ✓ Verify: "AWS Architecture" diagram appears in results
   ✓ Type "database"
   ✓ Verify: "Database Schema" diagram appears
   ✓ Verify: File icons show correctly (🎨 for canvas, 📝 for note)

6. TEST KEYBOARD NAVIGATION:
   ✓ Press Cmd+K
   ✓ Use Arrow Down key
   ✓ Verify: Selection moves down (blue highlight)
   ✓ Use Arrow Up key
   ✓ Verify: Selection moves up
   ✓ Press Enter
   ✓ Verify: Selected command executes
   ✓ Verify: Palette closes after command execution

7. TEST COMMAND EXECUTION:
   ✓ Press Cmd+K
   ✓ Select "New Canvas Diagram"
   ✓ Press Enter
   ✓ Verify: Create diagram modal opens
   ✓ Verify: "Canvas" type is pre-selected
   ✓ Close modal (Cancel)
   
   ✓ Press Cmd+K
   ✓ Type a diagram name (e.g., "AWS Architecture")
   ✓ Press Enter
   ✓ Verify: Navigates to that diagram's editor

8. TEST RECENT COMMANDS:
   ✓ Execute a command (e.g., "Go to Starred")
   ✓ Press Cmd+K again
   ✓ Verify: Recently used command shows "Recent" badge
   ✓ Verify: Recent commands appear at the top of the list

9. TEST FUZZY MATCHING:
   ✓ Press Cmd+K
   ✓ Type "nw cnvs" (abbreviation for "new canvas")
   ✓ Verify: "New Canvas Diagram" still appears in results
   ✓ This tests fuzzy matching algorithm

10. TEST UI/UX POLISH:
    ✓ Verify: Modal has semi-transparent backdrop
    ✓ Verify: Commands have icons (emojis)
    ✓ Verify: Categories shown (commands, navigation, files)
    ✓ Verify: Hover states work on commands
    ✓ Verify: Footer shows keyboard shortcuts hint
    ✓ Verify: No console errors in browser DevTools

EXPECTED RESULTS:
✅ All 10 test scenarios should pass
✅ Command palette opens/closes smoothly
✅ Search is instant and responsive
✅ Keyboard navigation works perfectly
✅ All commands execute correctly
✅ UI is polished and professional

If all tests pass, mark Feature #679 as passing in feature_list.json!
""")
    
    return True

if __name__ == "__main__":
    try:
        success = test_command_palette()
        if success:
            print("\n" + "=" * 80)
            print("✅ BACKEND SETUP COMPLETE - Ready for UI testing!")
            print("=" * 80)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
