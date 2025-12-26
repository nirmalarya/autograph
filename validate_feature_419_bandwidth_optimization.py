#!/usr/bin/env python3
"""
Feature #419: Bandwidth optimization - delta updates only
==========================================================

CONTEXT:
Real-time collaboration should minimize bandwidth usage by sending only
the changed data (deltas), not the entire canvas state on every update.

VALIDATION CRITERIA:
1. When a user moves a shape, only position delta is sent
2. Full canvas_data is NOT transmitted on each update
3. Network payload size is minimal (delta only)
4. Update contains only changed fields (e.g., x, y coordinates)
5. Verify bandwidth efficiency with actual measurements

TEST APPROACH:
- User A joins collaboration room for a diagram
- User A sends a shape movement (position update)
- Capture the exact payload sent to other clients
- Verify payload contains ONLY delta (position change)
- Verify payload does NOT contain full canvas_data
- Measure payload size to confirm bandwidth optimization
"""

import asyncio
import socketio
import json
import sys
from datetime import datetime

# Test configuration
AUTH_SERVICE_URL = "http://localhost:8085"
COLLABORATION_SERVICE_URL = "http://localhost:8083"
API_GATEWAY_URL = "http://localhost:8080"

class BandwidthMonitor:
    """Monitor and track bandwidth usage"""
    def __init__(self):
        self.updates_received = []
        self.total_bytes = 0

    def record_update(self, update_data):
        """Record an update and its size"""
        update_json = json.dumps(update_data)
        size_bytes = len(update_json.encode('utf-8'))

        self.updates_received.append({
            'data': update_data,
            'size_bytes': size_bytes,
            'timestamp': datetime.now().isoformat()
        })
        self.total_bytes += size_bytes

    def get_stats(self):
        """Get bandwidth statistics"""
        return {
            'update_count': len(self.updates_received),
            'total_bytes': self.total_bytes,
            'average_bytes': self.total_bytes / len(self.updates_received) if self.updates_received else 0,
            'updates': self.updates_received
        }

async def verify_email_in_db(email):
    """Verify user email directly in database"""
    import psycopg2
    import os

    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='autograph',
        user='autograph',
        password='autograph_dev_password'
    )
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_verified = true WHERE email = %s", (email,))
    conn.commit()
    cur.close()
    conn.close()

async def register_and_login(username, email, password):
    """Register and login a user, return auth token"""
    import httpx

    async with httpx.AsyncClient(follow_redirects=True) as client:
        # Register
        register_response = await client.post(
            f"{API_GATEWAY_URL}/api/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password
            }
        )

        if register_response.status_code not in [200, 201]:
            # User might already exist, try login
            pass

        # Verify email in database
        await verify_email_in_db(email)

        # Login
        login_response = await client.post(
            f"{API_GATEWAY_URL}/api/auth/login",
            json={
                "email": email,
                "password": password
            }
        )

        if login_response.status_code != 200:
            raise Exception(f"Login failed: {login_response.text}")

        login_data = login_response.json()
        access_token = login_data.get("access_token")

        # Decode JWT to get user_id from "sub" claim
        import jwt
        decoded_token = jwt.decode(access_token, options={"verify_signature": False})
        user_id = decoded_token.get("sub")

        return access_token, user_id

async def create_test_diagram(token, user_id):
    """Create a test diagram for collaboration"""
    import httpx

    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.post(
            f"{API_GATEWAY_URL}/api/diagrams",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": f"Bandwidth Test Diagram {datetime.now().isoformat()}",
                "diagram_type": "tldraw",
                "canvas_data": {
                    "shapes": {
                        "shape1": {
                            "id": "shape1",
                            "type": "rectangle",
                            "x": 100,
                            "y": 100,
                            "width": 200,
                            "height": 150,
                            "color": "blue"
                        }
                    }
                },
                "owner_id": user_id
            }
        )

        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to create diagram (status {response.status_code}): {response.text}")

        response_data = response.json()
        print(f"   DEBUG: Diagram creation response: {response_data}")  # DEBUG
        diagram_id = response_data.get("diagram", {}).get("id") or response_data.get("id")
        return diagram_id

