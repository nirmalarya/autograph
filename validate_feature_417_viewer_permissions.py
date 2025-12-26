#!/usr/bin/env python3
"""
Feature #417: Real-time collaboration: Collaborative permissions: viewer cannot edit

Test Steps:
1. User A (owner) shares with User B (viewer)
2. User B opens diagram
3. Verify User B can see edits
4. User B attempts to draw
5. Verify blocked: 'You have view-only access'
6. Verify User B's cursor visible but no edits allowed

This test validates that the collaboration service correctly enforces
view-only permissions for users with the VIEWER role.
"""

import socketio
import asyncio
import sys
import json

# Test Configuration
COLLABORATION_SERVICE_URL = "http://localhost:8083"
TEST_ROOM = "file:test-diagram-417"
USER_A_ID = "user-a-owner"
USER_B_ID = "user-b-viewer"
USER_A_NAME = "Alice (Owner)"
USER_B_NAME = "Bob (Viewer)"

# Global results
test_results = {
    "connect_user_a": False,
    "connect_user_b": False,
    "user_a_join_as_editor": False,
    "user_b_join_as_viewer": False,
    "user_b_sees_user_a": False,
    "user_b_cursor_visible": False,
    "user_b_diagram_update_blocked": False,
    "user_b_shape_created_blocked": False,
    "user_b_element_edit_blocked": False,
    "user_b_lock_element_blocked": False,
    "viewer_gets_correct_error_message": False,
}

# Track events
events_received = {
    "user_a": [],
    "user_b": []
}


