#!/usr/bin/env python3
"""
Validation script for Feature #392: Typing indicators - show when users typing

Tests:
1. Collaboration service health check
2. typing_status event handler exists
3. UserPresence tracks is_typing
4. Broadcast typing_update when user starts typing
5. typing_update includes username, is_typing
6. Real-time updates skip sender (skip_sid)
7. HTTP endpoint returns is_typing status
8. Typing indicator disappears when user stops typing
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
    "user_id": "user-a-392",
    "username": "User A Typing Test",
    "email": "usera-typing@test.com"
}

USER_B = {
    "user_id": "user-b-392",
    "username": "User B Typing Test",
    "email": "userb-typing@test.com"
}

ROOM_ID = "file:test-typing-room-392"


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

    async def test_typing_status_handler_exists(self):
        """Step 2: Verify typing_status event handler exists."""
        try:
            sio = socketio.AsyncClient()
            await sio.connect(SOCKET_URL, transports=['polling', 'websocket'])

            # Try to emit typing_status event
            response = await sio.call('typing_status', {
                'room': ROOM_ID,
                'user_id': USER_A['user_id'],
                'is_typing': True
            }, timeout=5)

            await sio.disconnect()

            if response and response.get('success'):
                self.log("STEP 2", "PASS", "typing_status event handler exists and responds")
                return True
            else:
                self.log("STEP 2", "FAIL", f"typing_status handler returned error: {response}")
                return False

        except Exception as e:
            self.log("STEP 2", "FAIL", f"Failed to test typing_status handler: {e}")
            return False

    async def test_user_presence_tracks_typing(self):
        """Step 3: Verify UserPresence tracks is_typing."""
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

            # Start typing
            await sio.emit('typing_status', {
                'room': ROOM_ID,
                'user_id': USER_A['user_id'],
                'is_typing': True
            })

            await asyncio.sleep(0.5)
            await sio.disconnect()

            # Check HTTP endpoint
            response = requests.get(f"{COLLABORATION_URL}/rooms/{ROOM_ID}/users")
            if response.status_code == 200:
                data = response.json()
                users = data.get('users', [])
                user_a_data = next((u for u in users if u['user_id'] == USER_A['user_id']), None)

                if user_a_data and user_a_data.get('is_typing') == True:
                    self.log("STEP 3", "PASS", f"UserPresence tracks is_typing: {user_a_data['is_typing']}")
                    return True
                else:
                    self.log("STEP 3", "FAIL", f"is_typing not tracked correctly: {user_a_data}")
                    return False
            else:
                self.log("STEP 3", "FAIL", f"Failed to get room users: {response.status_code}")
                return False

        except Exception as e:
            self.log("STEP 3", "FAIL", f"Failed to test user presence tracking: {e}")
            return False

    async def test_broadcast_typing_update(self):
        """Step 4: Verify broadcast of typing_update event."""
        try:
            client_a = socketio.AsyncClient()
            client_b = socketio.AsyncClient()

            received_event = None

            @client_b.event
            async def typing_update(data):
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

            # User A starts typing
            await client_a.emit('typing_status', {
                'room': ROOM_ID,
                'user_id': USER_A['user_id'],
                'is_typing': True
            })

            # Wait for broadcast
            await asyncio.sleep(1)

            await client_a.disconnect()
            await client_b.disconnect()

            if received_event:
                self.log("STEP 4", "PASS", f"Received typing_update broadcast: {received_event}")
                return received_event
            else:
                self.log("STEP 4", "FAIL", "Did not receive typing_update broadcast")
                return None

        except Exception as e:
            self.log("STEP 4", "FAIL", f"Failed to test broadcast: {e}")
            return None

    async def test_typing_update_content(self, event_data):
        """Step 5: Verify typing_update includes correct data."""
        if not event_data:
            self.log("STEP 5", "FAIL", "No event data to validate")
            return False

        required_fields = ['user_id', 'username', 'is_typing', 'timestamp']
        missing_fields = [f for f in required_fields if f not in event_data]

        if missing_fields:
            self.log("STEP 5", "FAIL", f"Missing fields in typing_update: {missing_fields}")
            return False

        if event_data['user_id'] == USER_A['user_id'] and event_data['is_typing'] == True:
            self.log("STEP 5", "PASS", "typing_update contains all required fields with correct data")
            return True
        else:
            self.log("STEP 5", "FAIL", f"Data mismatch in event: {event_data}")
            return False

    async def test_skip_sender(self):
        """Step 6: Verify skip_sid prevents echo to sender."""
        try:
            client_a = socketio.AsyncClient()

            received_own_typing = False

            @client_a.event
            async def typing_update(data):
                nonlocal received_own_typing
                if data.get('user_id') == USER_A['user_id']:
                    received_own_typing = True

            await client_a.connect(SOCKET_URL, transports=['polling', 'websocket'])

            await client_a.emit('join_room', {
                'room': ROOM_ID,
                'user_id': USER_A['user_id'],
                'username': USER_A['username'],
                'email': USER_A['email']
            })

            await asyncio.sleep(0.5)

            # User A starts typing
            await client_a.emit('typing_status', {
                'room': ROOM_ID,
                'user_id': USER_A['user_id'],
                'is_typing': True
            })

            # Wait to see if we receive our own event (we shouldn't)
            await asyncio.sleep(1)

            await client_a.disconnect()

            if not received_own_typing:
                self.log("STEP 6", "PASS", "Sender does not receive own typing_update (skip_sid works)")
                return True
            else:
                self.log("STEP 6", "FAIL", "Sender received own typing_update (skip_sid not working)")
                return False

        except Exception as e:
            self.log("STEP 6", "FAIL", f"Failed to test skip_sid: {e}")
            return False

    async def test_http_endpoint_typing(self):
        """Step 7: Verify HTTP endpoint returns is_typing status."""
        try:
            sio = socketio.AsyncClient()
            await sio.connect(SOCKET_URL, transports=['polling', 'websocket'])

            await sio.emit('join_room', {
                'room': ROOM_ID,
                'user_id': USER_A['user_id'],
                'username': USER_A['username'],
                'email': USER_A['email']
            })

            await sio.emit('typing_status', {
                'room': ROOM_ID,
                'user_id': USER_A['user_id'],
                'is_typing': True
            })

            await asyncio.sleep(0.5)
            await sio.disconnect()

            # Get via HTTP
            response = requests.get(f"{COLLABORATION_URL}/rooms/{ROOM_ID}/users")
            if response.status_code == 200:
                data = response.json()
                user_data = next((u for u in data['users'] if u['user_id'] == USER_A['user_id']), None)

                if user_data and user_data.get('is_typing') == True:
                    self.log("STEP 7", "PASS", f"HTTP endpoint returns is_typing: {user_data['is_typing']}")
                    return True
                else:
                    self.log("STEP 7", "FAIL", f"Wrong is_typing: {user_data}")
                    return False
            else:
                self.log("STEP 7", "FAIL", f"HTTP request failed: {response.status_code}")
                return False

        except Exception as e:
            self.log("STEP 7", "FAIL", f"Failed to test HTTP endpoint: {e}")
            return False

    async def test_typing_indicator_disappears(self):
        """Step 8: Verify typing indicator disappears when user stops typing."""
        try:
            client_a = socketio.AsyncClient()
            client_b = socketio.AsyncClient()

            typing_events = []

            @client_b.event
            async def typing_update(data):
                typing_events.append(data)

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

            # User A starts typing
            await client_a.emit('typing_status', {
                'room': ROOM_ID,
                'user_id': USER_A['user_id'],
                'is_typing': True
            })

            await asyncio.sleep(0.5)

            # User A stops typing
            await client_a.emit('typing_status', {
                'room': ROOM_ID,
                'user_id': USER_A['user_id'],
                'is_typing': False
            })

            await asyncio.sleep(1)

            await client_a.disconnect()
            await client_b.disconnect()

            # Should receive 2 events: start and stop
            if len(typing_events) >= 2:
                start_event = typing_events[0]
                stop_event = typing_events[-1]

                if start_event['is_typing'] == True and stop_event['is_typing'] == False:
                    self.log("STEP 8", "PASS", f"Typing indicator disappears correctly (received {len(typing_events)} events)")
                    return True
                else:
                    self.log("STEP 8", "FAIL", f"Typing events incorrect: {typing_events}")
                    return False
            else:
                self.log("STEP 8", "FAIL", f"Only received {len(typing_events)} events, expected 2")
                return False

        except Exception as e:
            self.log("STEP 8", "FAIL", f"Failed to test typing indicator disappearance: {e}")
            return False

    async def run_all_tests(self):
        """Run all validation tests."""
        print("=" * 80)
        print("FEATURE #392 VALIDATION: Typing Indicators")
        print("=" * 80)
        print()

        # Step 1: Health check
        if not await self.test_collaboration_health():
            print("\n❌ Collaboration service not healthy. Cannot proceed.")
            return False

        # Step 2: Handler exists
        if not await self.test_typing_status_handler_exists():
            print("\n❌ typing_status handler not working. Cannot proceed.")
            return False

        # Step 3: Track typing in UserPresence
        if not await self.test_user_presence_tracks_typing():
            print("\n❌ UserPresence not tracking is_typing")
            return False

        # Step 4 & 5: Broadcast and content
        event_data = await self.test_broadcast_typing_update()
        if event_data:
            await self.test_typing_update_content(event_data)

        # Step 6: Skip sender
        await self.test_skip_sender()

        # Step 7: HTTP endpoint
        await self.test_http_endpoint_typing()

        # Step 8: Indicator disappears
        await self.test_typing_indicator_disappears()

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
            print("✅ ALL TESTS PASSED - Feature #392 is working correctly!")
            return True
        else:
            print(f"❌ {failed} TEST(S) FAILED - Feature #392 needs fixes")
            return False


async def main():
    validator = ValidationTest()
    success = await validator.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
