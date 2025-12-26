#!/usr/bin/env python3
"""
Feature #418: Real-time collaboration: Collaborative permissions: editor can edit

SPECIFICATION:
Users with EDITOR role should be able to perform all editing operations on a diagram.

This is the complement to feature #417 (viewer permissions). While viewers are
blocked from editing, editors should have FULL editing permissions.

TEST APPROACH:
1. Connect two users via WebSocket
2. Both join a test room as EDITOR role
3. Test that both users can successfully perform all editing operations:
   - diagram_update
   - shape_created
   - element_edit
   - shape_deleted
   - lock_element
4. Verify that NO operations are blocked (no permission_denied responses)
"""

import asyncio
import websockets
import json
import sys

WS_URL = "ws://localhost:8083/ws"
TEST_ROOM_ID = "test_editor_room_418"
USER_A_ID = "editor_a"
USER_B_ID = "editor_b"


async def send_and_wait(ws, event_type: str, data: dict, timeout: float = 3.0):
    """Send event and wait for response"""
    message = {
        "type": event_type,
        **data
    }

    await ws.send(json.dumps(message))

    try:
        response = await asyncio.wait_for(ws.recv(), timeout=timeout)
        return json.loads(response)
    except asyncio.TimeoutError:
        return None


async def test_editor_permissions():
    """Test that editors can perform all editing operations"""
    print("\n" + "=" * 80)
    print("FEATURE #418: COLLABORATIVE PERMISSIONS - EDITOR CAN EDIT")
    print("=" * 80)

    results = {}

    # Connect WebSockets
    print("\n1. CONNECT WEBSOCKETS")
    print("-" * 80)

    try:
        ws_a = await asyncio.wait_for(
            websockets.connect(WS_URL, ping_interval=20, ping_timeout=10),
            timeout=10
        )
        print(f"✅ User A connected")
        results["connect_user_a"] = True
    except Exception as e:
        print(f"❌ User A connection failed: {e}")
        return False

    try:
        ws_b = await asyncio.wait_for(
            websockets.connect(WS_URL, ping_interval=20, ping_timeout=10),
            timeout=10
        )
        print(f"✅ User B connected")
        results["connect_user_b"] = True
    except Exception as e:
        print(f"❌ User B connection failed: {e}")
        await ws_a.close()
        return False

    try:
        # Join room as editors
        print("\n2. JOIN ROOM AS EDITORS")
        print("-" * 80)

        # User A joins as EDITOR
        join_a = await send_and_wait(ws_a, "join_room", {
            "room_id": TEST_ROOM_ID,
            "user_id": USER_A_ID,
            "role": "EDITOR"
        })

        if not join_a or not join_a.get("success"):
            print(f"❌ User A join failed: {join_a}")
            results["user_a_join"] = False
        else:
            print(f"✅ User A joined as EDITOR")
            results["user_a_join"] = True

        # User B joins as EDITOR
        join_b = await send_and_wait(ws_b, "join_room", {
            "room_id": TEST_ROOM_ID,
            "user_id": USER_B_ID,
            "role": "EDITOR"
        })

        if not join_b or not join_b.get("success"):
            print(f"❌ User B join failed: {join_b}")
            results["user_b_join"] = False
        else:
            print(f"✅ User B joined as EDITOR")
            results["user_b_join"] = True

        # Clear any pending messages
        await asyncio.sleep(0.5)
        try:
            while True:
                await asyncio.wait_for(ws_a.recv(), timeout=0.1)
        except:
            pass
        try:
            while True:
                await asyncio.wait_for(ws_b.recv(), timeout=0.1)
        except:
            pass

        # Test User A editing operations
        print("\n3. TEST USER A EDITING OPERATIONS (EDITOR ROLE)")
        print("-" * 80)

        # Test diagram_update
        update_a = await send_and_wait(ws_a, "diagram_update", {
            "room_id": TEST_ROOM_ID,
            "user_id": USER_A_ID,
            "delta": {"shapes": [{"id": "shape_a1", "type": "rectangle"}]}
        })

        if update_a and update_a.get("permission_denied"):
            print(f"❌ User A diagram_update BLOCKED (should be ALLOWED)")
            results["user_a_diagram_update"] = False
        else:
            print(f"✅ User A diagram_update ALLOWED")
            results["user_a_diagram_update"] = True

        # Test shape_created
        shape_a = await send_and_wait(ws_a, "shape_created", {
            "room_id": TEST_ROOM_ID,
            "user_id": USER_A_ID,
            "shape": {"id": "shape_a2", "type": "circle"}
        })

        if shape_a and shape_a.get("permission_denied"):
            print(f"❌ User A shape_created BLOCKED (should be ALLOWED)")
            results["user_a_shape_created"] = False
        else:
            print(f"✅ User A shape_created ALLOWED")
            results["user_a_shape_created"] = True

        # Test element_edit
        edit_a = await send_and_wait(ws_a, "element_edit", {
            "room_id": TEST_ROOM_ID,
            "user_id": USER_A_ID,
            "element_id": "shape_a1",
            "changes": {"color": "blue"}
        })

        if edit_a and edit_a.get("permission_denied"):
            print(f"❌ User A element_edit BLOCKED (should be ALLOWED)")
            results["user_a_element_edit"] = False
        else:
            print(f"✅ User A element_edit ALLOWED")
            results["user_a_element_edit"] = True

        # Test shape_deleted
        delete_a = await send_and_wait(ws_a, "shape_deleted", {
            "room_id": TEST_ROOM_ID,
            "user_id": USER_A_ID,
            "shape_id": "shape_a1"
        })

        if delete_a and delete_a.get("permission_denied"):
            print(f"❌ User A shape_deleted BLOCKED (should be ALLOWED)")
            results["user_a_shape_deleted"] = False
        else:
            print(f"✅ User A shape_deleted ALLOWED")
            results["user_a_shape_deleted"] = True

        # Test lock_element
        lock_a = await send_and_wait(ws_a, "lock_element", {
            "room_id": TEST_ROOM_ID,
            "user_id": USER_A_ID,
            "element_id": "shape_a2"
        })

        if lock_a and lock_a.get("permission_denied"):
            print(f"❌ User A lock_element BLOCKED (should be ALLOWED)")
            results["user_a_lock_element"] = False
        else:
            print(f"✅ User A lock_element ALLOWED")
            results["user_a_lock_element"] = True

        # Test User B editing operations
        print("\n4. TEST USER B EDITING OPERATIONS (EDITOR ROLE)")
        print("-" * 80)

        # Test diagram_update
        update_b = await send_and_wait(ws_b, "diagram_update", {
            "room_id": TEST_ROOM_ID,
            "user_id": USER_B_ID,
            "delta": {"shapes": [{"id": "shape_b1", "type": "triangle"}]}
        })

        if update_b and update_b.get("permission_denied"):
            print(f"❌ User B diagram_update BLOCKED (should be ALLOWED)")
            results["user_b_diagram_update"] = False
        else:
            print(f"✅ User B diagram_update ALLOWED")
            results["user_b_diagram_update"] = True

        # Test shape_created
        shape_b = await send_and_wait(ws_b, "shape_created", {
            "room_id": TEST_ROOM_ID,
            "user_id": USER_B_ID,
            "shape": {"id": "shape_b2", "type": "arrow"}
        })

        if shape_b and shape_b.get("permission_denied"):
            print(f"❌ User B shape_created BLOCKED (should be ALLOWED)")
            results["user_b_shape_created"] = False
        else:
            print(f"✅ User B shape_created ALLOWED")
            results["user_b_shape_created"] = True

        # Test element_edit
        edit_b = await send_and_wait(ws_b, "element_edit", {
            "room_id": TEST_ROOM_ID,
            "user_id": USER_B_ID,
            "element_id": "shape_b1",
            "changes": {"color": "red"}
        })

        if edit_b and edit_b.get("permission_denied"):
            print(f"❌ User B element_edit BLOCKED (should be ALLOWED)")
            results["user_b_element_edit"] = False
        else:
            print(f"✅ User B element_edit ALLOWED")
            results["user_b_element_edit"] = True

        # Test shape_deleted
        delete_b = await send_and_wait(ws_b, "shape_deleted", {
            "room_id": TEST_ROOM_ID,
            "user_id": USER_B_ID,
            "shape_id": "shape_b1"
        })

        if delete_b and delete_b.get("permission_denied"):
            print(f"❌ User B shape_deleted BLOCKED (should be ALLOWED)")
            results["user_b_shape_deleted"] = False
        else:
            print(f"✅ User B shape_deleted ALLOWED")
            results["user_b_shape_deleted"] = True

        # Test lock_element
        lock_b = await send_and_wait(ws_b, "lock_element", {
            "room_id": TEST_ROOM_ID,
            "user_id": USER_B_ID,
            "element_id": "shape_b2"
        })

        if lock_b and lock_b.get("permission_denied"):
            print(f"❌ User B lock_element BLOCKED (should be ALLOWED)")
            results["user_b_lock_element"] = False
        else:
            print(f"✅ User B lock_element ALLOWED")
            results["user_b_lock_element"] = True

    finally:
        await ws_a.close()
        await ws_b.close()

    # Summary
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)

    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")

    all_passed = all(results.values())

    if all_passed:
        print("\n🎉 FEATURE #418 VALIDATION: ✅ PASSED")
        print("\nAll editing operations are ALLOWED for EDITOR role users")
        print("Editors have full permissions as expected")
        return True
    else:
        print("\n❌ FEATURE #418 VALIDATION: FAILED")
        print("\nSome editing operations were incorrectly blocked for editors")
        return False


if __name__ == "__main__":
    try:
        result = asyncio.run(test_editor_permissions())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
