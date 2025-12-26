#!/usr/bin/env python3
"""
Feature #418: Real-time collaboration: Collaborative permissions: editor can edit

VALIDATION TEST:
This test verifies that users with EDITOR role CAN perform all editing operations.
This is the complement to feature #417 (viewer permissions).

TEST SCENARIO:
1. Connect two users via Socket.IO
2. Both users join a room as EDITOR role
3. Verify that both users can successfully:
   - Update diagram (diagram_update)
   - Create shapes (shape_created)
   - Edit elements (element_edit)
   - Delete shapes (shape_deleted)
   - Lock elements (lock_element)
4. Verify NO operations return permission_denied errors
"""

import asyncio
import socketio

# Test configuration
COLLABORATION_URL = "http://localhost:8083"
TEST_ROOM_ID = "test_editor_permissions_418"
USER_A_NAME = "Alice (Editor A)"
USER_A_ID = "editor_a_418"
USER_B_NAME = "Bob (Editor B)"
USER_B_ID = "editor_b_418"

# Global results
test_results = {
    "connect_user_a": False,
    "connect_user_b": False,
    "user_a_join": False,
    "user_b_join": False,
    "user_a_diagram_update": False,
    "user_a_shape_created": False,
    "user_a_element_edit": False,
    "user_a_shape_deleted": False,
    "user_a_lock_element": False,
    "user_b_diagram_update": False,
    "user_b_shape_created": False,
    "user_b_element_edit": False,
    "user_b_shape_deleted": False,
    "user_b_lock_element": False,
}

# Track events
events_received = {
    "user_a": [],
    "user_b": []
}


