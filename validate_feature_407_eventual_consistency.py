#!/usr/bin/env python3
"""
Feature #407: Real-time Collaboration - Eventual Consistency
Tests that all clients converge to the same state after concurrent edits.

Test Scenarios:
1. Two clients make concurrent edits to different elements
2. Two clients make concurrent edits to the same element
3. Verify operational transform resolves conflicts
4. Verify all clients converge to identical state
5. Verify no divergence after multiple concurrent operations
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
TEST_ROOM = "test_room_eventual_consistency"

# Generate JWT tokens
# Must match the actual JWT_SECRET used by the service
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
TOKEN_C = generate_token('test_user_c', 'User C', 'user_c@test.com')


async def test_eventual_consistency():
    """Test that concurrent edits lead to eventual consistency."""

    print("=" * 80)
    print("Feature #407: Eventual Consistency Test")
    print("=" * 80)

    # Create three clients to simulate concurrent editing
    client_a = socketio.AsyncClient()
    client_b = socketio.AsyncClient()
    client_c = socketio.AsyncClient()  # Observer client

    # Track state for each client
    states = {
        'client_a': {},
        'client_b': {},
        'client_c': {}
    }

    # Track received updates
    updates_received = {
        'client_a': [],
        'client_b': [],
        'client_c': []
    }

    def create_update_handler(client_name):
        """Create update handler for a specific client."""
        async def handler(data):
            print(f"[{client_name}] Received update: {data}")
            updates_received[client_name].append(data)

            # Update local state
            if 'element_id' in data and 'value' in data:
                states[client_name][data['element_id']] = data['value']
        return handler

    def create_resolved_handler(client_name):
        """Create OT resolved update handler."""
        async def handler(data):
            print(f"[{client_name}] Received OT resolved update: {data}")
            updates_received[client_name].append(data)

            # Update local state with OT-resolved value
            if 'element_id' in data and 'value' in data:
                states[client_name][data['element_id']] = data['value']
                print(f"[{client_name}] State updated: {states[client_name]}")
        return handler

    # Set up event handlers
    client_a.on('update', create_update_handler('client_a'))
    client_a.on('element_update_resolved', create_resolved_handler('client_a'))

    client_b.on('update', create_update_handler('client_b'))
    client_b.on('element_update_resolved', create_resolved_handler('client_b'))

    client_c.on('update', create_update_handler('client_c'))
    client_c.on('element_update_resolved', create_resolved_handler('client_c'))

    try:
        # Step 1: Connect all clients
        print("\n1. Connecting all clients...")
        await client_a.connect(COLLABORATION_SERVICE_URL, auth={'token': TOKEN_A})
        await client_b.connect(COLLABORATION_SERVICE_URL, auth={'token': TOKEN_B})
        await client_c.connect(COLLABORATION_SERVICE_URL, auth={'token': TOKEN_C})
        print("✓ All clients connected")

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
        await client_c.emit('join_room', {
            'room': TEST_ROOM,
            'user_id': 'user_c',
            'username': 'User C (Observer)'
        })
        await asyncio.sleep(1)
        print("✓ All clients joined room")

        # Step 3: Concurrent edits to DIFFERENT elements
        print("\n3. Testing concurrent edits to DIFFERENT elements...")

        # Client A edits element 1
        await client_a.emit('element_update_ot', {
            'room': TEST_ROOM,
            'user_id': 'user_a',
            'element_id': 'element_1',
            'operation_type': 'move',
            'old_value': {'x': 0, 'y': 0},
            'new_value': {'x': 100, 'y': 100}
        })

        # Client B edits element 2 (different element, should not conflict)
        await client_b.emit('element_update_ot', {
            'room': TEST_ROOM,
            'user_id': 'user_b',
            'element_id': 'element_2',
            'operation_type': 'move',
            'old_value': {'x': 0, 'y': 0},
            'new_value': {'x': 200, 'y': 200}
        })

        # Wait for updates to propagate
        await asyncio.sleep(2)

        # Verify all clients have both updates
        print("\n   Verifying state convergence (different elements):")
        print(f"   Client A state: {states['client_a']}")
        print(f"   Client B state: {states['client_b']}")
        print(f"   Client C state: {states['client_c']}")

        # All clients should have both elements
        assert 'element_1' in states['client_a'], "Client A missing element_1"
        assert 'element_2' in states['client_a'], "Client A missing element_2"
        assert 'element_1' in states['client_b'], "Client B missing element_1"
        assert 'element_2' in states['client_b'], "Client B missing element_2"
        assert 'element_1' in states['client_c'], "Client C missing element_1"
        assert 'element_2' in states['client_c'], "Client C missing element_2"

        print("   ✓ All clients converged (different elements)")

        # Step 4: Concurrent edits to SAME element
        print("\n4. Testing concurrent edits to SAME element...")

        # Clear previous state
        updates_received['client_a'].clear()
        updates_received['client_b'].clear()
        updates_received['client_c'].clear()

        # Both clients edit the same element concurrently
        # Client A moves element_3 to (300, 300)
        timestamp_a = datetime.utcnow()
        await client_a.emit('element_update_ot', {
            'room': TEST_ROOM,
            'user_id': 'user_a',
            'element_id': 'element_3',
            'operation_type': 'move',
            'old_value': {'x': 0, 'y': 0},
            'new_value': {'x': 300, 'y': 300}
        })

        # Client B moves element_3 to (400, 400) slightly later
        await asyncio.sleep(0.1)  # Small delay to create ordering
        timestamp_b = datetime.utcnow()
        await client_b.emit('element_update_ot', {
            'room': TEST_ROOM,
            'user_id': 'user_b',
            'element_id': 'element_3',
            'operation_type': 'move',
            'old_value': {'x': 0, 'y': 0},
            'new_value': {'x': 400, 'y': 400}
        })

        # Wait for OT to resolve
        await asyncio.sleep(2)

        print("\n   Verifying OT conflict resolution:")
        print(f"   Client A state for element_3: {states['client_a'].get('element_3')}")
        print(f"   Client B state for element_3: {states['client_b'].get('element_3')}")
        print(f"   Client C state for element_3: {states['client_c'].get('element_3')}")

        # All clients should have the same final state (OT resolved)
        final_state_a = states['client_a'].get('element_3')
        final_state_b = states['client_b'].get('element_3')
        final_state_c = states['client_c'].get('element_3')

        assert final_state_a is not None, "Client A has no state for element_3"
        assert final_state_b is not None, "Client B has no state for element_3"
        assert final_state_c is not None, "Client C has no state for element_3"

        # The key test: all clients converge to the same state
        assert final_state_a == final_state_b == final_state_c, \
            f"States diverged! A={final_state_a}, B={final_state_b}, C={final_state_c}"

        print("   ✓ All clients converged to same state (OT resolved)")
        print(f"   ✓ Final converged state: {final_state_a}")

        # Step 5: Multiple concurrent operations
        print("\n5. Testing multiple concurrent operations...")

        # Clear state
        states['client_a'].clear()
        states['client_b'].clear()
        states['client_c'].clear()
        updates_received['client_a'].clear()
        updates_received['client_b'].clear()
        updates_received['client_c'].clear()

        # Create multiple concurrent operations
        operations = [
            # Client A operations
            {'client': client_a, 'user_id': 'user_a', 'element_id': 'elem_1', 'value': {'size': 100}},
            {'client': client_a, 'user_id': 'user_a', 'element_id': 'elem_2', 'value': {'color': 'red'}},
            # Client B operations
            {'client': client_b, 'user_id': 'user_b', 'element_id': 'elem_1', 'value': {'size': 200}},
            {'client': client_b, 'user_id': 'user_b', 'element_id': 'elem_3', 'value': {'type': 'circle'}},
        ]

        # Send all operations concurrently
        for op in operations:
            await op['client'].emit('element_update_ot', {
                'room': TEST_ROOM,
                'user_id': op['user_id'],
                'element_id': op['element_id'],
                'operation_type': 'update',
                'old_value': {},
                'new_value': op['value']
            })
            await asyncio.sleep(0.05)  # Tiny delay to simulate network

        # Wait for convergence
        await asyncio.sleep(3)

        print("\n   Verifying eventual consistency:")
        print(f"   Client A state: {states['client_a']}")
        print(f"   Client B state: {states['client_b']}")
        print(f"   Client C state: {states['client_c']}")

        # Check that all clients have the same set of elements
        elements_a = set(states['client_a'].keys())
        elements_b = set(states['client_b'].keys())
        elements_c = set(states['client_c'].keys())

        assert elements_a == elements_b == elements_c, \
            f"Element sets diverged! A={elements_a}, B={elements_b}, C={elements_c}"

        print(f"   ✓ All clients have same elements: {elements_a}")

        # Check that conflicting element (elem_1) converged
        if 'elem_1' in states['client_a']:
            assert states['client_a']['elem_1'] == states['client_b']['elem_1'] == states['client_c']['elem_1'], \
                "Conflicting element elem_1 did not converge"
            print(f"   ✓ Conflicting element elem_1 converged to: {states['client_a']['elem_1']}")

        # Step 6: Verify no divergence
        print("\n6. Final convergence verification...")

        # All states should be identical
        assert states['client_a'] == states['client_b'] == states['client_c'], \
            "Final states diverged!"

        print("   ✓ All clients have IDENTICAL final state")
        print("   ✓ No divergence detected")
        print("   ✓ Eventual consistency VERIFIED")

        # Summary
        print("\n" + "=" * 80)
        print("✓ Feature #407: EVENTUAL CONSISTENCY - ALL TESTS PASSED")
        print("=" * 80)
        print("\nTest Results:")
        print("  1. ✓ Concurrent edits to different elements converge")
        print("  2. ✓ Concurrent edits to same element resolved by OT")
        print("  3. ✓ All clients converge to identical state")
        print("  4. ✓ Multiple concurrent operations handled correctly")
        print("  5. ✓ No divergence after conflict resolution")
        print("  6. ✓ Operational transform ensures consistency")
        print("\nConclusion: The system guarantees eventual consistency!")

        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        print("\nDisconnecting clients...")
        try:
            await client_a.disconnect()
            await client_b.disconnect()
            await client_c.disconnect()
        except:
            pass


if __name__ == "__main__":
    success = asyncio.run(test_eventual_consistency())
    exit(0 if success else 1)
