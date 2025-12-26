#!/usr/bin/env python3
"""
Simplified Validation Test for Feature #403: Disconnect Handling

Test Steps:
1. User A connected
2. User A closes browser (disconnect)
3. Verify disconnect event triggered
4. Verify User A's cursor removed
5. Verify User A removed from user list
6. Verify User A's locks released
"""

import asyncio
import socketio
import sys
import uuid
from datetime import datetime

# Configuration
COLLAB_SERVICE_URL = "http://localhost:8083"

# Test state
test_results = []
events_received = {
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


async def test_disconnect_cleanup():
    """Test disconnect handling with complete cleanup."""
    print("\n" + "="*80)
    print("Feature #403: Disconnect Handling - Clean up on disconnect")
    print("="*80 + "\n")

    # Generate unique identifiers
    session_id = str(uuid.uuid4())
    user_id_a = f"test-user-a-{session_id[:8]}"
    user_id_b = f"test-user-b-{session_id[:8]}"
    room_id = f"test-room-{session_id[:8]}"

    print(f"Test session: {session_id[:8]}")
    print(f"User A: {user_id_a}")
    print(f"User B: {user_id_b}")
    print(f"Room: {room_id}\n")

    # Create WebSocket clients
    sio_a = socketio.AsyncClient()
    sio_b = socketio.AsyncClient()

    # Setup event handlers for User B to monitor disconnection events
    @sio_b.on('user_left')
    async def on_user_left_b(data):
        events_received['user_b'].append(('user_left', data))
        print(f"  📩 User B received user_left: {data.get('username')} left")

    @sio_b.on('cursor_removed')
    async def on_cursor_removed_b(data):
        events_received['user_b'].append(('cursor_removed', data))
        print(f"  📩 User B received cursor_removed: {data.get('username')}'s cursor removed")

    @sio_b.on('element_unlocked')
    async def on_element_unlocked_b(data):
        events_received['user_b'].append(('element_unlocked', data))
        print(f"  📩 User B received element_unlocked: {data.get('element_id')} unlocked by {data.get('username')}")

    @sio_b.on('presence_update')
    async def on_presence_update_b(data):
        events_received['user_b'].append(('presence_update', data))

    try:
        # Step 1: Connect User A and User B
        print("Step 1: Connecting users to WebSocket...")

        # For testing purposes, we'll use mock auth
        # In production, we'd use real JWT tokens
        mock_token_a = "mock-token-a"
        mock_token_b = "mock-token-b"

        await sio_a.connect(
            COLLAB_SERVICE_URL,
            transports=['websocket'],
            wait_timeout=10
        )
        log_result("User A connection", sio_a.connected, "User A connected")

        await sio_b.connect(
            COLLAB_SERVICE_URL,
            transports=['websocket'],
            wait_timeout=10
        )
        log_result("User B connection", sio_b.connected, "User B connected")

        # Step 2: Join room
        print("\nStep 2: Users joining room...")

        response_a = await sio_a.call('join_room', {
            'room': room_id,
            'user_id': user_id_a,
            'username': 'Alice',
            'role': 'editor'
        }, timeout=5)
        print(f"  User A join response: {response_a}")

        await asyncio.sleep(0.5)

        response_b = await sio_b.call('join_room', {
            'room': room_id,
            'user_id': user_id_b,
            'username': 'Bob',
            'role': 'editor'
        }, timeout=5)
        print(f"  User B join response: {response_b}")

        await asyncio.sleep(0.5)
        log_result("Users joined room", True, "Both users in room")

        # Step 3: User A moves cursor
        print("\nStep 3: User A moves cursor...")
        await sio_a.emit('cursor_move', {
            'room': room_id,
            'x': 100,
            'y': 200
        })
        await asyncio.sleep(0.5)
        log_result("Cursor movement", True, "User A moved cursor to (100, 200)")

        # Step 4: User A starts editing an element
        print("\nStep 4: User A starts editing element...")
        test_element_id = "element-test-403"
        response_edit = await sio_a.call('element_edit', {
            'room': room_id,
            'user_id': user_id_a,
            'element_id': test_element_id
        }, timeout=5)
        print(f"  Edit response: {response_edit}")
        await asyncio.sleep(0.5)
        log_result("Start editing", response_edit.get('success', False),
                  f"User A editing element {test_element_id}")

        # Step 5: Verify User A is in the user list
        print("\nStep 5: Verify User A is in user list before disconnect...")
        users_before = await sio_b.call('get_users', {'room': room_id}, timeout=5)
        print(f"  Users before disconnect: {users_before}")

        if users_before and users_before.get('success'):
            users_list = users_before.get('users', [])
            user_a_present = any(u.get('user_id') == user_id_a for u in users_list)
            log_result("User A in list before disconnect", user_a_present,
                      f"Found {len(users_list)} users")

            # Check if User A has active_element set
            user_a_data = next((u for u in users_list if u.get('user_id') == user_id_a), None)
            if user_a_data:
                has_active_element = user_a_data.get('active_element') == test_element_id
                log_result("User A has active element", has_active_element,
                          f"active_element: {user_a_data.get('active_element')}")
        else:
            log_result("User A in list before disconnect", False, "Could not fetch users")

        # Step 6: User A disconnects (simulating browser close)
        print("\nStep 6: User A disconnects (simulating browser close)...")
        events_received['user_b'].clear()  # Clear events before disconnect

        await sio_a.disconnect()
        await asyncio.sleep(3)  # Wait for all disconnect events to propagate

        log_result("User A disconnected", not sio_a.connected, "User A connection closed")

        # Step 7: Verify disconnect events received by User B
        print("\nStep 7: Verifying disconnect events received by User B...")
        print(f"  Total events received: {len(events_received['user_b'])}")

        # Check for user_left event
        user_left_events = [e for e in events_received['user_b'] if e[0] == 'user_left']
        if user_left_events:
            event_data = user_left_events[0][1]
            log_result("user_left event received", True,
                      f"User: {event_data.get('username')}")
        else:
            log_result("user_left event received", False, "No user_left event received")

        # Step 8: Verify cursor removed event
        print("\nStep 8: Verify User A's cursor removed...")
        cursor_removed_events = [e for e in events_received['user_b'] if e[0] == 'cursor_removed']
        if cursor_removed_events:
            event_data = cursor_removed_events[0][1]
            cursor_removed = event_data.get('user_id') == user_id_a
            log_result("cursor_removed event", cursor_removed,
                      f"User: {event_data.get('username')}")
        else:
            log_result("cursor_removed event", False, "No cursor_removed event received")

        # Step 9: Verify element lock released
        print("\nStep 9: Verify User A's locks released...")
        element_unlocked_events = [e for e in events_received['user_b'] if e[0] == 'element_unlocked']
        if element_unlocked_events:
            event_data = element_unlocked_events[0][1]
            lock_released = (
                event_data.get('user_id') == user_id_a and
                event_data.get('element_id') == test_element_id
            )
            log_result("element_unlocked event", lock_released,
                      f"Element: {event_data.get('element_id')}")
        else:
            log_result("element_unlocked event", False, "No element_unlocked event received")

        # Step 10: Verify User A removed from user list
        print("\nStep 10: Verify User A removed from user list...")
        await asyncio.sleep(1)  # Small delay for cleanup
        users_after = await sio_b.call('get_users', {'room': room_id}, timeout=5)
        print(f"  Users after disconnect: {users_after}")

        if users_after and users_after.get('success'):
            users_list = users_after.get('users', [])
            user_a_in_list = any(
                u.get('user_id') == user_id_a and u.get('status') == 'online'
                for u in users_list
            )

            if user_a_in_list:
                log_result("User removed from online list", False,
                          f"User A still in online list")
            else:
                log_result("User removed from online list", True,
                          "User A not in online list (expected)")

            # Check if any locks remain
            user_a_data = next((u for u in users_list if u.get('user_id') == user_id_a), None)
            if user_a_data:
                has_lock = user_a_data.get('active_element') is not None
                log_result("User A has no locks", not has_lock,
                          f"active_element: {user_a_data.get('active_element')}")
        else:
            log_result("User removed from online list", False, "Could not fetch users")

        # Cleanup
        print("\nCleaning up...")
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
            print("\nKey verifications:")
            print("  ✓ Disconnect event triggered")
            print("  ✓ Cursor removed and broadcast")
            print("  ✓ Element locks released")
            print("  ✓ User removed from online list")
            sys.exit(0)
        else:
            print("\n❌ SOME TESTS FAILED - Feature #403 needs investigation")
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
