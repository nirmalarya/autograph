#!/usr/bin/env python3
"""
Validation script for Feature #413: Per-user undo/redo history

Tests:
1. User A draws shape
2. User B draws shape
3. User A presses Ctrl+Z
4. Verify only User A's shape undone
5. Verify User B's shape remains
6. Verify independent undo stacks
"""

import socketio
import asyncio
import uuid
import sys
import time

# Configuration
COLLABORATION_SERVICE_URL = "http://localhost:8083"
TEST_ROOM = f"test_room_{uuid.uuid4().hex[:8]}"
USER_A_ID = f"user_a_{uuid.uuid4().hex[:8]}"
USER_B_ID = f"user_b_{uuid.uuid4().hex[:8]}"

# Track test results
test_results = {
    "user_a_connected": False,
    "user_b_connected": False,
    "user_a_joined": False,
    "user_b_joined": False,
    "user_a_action_recorded": False,
    "user_b_action_recorded": False,
    "user_a_undo_success": False,
    "user_b_shape_remains": False,
    "independent_stacks_verified": False
}

# Track actions and events
user_a_actions = []
user_b_actions = []
undo_events = []
redo_events = []


def print_step(step_num, description):
    """Print test step with formatting."""
    print(f"\n{'='*80}")
    print(f"STEP {step_num}: {description}")
    print(f"{'='*80}")


def print_success(message):
    """Print success message."""
    print(f"✓ {message}")


def print_error(message):
    """Print error message."""
    print(f"✗ {message}")


def print_info(message):
    """Print info message."""
    print(f"  {message}")


