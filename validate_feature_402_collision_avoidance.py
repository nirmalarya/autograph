#!/usr/bin/env python3
"""
Feature #402: Real-time collaboration - Collision avoidance
Validation: Warn if two users try to edit the same element

Steps:
1. User A selects and starts editing shape
2. User B attempts to edit same shape
3. Verify warning: 'User A is currently editing this'
4. Verify User B cannot edit
5. User A finishes
6. Verify User B can now edit
"""

import socketio
import asyncio
import requests
import jwt
from datetime import datetime, timedelta
import sys

# Configuration
import os
AUTH_URL = "http://localhost:8085"
COLLAB_URL = "http://localhost:8083"
# Use same JWT secret as the service (must match docker-compose.yml)
JWT_SECRET = os.getenv("JWT_SECRET", "please-set-jwt-secret-in-environment")

def create_test_token(user_id, username, email):
    """Create a JWT token for testing."""
    payload = {
        "user_id": user_id,
        "username": username,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

async def test_collision_avoidance():
    """Test collision avoidance for concurrent element editing."""

    print("=" * 70)
    print("Feature #402: Collision Avoidance - E2E Test")
    print("=" * 70)

    # Create two test users
    user_a_id = "user-a-test-402"
    user_a_name = "Alice"
    user_a_email = "alice@test.com"

    user_b_id = "user-b-test-402"
    user_b_name = "Bob"
    user_b_email = "bob@test.com"

    # Create JWT tokens
    token_a = create_test_token(user_a_id, user_a_name, user_a_email)
    token_b = create_test_token(user_b_id, user_b_name, user_b_email)

    print(f"\n1️⃣  Created test users:")
    print(f"   User A: {user_a_name} ({user_a_id})")
    print(f"   User B: {user_b_name} ({user_b_id})")

    # Room and element IDs
    room_id = "file:test-collision-402"
    element_id = "shape-123"

    # Create Socket.IO clients
    sio_a = socketio.AsyncClient()
    sio_b = socketio.AsyncClient()

    # Track events
    events_a = []
    events_b = []

    @sio_a.event
    async def connect():
        events_a.append("connected")
        print(f"\n2️⃣  User A connected to collaboration service")

    @sio_b.event
    async def connect():
        events_b.append("connected")
        print(f"   User B connected to collaboration service")

    @sio_a.event
    async def element_active(data):
        events_a.append(("element_active", data))

    @sio_b.event
    async def element_active(data):
        events_b.append(("element_active", data))

    try:
        # Connect both users
        await sio_a.connect(
            COLLAB_URL,
            auth={"token": token_a},
            transports=['websocket']
        )

        await sio_b.connect(
            COLLAB_URL,
            auth={"token": token_b},
            transports=['websocket']
        )

        await asyncio.sleep(1)

        # Both users join the room
        print(f"\n3️⃣  Both users joining room: {room_id}")

        result_a = await sio_a.call('join_room', {
            'room': room_id,
            'user_id': user_a_id,
            'username': user_a_name
        })

        result_b = await sio_b.call('join_room', {
            'room': room_id,
            'user_id': user_b_id,
            'username': user_b_name
        })

        if not result_a.get('success') or not result_b.get('success'):
            print("❌ Failed to join room")
            return False

        print(f"   ✅ Both users joined successfully")
        print(f"   Room has {result_b['members']} members")

        await asyncio.sleep(0.5)

        # Step 1: User A starts editing element
        print(f"\n4️⃣  User A starts editing element: {element_id}")

        edit_result_a = await sio_a.call('element_edit', {
            'room': room_id,
            'user_id': user_a_id,
            'element_id': element_id
        })

        if not edit_result_a.get('success'):
            print(f"❌ User A failed to start editing: {edit_result_a}")
            return False

        print(f"   ✅ User A is now editing {element_id}")

        await asyncio.sleep(0.5)

        # Step 2: User B tries to edit the same element (should be rejected)
        print(f"\n5️⃣  User B tries to edit the same element: {element_id}")

        edit_result_b = await sio_b.call('element_edit', {
            'room': room_id,
            'user_id': user_b_id,
            'element_id': element_id
        })

        # Step 3: Verify collision detection
        print(f"\n6️⃣  Checking collision detection...")

        if edit_result_b.get('success'):
            print(f"❌ FAIL: User B was allowed to edit (no collision detection)")
            print(f"   Result: {edit_result_b}")
            return False

        if edit_result_b.get('error') != 'collision':
            print(f"❌ FAIL: Wrong error type: {edit_result_b.get('error')}")
            print(f"   Expected: 'collision'")
            return False

        message = edit_result_b.get('message', '')
        if user_a_name not in message or 'currently editing' not in message:
            print(f"❌ FAIL: Wrong warning message: {message}")
            print(f"   Expected message containing: '{user_a_name} is currently editing this'")
            return False

        editing_user = edit_result_b.get('editing_user', {})
        if editing_user.get('user_id') != user_a_id:
            print(f"❌ FAIL: Wrong editing user ID: {editing_user.get('user_id')}")
            return False

        print(f"   ✅ Collision detected correctly!")
        print(f"   ✅ Warning message: '{message}'")
        print(f"   ✅ Editing user: {editing_user.get('username')} ({editing_user.get('user_id')})")

        # Step 4: User B cannot edit
        print(f"\n7️⃣  Verified: User B cannot edit while User A is editing")

        # Step 5: User A finishes editing
        print(f"\n8️⃣  User A finishes editing (sets element_id to null)")

        finish_result_a = await sio_a.call('element_edit', {
            'room': room_id,
            'user_id': user_a_id,
            'element_id': None  # null means stop editing
        })

        if not finish_result_a.get('success'):
            print(f"❌ User A failed to finish editing: {finish_result_a}")
            return False

        print(f"   ✅ User A stopped editing")

        await asyncio.sleep(0.5)

        # Step 6: User B can now edit
        print(f"\n9️⃣  User B tries to edit again (should succeed now)")

        edit_result_b2 = await sio_b.call('element_edit', {
            'room': room_id,
            'user_id': user_b_id,
            'element_id': element_id
        })

        if not edit_result_b2.get('success'):
            print(f"❌ FAIL: User B still cannot edit after User A finished")
            print(f"   Result: {edit_result_b2}")
            return False

        print(f"   ✅ User B can now edit {element_id}")

        # Cleanup
        await sio_a.call('leave_room', {'room': room_id})
        await sio_b.call('leave_room', {'room': room_id})

        await sio_a.disconnect()
        await sio_b.disconnect()

        print(f"\n{'='*70}")
        print(f"✅ Feature #402: COLLISION AVOIDANCE - ALL TESTS PASSED")
        print(f"{'='*70}")
        print(f"\nVerified:")
        print(f"  ✅ User A can start editing element")
        print(f"  ✅ User B is blocked when trying to edit same element")
        print(f"  ✅ Collision error returned with warning message")
        print(f"  ✅ Warning identifies User A by name")
        print(f"  ✅ User B can edit after User A finishes")
        print(f"\n")

        return True

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if sio_a.connected:
            await sio_a.disconnect()
        if sio_b.connected:
            await sio_b.disconnect()

async def main():
    """Run the test."""
    success = await test_collision_avoidance()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
