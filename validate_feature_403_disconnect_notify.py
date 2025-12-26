#!/usr/bin/env python3
"""
Validate Feature #403: Real-time collaboration disconnect notification

Steps:
- User A and B collaborating
- User A disconnects
- Verify User B sees notification: 'User A left'
- Verify User A's cursor disappears
- Verify User A marked offline
"""

import asyncio
import socketio
import sys
import time

COLLAB_URL = "http://localhost:8083"

async def test_disconnect_notification():
    """Test that disconnect notifications are sent to other users"""

    print("🧪 Testing Feature #403: Disconnect Notification")
    print("=" * 60)

    # Create test diagram and get diagram_id
    import requests
    import psycopg2

    # Register and login user A
    timestamp = int(time.time())
    register_resp = requests.post("http://localhost:8080/api/auth/register", json={
        "username": f"userA_disconnect_{timestamp}",
        "email": f"userA_disconnect_{timestamp}@test.com",
        "password": "TestPass123@"
    })

    if register_resp.status_code not in [200, 201]:
        print(f"❌ Failed to register user A: {register_resp.status_code}")
        print(register_resp.text)
        return False

    userA_data = register_resp.json()
    userA_id = userA_data.get('id')
    print(f"✅ User A registered: {userA_data.get('email')}")

    # Verify email for user A (bypass by updating database directly)
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="autograph",
        user="autograph",
        password="autograph_dev_password"
    )
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_verified = true WHERE id = %s", (userA_id,))
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ User A email verified")

    # Login user A
    login_resp = requests.post("http://localhost:8080/api/auth/login", json={
        "email": f"userA_disconnect_{timestamp}@test.com",
        "password": "TestPass123@"
    })

    if login_resp.status_code != 200:
        print(f"❌ Failed to login user A: {login_resp.status_code}")
        print(login_resp.text)
        return False

    tokenA = login_resp.json().get("access_token")
    print(f"✅ User A logged in")

    # Register and login user B
    timestamp_b = timestamp + 1
    register_resp = requests.post("http://localhost:8080/api/auth/register", json={
        "username": f"userB_disconnect_{timestamp_b}",
        "email": f"userB_disconnect_{timestamp_b}@test.com",
        "password": "TestPass123@"
    })

    if register_resp.status_code not in [200, 201]:
        print(f"❌ Failed to register user B: {register_resp.status_code}")
        return False

    userB_data = register_resp.json()
    userB_id = userB_data.get('id')
    print(f"✅ User B registered: {userB_data.get('email')}")

    # Verify email for user B (bypass by updating database directly)
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="autograph",
        user="autograph",
        password="autograph_dev_password"
    )
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_verified = true WHERE id = %s", (userB_id,))
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ User B email verified")

    # Login user B
    login_resp = requests.post("http://localhost:8080/api/auth/login", json={
        "email": f"userB_disconnect_{timestamp_b}@test.com",
        "password": "TestPass123@"
    })

    if login_resp.status_code != 200:
        print(f"❌ Failed to login user B: {login_resp.status_code}")
        print(login_resp.text)
        return False

    tokenB = login_resp.json().get("access_token")
    print(f"✅ User B logged in")

    # Create a diagram as user A
    diagram_resp = requests.post(
        "http://localhost:8080/api/diagrams",
        headers={"Authorization": f"Bearer {tokenA}"},
        json={
            "title": "Disconnect Test",
            "diagram_type": "canvas"
        }
    )

    if diagram_resp.status_code not in [200, 201]:
        print(f"❌ Failed to create diagram: {diagram_resp.status_code}")
        return False

    diagram_id = diagram_resp.json().get("id")
    print(f"✅ Created test diagram: {diagram_id}")

    # Track events received by user B
    events_received = []
    cursor_removed = False
    user_left = False
    connection_ready_a = asyncio.Event()
    connection_ready_b = asyncio.Event()

    try:
        # Create Socket.IO clients
        sio_a = socketio.AsyncClient()
        sio_b = socketio.AsyncClient()

        # Setup event handlers for user A
        @sio_a.on('connect')
        async def on_connect_a():
            print(f"✅ User A connected to Socket.IO")
            connection_ready_a.set()

        # Setup event handlers for user B
        @sio_b.on('connect')
        async def on_connect_b():
            print(f"✅ User B connected to Socket.IO")
            connection_ready_b.set()

        @sio_b.on('cursor_removed')
        async def on_cursor_removed(data):
            nonlocal cursor_removed
            cursor_removed = True
            events_received.append({'type': 'cursor_removed', 'data': data})
            print(f"   ✓ Received: cursor_removed for user: {data.get('user_id')}")

        @sio_b.on('user_left')
        async def on_user_left(data):
            nonlocal user_left
            user_left = True
            events_received.append({'type': 'user_left', 'data': data})
            print(f"   ✓ Received: user_left - {data.get('username')}")

        @sio_b.on('user_joined')
        async def on_user_joined(data):
            events_received.append({'type': 'user_joined', 'data': data})
            print(f"   ✓ User B received: user_joined - {data.get('username')}")

        @sio_b.on('cursor_move')
        async def on_cursor_move(data):
            events_received.append({'type': 'cursor_move', 'data': data})
            print(f"   ✓ User B received: cursor_move from {data.get('user_id')}")

        # Connect user A
        await sio_a.connect(
            COLLAB_URL,
            auth={'token': tokenA},
            transports=['websocket']
        )
        await connection_ready_a.wait()

        # Join room as user A
        room_id = f"file:{diagram_id}"
        await sio_a.emit('join_room', {'room': room_id})
        await asyncio.sleep(0.5)  # Wait for room join

        # Connect user B
        await sio_b.connect(
            COLLAB_URL,
            auth={'token': tokenB},
            transports=['websocket']
        )
        await connection_ready_b.wait()

        # Join room as user B
        await sio_b.emit('join_room', {'room': room_id})
        await asyncio.sleep(0.5)  # Wait for room join and user_joined event

        # Move cursor as user A to establish presence
        await sio_a.emit('cursor_move', {
            'room': room_id,
            'x': 100,
            'y': 200
        })
        await asyncio.sleep(0.5)  # Wait for cursor_move event

        # Now disconnect user A
        print(f"\n🔌 Disconnecting User A...")
        await sio_a.disconnect()

        # Wait for disconnect events
        print(f"\n📡 Checking events received by User B:")
        await asyncio.sleep(3)  # Wait for disconnect events

        # Disconnect user B
        await sio_b.disconnect()

        # Verify results
        print(f"\n📊 Validation Results:")
        print(f"   Events received: {len(events_received)}")

        success = True

        if not cursor_removed:
            print(f"   ❌ FAIL: cursor_removed event not received")
            success = False
        else:
            print(f"   ✅ cursor_removed event received")

        if not user_left:
            print(f"   ❌ FAIL: user_left event not received")
            success = False
        else:
            print(f"   ✅ user_left event received")

        if success:
            print(f"\n✅ Feature #403 validation PASSED")
            print(f"   - User B notified when User A disconnected")
            print(f"   - Cursor removed event sent")
            print(f"   - User left event sent")
            return True
        else:
            print(f"\n❌ Feature #403 validation FAILED")
            print(f"\nAll events received by User B:")
            for event in events_received:
                print(f"  - {event['type']}: {event['data']}")
            return False

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_disconnect_notification())
    sys.exit(0 if result else 1)