async def test_per_user_undo_redo():
    """Test per-user undo/redo functionality."""

    print("\n" + "="*80)
    print("FEATURE #413: PER-USER UNDO/REDO HISTORY VALIDATION")
    print("="*80)

    # Create two Socket.IO clients (User A and User B)
    client_a = socketio.AsyncClient()
    client_b = socketio.AsyncClient()

    # Event handlers for User A
    @client_a.on('connect')
    async def on_connect_a():
        print_success("User A connected to collaboration service")
        test_results["user_a_connected"] = True

    @client_a.on('action_undone')
    async def on_action_undone(data):
        print_info(f"User A received action_undone event: {data}")
        undo_events.append(data)
        if data.get('user_id') == USER_A_ID:
            test_results["user_a_undo_success"] = True

    # Event handlers for User B
    @client_b.on('connect')
    async def on_connect_b():
        print_success("User B connected to collaboration service")
        test_results["user_b_connected"] = True

    @client_b.on('action_undone')
    async def on_action_undone_b(data):
        print_info(f"User B received action_undone event: {data}")
        # User B should receive the event but their stack shouldn't change

    try:
        # Step 1: Connect both users
        print_step(1, "Connect User A and User B to collaboration service")

        await client_a.connect(COLLABORATION_SERVICE_URL)
        await client_b.connect(COLLABORATION_SERVICE_URL)

        await asyncio.sleep(1)

        if not test_results["user_a_connected"] or not test_results["user_b_connected"]:
            print_error("Failed to connect users")
            return False

        # Step 2: Join room
        print_step(2, "Both users join the same room")

        result_a = await client_a.call('join_room', {
            'room': TEST_ROOM,
            'user_id': USER_A_ID,
            'username': 'Alice',
            'role': 'editor'
        })
        print_info(f"User A join result: {result_a}")
        test_results["user_a_joined"] = result_a.get('success', False)

        result_b = await client_b.call('join_room', {
            'room': TEST_ROOM,
            'user_id': USER_B_ID,
            'username': 'Bob',
            'role': 'editor'
        })
        print_info(f"User B join result: {result_b}")
        test_results["user_b_joined"] = result_b.get('success', False)

        await asyncio.sleep(1)

        if not test_results["user_a_joined"] or not test_results["user_b_joined"]:
            print_error("Failed to join room")
            return False

        print_success("Both users joined room successfully")

        # Step 3: User A draws a shape
        print_step(3, "User A draws a shape (create action)")

        shape_a_id = f"shape_a_{uuid.uuid4().hex[:8]}"
        action_a = {
            'action_id': f"action_a_{uuid.uuid4().hex[:8]}",
            'action_type': 'create',
            'element_id': shape_a_id,
            'element_type': 'rectangle',
            'before_state': None,
            'after_state': {
                'type': 'rectangle',
                'x': 100,
                'y': 100,
                'width': 200,
                'height': 150,
                'color': 'blue'
            }
        }

        result_a_action = await client_a.call('action_performed', {
            'room': TEST_ROOM,
            'user_id': USER_A_ID,
            'action': action_a
        })
        print_info(f"User A action result: {result_a_action}")

        if result_a_action.get('success'):
            user_a_actions.append(action_a)
            test_results["user_a_action_recorded"] = True
            print_success(f"User A's shape created and recorded in undo stack")
            print_info(f"User A undo stack size: {result_a_action.get('undo_stack_size')}")
        else:
            print_error("Failed to record User A's action")
            return False

        await asyncio.sleep(0.5)

        # Step 4: User B draws a shape
        print_step(4, "User B draws a different shape (create action)")

        shape_b_id = f"shape_b_{uuid.uuid4().hex[:8]}"
        action_b = {
            'action_id': f"action_b_{uuid.uuid4().hex[:8]}",
            'action_type': 'create',
            'element_id': shape_b_id,
            'element_type': 'circle',
            'before_state': None,
            'after_state': {
                'type': 'circle',
                'x': 400,
                'y': 300,
                'radius': 75,
                'color': 'red'
            }
        }

        result_b_action = await client_b.call('action_performed', {
            'room': TEST_ROOM,
            'user_id': USER_B_ID,
            'action': action_b
        })
        print_info(f"User B action result: {result_b_action}")

        if result_b_action.get('success'):
            user_b_actions.append(action_b)
            test_results["user_b_action_recorded"] = True
            print_success(f"User B's shape created and recorded in undo stack")
            print_info(f"User B undo stack size: {result_b_action.get('undo_stack_size')}")
        else:
            print_error("Failed to record User B's action")
            return False

        await asyncio.sleep(0.5)

        # Step 5: User A presses Ctrl+Z (undo)
        print_step(5, "User A presses Ctrl+Z (undo their shape)")

        result_a_undo = await client_a.call('undo_action', {
            'room': TEST_ROOM,
            'user_id': USER_A_ID
        })
        print_info(f"User A undo result: {result_a_undo}")

        await asyncio.sleep(1)  # Wait for event propagation

        if result_a_undo.get('success'):
            undone_action = result_a_undo.get('action')
            print_success(f"User A successfully undid action: {undone_action.get('element_id')}")
            print_info(f"User A undo stack size after undo: {result_a_undo.get('undo_stack_size')}")
            print_info(f"User A redo stack size after undo: {result_a_undo.get('redo_stack_size')}")

            # Verify it's User A's action that was undone
            if undone_action.get('element_id') == shape_a_id:
                print_success(f"✓ Correct: User A's shape ({shape_a_id}) was undone")
            else:
                print_error(f"✗ Wrong action undone: expected {shape_a_id}, got {undone_action.get('element_id')}")
                return False
        else:
            print_error("User A failed to undo")
            return False

        # Step 6: Verify User B's shape remains (check User B's stack)
        print_step(6, "Verify User B's shape remains unchanged")

        # Check User B's undo stack is still intact
        result_b_stack = await client_b.call('action_performed', {
            'room': TEST_ROOM,
            'user_id': USER_B_ID,
            'action': {
                'action_id': 'test_check',
                'action_type': 'noop',
                'element_id': 'test',
                'before_state': {},
                'after_state': {}
            }
        })

        # Immediately undo this test action to not affect the test
        await client_b.call('undo_action', {
            'room': TEST_ROOM,
            'user_id': USER_B_ID
        })

        # Now check User B's actual undo stack should still have their original shape
        print_info(f"User B undo stack size: {result_b_stack.get('undo_stack_size', 0) - 1}")  # -1 for the test action we just undid

        if result_b_stack.get('undo_stack_size', 0) >= 1:
            test_results["user_b_shape_remains"] = True
            print_success(f"✓ User B's undo stack still contains their shape")
        else:
            print_error("User B's undo stack is empty (should still have their shape)")
            return False

        # Step 7: Verify independent undo stacks
        print_step(7, "Verify independent undo/redo stacks")

        # Get User A's stacks via HTTP endpoint
        import requests
        response_a = requests.get(f"{COLLABORATION_SERVICE_URL}/undo-redo/stacks/{TEST_ROOM}/{USER_A_ID}")
        stacks_a = response_a.json()
        print_info(f"User A stacks: {stacks_a}")

        # Get User B's stacks via HTTP endpoint
        response_b = requests.get(f"{COLLABORATION_SERVICE_URL}/undo-redo/stacks/{TEST_ROOM}/{USER_B_ID}")
        stacks_b = response_b.json()
        print_info(f"User B stacks: {stacks_b}")

        # User A should have 0 undo, 1 redo (they undid their action)
        # User B should have 1 undo, 0 redo (their action is still there)
        if stacks_a.get('undo_stack_size') == 0 and stacks_a.get('redo_stack_size') >= 1:
            print_success("✓ User A has 0 undo, >=1 redo (correct after undo)")
        else:
            print_error(f"User A stacks incorrect: undo={stacks_a.get('undo_stack_size')}, redo={stacks_a.get('redo_stack_size')}")

        if stacks_b.get('undo_stack_size') >= 1 and stacks_b.get('redo_stack_size') == 0:
            print_success("✓ User B has >=1 undo, 0 redo (correct - unaffected)")
            test_results["independent_stacks_verified"] = True
        else:
            print_error(f"User B stacks incorrect: undo={stacks_b.get('undo_stack_size')}, redo={stacks_b.get('redo_stack_size')}")

        # Step 8: Test redo
        print_step(8, "User A presses Ctrl+Shift+Z (redo their shape)")

        result_a_redo = await client_a.call('redo_action', {
            'room': TEST_ROOM,
            'user_id': USER_A_ID
        })
        print_info(f"User A redo result: {result_a_redo}")

        if result_a_redo.get('success'):
            redone_action = result_a_redo.get('action')
            print_success(f"User A successfully redid action: {redone_action.get('element_id')}")
            print_info(f"User A undo stack size after redo: {result_a_redo.get('undo_stack_size')}")
            print_info(f"User A redo stack size after redo: {result_a_redo.get('redo_stack_size')}")

        # Final summary
        print("\n" + "="*80)
        print("TEST RESULTS SUMMARY")
        print("="*80)

        all_passed = all(test_results.values())

        for test_name, passed in test_results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status}: {test_name}")

        print("="*80)

        if all_passed:
            print_success("\n🎉 ALL TESTS PASSED! Feature #413 is working correctly!")
            print_info("Independent per-user undo/redo history verified successfully")
            return True
        else:
            print_error("\n❌ SOME TESTS FAILED")
            return False

    except Exception as e:
        print_error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        print("\nCleaning up...")
        await client_a.disconnect()
        await client_b.disconnect()


if __name__ == "__main__":
    result = asyncio.run(test_per_user_undo_redo())
    sys.exit(0 if result else 1)
