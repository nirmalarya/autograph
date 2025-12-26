#!/usr/bin/env python3
"""
Validation Test for Feature #403: Disconnect Handling - Clean up on disconnect

Test Steps:
1. User A connected
2. User A closes browser (disconnect)
3. Verify disconnect event triggered
4. Verify User A's cursor removed
5. Verify User A removed from user list
6. Verify User A's locks released (if editing)
"""

import asyncio
import socketio
import requests
import json
import sys
from datetime import datetime

# Configuration
AUTH_SERVICE_URL = "http://localhost:8080/api/auth"
COLLAB_SERVICE_URL = "http://localhost:8083"
DIAGRAM_SERVICE_URL = "http://localhost:8082"

# Test state
test_results = []
events_received = {
    'user_a': [],
    'user_b': []
}


def log_result(test_name, passed, message=""):
    """Log a test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    result = f"{status}: {test_name}"
    if message:
        result += f" - {message}"
    print(result)
    test_results.append({"test": test_name, "passed": passed, "message": message})
    return passed


async def register_and_login(username, email, password):
    """Register and login a user."""
    try:
        # Register
        register_response = requests.post(
            f"{AUTH_SERVICE_URL}/register",
            json={"username": username, "email": email, "password": password},
            timeout=5
        )

        # Login
        login_response = requests.post(
            f"{AUTH_SERVICE_URL}/login",
            json={"email": email, "password": password},
            timeout=5
        )

        if login_response.status_code == 200:
            data = login_response.json()
            return data.get("access_token"), data.get("user", {}).get("id")
        return None, None
    except Exception as e:
        print(f"Error during auth: {e}")
        return None, None


async def create_test_diagram(token):
    """Create a test diagram."""
    try:
        response = requests.post(
            f"{DIAGRAM_SERVICE_URL}/diagrams",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": f"Feature 403 Test - {datetime.now().isoformat()}",
                "content": {"elements": []},
                "diagram_type": "canvas"
            },
            timeout=5
        )

        if response.status_code in [200, 201]:
            return response.json().get("id")
        return None
    except Exception as e:
        print(f"Error creating diagram: {e}")
        return None


async def test_disconnect_cleanup():
    """Test disconnect handling with complete cleanup."""
    print("\n" + "="*80)
    print("Feature #403: Disconnect Handling - Clean up on disconnect")
    print("="*80 + "\n")

    # Step 1: Register and login users
    print("Step 1: Register and login users...")
    token_a, user_id_a = await register_and_login(
        f"alice_disconnect_{datetime.now().timestamp()}",
        f"alice_disconnect_{datetime.now().timestamp()}@test.com",
        "SecurePass123!"
    )

    token_b, user_id_b = await register_and_login(
        f"bob_disconnect_{datetime.now().timestamp()}",
        f"bob_disconnect_{datetime.now().timestamp()}@test.com",
        "SecurePass123!"
    )

    if not token_a or not token_b:
        log_result("User authentication", False, "Failed to authenticate users")
        return False

    log_result("User authentication", True, f"Users authenticated: {user_id_a}, {user_id_b}")

    # Step 2: Create test diagram
    print("\nStep 2: Create test diagram...")
    diagram_id = await create_test_diagram(token_a)

    if not diagram_id:
        log_result("Diagram creation", False, "Failed to create test diagram")
        return False

    log_result("Diagram creation", True, f"Diagram created: {diagram_id}")
    room_id = f"file:{diagram_id}"

    # Step 3: Connect User A and User B to the room
    print("\nStep 3: Connect users to WebSocket...")

    sio_a = socketio.AsyncClient()
    sio_b = socketio.AsyncClient()

    # Setup event handlers for User B to monitor disconnection events
    @sio_b.on('user_left')
    async def on_user_left_b(data):
        events_received['user_b'].append(('user_left', data))
        print(f"  User B received user_left event: {data}")

    @sio_b.on('cursor_removed')
    async def on_cursor_removed_b(data):
        events_received['user_b'].append(('cursor_removed', data))
        print(f"  User B received cursor_removed event: {data}")

    @sio_b.on('element_unlocked')
    async def on_element_unlocked_b(data):
        events_received['user_b'].append(('element_unlocked', data))
        print(f"  User B received element_unlocked event: {data}")

    try:
        # Connect both users
        await sio_a.connect(
            COLLAB_SERVICE_URL,
            auth={"token": token_a},
            transports=['websocket']
        )
        log_result("User A connection", sio_a.connected, "User A connected")

        await sio_b.connect(
            COLLAB_SERVICE_URL,
            auth={"token": token_b},
            transports=['websocket']
        )
        log_result("User B connection", sio_b.connected, "User B connected")

        # Join room
        await sio_a.emit('join_room', {
            'room': room_id,
            'user_id': user_id_a,
            'username': 'Alice',
            'role': 'editor'
        })
        await asyncio.sleep(0.5)

        await sio_b.emit('join_room', {
            'room': room_id,
            'user_id': user_id_b,
            'username': 'Bob',
            'role': 'editor'
        })
        await asyncio.sleep(0.5)

        log_result("Users joined room", True, "Both users in room")

        # Step 4: User A moves cursor
        print("\nStep 4: User A moves cursor...")
        await sio_a.emit('cursor_move', {
            'room': room_id,
            'x': 100,
            'y': 200
        })
        await asyncio.sleep(0.5)
        log_result("Cursor movement", True, "User A moved cursor to (100, 200)")

        # Step 5: User A starts editing an element
        print("\nStep 5: User A starts editing element...")
        test_element_id = "element-123"
        await sio_a.emit('update_presence', {
            'room': room_id,
            'user_id': user_id_a,
            'element_id': test_element_id
        })
        await asyncio.sleep(0.5)
        log_result("Start editing", True, f"User A editing element {test_element_id}")

        # Step 6: User A disconnects (simulating browser close)
        print("\nStep 6: User A disconnects (simulating browser close)...")
        events_received['user_b'].clear()  # Clear events before disconnect
        await sio_a.disconnect()
        await asyncio.sleep(2)  # Wait for all disconnect events to propagate

        log_result("User A disconnected", not sio_a.connected, "User A connection closed")

        # Step 7: Verify disconnect event triggered
        print("\nStep 7: Verify disconnect events received...")

        # Check for user_left event
        user_left_events = [e for e in events_received['user_b'] if e[0] == 'user_left']
        if user_left_events:
            log_result("user_left event received", True, f"Data: {user_left_events[0][1]}")
        else:
            log_result("user_left event received", False, "No user_left event received")

        # Step 8: Verify cursor removed
        print("\nStep 8: Verify User A's cursor removed...")
        cursor_removed_events = [e for e in events_received['user_b'] if e[0] == 'cursor_removed']
        if cursor_removed_events:
            event_data = cursor_removed_events[0][1]
            cursor_removed = event_data.get('user_id') == user_id_a
            log_result("Cursor removed event", cursor_removed, f"User: {event_data.get('username')}")
        else:
            log_result("Cursor removed event", False, "No cursor_removed event received")

        # Step 9: Verify element lock released
        print("\nStep 9: Verify User A's locks released...")
        element_unlocked_events = [e for e in events_received['user_b'] if e[0] == 'element_unlocked']
        if element_unlocked_events:
            event_data = element_unlocked_events[0][1]
            lock_released = (
                event_data.get('user_id') == user_id_a and
                event_data.get('element_id') == test_element_id
            )
            log_result("Element lock released", lock_released,
                      f"Element: {event_data.get('element_id')}, User: {event_data.get('username')}")
        else:
            log_result("Element lock released", False, "No element_unlocked event received")

        # Step 10: Verify User A removed from user list (by checking get_users)
        print("\nStep 10: Verify User A removed from user list...")
        users_response = await sio_b.call('get_users', {'room': room_id}, timeout=5)

        if users_response and users_response.get('success'):
            users_list = users_response.get('users', [])
            user_a_in_list = any(u.get('user_id') == user_id_a and u.get('status') == 'online' for u in users_list)

            if user_a_in_list:
                log_result("User removed from list", False,
                          f"User A still in online list: {users_list}")
            else:
                log_result("User removed from list", True,
                          "User A not in online list (expected)")
        else:
            log_result("User removed from list", False, "Could not fetch user list")

        # Cleanup
        await sio_b.disconnect()

        return True

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        log_result("Disconnect cleanup test", False, str(e))
        return False


async def main():
    """Run all tests."""
    try:
        success = await test_disconnect_cleanup()

        # Print summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)

        passed = sum(1 for r in test_results if r["passed"])
        total = len(test_results)

        print(f"\nTests passed: {passed}/{total}")

        if passed == total:
            print("\n✅ ALL TESTS PASSED - Feature #403 is working correctly!")
            sys.exit(0)
        else:
            print("\n❌ SOME TESTS FAILED - Feature #403 needs fixes")
            print("\nFailed tests:")
            for result in test_results:
                if not result["passed"]:
                    print(f"  - {result['test']}: {result['message']}")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