async def test_bandwidth_optimization():
    """
    Test #419: Bandwidth optimization with delta updates
    """
    print("=" * 80)
    print("Feature #419: Bandwidth Optimization - Delta Updates Only")
    print("=" * 80)

    # Test counters
    tests_passed = 0
    tests_failed = 0

    # Bandwidth monitor
    bandwidth_monitor = BandwidthMonitor()

    try:
        # Step 1: Register and login two users
        print("\n1. Setting up users...")
        token_a, user_id_a = await register_and_login(
            "bandwidth_user_a",
            "bandwidth_a@test.com",
            "SecurePass123!"
        )
        print(f"   ✓ User A registered (ID: {user_id_a})")

        token_b, user_id_b = await register_and_login(
            "bandwidth_user_b",
            "bandwidth_b@test.com",
            "SecurePass123!"
        )
        print(f"   ✓ User B registered (ID: {user_id_b})")

        # Step 2: Create a test diagram
        print("\n2. Creating test diagram...")
        diagram_id = await create_test_diagram(token_a, user_id_a)
        print(f"   ✓ Diagram created (ID: {diagram_id})")

        # Step 3: Connect User B to collaboration room (passive listener)
        print("\n3. Connecting User B to room (listener)...")
        sio_b = socketio.AsyncClient()

        update_received = asyncio.Event()
        received_update_data = {}

        @sio_b.on('update')
        async def on_update(data):
            """Capture updates sent to other clients"""
            nonlocal received_update_data
            received_update_data = data
            bandwidth_monitor.record_update(data)
            print(f"   📦 User B received update: {json.dumps(data, indent=2)}")
            update_received.set()

        await sio_b.connect(COLLABORATION_SERVICE_URL)
        await sio_b.emit('join_room', {
            'room': f'file:{diagram_id}',
            'user_id': user_id_b,
            'username': 'bandwidth_user_b',
            'role': 'editor'
        })
        print(f"   ✓ User B joined room: file:{diagram_id}")

        # Step 4: Connect User A and send a delta update (position change only)
        print("\n4. Connecting User A to room...")
        sio_a = socketio.AsyncClient()

        await sio_a.connect(COLLABORATION_SERVICE_URL)
        await sio_a.emit('join_room', {
            'room': f'file:{diagram_id}',
            'user_id': user_id_a,
            'username': 'bandwidth_user_a',
            'role': 'editor'
        })
        print(f"   ✓ User A joined room: file:{diagram_id}")

        # Step 5: User A sends position delta update (ONLY changed fields)
        print("\n5. User A sends position delta update...")
        delta_update = {
            "type": "shape_moved",
            "shape_id": "shape1",
            "x": 150,  # Changed from 100 to 150 (delta: +50)
            "y": 120   # Changed from 100 to 120 (delta: +20)
            # NOTE: No full canvas_data, no unchanged fields
        }

        response = await sio_a.emit('diagram_update', {
            'room': f'file:{diagram_id}',
            'user_id': user_id_a,
            'update': delta_update
        }, callback=True)

        print(f"   ✓ Delta update sent: {json.dumps(delta_update, indent=2)}")
        print(f"   ✓ Server response: {response}")

        # Wait for User B to receive the update
        await asyncio.wait_for(update_received.wait(), timeout=5.0)

        # Step 6: Validate the received update
        print("\n6. Validating bandwidth optimization...")

        # Test 6.1: Update received
        if received_update_data:
            print("   ✅ Test 6.1 PASSED: Update received by User B")
            tests_passed += 1
        else:
            print("   ❌ Test 6.1 FAILED: No update received")
            tests_failed += 1

        # Test 6.2: Update contains only delta (type, shape_id, x, y)
        delta_keys = set(received_update_data.keys())
        expected_keys = {'type', 'shape_id', 'x', 'y'}

        if delta_keys == expected_keys:
            print(f"   ✅ Test 6.2 PASSED: Update contains only delta fields {expected_keys}")
            tests_passed += 1
        else:
            print(f"   ❌ Test 6.2 FAILED: Update keys {delta_keys} != expected {expected_keys}")
            tests_failed += 1

        # Test 6.3: Update does NOT contain full canvas_data
        if 'canvas_data' not in received_update_data:
            print("   ✅ Test 6.3 PASSED: No full canvas_data in update")
            tests_passed += 1
        else:
            print("   ❌ Test 6.3 FAILED: Update contains full canvas_data (bandwidth waste!)")
            tests_failed += 1

        # Test 6.4: Update does NOT contain shapes collection
        if 'shapes' not in received_update_data:
            print("   ✅ Test 6.4 PASSED: No shapes collection in update")
            tests_passed += 1
        else:
            print("   ❌ Test 6.4 FAILED: Update contains shapes collection (bandwidth waste!)")
            tests_failed += 1

        # Test 6.5: Payload size is minimal (< 200 bytes for simple position update)
        stats = bandwidth_monitor.get_stats()
        payload_size = stats['total_bytes']

        if payload_size < 200:
            print(f"   ✅ Test 6.5 PASSED: Payload size is minimal ({payload_size} bytes < 200 bytes)")
            tests_passed += 1
        else:
            print(f"   ❌ Test 6.5 FAILED: Payload size too large ({payload_size} bytes >= 200 bytes)")
            tests_failed += 1

        # Test 6.6: Position values match the delta
        if received_update_data.get('x') == 150 and received_update_data.get('y') == 120:
            print(f"   ✅ Test 6.6 PASSED: Position values correct (x=150, y=120)")
            tests_passed += 1
        else:
            print(f"   ❌ Test 6.6 FAILED: Position values incorrect")
            tests_failed += 1

        # Test 6.7: Update type is specific (not generic 'update')
        if received_update_data.get('type') == 'shape_moved':
            print(f"   ✅ Test 6.7 PASSED: Update type is specific ('shape_moved')")
            tests_passed += 1
        else:
            print(f"   ❌ Test 6.7 FAILED: Update type not specific")
            tests_failed += 1

        # Step 7: Send multiple updates and verify bandwidth efficiency
        print("\n7. Testing multiple updates for bandwidth efficiency...")

        for i in range(5):
            update_received.clear()

            delta_update = {
                "type": "shape_moved",
                "shape_id": "shape1",
                "x": 150 + (i * 10),
                "y": 120 + (i * 10)
            }

            await sio_a.emit('diagram_update', {
                'room': f'file:{diagram_id}',
                'user_id': user_id_a,
                'update': delta_update
            }, callback=True)

            await asyncio.wait_for(update_received.wait(), timeout=5.0)

        stats = bandwidth_monitor.get_stats()
        print(f"   📊 Bandwidth statistics:")
        print(f"      - Total updates: {stats['update_count']}")
        print(f"      - Total bytes: {stats['total_bytes']}")
        print(f"      - Average bytes per update: {stats['average_bytes']:.2f}")

        # Test 7.1: Average payload size remains small
        if stats['average_bytes'] < 200:
            print(f"   ✅ Test 7.1 PASSED: Average payload size optimal ({stats['average_bytes']:.2f} bytes)")
            tests_passed += 1
        else:
            print(f"   ❌ Test 7.1 FAILED: Average payload size too large ({stats['average_bytes']:.2f} bytes)")
            tests_failed += 1

        # Test 7.2: Total bandwidth for 6 updates is reasonable (< 1.2KB)
        if stats['total_bytes'] < 1200:
            print(f"   ✅ Test 7.2 PASSED: Total bandwidth efficient ({stats['total_bytes']} bytes < 1.2KB)")
            tests_passed += 1
        else:
            print(f"   ❌ Test 7.2 FAILED: Total bandwidth excessive ({stats['total_bytes']} bytes >= 1.2KB)")
            tests_failed += 1

        # Cleanup
        await sio_a.disconnect()
        await sio_b.disconnect()

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        tests_failed += 1

    # Final results
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests passed: {tests_passed}")
    print(f"Tests failed: {tests_failed}")
    print(f"Total tests:  {tests_passed + tests_failed}")

    if tests_failed == 0:
        print("\n✅ ALL TESTS PASSED")
        print("\nFeature #419 validated successfully:")
        print("- Bandwidth optimization confirmed")
        print("- Only delta updates transmitted")
        print("- No full canvas_data sent")
        print("- Minimal payload sizes verified")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(test_bandwidth_optimization())
    sys.exit(exit_code)
