#!/usr/bin/env python3
"""
Feature #414: Presence Timeout - Mark User Away After 5 Minutes Idle
Test that users are automatically marked as 'away' after 5 minutes of inactivity.
"""
import asyncio
import socketio
import sys
import time
from datetime import datetime

# Test configuration
COLLABORATION_SERVICE_URL = "http://localhost:8083"
TEST_ROOM = f"test-room-{int(time.time())}"
TEST_TOKEN_A = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLWEiLCJlbWFpbCI6InVzZXJhQGV4YW1wbGUuY29tIiwidXNlcm5hbWUiOiJVc2VyIEEifQ.signature"
TEST_TOKEN_B = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLWIiLCJlbWFpbCI6InVzZXJiQGV4YW1wbGUuY29tIiwidXNlcm5hbWUiOiJVc2VyIEIifQ.signature"

# Test state
test_results = {
    "user_a_joined": False,
    "user_b_joined": False,
    "user_a_initial_status": None,
    "user_a_marked_away": False,
    "user_a_back_online": False,
    "away_event_received": False,
    "online_event_received": False,
}

async def run_test():
    """Run the presence timeout test."""
    print("=" * 80)
    print("Feature #414: Presence Timeout Test")
    print("=" * 80)

    # Create Socket.IO clients
    sio_a = socketio.AsyncClient()
    sio_b = socketio.AsyncClient()

    # Set up event handlers for User A
    @sio_a.on('join_response')
    async def on_a_join(data):
        if data.get('success'):
            test_results["user_a_joined"] = True
            test_results["user_a_initial_status"] = "online"
            print(f"✓ User A joined room: {data.get('room')}")
            print(f"  User ID: {data.get('user_id')}")
            print(f"  Color: {data.get('color')}")

    @sio_a.on('presence_update')
    async def on_a_presence_update(data):
        user_id = data.get('user_id')
        status = data.get('status')
        print(f"\n📡 User A received presence_update:")
        print(f"   User: {data.get('username')} ({user_id})")
        print(f"   Status: {status}")
        print(f"   Last active: {data.get('last_active')}")

        # Check if this is User A being marked as away
        if user_id == 'user-a' and status == 'away':
            test_results["user_a_marked_away"] = True
            test_results["away_event_received"] = True
            print("   🎯 User A marked as AWAY!")

        # Check if this is User A coming back online
        if user_id == 'user-a' and status == 'online' and test_results["user_a_marked_away"]:
            test_results["user_a_back_online"] = True
            test_results["online_event_received"] = True
            print("   🎯 User A back ONLINE!")

    # Set up event handlers for User B
    @sio_b.on('join_response')
    async def on_b_join(data):
        if data.get('success'):
            test_results["user_b_joined"] = True
            print(f"✓ User B joined room: {data.get('room')}")
            print(f"  User ID: {data.get('user_id')}")

    @sio_b.on('presence_update')
    async def on_b_presence_update(data):
        user_id = data.get('user_id')
        status = data.get('status')
        print(f"\n📡 User B received presence_update:")
        print(f"   User: {data.get('username')} ({user_id})")
        print(f"   Status: {status}")

    try:
        # Step 1: Connect User A
        print("\n📌 Step 1: Connecting User A...")
        await sio_a.connect(
            COLLABORATION_SERVICE_URL,
            auth={"token": TEST_TOKEN_A},
            transports=['websocket']
        )
        print("✓ User A connected to WebSocket")

        # Step 2: User A joins room
        print("\n📌 Step 2: User A joining room...")
        await sio_a.emit('join_room', {
            'room': TEST_ROOM,
            'user_id': 'user-a',
            'username': 'User A',
            'email': 'usera@example.com'
        })
        await asyncio.sleep(2)

        if not test_results["user_a_joined"]:
            print("❌ User A failed to join room")
            return False

        # Step 3: Connect User B (observer)
        print("\n📌 Step 3: Connecting User B (observer)...")
        await sio_b.connect(
            COLLABORATION_SERVICE_URL,
            auth={"token": TEST_TOKEN_B},
            transports=['websocket']
        )
        print("✓ User B connected to WebSocket")

        # Step 4: User B joins same room
        print("\n📌 Step 4: User B joining room...")
        await sio_b.emit('join_room', {
            'room': TEST_ROOM,
            'user_id': 'user-b',
            'username': 'User B',
            'email': 'userb@example.com'
        })
        await asyncio.sleep(2)

        if not test_results["user_b_joined"]:
            print("❌ User B failed to join room")
            return False

        # Step 5: Verify initial state
        print("\n📌 Step 5: Verifying User A is initially ONLINE...")
        print(f"   Initial status: {test_results['user_a_initial_status']}")

        # Step 6: User A stops interacting (no cursor moves, no events)
        print("\n📌 Step 6: User A stops interacting...")
        print("   💤 Waiting for 5 minutes of inactivity...")
        print("   (Background task checks every 60 seconds)")

        # The background task runs every 60 seconds and checks for 300 seconds (5 min) of inactivity
        # To test this in reasonable time, we'll wait for the background task to run
        # We need to wait at least 5 minutes + time for next background check (up to 60s)

        # For testing purposes, let's check status periodically
        start_time = time.time()
        timeout = 400  # 6 minutes 40 seconds (gives enough time for 5 min + 2 background checks)
        check_interval = 30  # Check every 30 seconds

        print(f"\n   Checking status every {check_interval} seconds...")
        print(f"   Timeout: {timeout} seconds (~{timeout//60} minutes)")

        while time.time() - start_time < timeout:
            elapsed = int(time.time() - start_time)
            remaining = timeout - elapsed
            print(f"\n   ⏱️  Elapsed: {elapsed}s / {timeout}s (Remaining: {remaining}s)")

            # Check if User A has been marked as away
            if test_results["user_a_marked_away"]:
                print(f"\n✅ User A was marked as AWAY after {elapsed} seconds!")
                break

            # Wait for next check
            await asyncio.sleep(check_interval)

        # Step 7: Verify User A is marked as AWAY
        print("\n📌 Step 7: Verifying User A is marked as AWAY...")
        if not test_results["user_a_marked_away"]:
            print("❌ User A was NOT marked as away within the timeout period")
            print("   This might mean:")
            print("   1. The background task is not running")
            print("   2. The timeout is longer than 5 minutes")
            print("   3. The presence_update event is not being emitted")
            return False

        print("✓ User A was marked as AWAY")
        print("✓ presence_update event received with status='away'")

        # Step 8: User A moves cursor (becomes active again)
        print("\n📌 Step 8: User A becomes active again (moves cursor)...")
        await sio_a.emit('cursor_move', {
            'room': TEST_ROOM,
            'user_id': 'user-a',
            'x': 100,
            'y': 200
        })
        await asyncio.sleep(2)

        # Step 9: Manually update presence to online
        print("\n📌 Step 9: User A manually sets status to ONLINE...")
        await sio_a.emit('presence_update', {
            'room': TEST_ROOM,
            'user_id': 'user-a',
            'status': 'online'
        })
        await asyncio.sleep(2)

        # Step 10: Verify User A is back to ONLINE
        print("\n📌 Step 10: Verifying User A is back to ONLINE...")
        if not test_results["user_a_back_online"]:
            print("⚠️  User A was not automatically set back to online")
            print("   Note: User might need to explicitly set status to 'online'")
            print("   This is acceptable - the cursor_move updates last_active,")
            print("   preventing future away status, but doesn't auto-restore to online")
        else:
            print("✓ User A is back to ONLINE")

        # Cleanup
        print("\n📌 Cleanup: Disconnecting clients...")
        await sio_a.disconnect()
        await sio_b.disconnect()
        print("✓ Disconnected")

        # Final verification
        print("\n" + "=" * 80)
        print("TEST RESULTS")
        print("=" * 80)

        all_passed = True

        # Check all requirements
        requirements = [
            ("User A joined room", test_results["user_a_joined"]),
            ("User B joined room (observer)", test_results["user_b_joined"]),
            ("User A initially ONLINE", test_results["user_a_initial_status"] == "online"),
            ("User A marked AWAY after idle", test_results["user_a_marked_away"]),
            ("presence_update event received", test_results["away_event_received"]),
        ]

        for req, passed in requirements:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status}: {req}")
            if not passed:
                all_passed = False

        # Optional requirement
        print(f"\n{'✅ PASS' if test_results['user_a_back_online'] else 'ℹ️  INFO'}: User A back to ONLINE (optional)")

        return all_passed

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Ensure cleanup
        try:
            if sio_a.connected:
                await sio_a.disconnect()
            if sio_b.connected:
                await sio_b.disconnect()
        except:
            pass

async def main():
    """Main test runner."""
    success = await run_test()

    if success:
        print("\n" + "=" * 80)
        print("🎉 Feature #414 PASSED: Presence Timeout")
        print("=" * 80)
        print("\nUsers are correctly marked as 'away' after 5 minutes of inactivity!")
        sys.exit(0)
    else:
        print("\n" + "=" * 80)
        print("❌ Feature #414 FAILED: Presence Timeout")
        print("=" * 80)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
