#!/usr/bin/env python3
"""
Validation script for Feature #411: Follow mode - follow another user's viewport
Tests:
1. User B clicks 'Follow User A'
2. User A pans canvas
3. Verify User B's viewport follows
4. User A zooms
5. Verify User B's zoom matches
6. User B clicks 'Unfollow'
7. Verify independent control restored
"""

import asyncio
import socketio
import requests
import sys
from datetime import datetime

COLLAB_URL = "http://localhost:8083"
ROOM_ID = "test_room_follow_mode"

# Track received events
events_received = []


async def test_follow_mode():
    """Test follow mode functionality."""
    print("=" * 80)
    print("FEATURE #411: FOLLOW MODE VALIDATION")
    print("=" * 80)

    # Create two Socket.IO clients for User A and User B
    sio_a = socketio.AsyncClient()
    sio_b = socketio.AsyncClient()

    user_a_id = "test_user_a"
    user_b_id = "test_user_b"

    # Track viewport changes for User B
    user_b_viewport = {'pan_x': 0, 'pan_y': 0, 'zoom': 1.0}
    follow_started = asyncio.Event()
    viewport_sync_received = asyncio.Event()
    viewport_changed_received = []
    follow_stopped = asyncio.Event()

    # Event handlers for User A
    @sio_a.on('connect')
    async def on_connect_a():
        print("✓ User A connected")

    @sio_a.on('user_joined')
    async def on_user_joined_a(data):
        print(f"  User A received: user_joined - {data.get('username')}")

    # Event handlers for User B
    @sio_b.on('connect')
    async def on_connect_b():
        print("✓ User B connected")

    @sio_b.on('user_joined')
    async def on_user_joined_b(data):
        print(f"  User B received: user_joined - {data.get('username')}")

    @sio_b.on('follow_started')
    async def on_follow_started(data):
        print(f"✓ User B received follow_started: following {data.get('following_username')}")
        events_received.append(('follow_started', data))
        follow_started.set()

    @sio_b.on('viewport_sync')
    async def on_viewport_sync(data):
        print(f"✓ User B received viewport_sync: {data.get('viewport')}")
        events_received.append(('viewport_sync', data))
        viewport_sync_received.set()

    @sio_b.on('viewport_changed')
    async def on_viewport_changed(data):
        user_id = data.get('user_id')
        followers = data.get('followers', [])

        # Only apply if User B is in the followers list
        if user_b_id in followers:
            user_b_viewport['pan_x'] = data.get('pan_x')
            user_b_viewport['pan_y'] = data.get('pan_y')
            user_b_viewport['zoom'] = data.get('zoom')
            print(f"✓ User B viewport updated: pan=({user_b_viewport['pan_x']}, {user_b_viewport['pan_y']}), zoom={user_b_viewport['zoom']}")
            viewport_changed_received.append(data)

    @sio_b.on('follow_stopped')
    async def on_follow_stopped(data):
        print(f"✓ User B received follow_stopped")
        events_received.append(('follow_stopped', data))
        follow_stopped.set()

    try:
        # Step 1: Connect both users
        print("\nStep 1: Connecting users...")
        await sio_a.connect(COLLAB_URL)
        await sio_b.connect(COLLAB_URL)
        await asyncio.sleep(0.5)

        # Step 2: Join room
        print("\nStep 2: Users join room...")
        response_a = await sio_a.call('join_room', {
            'room': ROOM_ID,
            'user_id': user_a_id,
            'username': 'User A'
        })
        print(f"  User A join result: {response_a.get('success')}")

        response_b = await sio_b.call('join_room', {
            'room': ROOM_ID,
            'user_id': user_b_id,
            'username': 'User B'
        })
        print(f"  User B join result: {response_b.get('success')}")
        await asyncio.sleep(0.5)

        # Step 3: User B clicks 'Follow User A'
        print("\nStep 3: User B starts following User A...")
        response = await sio_b.call('follow_user', {
            'room': ROOM_ID,
            'follower_id': user_b_id,
            'following_id': user_a_id
        })
        print(f"  Follow request result: {response}")

        # Wait for follow_started event
        await asyncio.wait_for(follow_started.wait(), timeout=2.0)
        print("✓ Follow mode activated")

        # Step 4: User A pans canvas
        print("\nStep 4: User A pans canvas to (100, 200)...")
        viewport_changed_received.clear()
        await sio_a.call('viewport_update', {
            'room': ROOM_ID,
            'user_id': user_a_id,
            'pan_x': 100,
            'pan_y': 200,
            'zoom': 1.0
        })
        await asyncio.sleep(0.5)

        # Step 5: Verify User B's viewport follows (pan)
        print("\nStep 5: Verify User B's viewport followed pan...")
        if user_b_viewport['pan_x'] == 100 and user_b_viewport['pan_y'] == 200:
            print("✓ User B's viewport correctly followed User A's pan")
        else:
            print(f"✗ FAILED: User B's viewport did not follow pan. Got: {user_b_viewport}")
            return False

        # Step 6: User A zooms
        print("\nStep 6: User A zooms to 1.5...")
        viewport_changed_received.clear()
        await sio_a.call('viewport_update', {
            'room': ROOM_ID,
            'user_id': user_a_id,
            'pan_x': 100,
            'pan_y': 200,
            'zoom': 1.5
        })
        await asyncio.sleep(0.5)

        # Step 7: Verify User B's zoom matches
        print("\nStep 7: Verify User B's zoom matches...")
        if user_b_viewport['zoom'] == 1.5:
            print("✓ User B's zoom correctly followed User A's zoom")
        else:
            print(f"✗ FAILED: User B's zoom did not follow. Got: {user_b_viewport['zoom']}")
            return False

        # Step 8: User B clicks 'Unfollow'
        print("\nStep 8: User B unfollows User A...")
        response = await sio_b.call('unfollow_user', {
            'room': ROOM_ID,
            'follower_id': user_b_id
        })
        print(f"  Unfollow request result: {response}")

        # Wait for follow_stopped event
        await asyncio.wait_for(follow_stopped.wait(), timeout=2.0)
        print("✓ Follow mode deactivated")

        # Step 9: Verify independent control restored
        print("\nStep 9: Verify independent control restored...")
        # User A pans again
        user_b_before = dict(user_b_viewport)
        await sio_a.call('viewport_update', {
            'room': ROOM_ID,
            'user_id': user_a_id,
            'pan_x': 300,
            'pan_y': 400,
            'zoom': 2.0
        })
        await asyncio.sleep(0.5)

        # User B's viewport should NOT change
        if user_b_viewport == user_b_before:
            print("✓ User B's viewport remained independent (did not follow)")
        else:
            print(f"✗ FAILED: User B's viewport still following. Before: {user_b_before}, After: {user_b_viewport}")
            return False

        # Step 10: Test HTTP API - get follow relationships
        print("\nStep 10: Test HTTP API - get follow relationships...")

        # Re-establish follow for API test
        await sio_b.call('follow_user', {
            'room': ROOM_ID,
            'follower_id': user_b_id,
            'following_id': user_a_id
        })
        await asyncio.sleep(0.3)

        response = requests.get(f"{COLLAB_URL}/rooms/{ROOM_ID}/follow-relationships")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ HTTP API returned {data.get('count')} follow relationship(s)")

            if data.get('count') == 1:
                rel = data.get('relationships', [])[0]
                if (rel.get('follower_id') == user_b_id and
                    rel.get('following_id') == user_a_id):
                    print("✓ Follow relationship correctly stored")
                else:
                    print(f"✗ FAILED: Incorrect relationship: {rel}")
                    return False
            else:
                print(f"✗ FAILED: Expected 1 relationship, got {data.get('count')}")
                return False
        else:
            print(f"✗ FAILED: HTTP API returned {response.status_code}")
            return False

        print("\n" + "=" * 80)
        print("ALL TESTS PASSED ✓")
        print("=" * 80)
        return True

    except asyncio.TimeoutError:
        print(f"\n✗ FAILED: Timeout waiting for events")
        return False
    except Exception as e:
        print(f"\n✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        try:
            await sio_a.disconnect()
            await sio_b.disconnect()
        except:
            pass


async def main():
    """Main function."""
    # Check if service is healthy
    try:
        response = requests.get(f"{COLLAB_URL}/health", timeout=5)
        if response.status_code != 200:
            print("✗ Collaboration service is not healthy")
            sys.exit(1)
        print("✓ Collaboration service is healthy")
    except Exception as e:
        print(f"✗ Cannot connect to collaboration service: {e}")
        sys.exit(1)

    # Run test
    success = await test_follow_mode()

    if success:
        print("\n✓ Feature #411 validation PASSED")
        sys.exit(0)
    else:
        print("\n✗ Feature #411 validation FAILED")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
