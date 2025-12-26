#!/usr/bin/env python3
"""
Feature #422: Horizontal Scaling with Redis Pub/Sub
Tests that collaboration service can scale horizontally with multiple instances.

Test Steps:
1. Start 2 collaboration service instances on different ports
2. User A connects to instance 1 (port 8083)
3. User B connects to instance 2 (port 8093)
4. User A makes edit
5. Verify Redis pub/sub broadcasts message
6. Verify User B receives edit on instance 2
7. Verify cross-instance collaboration works
"""
import asyncio
import socketio
import json
import sys
import time
import redis.asyncio as redis
from datetime import datetime

# Test configuration
INSTANCE_1_URL = "http://localhost:8083"
INSTANCE_2_URL = "http://localhost:8093"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
ROOM_ID = "test-room-horizontal-scaling"
TEST_USER_A_TOKEN = None
TEST_USER_B_TOKEN = None

# Track received messages
messages_received_by_user_a = []
messages_received_by_user_b = []
redis_messages = []


async def get_test_tokens():
    """Get JWT tokens for test users."""
    import aiohttp
    import uuid
    import subprocess

    auth_url = "http://localhost:8085"  # Direct to auth service

    # Generate unique emails for this test run
    test_id = str(uuid.uuid4())[:8]
    email_a = f"horizontal-test-a-{test_id}@example.com"
    email_b = f"horizontal-test-b-{test_id}@example.com"
    password = "TestPass123!"

    async with aiohttp.ClientSession() as session:
        # Register User A
        async with session.post(f"{auth_url}/register", json={
            "email": email_a,
            "password": password
        }) as resp:
            if resp.status not in [200, 201]:
                print(f"Failed to register user A: {resp.status}")
                text = await resp.text()
                print(f"Response: {text}")
                return None, None

        # Register User B
        async with session.post(f"{auth_url}/register", json={
            "email": email_b,
            "password": password
        }) as resp:
            if resp.status not in [200, 201]:
                print(f"Failed to register user B: {resp.status}")
                text = await resp.text()
                print(f"Response: {text}")
                return None, None

    # Verify both users via database (since email verification is required)
    verify_cmd = f"docker exec autograph-postgres psql -U autograph -d autograph -c \"UPDATE users SET is_verified = true WHERE email IN ('{email_a}', '{email_b}');\""
    subprocess.run(verify_cmd, shell=True, capture_output=True)
    print(f"✅ Verified users in database")

    async with aiohttp.ClientSession() as session:
        # Login User A
        async with session.post(f"{auth_url}/login", json={
            "email": email_a,
            "password": password
        }) as resp:
            if resp.status == 200:
                data = await resp.json()
                user_a_token = data.get("access_token")
            else:
                print(f"Failed to login user A: {resp.status}")
                text = await resp.text()
                print(f"Response: {text}")
                return None, None

        # Login User B
        async with session.post(f"{auth_url}/login", json={
            "email": email_b,
            "password": password
        }) as resp:
            if resp.status == 200:
                data = await resp.json()
                user_b_token = data.get("access_token")
            else:
                print(f"Failed to login user B: {resp.status}")
                text = await resp.text()
                print(f"Response: {text}")
                return user_a_token, None

    return user_a_token, user_b_token


async def monitor_redis_pubsub():
    """Monitor Redis pub/sub messages for the test room."""
    try:
        r = await redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True
        )

        pubsub = r.pubsub()
        await pubsub.subscribe(f"room:{ROOM_ID}")

        print(f"📡 Redis monitor: Subscribed to room:{ROOM_ID}")

        async for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    redis_messages.append(data)
                    print(f"📡 Redis received: {data.get('type', 'unknown')} from {data.get('user_id', 'unknown')}")
                except json.JSONDecodeError:
                    pass

    except Exception as e:
        print(f"❌ Redis monitor error: {e}")


