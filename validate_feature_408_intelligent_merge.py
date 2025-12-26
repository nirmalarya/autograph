#!/usr/bin/env python3
"""
Feature #409: Conflict resolution - intelligent merge for complex conflicts

Tests that non-conflicting operations (move + resize) can be intelligently merged.

Test Scenarios:
1. User A moves a shape to (100, 100)
2. User B resizes the same shape to 200x150
3. Verify both operations are applied (intelligent merge)
4. Verify shape is at (100, 100) with size 200x150
5. Verify merge logged (not conflict)
"""

import socketio
import asyncio
import time
import json
import jwt
import os
from datetime import datetime, timedelta

# Test configuration
COLLABORATION_SERVICE_URL = "http://localhost:8083"
TEST_ROOM = "test_room_intelligent_merge"

# Generate JWT tokens
JWT_SECRET = os.getenv('JWT_SECRET', 'please-set-jwt-secret-in-environment')
JWT_ALGORITHM = 'HS256'

def generate_token(user_id, username, email):
    """Generate a JWT token for a test user."""
    payload = {
        'sub': user_id,
        'user_id': user_id,
        'username': username,
        'email': email,
        'exp': datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

TOKEN_A = generate_token('test_user_a', 'User A', 'user_a@test.com')
TOKEN_B = generate_token('test_user_b', 'User B', 'user_b@test.com')


async def test_intelligent_merge():
    """Test intelligent merge of non-conflicting operations."""

    print("=" * 80)
    print("Feature #409: Intelligent Merge for Non-Conflicting Operations")
    print("=" * 80)

    # Create two clients
    client_a = socketio.AsyncClient()
    client_b = socketio.AsyncClient()

    # Track received updates
    updates_a = []
    updates_b = []

    # Track final state
    final_state_a = {}
    final_state_b = {}

    def create_update_handler(client_name, updates_list, state_dict):
        """Create update handler for a specific client."""
        async def handler(data):
            print(f"[{client_name}] Received update: {data}")
            updates_list.append(data)

            # Track element state
            if 'element_id' in data:
                element_id = data['element_id']
                if element_id not in state_dict:
                    state_dict[element_id] = {}

                # Merge properties
                if 'operation_type' in data:
                    if data['operation_type'] == 'move' and 'new_value' in data:
                        if 'x' in data['new_value']:
                            state_dict[element_id]['x'] = data['new_value']['x']
                        if 'y' in data['new_value']:
                            state_dict[element_id]['y'] = data['new_value']['y']
                    elif data['operation_type'] == 'resize' and 'new_value' in data:
                        if 'width' in data['new_value']:
                            state_dict[element_id]['width'] = data['new_value']['width']
                        if 'height' in data['new_value']:
                            state_dict[element_id]['height'] = data['new_value']['height']

        return handler

    def create_operation_handler(client_name, updates_list, state_dict):
        """Create operation_applied handler."""
        async def handler(data):
            print(f"[{client_name}] Operation applied: {data}")
            updates_list.append(data)

            # Extract the actual operation data
            op_data = data.get('data', data)

            if 'element_id' in op_data:
                element_id = op_data['element_id']
                if element_id not in state_dict:
                    state_dict[element_id] = {}

                # Merge properties from operation
                if 'operation_type' in op_data and 'new_value' in op_data:
                    new_value = op_data['new_value']
                    operation_type = op_data['operation_type']

                    if operation_type == 'move':
                        if 'x' in new_value:
                            state_dict[element_id]['x'] = new_value['x']
                        if 'y' in new_value:
                            state_dict[element_id]['y'] = new_value['y']
                    elif operation_type == 'resize':
                        if 'width' in new_value:
                            state_dict[element_id]['width'] = new_value['width']
                        if 'height' in new_value:
                            state_dict[element_id]['height'] = new_value['height']
                    elif operation_type == 'merged':
                        # For merged operations, update all properties from new_value
                        if isinstance(new_value, dict):
                            state_dict[element_id].update(new_value)
        return handler

    # Set up event handlers
    client_a.on('update', create_update_handler('client_a', updates_a, final_state_a))
    client_a.on('operation_applied', create_operation_handler('client_a', updates_a, final_state_a))

    client_b.on('update', create_update_handler('client_b', updates_b, final_state_b))
    client_b.on('operation_applied', create_operation_handler('client_b', updates_b, final_state_b))

    try:
        # Step 1: Connect clients
        print("\n1. Connecting clients...")
        await client_a.connect(COLLABORATION_SERVICE_URL, auth={'token': TOKEN_A})
        await client_b.connect(COLLABORATION_SERVICE_URL, auth={'token': TOKEN_B})
        print("✓ Clients connected")

        # Step 2: Join room
        print("\n2. Joining room...")
        await client_a.emit('join_room', {
            'room': TEST_ROOM,
            'user_id': 'user_a',
            'username': 'User A'
        })
        await client_b.emit('join_room', {
            'room': TEST_ROOM,
            'user_id': 'user_b',
            'username': 'User B'
        })
        await asyncio.sleep(0.5)
        print("✓ Joined room")

        # Step 3: User A moves shape (concurrently with User B resize)
        print("\n3. User A moves shape to (100, 100)...")
        await client_a.emit('operation', {
            'room': TEST_ROOM,
            'user_id': 'user_a',
            'element_id': 'shape_123',
            'operation_type': 'move',
            'old_value': {'x': 0, 'y': 0},
            'new_value': {'x': 100, 'y': 100}
        })

        # Small delay to make operations "concurrent" but not simultaneous
        await asyncio.sleep(0.05)

        # Step 4: User B resizes same shape (concurrent operation)
        print("4. User B resizes same shape to 200x150...")
        await client_b.emit('operation', {
            'room': TEST_ROOM,
            'user_id': 'user_b',
            'element_id': 'shape_123',
            'operation_type': 'resize',
            'old_value': {'width': 50, 'height': 50},
            'new_value': {'width': 200, 'height': 150}
        })

        # Wait for operations to propagate
        await asyncio.sleep(2)

        # Verification
        print("\n" + "=" * 80)
        print("VERIFICATION")
        print("=" * 80)

        all_updates = updates_a + updates_b
        print(f"\nTotal updates received: {len(all_updates)}")
        print(f"User A received: {len(updates_a)} updates")
        print(f"User B received: {len(updates_b)} updates")

        # Test 1: Check for move and merged operations (intelligent merge)
        move_ops = [u for u in all_updates if isinstance(u, dict) and
                   (u.get('operation_type') == 'move' or
                    u.get('data', {}).get('operation_type') == 'move')]
        merged_ops = [u for u in all_updates if isinstance(u, dict) and
                     (u.get('operation_type') == 'merged' or
                      u.get('data', {}).get('operation_type') == 'merged')]

        print(f"\nMove operations found: {len(move_ops)}")
        print(f"Merged operations found: {len(merged_ops)}")

        # With intelligent merge: we should see 1 move operation, then 1 merged operation
        test1_pass = len(move_ops) > 0 and len(merged_ops) > 0
        print(f"\nTest 1: Operations applied (move + merged) - {'✓ PASS' if test1_pass else '✗ FAIL'}")

        # Test 2: Check final state convergence
        print(f"\nFinal state User A: {final_state_a}")
        print(f"Final state User B: {final_state_b}")

        shape_state_a = final_state_a.get('shape_123', {})
        shape_state_b = final_state_b.get('shape_123', {})

        # Both clients should have converged to the same state
        test2_pass = shape_state_a == shape_state_b and len(shape_state_a) > 0
        print(f"\nTest 2: State convergence - {'✓ PASS' if test2_pass else '✗ FAIL'}")

        # Test 3: Check that BOTH move and resize were applied
        # Shape should have position from move AND size from resize
        has_position = 'x' in shape_state_a and 'y' in shape_state_a
        has_size = 'width' in shape_state_a and 'height' in shape_state_a

        test3_pass = has_position and has_size
        print(f"\nTest 3: Intelligent merge (both changes applied) - {'✓ PASS' if test3_pass else '✗ FAIL'}")

        if test3_pass:
            print(f"  Position: ({shape_state_a.get('x')}, {shape_state_a.get('y')})")
            print(f"  Size: {shape_state_a.get('width')}x{shape_state_a.get('height')}")

        # Test 4: Verify expected values
        test4_pass = (shape_state_a.get('x') == 100 and
                      shape_state_a.get('y') == 100 and
                      shape_state_a.get('width') == 200 and
                      shape_state_a.get('height') == 150)
        print(f"\nTest 4: Correct merged values - {'✓ PASS' if test4_pass else '✗ FAIL'}")

        all_pass = test1_pass and test2_pass and test3_pass and test4_pass

        print("\n" + "=" * 80)
        if all_pass:
            print("✓ ALL TESTS PASSED - Feature #409 Working!")
        else:
            print("✗ SOME TESTS FAILED")
        print("=" * 80)

        return all_pass

    finally:
        # Cleanup
        await client_a.disconnect()
        await client_b.disconnect()


if __name__ == "__main__":
    try:
        result = asyncio.run(test_intelligent_merge())
        exit(0 if result else 1)
    except Exception as e:
        print(f"\n✗ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