async def run_test():
    """Main test function."""
    print("\n" + "=" * 70)
    print("FEATURE #417: Viewer Cannot Edit - Permission Enforcement Test")
    print("=" * 70)

    # Create socket.io clients
    sio_a = socketio.AsyncClient()
    sio_b = socketio.AsyncClient()

    # Event handlers for User A
    @sio_a.on('connect')
    async def on_connect_a():
        test_results["connect_user_a"] = True
        print(f"✓ User A ({USER_A_NAME}) connected")

    @sio_a.on('user_joined')
    async def on_user_joined_a(data):
        events_received["user_a"].append(("user_joined", data))
        print(f"  User A received user_joined: {data.get('username')}")

    @sio_a.on('cursor_update')
    async def on_cursor_update_a(data):
        events_received["user_a"].append(("cursor_update", data))
        if data.get('user_id') == USER_B_ID:
            test_results["user_b_cursor_visible"] = True
            print(f"  ✓ User A sees User B's cursor at ({data.get('x')}, {data.get('y')})")

    # Event handlers for User B
    @sio_b.on('connect')
    async def on_connect_b():
        test_results["connect_user_b"] = True
        print(f"✓ User B ({USER_B_NAME}) connected")

    @sio_b.on('user_list')
    async def on_user_list_b(data):
        events_received["user_b"].append(("user_list", data))
        users = data.get('users', [])
        for user in users:
            if user.get('user_id') == USER_A_ID:
                test_results["user_b_sees_user_a"] = True
                print(f"  ✓ User B sees User A in room (role: {user.get('role')})")

    @sio_b.on('user_joined')
    async def on_user_joined_b(data):
        events_received["user_b"].append(("user_joined", data))
        # This will be triggered if any user joins after User B

    @sio_b.on('presence_update')
    async def on_presence_update_b(data):
        events_received["user_b"].append(("presence_update", data))

    try:
        # Step 1: Connect both users
        print("\nStep 1: Connecting users to collaboration service...")
        await sio_a.connect(COLLABORATION_SERVICE_URL, socketio_path='/socket.io')
        await sio_b.connect(COLLABORATION_SERVICE_URL, socketio_path='/socket.io')
        await asyncio.sleep(0.5)

        # Step 2: User A joins as EDITOR (owner)
        print("\nStep 2: User A joins room as EDITOR...")
        response_a = await sio_a.call('join_room', {
            'room': TEST_ROOM,
            'user_id': USER_A_ID,
            'username': USER_A_NAME,
            'role': 'editor'
        })
        if response_a.get('success'):
            test_results["user_a_join_as_editor"] = True
            print(f"  ✓ User A joined as EDITOR")
        else:
            print(f"  ✗ User A failed to join: {response_a.get('error')}")
        await asyncio.sleep(0.5)

        # Step 3: User B joins as VIEWER
        print("\nStep 3: User B joins room as VIEWER...")
        response_b = await sio_b.call('join_room', {
            'room': TEST_ROOM,
            'user_id': USER_B_ID,
            'username': USER_B_NAME,
            'role': 'viewer'
        })
        if response_b.get('success'):
            test_results["user_b_join_as_viewer"] = True
            print(f"  ✓ User B joined as VIEWER")
            user_list = response_b.get('users', [])
            print(f"  Users in room: {len(user_list)}")
            # Check if User A is in the user list returned by join_room
            for user in user_list:
                if user.get('user_id') == USER_A_ID:
                    test_results["user_b_sees_user_a"] = True
                    print(f"  ✓ User B sees User A in user list (role: {user.get('role')})")
        else:
            print(f"  ✗ User B failed to join: {response_b.get('error')}")
        await asyncio.sleep(0.5)

        # Step 4: User B moves cursor (should work - viewers can move cursor)
        print("\nStep 4: User B moves cursor...")
        cursor_response = await sio_b.call('cursor_move', {
            'room': TEST_ROOM,
            'user_id': USER_B_ID,
            'x': 100,
            'y': 200
        })
        print(f"  Cursor move result: {cursor_response}")
        await asyncio.sleep(0.5)

        # Step 5: User B attempts diagram_update (should be BLOCKED)
        print("\nStep 5: User B attempts diagram_update (should be blocked)...")
        diagram_update_response = await sio_b.call('diagram_update', {
            'room': TEST_ROOM,
            'user_id': USER_B_ID,
            'update': {'test': 'data'}
        })
        if not diagram_update_response.get('success'):
            test_results["user_b_diagram_update_blocked"] = True
            error = diagram_update_response.get('error', '')
            if error == "You have view-only access":
                test_results["viewer_gets_correct_error_message"] = True
                print(f"  ✓ Diagram update blocked with correct error: '{error}'")
            else:
                print(f"  ⚠ Diagram update blocked but error message wrong: '{error}'")
        else:
            print(f"  ✗ SECURITY ISSUE: Viewer was able to send diagram update!")

        # Step 6: User B attempts shape_created (should be BLOCKED)
        print("\nStep 6: User B attempts shape_created (should be blocked)...")
        shape_response = await sio_b.call('shape_created', {
            'room': TEST_ROOM,
            'user_id': USER_B_ID,
            'shape_type': 'rectangle',
            'shape_id': 'rect-123'
        })
        if not shape_response.get('success'):
            test_results["user_b_shape_created_blocked"] = True
            error = shape_response.get('error', '')
            print(f"  ✓ Shape creation blocked: '{error}'")
        else:
            print(f"  ✗ SECURITY ISSUE: Viewer was able to create shape!")

        # Step 7: User B attempts element_edit (should be BLOCKED)
        print("\nStep 7: User B attempts element_edit (should be blocked)...")
        element_edit_response = await sio_b.call('element_edit', {
            'room': TEST_ROOM,
            'user_id': USER_B_ID,
            'element_id': 'elem-456'
        })
        if not element_edit_response.get('success'):
            test_results["user_b_element_edit_blocked"] = True
            error = element_edit_response.get('error', '')
            print(f"  ✓ Element edit blocked: '{error}'")
        else:
            print(f"  ✗ SECURITY ISSUE: Viewer was able to edit element!")

        # Step 8: User B attempts lock_element (should be BLOCKED)
        print("\nStep 8: User B attempts lock_element (should be blocked)...")
        lock_response = await sio_b.call('lock_element', {
            'room': TEST_ROOM,
            'user_id': USER_B_ID,
            'element_id': 'elem-789',
            'username': USER_B_NAME
        })
        if not lock_response.get('success'):
            test_results["user_b_lock_element_blocked"] = True
            error = lock_response.get('error', '')
            print(f"  ✓ Element lock blocked: '{error}'")
        else:
            print(f"  ✗ SECURITY ISSUE: Viewer was able to lock element!")

        await asyncio.sleep(1)

    except Exception as e:
        print(f"\n✗ Test error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        await sio_a.disconnect()
        await sio_b.disconnect()

    # Print results
    print("\n" + "=" * 70)
    print("TEST RESULTS")
    print("=" * 70)

    all_pass = True
    for test_name, result in test_results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
        if not result:
            all_pass = False

    print("\n" + "=" * 70)
    if all_pass:
        print("✓ FEATURE #417: ALL TESTS PASSED")
        print("Viewer permissions are correctly enforced!")
        print("=" * 70)
        return 0
    else:
        print("✗ FEATURE #417: SOME TESTS FAILED")
        failed_tests = [name for name, result in test_results.items() if not result]
        print(f"Failed tests: {', '.join(failed_tests)}")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_test())
    sys.exit(exit_code)