async def test_horizontal_scaling():
    """Test horizontal scaling with 2 instances."""
    global TEST_USER_A_TOKEN, TEST_USER_B_TOKEN

    print("=" * 80)
    print("TEST: Feature #422 - Horizontal Scaling with Redis")
    print("=" * 80)

    # Step 1: Get auth tokens
    print("\n1️⃣  Getting auth tokens...")
    TEST_USER_A_TOKEN, TEST_USER_B_TOKEN = await get_test_tokens()

    if not TEST_USER_A_TOKEN or not TEST_USER_B_TOKEN:
        print("❌ Failed to get auth tokens")
        return False

    print(f"✅ Got tokens for users A and B")

    # Step 2: Start Redis monitor
    print("\n2️⃣  Starting Redis pub/sub monitor...")
    redis_task = asyncio.create_task(monitor_redis_pubsub())
    await asyncio.sleep(1)  # Let monitor start

    # Step 3: Create Socket.IO clients for both instances
    print("\n3️⃣  Creating Socket.IO clients...")

    sio_a = socketio.AsyncClient()
    sio_b = socketio.AsyncClient()

    # Event handlers for User A (Instance 1)
    @sio_a.on('connect')
    async def on_connect_a():
        print(f"✅ User A connected to Instance 1 ({INSTANCE_1_URL})")

    @sio_a.on('update')
    async def on_update_a(data):
        messages_received_by_user_a.append(data)
        print(f"📥 User A received: {data.get('type', 'unknown')}")

    @sio_a.on('presence_update')
    async def on_presence_a(data):
        print(f"👤 User A - Presence update: {data}")

    # Event handlers for User B (Instance 2)
    @sio_b.on('connect')
    async def on_connect_b():
        print(f"✅ User B connected to Instance 2 ({INSTANCE_2_URL})")

    @sio_b.on('update')
    async def on_update_b(data):
        messages_received_by_user_b.append(data)
        print(f"📥 User B received: {data.get('type', 'unknown')}")

    @sio_b.on('presence_update')
    async def on_presence_b(data):
        print(f"👤 User B - Presence update: {data}")

    # Step 4: Connect to instances
    print("\n4️⃣  Connecting users to different instances...")

    try:
        # User A connects to Instance 1
        await sio_a.connect(
            INSTANCE_1_URL,
            auth={'token': f'Bearer {TEST_USER_A_TOKEN}'},
            transports=['websocket']
        )
        await asyncio.sleep(1)

        # User B connects to Instance 2
        await sio_b.connect(
            INSTANCE_2_URL,
            auth={'token': f'Bearer {TEST_USER_B_TOKEN}'},
            transports=['websocket']
        )
        await asyncio.sleep(1)

    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        redis_task.cancel()
        return False

    # Step 5: Both users join the same room
    print(f"\n5️⃣  Joining room '{ROOM_ID}'...")

    await sio_a.emit('join_room', {
        'room': ROOM_ID,  # The handler expects 'room', not 'room_id'
        'role': 'editor'
    })

    await sio_b.emit('join_room', {
        'room': ROOM_ID,  # The handler expects 'room', not 'room_id'
        'role': 'editor'
    })

    await asyncio.sleep(2)  # Wait for join to complete

    # Step 6: User A sends an edit from Instance 1
    print("\n6️⃣  User A (Instance 1) sends diagram update...")

    update_payload = {
        'type': 'element_update',
        'element_id': 'shape-123',
        'changes': {
            'x': 100,
            'y': 200,
            'width': 150,
            'height': 100,
            'text': 'Cross-instance test'
        },
        'timestamp': datetime.utcnow().isoformat()
    }

    await sio_a.emit('diagram_update', {
        'room': ROOM_ID,
        'update': update_payload
    })

    print(f"📤 User A sent update: {update_payload['element_id']}")

    # Step 7: Wait for message propagation
    print("\n7️⃣  Waiting for message propagation...")
    await asyncio.sleep(3)

    # Step 8: Verify User B received the edit on Instance 2
    print("\n8️⃣  Verifying cross-instance delivery...")

    success = True

    # Check if User B received the edit
    user_b_received_edit = any(
        msg.get('type') == 'element_update' and
        msg.get('element_id') == 'shape-123'
        for msg in messages_received_by_user_b
    )

    if user_b_received_edit:
        print("✅ User B (Instance 2) received edit from User A (Instance 1)")
    else:
        print("❌ User B did NOT receive edit from User A")
        print(f"   User B received {len(messages_received_by_user_b)} messages")
        success = False

    # Check if Redis pub/sub broadcast occurred
    redis_broadcast = any(
        msg.get('type') == 'element_update' and
        msg.get('element_id') == 'shape-123'
        for msg in redis_messages
    )

    if redis_broadcast:
        print("✅ Redis pub/sub broadcast detected")
    else:
        print("❌ No Redis pub/sub broadcast detected")
        print(f"   Redis received {len(redis_messages)} messages")
        success = False

    # Step 9: Test reverse direction (User B → User A)
    print("\n9️⃣  Testing reverse direction (User B → User A)...")

    messages_received_by_user_a.clear()

    reverse_update = {
        'type': 'element_update',
        'element_id': 'shape-456',
        'changes': {
            'x': 300,
            'y': 400,
            'text': 'Reverse test'
        },
        'timestamp': datetime.utcnow().isoformat()
    }

    await sio_b.emit('diagram_update', {
        'room': ROOM_ID,
        'update': reverse_update
    })

    print(f"📤 User B sent update: {reverse_update['element_id']}")

    await asyncio.sleep(3)

    user_a_received_reverse = any(
        msg.get('type') == 'element_update' and
        msg.get('element_id') == 'shape-456'
        for msg in messages_received_by_user_a
    )

    if user_a_received_reverse:
        print("✅ User A (Instance 1) received edit from User B (Instance 2)")
    else:
        print("❌ User A did NOT receive edit from User B")
        success = False

    # Step 10: Cleanup
    print("\n🔟 Cleaning up...")

    await sio_a.disconnect()
    await sio_b.disconnect()
    redis_task.cancel()

    print("\n" + "=" * 80)
    if success:
        print("✅ HORIZONTAL SCALING TEST PASSED")
        print("   • 2 instances running and communicating")
        print("   • Redis pub/sub broadcasting works")
        print("   • Cross-instance collaboration successful")
    else:
        print("❌ HORIZONTAL SCALING TEST FAILED")
        print("   Check that both instances are running:")
        print(f"   - Instance 1: {INSTANCE_1_URL}")
        print(f"   - Instance 2: {INSTANCE_2_URL}")
    print("=" * 80)

    return success


async def main():
    """Main test runner."""
    try:
        success = await test_horizontal_scaling()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
