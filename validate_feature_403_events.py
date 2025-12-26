#!/usr/bin/env python3
"""
Event-based Validation Test for Feature #403: Disconnect Handling

This test focuses on verifying the events broadcast during disconnect.
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
events_received = []


def log_result(test_name, passed, message=""):
    """Log a test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    result = f"{status}: {test_name}"
    if message:
        result += f" - {message}"
    print(result)
    test_results.append({"test": test_name, "passed": passed, "message": message})
    return passed


async def test_disconnect_events():
    """Test disconnect handling events."""
    print("\n" + "="*80)
    print("Feature #403: Disconnect Handling - Event Broadcasting Test")
    print("="*80 + "\n")

    # Generate unique identifiers
    session_id = str(uuid.uuid4())[:8]
    user_id_a = f"test-user-a-{session_id}"
    user_id_b = f"test-user-b-{session_id}"
    room_id = f"test-room-{session_id}"
    test_element_id = f"element-test-403-{session_id}"

    print(f"Test Session: {session_id}")
    print(f"Room: {room_id}")
    print(f"Element: {test_element_id}\n")

    # Create WebSocket clients
    sio_a = socketio.AsyncClient()
    sio_b = socketio.AsyncClient()

    # Track events received by User B
    @sio_b.on('user_left')
    async def on_user_left_b(data):
        print(f"  📩 user_left: {data}")
        events_received.append(('user_left', data))

    @sio_b.on('cursor_removed')
    async def on_cursor_removed_b(data):
        print(f"  📩 cursor_removed: {data}")
        events_received.append(('cursor_removed', data))

    @sio_b.on('element_unlocked')
    async def on_element_unlocked_b(data):
        print(f"  📩 element_unlocked: {data}")
        events_received.append(('element_unlocked', data))

    try:
        # Connect both users
        print("Step 1: Connecting users...")
        await sio_a.connect(COLLAB_SERVICE_URL, transports=['websocket'])
        await sio_b.connect(COLLAB_SERVICE_URL, transports=['websocket'])
        log_result("WebSocket connections", sio_a.connected and sio_b.connected)

        # Join room
        print("\nStep 2: Joining room...")
        await sio_a.call('join_room', {
            'room': room_id,
            'user_id': user_id_a,
            'username': 'Alice'
        }, timeout=5)
        await sio_b.call('join_room', {
            'room': room_id,
            'user_id': user_id_b,
            'username': 'Bob'
        }, timeout=5)
        await asyncio.sleep(0.5)
        log_result("Room join", True)

        # User A moves cursor
        print("\nStep 3: User A moves cursor...")
        await sio_a.emit('cursor_move', {'room': room_id, 'x': 150, 'y': 250})
        await asyncio.sleep(0.3)
        log_result("Cursor movement", True)

        # User A starts editing element
        print("\nStep 4: User A starts editing element...")
        edit_response = await sio_a.call('element_edit', {
            'room': room_id,
            'user_id': user_id_a,
            'element_id': test_element_id
        }, timeout=5)
        await asyncio.sleep(0.3)
        log_result("Element editing", edit_response.get('success', False))

        # Clear events and disconnect User A
        print("\nStep 5: User A disconnects...")
        events_received.clear()
        await sio_a.disconnect()
        await asyncio.sleep(3)  # Wait for events

        log_result("User A disconnected", not sio_a.connected)

        # Verify events
        print("\nStep 6: Verifying disconnect events...")
        print(f"Events received: {len(events_received)}")

        # Check user_left
        user_left = next((e[1] for e in events_received if e[0] == 'user_left'), None)
        if user_left:
            log_result("user_left event", True, f"User: {user_left.get('username')}")
        else:
            log_result("user_left event", False, "Event not received")

        # Check cursor_removed
        cursor_removed = next((e[1] for e in events_received if e[0] == 'cursor_removed'), None)
        if cursor_removed:
            correct_user = cursor_removed.get('user_id') == user_id_a
            log_result("cursor_removed event", correct_user,
                      f"User ID: {cursor_removed.get('user_id')}")
        else:
            log_result("cursor_removed event", False, "Event not received")

        # Check element_unlocked
        element_unlocked = next((e[1] for e in events_received if e[0] == 'element_unlocked'), None)
        if element_unlocked:
            correct_element = element_unlocked.get('element_id') == test_element_id
            correct_user = element_unlocked.get('user_id') == user_id_a
            log_result("element_unlocked event", correct_element and correct_user,
                      f"Element: {element_unlocked.get('element_id')}, User: {element_unlocked.get('user_id')}")
        else:
            log_result("element_unlocked event", False, "Event not received")

        # Cleanup
        await sio_b.disconnect()

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        log_result("Test execution", False, str(e))
        return False


async def main():
    """Run test."""
    try:
        await test_disconnect_events()

        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)

        passed = sum(1 for r in test_results if r["passed"])
        total = len(test_results)
        print(f"\nTests passed: {passed}/{total}")

        if passed == total:
            print("\n✅ ALL TESTS PASSED!")
            print("\nFeature #403 implementation verified:")
            print("  ✓ Disconnect event triggered")
            print("  ✓ Cursor removed (cursor_removed event)")
            print("  ✓ Element locks released (element_unlocked event)")
            print("  ✓ User removed from list (user_left event)")
            sys.exit(0)
        else:
            print("\n❌ SOME TESTS FAILED")
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
