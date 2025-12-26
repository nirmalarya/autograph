#!/usr/bin/env python3
"""
Validation script for Feature #414: Collaborative element locks
Tests:
1. User A locks element for editing
2. Lock icon shown (via lock_element event broadcast)
3. User B attempts to edit same element
4. Blocked with message "Locked by User A"
5. User A unlocks element
6. User B can now edit (lock succeeds)
"""

import socketio
import asyncio
import requests
import time
import sys

BASE_URL = "http://localhost:8083"
ROOM = "file:test-diagram-414"

# Create two Socket.IO clients
sio_userA = socketio.AsyncClient()
sio_userB = socketio.AsyncClient()

# Track events received
events_userA = []
events_userB = []


@sio_userA.event
async def element_locked(data):
    """Track element_locked events for User A"""
    print(f"[User A] Received element_locked: {data}")
    events_userA.append(('element_locked', data))


@sio_userA.event
async def element_unlocked(data):
    """Track element_unlocked events for User A"""
    print(f"[User A] Received element_unlocked: {data}")
    events_userA.append(('element_unlocked', data))


@sio_userB.event
async def element_locked(data):
    """Track element_locked events for User B"""
    print(f"[User B] Received element_locked: {data}")
    events_userB.append(('element_locked', data))


@sio_userB.event
async def element_unlocked(data):
    """Track element_unlocked events for User B"""
    print(f"[User B] Received element_unlocked: {data}")
    events_userB.append(('element_unlocked', data))


async def test_element_locks():
    """Test collaborative element locking feature."""

    try:
        print("\n=== Feature #414: Collaborative Element Locks ===\n")

        # Step 1: Connect both users
        print("Step 1: Connecting users...")
        await sio_userA.connect(f'{BASE_URL}')
        await sio_userB.connect(f'{BASE_URL}')
        print("✓ Both users connected")

        # Join room for both users
        print("\nStep 2: Joining room...")
        await sio_userA.emit('join_room', {
            'room': ROOM,
            'user_id': 'user-a',
            'username': 'User A'
        })
        await sio_userB.emit('join_room', {
            'room': ROOM,
            'user_id': 'user-b',
            'username': 'User B'
        })
        await asyncio.sleep(1)
        print("✓ Both users joined room")

        # Clear event buffers
        events_userA.clear()
        events_userB.clear()

        # Step 3: User A locks element
        print("\nStep 3: User A locks shape-123...")
        result = await sio_userA.call('lock_element', {
            'room': ROOM,
            'element_id': 'shape-123',
            'user_id': 'user-a',
            'username': 'User A'
        })
        print(f"Lock result: {result}")

        if not result.get('success'):
            print(f"✗ Failed to lock element: {result.get('error')}")
            return False

        print("✓ User A locked shape-123")
        await asyncio.sleep(0.5)

        # Verify both users received element_locked event
        userA_received_lock = any(e[0] == 'element_locked' and e[1].get('element_id') == 'shape-123' for e in events_userA)
        userB_received_lock = any(e[0] == 'element_locked' and e[1].get('element_id') == 'shape-123' for e in events_userB)

        if not userA_received_lock or not userB_received_lock:
            print(f"✗ Not all users received element_locked event")
            print(f"  User A received: {userA_received_lock}")
            print(f"  User B received: {userB_received_lock}")
            return False

        print("✓ Both users received element_locked event (lock icon shown)")

        # Step 4: User B attempts to lock same element
        print("\nStep 4: User B attempts to lock shape-123...")
        result = await sio_userB.call('lock_element', {
            'room': ROOM,
            'element_id': 'shape-123',
            'user_id': 'user-b',
            'username': 'User B'
        })
        print(f"Lock result: {result}")

        if result.get('success'):
            print("✗ User B should not be able to lock element locked by User A")
            return False

        error_msg = result.get('error', '')
        if 'User A' not in error_msg and 'Locked by' not in error_msg:
            print(f"✗ Error message should mention 'Locked by User A', got: {error_msg}")
            return False

        print(f"✓ User B blocked with message: '{error_msg}'")

        # Step 5: User A unlocks element
        print("\nStep 5: User A unlocks shape-123...")
        events_userA.clear()
        events_userB.clear()

        result = await sio_userA.call('unlock_element', {
            'room': ROOM,
            'element_id': 'shape-123',
            'user_id': 'user-a'
        })
        print(f"Unlock result: {result}")

        if not result.get('success'):
            print(f"✗ Failed to unlock element: {result.get('error')}")
            return False

        print("✓ User A unlocked shape-123")
        await asyncio.sleep(0.5)

        # Verify both users received element_unlocked event
        userA_received_unlock = any(e[0] == 'element_unlocked' and e[1].get('element_id') == 'shape-123' for e in events_userA)
        userB_received_unlock = any(e[0] == 'element_unlocked' and e[1].get('element_id') == 'shape-123' for e in events_userB)

        if not userA_received_unlock or not userB_received_unlock:
            print(f"✗ Not all users received element_unlocked event")
            return False

        print("✓ Both users received element_unlocked event")

        # Step 6: User B can now lock element
        print("\nStep 6: User B now locks shape-123...")
        result = await sio_userB.call('lock_element', {
            'room': ROOM,
            'element_id': 'shape-123',
            'user_id': 'user-b',
            'username': 'User B'
        })
        print(f"Lock result: {result}")

        if not result.get('success'):
            print(f"✗ User B should be able to lock after User A unlocked: {result.get('error')}")
            return False

        print("✓ User B successfully locked shape-123")

        # Test HTTP endpoint
        print("\nStep 7: Verify HTTP endpoint...")
        response = requests.get(f"{BASE_URL}/element-locks/{ROOM}")
        locks_data = response.json()
        print(f"Locks data: {locks_data}")

        if locks_data.get('count') != 1:
            print(f"✗ Expected 1 lock, got {locks_data.get('count')}")
            return False

        if 'shape-123' not in locks_data.get('locks', {}):
            print("✗ shape-123 should be in locks")
            return False

        if locks_data['locks']['shape-123']['user_id'] != 'user-b':
            print(f"✗ shape-123 should be locked by user-b")
            return False

        print("✓ HTTP endpoint returns correct lock data")

        # Cleanup
        await sio_userB.call('unlock_element', {
            'room': ROOM,
            'element_id': 'shape-123',
            'user_id': 'user-b'
        })

        print("\n=== All Steps Passed! ===")
        print("✓ User A locks shape for editing")
        print("✓ Lock icon shown (element_locked event)")
        print("✓ User B attempts to edit")
        print("✓ Blocked with message: 'Locked by User A'")
        print("✓ User A unlocks")
        print("✓ User B can now edit")
        print("\nFeature #414: PASSING ✅")

        return True

    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Disconnect
        if sio_userA.connected:
            await sio_userA.disconnect()
        if sio_userB.connected:
            await sio_userB.disconnect()


async def main():
    """Main entry point."""
    success = await test_element_locks()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
