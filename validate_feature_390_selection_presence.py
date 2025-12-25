#!/usr/bin/env python3
"""
Validation script for Feature #390: Selection presence - highlight what others selected

Tests:
1. Collaboration service health check
2. selection_change event handler exists
3. UserPresence tracks selected_elements
4. Broadcast selection_update event to room
5. selection_update includes username, color, selected_elements
6. Real-time updates skip sender (skip_sid)
7. HTTP endpoint returns selected_elements
8. Selection updates in real-time between users
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
    "user_id": "user-a-390",
    "username": "User A Selection Test",
    "email": "usera-selection@test.com",
    "token": "fake-jwt-token-a"
}

USER_B = {
    "user_id": "user-b-390",
    "username": "User B Selection Test",
    "email": "userb-selection@test.com",
    "token": "fake-jwt-token-b"
}

ROOM_ID = "file:test-selection-room-390"


class ValidationTest:
    def __init__(self):
        self.results = []
        self.user_a_client = None
        self.user_b_client = None
        self.user_b_received_selection = None

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

    async def test_selection_handler_exists(self):
        """Step 2: Verify selection_change event handler exists."""
        try:
            # Connect client
            sio = socketio.AsyncClient()

            connected = False

            @sio.event
            async def connect():
                nonlocal connected
                connected = True

            await sio.connect(SOCKET_URL, transports=['polling', 'websocket'])
            await asyncio.sleep(1)

            if not connected:
                self.log("STEP 2", "FAIL", "Failed to connect to WebSocket")
                await sio.disconnect()
                return False

            # Try to emit selection_change event
            response = await sio.call('selection_change', {
                'room': ROOM_ID,
                'user_id': USER_A['user_id'],
                'selected_elements': ['test-element-id']
            }, timeout=5)

            await sio.disconnect()

            if response and response.get('success'):
                self.log("STEP 2", "PASS", "selection_change event handler exists and responds")
                return True
            else:
                self.log("STEP 2", "FAIL", f"selection_change handler returned error: {response}")
                return False

        except Exception as e:
            self.log("STEP 2", "FAIL", f"Failed to test selection_change handler: {e}")
            return False

    async def test_user_presence_tracks_selection(self):
        """Step 3: Verify UserPresence tracks selected_elements."""
        try:
            # Connect and join room
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

            # Send selection change
            await sio.emit('selection_change', {
                'room': ROOM_ID,
                'user_id': USER_A['user_id'],
                'selected_elements': ['rect-1', 'rect-2', 'circle-1']
            })

            await asyncio.sleep(0.5)
            await sio.disconnect()

            # Check HTTP endpoint
            response = requests.get(f"{COLLABORATION_URL}/rooms/{ROOM_ID}/users")
            if response.status_code == 200:
                data = response.json()
                users = data.get('users', [])
                user_a_data = next((u for u in users if u['user_id'] == USER_A['user_id']), None)

                if user_a_data and 'selected_elements' in user_a_data:
                    selected = user_a_data['selected_elements']
                    if 'rect-1' in selected and 'rect-2' in selected and 'circle-1' in selected:
                        self.log("STEP 3", "PASS", f"UserPresence tracks selected_elements: {selected}")
                        return True
                    else:
                        self.log("STEP 3", "FAIL", f"Selected elements mismatch: {selected}")
                        return False
                else:
                    self.log("STEP 3", "FAIL", "selected_elements not found in user presence")
                    return False
            else:
                self.log("STEP 3", "FAIL", f"Failed to get room users: {response.status_code}")
                return False

        except Exception as e:
            self.log("STEP 3", "FAIL", f"Failed to test user presence tracking: {e}")
            return False

    async def test_broadcast_selection_update(self):
        """Step 4: Verify broadcast of selection_update event."""
        try:
            # Create two clients
            client_a = socketio.AsyncClient()
            client_b = socketio.AsyncClient()

            received_event = None

            @client_b.event
            async def selection_update(data):
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

            # User A selects elements
            await client_a.emit('selection_change', {
                'room': ROOM_ID,
                'user_id': USER_A['user_id'],
                'selected_elements': ['rect-100', 'rect-200']
            })

            # Wait for broadcast
            await asyncio.sleep(1)

            await client_a.disconnect()
            await client_b.disconnect()

            if received_event:
                self.log("STEP 4", "PASS", f"Received selection_update broadcast: {received_event}")
                return received_event
            else:
                self.log("STEP 4", "FAIL", "Did not receive selection_update broadcast")
                return None

        except Exception as e:
            self.log("STEP 4", "FAIL", f"Failed to test broadcast: {e}")
            return None

    async def test_selection_update_content(self, event_data):
        """Step 5: Verify selection_update includes correct data."""
        if not event_data:
            self.log("STEP 5", "FAIL", "No event data to validate")
            return False

        required_fields = ['user_id', 'username', 'color', 'selected_elements', 'timestamp']
        missing_fields = [f for f in required_fields if f not in event_data]

        if missing_fields:
            self.log("STEP 5", "FAIL", f"Missing fields in selection_update: {missing_fields}")
            return False

        if event_data['user_id'] == USER_A['user_id']:
            if 'rect-100' in event_data['selected_elements'] and 'rect-200' in event_data['selected_elements']:
                self.log("STEP 5", "PASS", f"selection_update contains all required fields with correct data")
                return True
            else:
                self.log("STEP 5", "FAIL", f"Selected elements mismatch in event: {event_data['selected_elements']}")
                return False
        else:
            self.log("STEP 5", "FAIL", f"Wrong user_id in event: {event_data['user_id']}")
            return False

    async def test_skip_sender(self):
        """Step 6: Verify skip_sid prevents echo to sender."""
        try:
            client_a = socketio.AsyncClient()

            received_own_selection = False

            @client_a.event
            async def selection_update(data):
                nonlocal received_own_selection
                if data.get('user_id') == USER_A['user_id']:
                    received_own_selection = True

            await client_a.connect(SOCKET_URL, transports=['polling', 'websocket'])

            await client_a.emit('join_room', {
                'room': ROOM_ID,
                'user_id': USER_A['user_id'],
                'username': USER_A['username'],
                'email': USER_A['email']
            })

            await asyncio.sleep(0.5)

            # User A selects elements
            await client_a.emit('selection_change', {
                'room': ROOM_ID,
                'user_id': USER_A['user_id'],
                'selected_elements': ['no-echo-test']
            })

            # Wait to see if we receive our own event (we shouldn't)
            await asyncio.sleep(1)

            await client_a.disconnect()

            if not received_own_selection:
                self.log("STEP 6", "PASS", "Sender does not receive own selection_update (skip_sid works)")
                return True
            else:
                self.log("STEP 6", "FAIL", "Sender received own selection_update (skip_sid not working)")
                return False

        except Exception as e:
            self.log("STEP 6", "FAIL", f"Failed to test skip_sid: {e}")
            return False

    async def test_http_endpoint_selection(self):
        """Step 7: Verify HTTP endpoint returns selected_elements."""
        try:
            # Connect and set selection
            sio = socketio.AsyncClient()
            await sio.connect(SOCKET_URL, transports=['polling', 'websocket'])

            await sio.emit('join_room', {
                'room': ROOM_ID,
                'user_id': USER_A['user_id'],
                'username': USER_A['username'],
                'email': USER_A['email']
            })

            await sio.emit('selection_change', {
                'room': ROOM_ID,
                'user_id': USER_A['user_id'],
                'selected_elements': ['http-test-1', 'http-test-2']
            })

            await asyncio.sleep(0.5)
            await sio.disconnect()

            # Get via HTTP
            response = requests.get(f"{COLLABORATION_URL}/rooms/{ROOM_ID}/users")
            if response.status_code == 200:
                data = response.json()
                user_data = next((u for u in data['users'] if u['user_id'] == USER_A['user_id']), None)

                if user_data and user_data.get('selected_elements'):
                    selected = user_data['selected_elements']
                    if 'http-test-1' in selected and 'http-test-2' in selected:
                        self.log("STEP 7", "PASS", f"HTTP endpoint returns selected_elements: {selected}")
                        return True
                    else:
                        self.log("STEP 7", "FAIL", f"Wrong selected_elements: {selected}")
                        return False
                else:
                    self.log("STEP 7", "FAIL", "selected_elements not in HTTP response")
                    return False
            else:
                self.log("STEP 7", "FAIL", f"HTTP request failed: {response.status_code}")
                return False

        except Exception as e:
            self.log("STEP 7", "FAIL", f"Failed to test HTTP endpoint: {e}")
            return False

    async def test_realtime_selection_updates(self):
        """Step 8: Verify real-time selection updates between users."""
        try:
            client_a = socketio.AsyncClient()
            client_b = socketio.AsyncClient()

            user_b_selections = []

            @client_b.event
            async def selection_update(data):
                user_b_selections.append(data)

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

            # User A makes multiple selections
            selections = [
                ['rect-1'],
                ['rect-1', 'rect-2'],
                ['circle-1', 'circle-2', 'rect-3']
            ]

            for selected in selections:
                await client_a.emit('selection_change', {
                    'room': ROOM_ID,
                    'user_id': USER_A['user_id'],
                    'selected_elements': selected
                })
                await asyncio.sleep(0.3)

            await asyncio.sleep(1)

            await client_a.disconnect()
            await client_b.disconnect()

            if len(user_b_selections) >= 3:
                # Check that User B received the selections
                last_selection = user_b_selections[-1]
                if ('circle-1' in last_selection['selected_elements'] and
                    'circle-2' in last_selection['selected_elements'] and
                    'rect-3' in last_selection['selected_elements']):
                    self.log("STEP 8", "PASS", f"Real-time selection updates work (received {len(user_b_selections)} updates)")
                    return True
                else:
                    self.log("STEP 8", "FAIL", f"Selection data mismatch: {last_selection}")
                    return False
            else:
                self.log("STEP 8", "FAIL", f"Only received {len(user_b_selections)} updates, expected 3")
                return False

        except Exception as e:
            self.log("STEP 8", "FAIL", f"Failed to test real-time updates: {e}")
            return False

    async def run_all_tests(self):
        """Run all validation tests."""
        print("=" * 80)
        print("FEATURE #390 VALIDATION: Selection Presence")
        print("=" * 80)
        print()

        # Step 1: Health check
        if not await self.test_collaboration_health():
            print("\n❌ Collaboration service not healthy. Cannot proceed.")
            return False

        # Step 2: Handler exists
        if not await self.test_selection_handler_exists():
            print("\n❌ selection_change handler not working. Cannot proceed.")
            return False

        # Step 3: Track selection in UserPresence
        if not await self.test_user_presence_tracks_selection():
            print("\n❌ UserPresence not tracking selected_elements")
            return False

        # Step 4 & 5: Broadcast and content
        event_data = await self.test_broadcast_selection_update()
        if event_data:
            await self.test_selection_update_content(event_data)

        # Step 6: Skip sender
        await self.test_skip_sender()

        # Step 7: HTTP endpoint
        await self.test_http_endpoint_selection()

        # Step 8: Real-time updates
        await self.test_realtime_selection_updates()

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
            print("✅ ALL TESTS PASSED - Feature #390 is working correctly!")
            return True
        else:
            print(f"❌ {failed} TEST(S) FAILED - Feature #390 needs fixes")
            return False


async def main():
    validator = ValidationTest()
    success = await validator.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