async def run_test():
    """Main test function."""
    print("\n" + "=" * 70)
    print("FEATURE #418: Editor Can Edit - Permission Verification Test")
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

    @sio_a.on('diagram_update')
    async def on_diagram_update_a(data):
        events_received["user_a"].append(("diagram_update", data))

    # Event handlers for User B
    @sio_b.on('connect')
    async def on_connect_b():
        test_results["connect_user_b"] = True
        print(f"✓ User B ({USER_B_NAME}) connected")

    @sio_b.on('user_joined')
    async def on_user_joined_b(data):
        events_received["user_b"].append(("user_joined", data))

    @sio_b.on('diagram_update')
    async def on_diagram_update_b(data):
        events_received["user_b"].append(("diagram_update", data))

    try:
        # Step 1: Connect users
        print("\nStep 1: Connecting users to collaboration service...")
        await sio_a.connect(COLLABORATION_URL)
        await sio_b.connect(COLLABORATION_URL)
        await asyncio.sleep(0.5)

        # Step 2: User A joins as EDITOR
        print("\nStep 2: User A joins room as EDITOR...")
        try:
            join_result_a = await asyncio.wait_for(
                sio_a.call('join_room', {
                    'room': TEST_ROOM_ID,
                    'user_id': USER_A_ID,
                    'username': USER_A_NAME,
                    'role': 'editor'
                }),
                timeout=5.0
            )

            if join_result_a.get('success'):
                test_results["user_a_join"] = True
                print(f"  ✓ User A joined as EDITOR")
            else:
                print(f"  ✗ User A join failed: {join_result_a}")
        except asyncio.TimeoutError:
            print(f"  ✗ User A join timed out")
        except Exception as e:
            print(f"  ✗ User A join error: {e}")

        await asyncio.sleep(0.3)

        # Step 3: User B joins as EDITOR
        print("\nStep 3: User B joins room as EDITOR...")
        try:
            join_result_b = await asyncio.wait_for(
                sio_b.call('join_room', {
                    'room': TEST_ROOM_ID,
                    'user_id': USER_B_ID,
                    'username': USER_B_NAME,
                    'role': 'editor'
                }),
                timeout=5.0
            )

            if join_result_b.get('success'):
                test_results["user_b_join"] = True
                print(f"  ✓ User B joined as EDITOR")
            else:
                print(f"  ✗ User B join failed: {join_result_b}")
        except asyncio.TimeoutError:
            print(f"  ✗ User B join timed out")
        except Exception as e:
            print(f"  ✗ User B join error: {e}")

        await asyncio.sleep(0.3)

        # Step 4: User A attempts editing operations (should ALL succeed)
        print("\nStep 4: User A attempts editing operations (should succeed)...")

        # Test diagram_update
        result = await sio_a.call('diagram_update', {
            'room': TEST_ROOM_ID,
            'user_id': USER_A_ID,
            'delta': {'shapes': [{'id': 'shape_a1', 'type': 'rectangle'}]}
        })

        if result.get('success') and not result.get('permission_denied'):
            test_results["user_a_diagram_update"] = True
            print(f"  ✓ diagram_update ALLOWED (success: {result.get('success')})")
        elif result.get('permission_denied'):
            print(f"  ✗ diagram_update BLOCKED (should be allowed): {result.get('error')}")

        # Test shape_created
        result = await sio_a.call('shape_created', {
            'room': TEST_ROOM_ID,
            'user_id': USER_A_ID,
            'shape': {'id': 'shape_a2', 'type': 'circle'}
        })

        if result.get('success') and not result.get('permission_denied'):
            test_results["user_a_shape_created"] = True
            print(f"  ✓ shape_created ALLOWED")
        elif result.get('permission_denied'):
            print(f"  ✗ shape_created BLOCKED (should be allowed): {result.get('error')}")

        # Test element_edit
        result = await sio_a.call('element_edit', {
            'room': TEST_ROOM_ID,
            'user_id': USER_A_ID,
            'element_id': 'shape_a1',
            'changes': {'color': 'blue'}
        })

        if result.get('success') and not result.get('permission_denied'):
            test_results["user_a_element_edit"] = True
            print(f"  ✓ element_edit ALLOWED")
        elif result.get('permission_denied'):
            print(f"  ✗ element_edit BLOCKED (should be allowed): {result.get('error')}")

        # Test shape_deleted
        result = await sio_a.call('shape_deleted', {
            'room': TEST_ROOM_ID,
            'user_id': USER_A_ID,
            'shape_id': 'shape_a1'
        })

        if result.get('success') and not result.get('permission_denied'):
            test_results["user_a_shape_deleted"] = True
            print(f"  ✓ shape_deleted ALLOWED")
        elif result.get('permission_denied'):
            print(f"  ✗ shape_deleted BLOCKED (should be allowed): {result.get('error')}")

        # Test lock_element
        result = await sio_a.call('lock_element', {
            'room': TEST_ROOM_ID,
            'user_id': USER_A_ID,
            'element_id': 'shape_a2'
        })

        if result.get('success') and not result.get('permission_denied'):
            test_results["user_a_lock_element"] = True
            print(f"  ✓ lock_element ALLOWED")
        elif result.get('permission_denied'):
            print(f"  ✗ lock_element BLOCKED (should be allowed): {result.get('error')}")

        # Step 5: User B attempts editing operations (should ALL succeed)
        print("\nStep 5: User B attempts editing operations (should succeed)...")

        # Test diagram_update
        result = await sio_b.call('diagram_update', {
            'room': TEST_ROOM_ID,
            'user_id': USER_B_ID,
            'delta': {'shapes': [{'id': 'shape_b1', 'type': 'triangle'}]}
        })

        if result.get('success') and not result.get('permission_denied'):
            test_results["user_b_diagram_update"] = True
            print(f"  ✓ diagram_update ALLOWED")
        elif result.get('permission_denied'):
            print(f"  ✗ diagram_update BLOCKED (should be allowed): {result.get('error')}")

        # Test shape_created
        result = await sio_b.call('shape_created', {
            'room': TEST_ROOM_ID,
            'user_id': USER_B_ID,
            'shape': {'id': 'shape_b2', 'type': 'arrow'}
        })

        if result.get('success') and not result.get('permission_denied'):
            test_results["user_b_shape_created"] = True
            print(f"  ✓ shape_created ALLOWED")
        elif result.get('permission_denied'):
            print(f"  ✗ shape_created BLOCKED (should be allowed): {result.get('error')}")

        # Test element_edit
        result = await sio_b.call('element_edit', {
            'room': TEST_ROOM_ID,
            'user_id': USER_B_ID,
            'element_id': 'shape_b1',
            'changes': {'color': 'red'}
        })

        if result.get('success') and not result.get('permission_denied'):
            test_results["user_b_element_edit"] = True
            print(f"  ✓ element_edit ALLOWED")
        elif result.get('permission_denied'):
            print(f"  ✗ element_edit BLOCKED (should be allowed): {result.get('error')}")

        # Test shape_deleted
        result = await sio_b.call('shape_deleted', {
            'room': TEST_ROOM_ID,
            'user_id': USER_B_ID,
            'shape_id': 'shape_b1'
        })

        if result.get('success') and not result.get('permission_denied'):
            test_results["user_b_shape_deleted"] = True
            print(f"  ✓ shape_deleted ALLOWED")
        elif result.get('permission_denied'):
            print(f"  ✗ shape_deleted BLOCKED (should be allowed): {result.get('error')}")

        # Test lock_element
        result = await sio_b.call('lock_element', {
            'room': TEST_ROOM_ID,
            'user_id': USER_B_ID,
            'element_id': 'shape_b2'
        })

        if result.get('success') and not result.get('permission_denied'):
            test_results["user_b_lock_element"] = True
            print(f"  ✓ lock_element ALLOWED")
        elif result.get('permission_denied'):
            print(f"  ✗ lock_element BLOCKED (should be allowed): {result.get('error')}")

    finally:
        # Disconnect
        await sio_a.disconnect()
        await sio_b.disconnect()

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for v in test_results.values() if v)
    total = len(test_results)

    for test_name, result in test_results.items():
        status = "✓" if result else "✗"
        print(f"  {status} {test_name}")

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n🎉 FEATURE #418 VALIDATION: ✅ PASSED")
        print("\nAll editing operations are ALLOWED for EDITOR role users")
        print("Editors have full permissions as expected")
        return True
    else:
        print("\n❌ FEATURE #418 VALIDATION: FAILED")
        print("\nSome editing operations were incorrectly blocked for editors")
        return False


if __name__ == "__main__":
    import sys
    try:
        result = asyncio.run(run_test())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
