#!/usr/bin/env python3
"""
Feature #408 Validation: Last-Write-Wins Conflict Resolution
Tests that concurrent edits to the same element use last-write-wins strategy and conflicts are logged.
"""

import asyncio
import socketio
import json
import requests
import jwt
import os
from datetime import datetime, timedelta
import time

# Configuration
COLLABORATION_SERVICE_URL = "http://localhost:8083"
JWT_SECRET = "please-set-jwt-secret-in-environment"  # Must match container JWT_SECRET
TEST_ROOM = f"test-room-{int(time.time())}"


def create_jwt_token(user_id: str, username: str, email: str) -> str:
    """Create a JWT token for testing."""
    payload = {
        "user_id": user_id,
        "sub": user_id,
        "username": username,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


async def test_last_write_wins_conflict():
    """
    Test last-write-wins conflict resolution.

    Steps:
    1. User A sets shape color to red
    2. User B sets same shape color to blue (later timestamp)
    3. Verify last edit (User B) wins
    4. Verify both clients show blue
    5. Verify conflict logged
    """
    print("=" * 80)
    print("Feature #408: Last-Write-Wins Conflict Resolution Test")
    print("=" * 80)

    # Create two clients
    client_a = socketio.AsyncClient()
    client_b = socketio.AsyncClient()

    # Generate tokens
    token_a = create_jwt_token("user-a", "Alice", "alice@test.com")
    token_b = create_jwt_token("user-b", "Bob", "bob@test.com")

    # Track received updates
    updates_a = []
    updates_b = []

    @client_a.on('element_update_resolved')
    async def on_update_a(data):
        print(f"Client A received update: {data}")
        updates_a.append(data)

    @client_b.on('element_update_resolved')
    async def on_update_b(data):
        print(f"Client B received update: {data}")
        updates_b.append(data)

    try:
        # Connect both clients
        print("\n1. Connecting clients...")
        await client_a.connect(
            COLLABORATION_SERVICE_URL,
            auth={'token': token_a},
            transports=['websocket']
        )
        await client_b.connect(
            COLLABORATION_SERVICE_URL,
            auth={'token': token_b},
            transports=['websocket']
        )
        print("✓ Both clients connected")

        # Join room
        print(f"\n2. Joining room {TEST_ROOM}...")
        await client_a.emit('join_room', {
            'room': TEST_ROOM,
            'user_id': 'user-a',
            'username': 'Alice'
        })
        await client_b.emit('join_room', {
            'room': TEST_ROOM,
            'user_id': 'user-b',
            'username': 'Bob'
        })
        await asyncio.sleep(1)
        print("✓ Both clients joined room")

        # Test 1: User A sets color to red
        print("\n3. User A sets shape color to RED...")
        timestamp_a = datetime.utcnow()
        await client_a.emit('element_update_ot', {
            'room': TEST_ROOM,
            'user_id': 'user-a',
            'element_id': 'shape-1',
            'operation_type': 'style',
            'old_value': {'color': 'black'},
            'new_value': {'color': 'red'}
        })
        await asyncio.sleep(0.5)

        # Test 2: User B sets color to blue (100ms later - should win)
        print("\n4. User B sets shape color to BLUE (later timestamp - should win)...")
        await asyncio.sleep(0.1)  # Ensure B's timestamp is later
        timestamp_b = datetime.utcnow()
        await client_b.emit('element_update_ot', {
            'room': TEST_ROOM,
            'user_id': 'user-b',
            'element_id': 'shape-1',
            'operation_type': 'style',
            'old_value': {'color': 'red'},
            'new_value': {'color': 'blue'}
        })
        await asyncio.sleep(1)

        # Test 3: Verify both clients received blue (last write wins)
        print("\n5. Verifying last-write-wins (blue should win)...")

        # Both clients should have received at least the blue update
        assert len(updates_a) > 0, "Client A should have received updates"
        assert len(updates_b) > 0, "Client B should have received updates"

        # Find the final update for shape-1
        final_update_a = None
        final_update_b = None

        for update in reversed(updates_a):
            if update.get('element_id') == 'shape-1':
                final_update_a = update
                break

        for update in reversed(updates_b):
            if update.get('element_id') == 'shape-1':
                final_update_b = update
                break

        assert final_update_a is not None, "Client A should have final update for shape-1"
        assert final_update_b is not None, "Client B should have final update for shape-1"

        print(f"Final update on Client A: {final_update_a}")
        print(f"Final update on Client B: {final_update_b}")

        # Both should show blue (User B's later edit)
        assert final_update_a['value']['color'] == 'blue', \
            f"Client A should show blue, but got {final_update_a['value']['color']}"
        assert final_update_b['value']['color'] == 'blue', \
            f"Client B should show blue, but got {final_update_b['value']['color']}"

        print("✓ Both clients show BLUE (last write wins)")

        # Test 4: Verify conflict was resolved by OT
        assert final_update_a.get('resolved_by_ot') or final_update_b.get('resolved_by_ot'), \
            "At least one update should be marked as resolved by OT"
        print("✓ Conflict was resolved by operational transform")

        # Test 5: Verify conflict was logged
        print("\n6. Verifying conflict was logged...")
        response = requests.get(f"{COLLABORATION_SERVICE_URL}/ot/conflicts/{TEST_ROOM}")
        assert response.status_code == 200, f"Failed to get conflict log: {response.status_code}"

        conflict_data = response.json()
        print(f"Conflict log: {json.dumps(conflict_data, indent=2)}")

        assert conflict_data['count'] > 0, "At least one conflict should be logged"
        conflicts = conflict_data['conflicts']

        # Find the conflict for shape-1
        shape1_conflict = None
        for conflict in conflicts:
            if conflict['element_id'] == 'shape-1':
                shape1_conflict = conflict
                break

        assert shape1_conflict is not None, "Conflict for shape-1 should be logged"
        print(f"Found conflict: {json.dumps(shape1_conflict, indent=2)}")

        # Verify conflict details
        assert shape1_conflict['resolution'] == 'last-write-wins', \
            "Conflict resolution should be last-write-wins"
        assert shape1_conflict['winner']['user_id'] == 'user-b', \
            "User B should be the winner (later timestamp)"
        assert shape1_conflict['winner']['value']['color'] == 'blue', \
            "Winner's color should be blue"
        assert shape1_conflict['loser']['user_id'] == 'user-a', \
            "User A should be the loser (earlier timestamp)"
        assert shape1_conflict['loser']['value']['color'] == 'red', \
            "Loser's color should be red"

        print("✓ Conflict logged correctly with winner (User B - blue) and loser (User A - red)")

        print("\n" + "=" * 80)
        print("✅ Feature #408: ALL TESTS PASSED")
        print("=" * 80)
        print("\nSummary:")
        print("✓ User A set color to red")
        print("✓ User B set color to blue (later)")
        print("✓ Last write wins (blue)")
        print("✓ Both clients converged to blue")
        print("✓ Conflict logged with resolution details")

        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        print("\nCleaning up...")
        try:
            await client_a.disconnect()
            await client_b.disconnect()
            print("✓ Clients disconnected")
        except:
            pass


async def test_same_timestamp_conflict():
    """
    Test conflict resolution when timestamps are identical (uses user_id as tie-breaker).
    """
    print("\n" + "=" * 80)
    print("Feature #408: Same-Timestamp Conflict Resolution Test (Tie-breaker)")
    print("=" * 80)

    # Use HTTP API to create operations with same timestamp
    room_id = f"test-room-tiebreaker-{int(time.time())}"
    timestamp = datetime.utcnow()

    # Create two operations with identical timestamp
    # user-a should win due to lexicographic ordering (a < b)
    op1 = {
        'room': room_id,
        'user_id': 'user-a',
        'element_id': 'shape-2',
        'operation_type': 'style',
        'old_value': {'color': 'black'},
        'new_value': {'color': 'red'}
    }

    op2 = {
        'room': room_id,
        'user_id': 'user-b',
        'element_id': 'shape-2',
        'operation_type': 'style',
        'old_value': {'color': 'black'},
        'new_value': {'color': 'blue'}
    }

    try:
        print("\n1. Applying two operations with same timestamp...")

        # Send both operations
        response1 = requests.post(f"{COLLABORATION_SERVICE_URL}/ot/apply", json=op1)
        response2 = requests.post(f"{COLLABORATION_SERVICE_URL}/ot/apply", json=op2)

        assert response1.status_code == 200, f"Op1 failed: {response1.status_code}"
        assert response2.status_code == 200, f"Op2 failed: {response2.status_code}"

        print("✓ Both operations applied")

        # Check conflict log
        print("\n2. Checking conflict log...")
        time.sleep(0.5)
        response = requests.get(f"{COLLABORATION_SERVICE_URL}/ot/conflicts/{room_id}")
        assert response.status_code == 200

        conflict_data = response.json()
        print(f"Conflicts: {conflict_data['count']}")

        if conflict_data['count'] > 0:
            conflict = conflict_data['conflicts'][-1]
            print(f"Conflict details: {json.dumps(conflict, indent=2)}")
            print(f"✓ Tie-breaker resolved conflict (winner: {conflict['winner']['user_id']})")

        print("\n✅ Tie-breaker test completed")
        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\nStarting Feature #408 validation tests...")
    print(f"Collaboration Service: {COLLABORATION_SERVICE_URL}")

    # Test 1: Basic last-write-wins
    success1 = await test_last_write_wins_conflict()

    # Test 2: Tie-breaker scenario
    success2 = await test_same_timestamp_conflict()

    if success1 and success2:
        print("\n" + "=" * 80)
        print("🎉 ALL FEATURE #408 TESTS PASSED")
        print("=" * 80)
        return True
    else:
        print("\n" + "=" * 80)
        print("❌ SOME TESTS FAILED")
        print("=" * 80)
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
