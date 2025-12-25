#!/usr/bin/env python3
"""
Validation script for Feature #391: Active element indicator - who's editing which element

Tests:
1. Collaboration service health check
2. element_edit event handler exists
3. UserPresence tracks active_element
4. Broadcast element_active event when user starts editing
5. element_active includes username, color, element_id
6. Real-time updates skip sender (skip_sid)
7. HTTP endpoint returns active_element
8. Lock released when user finishes editing (element_id: null)
"""

import socketio
import asyncio
import requests
import sys
from datetime import datetime

# Configuration
COLLABORATION_URL = "http://localhost:8083"
SOCKET_URL = "http://localhost:8083"

# Test user data
USER_A = {
    "user_id": "user-a-391",
    "username": "User A Edit Test",
    "email": "usera-edit@test.com"
}

USER_B = {
    "user_id": "user-b-391",
    "username": "User B Edit Test",
    "email": "userb-edit@test.com"
}

ROOM_ID = "file:test-edit-room-391"


class ValidationTest:
    def __init__(self):
        self.results = []

    def log(self, step: str, status: str, message: str):
        """Log validation step."""
        symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "ℹ️"
        print(f"{symbol} [{step}] {message}")
        self.results.append({"step": step, "status": status, "message": message})

    async def test_collaboration_health(self):
        """Step 1: Check collaboration service health."""
        try:
            response = requests.get(f"{COLLABORATION_URL}/health", timeout=5)
            if response.status_code == 200:
                self.log("STEP 1", "PASS", "Collaboration service is healthy")
                return True
            else:
                self.log("STEP 1", "FAIL", f"Health check failed: {response.status_code}")
                return False
        except Exception as e:
            self.log("STEP 1", "FAIL", f"Cannot reach collaboration service: {e}")
            return False

    async def test_element_edit_handler_exists(self):
        """Step 2: Verify element_edit event handler exists."""
        try:
            sio = socketio.AsyncClient()
            await sio.connect(SOCKET_URL, transports=['polling', 'websocket'])

            # Try to emit element_edit event
            response = await sio.call('element_edit', {
                'room': ROOM_ID,
                'user_id': USER_A['user_id'],
                'element_id': 'test-element-123'
            }, timeout=5)

            await sio.disconnect()

            if response and response.get('success'):
                self.log("STEP 2", "PASS", "element_edit event handler exists and responds")
                return True
            else:
                self.log("STEP 2", "FAIL", f"element_edit handler returned error: {response}")
                return False

        except Exception as e:
            self.log("STEP 2", "FAIL", f"Failed to test element_edit handler: {e}")
            return False

    async def test_user_presence_tracks_active_element(self):
        """Step 3: Verify UserPresence tracks active_element."""
        try:
            sio = socketio.AsyncClient()
            await sio.connect(SOCKET_URL, transports=['polling', 'websocket'])

            # Join room
            await sio.emit('join_room', {
                'room': ROOM_ID,
                'user_id': USER_A['user_id'],
                'username': USER_A['username'],
                'email': USER_A['email']
            })

            await asyncio.sleep(0.5)

            # Start editing element
            await sio.emit('element_edit', {
                'room': ROOM_ID,
                'user_id': USER_A['user_id'],
                'element_id': 'text-element-456'
            })

            await asyncio.sleep(0.5)
            await sio.disconnect()

            # Check HTTP endpoint
            response = requests.get(f"{COLLABORATION_URL}/rooms/{ROOM_ID}/users")
            if response.status_code == 200:
                data = response.json()
                users = data.get('users', [])
                user_a_data = next((u for u in users if u['user_id'] == USER_A['user_id']), None)

                if user_a_data and user_a_data.get('active_element') == 'text-element-456':
                    self.log("STEP 3", "PASS", f"UserPresence tracks active_element: {user_a_data['active_element']}")
                    return True
                else:
                    self.log("STEP 3", "FAIL", f"active_element not tracked correctly: {user_a_data}")
                    return False
            else:
                self.log("STEP 3", "FAIL", f"Failed to get room users: {response.status_code}")
                return False

        except Exception as e:
            self.log("STEP 3", "FAIL", f"Failed to test user presence tracking: {e}")
            return False

    async def test_broadcast_element_active(self):
        """Step 4: Verify broadcast of element_active event."""
        try:
            client_a = socketio.AsyncClient()
            client_b = socketio.AsyncClient()

            received_event = None

            @client_b.event
            async def element_active(data):
                nonlocal received_event
                received_event = data

            # Connect both clients
            await client_a.connect(SOCKET_URL, transports=['polling', 'websocket'])
            await client_b.connect(SOCKET_URL, transports=['polling', 'websocket'])

            # Both join same room
            await client_a.emit('join_room', {
                'room': ROOM_ID,
                'user_id': USER_A['user_id'],
                'username': USER_A['username'],
                'email': USER_A['email']
            })

            await client_b.emit('join_room', {
                'room': ROOM_ID,
                'user_id': USER_B['user_id'],
                'username': USER_B['username'],
                'email': USER_B['email']
            })

            await asyncio.sleep(0.5)

            # User A starts editing
            await client_a.emit('element_edit', {
                'room': ROOM_ID,
                'user_id': USER_A['user_id'],
                'element_id': 'rect-999'
            })

            # Wait for broadcast
            await asyncio.sleep(1)

            await client_a.disconnect()
            await client_b.disconnect()

            if received_event:
                self.log("STEP 4", "PASS", f"Received element_active broadcast: {received_event}")
                return received_event
            else:
                self.log("STEP 4", "FAIL", "Did not receive element_active broadcast")
                return None

        except Exception as e:
            self.log("STEP 4", "FAIL", f"Failed to test broadcast: {e}")
            return None

    async def test_element_active_content(self, event_data):
        """Step 5: Verify element_active includes correct data."""
        if not event_data:
            self.log("STEP 5", "FAIL", "No event data to validate")
            return False

        required_fields = ['user_id', 'username', 'color', 'element_id', 'timestamp']
        missing_fields = [f for f in required_fields if f not in event_data]

        if missing_fields:
            self.log("STEP 5", "FAIL", f"Missing fields in element_active: {missing_fields}")
            return False

        if event_data['user_id'] == USER_A['user_id'] and event_data['element_id'] == 'rect-999':
            self.log("STEP 5", "PASS", "element_active contains all required fields with correct data")
            return True
        else:
            self.log("STEP 5", "FAIL", f"Data mismatch in event: {event_data}")
            return False

    async def test_skip_sender(self):
        """Step 6: Verify skip_sid prevents echo to sender."""
        try:
            client_a = socketio.AsyncClient()

            received_own_edit = False

            @client_a.event
            async def element_active(data):
                nonlocal received_own_edit
                if data.get('user_id') == USER_A['user_id']:
                    received_own_edit = True

            await client_a.connect(SOCKET_URL, transports=['polling', 'websocket'])

            await client_a.emit('join_room', {
                'room': ROOM_ID,
                'user_id': USER_A['user_id'],
                'username': USER_A['username'],
                'email': USER_A['email']
            })

            await asyncio.sleep(0.5)

            # User A starts editing
            await client_a.emit('element_edit', {
                'room': ROOM_ID,
                'user_id': USER_A['user_id'],
                'element_id': 'no-echo-test'
            })

            # Wait to see if we receive our own event (we shouldn't)
            await asyncio.sleep(1)

            await client_a.disconnect()

            if not received_own_edit:
                self.log("STEP 6", "PASS", "Sender does not receive own element_active (skip_sid works)")
                return True
            else:
                self.log("STEP 6", "FAIL", "Sender received own element_active (skip_sid not working)")
                return False

        except Exception as e:
            self.log("STEP 6", "FAIL", f"Failed to test skip_sid: {e}")
            return False

    async def test_http_endpoint_active_element(self):
        """Step 7: Verify HTTP endpoint returns active_element."""
        try:
            sio = socketio.AsyncClient()
            await sio.connect(SOCKET_URL, transports=['polling', 'websocket'])

            await sio.emit('join_room', {
                'room': ROOM_ID,
                'user_id': USER_A['user_id'],
                'username': USER_A['username'],
                'email': USER_A['email']
            })

            await sio.emit('element_edit', {
                'room': ROOM_ID,
                'user_id': USER_A['user_id'],
                'element_id': 'http-test-element'
            })

            await asyncio.sleep(0.5)
            await sio.disconnect()

            # Get via HTTP
            response = requests.get(f"{COLLABORATION_URL}/rooms/{ROOM_ID}/users")
            if response.status_code == 200:
                data = response.json()
                user_data = next((u for u in data['users'] if u['user_id'] == USER_A['user_id']), None)

                if user_data and user_data.get('active_element') == 'http-test-element':
                    self.log("STEP 7", "PASS", f"HTTP endpoint returns active_element: {user_data['active_element']}")
                    return True
                else:
                    self.log("STEP 7", "FAIL", f"Wrong active_element: {user_data}")
                    return False
            else:
                self.log("STEP 7", "FAIL", f"HTTP request failed: {response.status_code}")
                return False

        except Exception as e:
            self.log("STEP 7", "FAIL", f"Failed to test HTTP endpoint: {e}")
            return False

    async def test_lock_release(self):
        """Step 8: Verify lock released when user finishes editing."""
        try:
            client_a = socketio.AsyncClient()
            client_b = socketio.AsyncClient()

            lock_events = []

            @client_b.event
            async def element_active(data):
                lock_events.append(data)

            await client_a.connect(SOCKET_URL, transports=['polling', 'websocket'])
            await client_b.connect(SOCKET_URL, transports=['polling', 'websocket'])

            # Join room
            await client_a.emit('join_room', {
                'room': ROOM_ID,
                'user_id': USER_A['user_id'],
                'username': USER_A['username'],
                'email': USER_A['email']
            })

            await client_b.emit('join_room', {
                'room': ROOM_ID,
                'user_id': USER_B['user_id'],
                'username': USER_B['username'],
                'email': USER_B['email']
            })

            await asyncio.sleep(0.5)

            # User A starts editing
            await client_a.emit('element_edit', {
                'room': ROOM_ID,
                'user_id': USER_A['user_id'],
                'element_id': 'lock-test-element'
            })

            await asyncio.sleep(0.5)

            # User A finishes editing (null element_id)
            await client_a.emit('element_edit', {
                'room': ROOM_ID,
                'user_id': USER_A['user_id'],
                'element_id': None
            })

            await asyncio.sleep(1)

            await client_a.disconnect()
            await client_b.disconnect()

            # Should receive 2 events: lock and unlock
            if len(lock_events) >= 2:
                start_event = lock_events[0]
                end_event = lock_events[-1]

                if start_event['element_id'] == 'lock-test-element' and end_event['element_id'] is None:
                    self.log("STEP 8", "PASS", f"Lock released correctly (received {len(lock_events)} events)")
                    return True
                else:
                    self.log("STEP 8", "FAIL", f"Lock events incorrect: {lock_events}")
                    return False
            else:
                self.log("STEP 8", "FAIL", f"Only received {len(lock_events)} events, expected 2")
                return False

        except Exception as e:
            self.log("STEP 8", "FAIL", f"Failed to test lock release: {e}")
            return False

    async def run_all_tests(self):
        """Run all validation tests."""
        print("=" * 80)
        print("FEATURE #391 VALIDATION: Active Element Indicator")
        print("=" * 80)
        print()

        # Step 1: Health check
        if not await self.test_collaboration_health():
            print("\n❌ Collaboration service not healthy. Cannot proceed.")
            return False

        # Step 2: Handler exists
        if not await self.test_element_edit_handler_exists():
            print("\n❌ element_edit handler not working. Cannot proceed.")
            return False

        # Step 3: Track active element in UserPresence
        if not await self.test_user_presence_tracks_active_element():
            print("\n❌ UserPresence not tracking active_element")
            return False

        # Step 4 & 5: Broadcast and content
        event_data = await self.test_broadcast_element_active()
        if event_data:
            await self.test_element_active_content(event_data)

        # Step 6: Skip sender
        await self.test_skip_sender()

        # Step 7: HTTP endpoint
        await self.test_http_endpoint_active_element()

        # Step 8: Lock release
        await self.test_lock_release()

        # Summary
        print()
        print("=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)

        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')

        print(f"Total Tests: {len(self.results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print()

        if failed == 0:
            print("✅ ALL TESTS PASSED - Feature #391 is working correctly!")
            return True
        else:
            print(f"❌ {failed} TEST(S) FAILED - Feature #391 needs fixes")
            return False


async def main():
    validator = ValidationTest()
    success = await validator.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
