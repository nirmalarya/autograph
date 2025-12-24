#!/usr/bin/env python3
"""
Test WebSocket Notification Feature (#127)
Tests that diagram updates send WebSocket notifications to collaborators.
"""

import requests
import socketio
import time
import json
import sys
from datetime import datetime
import base64

# Configuration
DIAGRAM_SERVICE_URL = "http://localhost:8082"
COLLABORATION_SERVICE_URL = "http://localhost:8083"
AUTH_SERVICE_URL = "http://localhost:8085"
TEST_USER_EMAIL = "websocket-test@example.com"
TEST_USER_PASSWORD = "TestPassword123!"
TEST_USER_ID = None

# Track received messages
received_messages = []


def create_test_user():
    """Create a test user for the test."""
    global TEST_USER_ID
    
    print("Creating test user...")
    
    # Try to register
    register_response = requests.post(
        f"{AUTH_SERVICE_URL}/register",
        json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "full_name": "WebSocket Test User"
        }
    )
    
    if register_response.status_code == 200:
        print(f"✅ User registered successfully")
    elif register_response.status_code == 400:
        print(f"ℹ️  User already exists, proceeding with login")
    else:
        print(f"⚠️  Registration response: {register_response.status_code}")
    
    # Login to get user ID
    login_response = requests.post(
        f"{AUTH_SERVICE_URL}/login",
        json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
    )
    
    if login_response.status_code != 200:
        print(f"❌ Failed to login: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return False
    
    user_data = login_response.json()
    
    # Decode JWT to get user ID
    access_token = user_data.get("access_token")
    if not access_token:
        print("❌ No access token in response")
        return False
    
    # JWT format: header.payload.signature
    try:
        payload = access_token.split('.')[1]
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4)
        decoded = json.loads(base64.b64decode(payload))
        TEST_USER_ID = decoded.get("sub")
        
        if not TEST_USER_ID:
            print("❌ No 'sub' field in JWT")
            return False
    except Exception as e:
        print(f"❌ Failed to decode JWT: {e}")
        return False
    
    print(f"✅ Test user created/logged in: {TEST_USER_ID}")
    return True


def test_websocket_notification():
    """Test that diagram updates send WebSocket notifications."""
    print("=" * 80)
    print("TEST: WebSocket Notification on Diagram Update (Feature #127)")
    print("=" * 80)
    print()
    
    # Step 1: Create a test diagram
    print("Step 1: Creating test diagram...")
    create_response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/",
        json={
            "title": "WebSocket Test Diagram",
            "file_type": "canvas",
            "canvas_data": {"shapes": [{"type": "rectangle", "id": "1"}]}
        },
        headers={"X-User-ID": TEST_USER_ID}
    )
    
    if create_response.status_code != 200:
        print(f"❌ Failed to create diagram: {create_response.status_code}")
        print(create_response.text)
        return False
    
    diagram = create_response.json()
    diagram_id = diagram["id"]
    print(f"✅ Created diagram: {diagram_id}")
    print()
    
    # Step 2: Create Socket.IO client to simulate User B
    print("Step 2: Connecting User B via WebSocket...")
    sio = socketio.Client()
    
    @sio.on('connect')
    def on_connect():
        print("✅ User B connected to WebSocket")
    
    @sio.on('update')
    def on_update(data):
        print(f"📨 User B received update: {json.dumps(data, indent=2)}")
        received_messages.append(data)
    
    @sio.on('disconnect')
    def on_disconnect():
        print("🔌 User B disconnected")
    
    try:
        sio.connect(COLLABORATION_SERVICE_URL)
        time.sleep(1)
    except Exception as e:
        print(f"❌ Failed to connect to WebSocket: {e}")
        return False
    
    # Step 3: Join the diagram room
    print("Step 3: User B joining diagram room...")
    room_id = f"file:{diagram_id}"
    join_result = sio.call('join_room', {
        'room': room_id,
        'user_id': 'user-b',
        'username': 'User B'
    }, timeout=5)
    
    if not join_result.get('success'):
        print(f"❌ Failed to join room: {join_result}")
        sio.disconnect()
        return False
    
    print(f"✅ User B joined room: {room_id}")
    print(f"   Room members: {join_result.get('members', 0)}")
    print()
    
    # Step 4: User A updates the diagram
    print("Step 4: User A updating diagram...")
    time.sleep(1)  # Give WebSocket time to settle
    
    update_response = requests.put(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}",
        json={
            "title": "Updated via WebSocket Test",
            "canvas_data": {"shapes": [{"type": "circle", "id": "2"}]}
        },
        headers={"X-User-ID": TEST_USER_ID}
    )
    
    if update_response.status_code != 200:
        print(f"❌ Failed to update diagram: {update_response.status_code}")
        print(update_response.text)
        sio.disconnect()
        return False
    
    print("✅ User A updated diagram")
    print()
    
    # Step 5: Wait for WebSocket notification
    print("Step 5: Waiting for WebSocket notification...")
    time.sleep(2)  # Give time for message to arrive
    
    # Step 6: Verify notification received
    print("Step 6: Verifying notification...")
    if not received_messages:
        print("❌ No WebSocket notification received!")
        sio.disconnect()
        return False
    
    message = received_messages[0]
    print(f"✅ Notification received!")
    print(f"   Type: {message.get('type')}")
    print(f"   Diagram ID: {message.get('diagram_id')}")
    print(f"   User ID: {message.get('user_id')}")
    print(f"   Version: {message.get('version')}")
    print(f"   Timestamp: {message.get('timestamp')}")
    print()
    
    # Verify notification content
    success = True
    
    if message.get('type') != 'diagram_updated':
        print(f"❌ Wrong message type: {message.get('type')}")
        success = False
    
    if message.get('diagram_id') != diagram_id:
        print(f"❌ Wrong diagram ID: {message.get('diagram_id')}")
        success = False
    
    if message.get('user_id') != TEST_USER_ID:
        print(f"❌ Wrong user ID: {message.get('user_id')}")
        success = False
    
    if message.get('version') != 2:  # Should be version 2 after update
        print(f"❌ Wrong version: {message.get('version')}")
        success = False
    
    if not message.get('timestamp'):
        print("❌ Missing timestamp")
        success = False
    
    # Step 7: Cleanup
    print("Step 7: Cleaning up...")
    sio.disconnect()
    print("✅ Disconnected from WebSocket")
    print()
    
    # Summary
    print("=" * 80)
    if success:
        print("✅ TEST PASSED: WebSocket notification working correctly!")
        print()
        print("Summary:")
        print("  • User A and User B both viewing diagram")
        print("  • User A updated diagram")
        print("  • WebSocket message sent to room 'file:<id>'")
        print("  • User B received update notification")
        print("  • User B's canvas can update automatically")
        print("  • No full page reload required")
    else:
        print("❌ TEST FAILED: WebSocket notification not working correctly")
    print("=" * 80)
    
    return success


if __name__ == "__main__":
    try:
        # Create test user first
        if not create_test_user():
            print("❌ Failed to create test user")
            sys.exit(1)
        
        print()
        success = test_websocket_notification()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
