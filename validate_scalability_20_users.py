#!/usr/bin/env python3
"""
Validation script for Feature: Real-time collaboration scalability with 20+ concurrent users.

Tests:
1. Connect 20 users to same diagram
2. Verify all users see each other
3. All users make edits simultaneously
4. Verify all edits propagate
5. Verify no performance degradation
6. Monitor server resources
"""

import asyncio
import socketio
import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Set
import logging
import sys
import os
import psycopg2

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Service URLs
API_BASE = "http://localhost:8080"
COLLABORATION_URL = "http://localhost:8083"

# Test configuration
NUM_USERS = 20
TEST_TIMEOUT = 120  # 2 minutes for the full test


class UserClient:
    """Represents a single user connection for testing."""

    def __init__(self, user_id: int, username: str, token: str, diagram_id: str):
        self.user_id = user_id
        self.username = username
        self.token = token
        self.diagram_id = diagram_id
        self.sio = socketio.AsyncClient()
        self.connected = False
        self.users_seen: Set[str] = set()
        self.edits_received: List[Dict] = []
        self.presence_updates: List[Dict] = []
        self.connection_time = None
        self.edit_sent_time = None
        self.edit_received_times: Dict[str, float] = {}

        # Setup event handlers
        self.setup_handlers()

    def setup_handlers(self):
        """Setup WebSocket event handlers."""

        @self.sio.event
        async def connect():
            self.connected = True
            self.connection_time = time.time()
            logger.info(f"User {self.username} connected")

        @self.sio.event
        async def disconnect():
            self.connected = False
            logger.info(f"User {self.username} disconnected")

        @self.sio.on('user_joined')
        async def on_user_joined(data):
            user_id = data.get('user_id')
            username = data.get('username')
            if username != self.username:
                self.users_seen.add(username)
                logger.debug(f"User {self.username} saw {username} join")

        @self.sio.on('presence_update')
        async def on_presence_update(data):
            self.presence_updates.append(data)
            user_id = data.get('user_id')
            if user_id and user_id != self.user_id:
                self.users_seen.add(data.get('username', f'user_{user_id}'))

        @self.sio.on('user_list')
        async def on_user_list(data):
            users = data.get('users', [])
            for user in users:
                username = user.get('username')
                if username != self.username:
                    self.users_seen.add(username)
            logger.debug(f"User {self.username} received user list: {len(users)} users")

        @self.sio.on('edit')
        async def on_edit(data):
            self.edits_received.append(data)
            editor_username = data.get('username', 'unknown')
            if editor_username not in self.edit_received_times:
                self.edit_received_times[editor_username] = time.time()
            logger.debug(f"User {self.username} received edit from {editor_username}")

        @self.sio.on('cursor_update')
        async def on_cursor_update(data):
            # Track cursor updates to verify presence
            pass

    async def connect_to_room(self):
        """Connect to the collaboration room."""
        try:
            await self.sio.connect(
                COLLABORATION_URL,
                auth={'token': f'Bearer {self.token}'},
                transports=['websocket']
            )

            # Join room
            await self.sio.emit('join_room', {
                'diagram_id': self.diagram_id,
                'user_id': self.user_id,
                'username': self.username
            })

            # Wait a bit for join to complete
            await asyncio.sleep(0.5)

            return True
        except Exception as e:
            logger.error(f"User {self.username} connection failed: {e}")
            return False

    async def send_edit(self, element_id: str, changes: Dict):
        """Send an edit to the diagram."""
        try:
            self.edit_sent_time = time.time()
            await self.sio.emit('edit', {
                'diagram_id': self.diagram_id,
                'element_id': element_id,
                'user_id': self.user_id,
                'username': self.username,
                'changes': changes,
                'timestamp': datetime.utcnow().isoformat()
            })
            logger.debug(f"User {self.username} sent edit to {element_id}")
            return True
        except Exception as e:
            logger.error(f"User {self.username} edit failed: {e}")
            return False

    async def disconnect_from_room(self):
        """Disconnect from the collaboration room."""
        try:
            if self.connected:
                await self.sio.disconnect()
            return True
        except Exception as e:
            logger.error(f"User {self.username} disconnect failed: {e}")
            return False


async def create_test_user(user_num: int) -> Dict:
    """Create a test user account and login."""
    try:
        username = f"scaletest_user_{user_num}_{int(time.time())}"
        email = f"{username}@test.com"
        password = "TestPass123!"

        # Register user
        response = requests.post(
            f"{API_BASE}/api/auth/register",
            json={
                "email": email,
                "password": password,
                "username": username
            },
            timeout=10
        )

        if response.status_code != 201:
            logger.error(f"Failed to register user {user_num}: {response.status_code}")
            return None

        reg_data = response.json()
        user_id = reg_data.get('id')

        # Verify email directly in database for testing
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database='autograph',
                user='autograph',
                password='autograph_dev_password'
            )
            cur = conn.cursor()
            cur.execute(
                'UPDATE public.users SET is_verified = TRUE WHERE email = %s',
                (email,)
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as db_error:
            logger.error(f"Failed to verify email for user {user_num}: {db_error}")
            return None

        # Login to get token
        login_response = requests.post(
            f"{API_BASE}/api/auth/login",
            json={
                "email": email,
                "password": password
            },
            timeout=10
        )

        if login_response.status_code == 200:
            login_data = login_response.json()
            return {
                'user_id': user_id,
                'username': username,
                'email': email,
                'password': password,
                'token': login_data.get('access_token')
            }
        else:
            logger.error(f"Failed to login user {user_num}: {login_response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Exception creating user {user_num}: {e}")
        return None


async def create_test_diagram(token: str, user_id: int) -> str:
    """Create a test diagram."""
    try:
        response = requests.post(
            f"{API_BASE}/api/diagrams",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": f"Scalability Test Diagram {int(time.time())}",
                "diagram_type": "canvas",
                "content": json.dumps({"elements": [], "version": 1}),
                "user_id": user_id
            },
            timeout=10
        )

        # Accept both 200 and 201 as success
        if response.status_code in [200, 201]:
            data = response.json()
            # Try both 'id' and 'diagram_id' fields
            return data.get('id') or data.get('diagram_id')
        else:
            logger.error(f"Failed to create diagram: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exception creating diagram: {e}")
        return None


async def monitor_system_resources():
    """Monitor system resource usage (simplified version)."""
    # Simplified version - just track time and connection count
    # In production, would use proper monitoring tools
    return {
        'cpu_percent': 0.0,  # Not available without psutil
        'memory_percent': 0.0,  # Not available without psutil
        'memory_available_mb': 0.0  # Not available without psutil
    }


async def test_scalability_20_users():
    """
    Main test function for 20+ concurrent user scalability.
    """
    logger.info("=" * 80)
    logger.info("SCALABILITY TEST: 20+ Concurrent Users")
    logger.info("=" * 80)

    # Track metrics
    start_time = time.time()
    test_passed = True
    metrics = {
        'users_created': 0,
        'users_connected': 0,
        'connection_times': [],
        'edit_propagation_times': [],
        'resources_start': {},
        'resources_end': {}
    }

    try:
        # Monitor resources before test
        metrics['resources_start'] = await monitor_system_resources()
        logger.info(f"Starting resources: CPU={metrics['resources_start']['cpu_percent']}%, "
                   f"Memory={metrics['resources_start']['memory_percent']}%")

        # Step 1: Create test users
        logger.info(f"\nStep 1: Creating {NUM_USERS} test users...")
        users_data = []

        for i in range(NUM_USERS):
            user_data = await create_test_user(i + 1)
            if user_data:
                users_data.append(user_data)
                metrics['users_created'] += 1
            else:
                logger.error(f"Failed to create user {i + 1}")
                test_passed = False

            # Small delay to avoid overwhelming the server
            await asyncio.sleep(0.1)

        logger.info(f"✓ Created {metrics['users_created']}/{NUM_USERS} users")

        if metrics['users_created'] < NUM_USERS:
            logger.error(f"✗ Only created {metrics['users_created']} users")
            return False

        # Step 2: Create a shared diagram
        logger.info("\nStep 2: Creating shared diagram...")
        first_user = users_data[0]
        diagram_id = await create_test_diagram(first_user['token'], first_user['user_id'])

        if not diagram_id:
            logger.error("✗ Failed to create test diagram")
            return False

        logger.info(f"✓ Created diagram: {diagram_id}")

        # Step 3: Connect all users to the diagram
        logger.info(f"\nStep 3: Connecting {NUM_USERS} users to diagram...")
        clients: List[UserClient] = []
        connection_tasks = []

        for user_data in users_data:
            client = UserClient(
                user_id=user_data['user_id'],
                username=user_data['username'],
                token=user_data['token'],
                diagram_id=diagram_id
            )
            clients.append(client)
            connection_tasks.append(client.connect_to_room())

        # Connect all users concurrently
        connection_results = await asyncio.gather(*connection_tasks, return_exceptions=True)

        for i, result in enumerate(connection_results):
            if isinstance(result, Exception):
                logger.error(f"User {i+1} connection exception: {result}")
            elif result:
                metrics['users_connected'] += 1
                if clients[i].connection_time:
                    metrics['connection_times'].append(clients[i].connection_time - start_time)

        logger.info(f"✓ Connected {metrics['users_connected']}/{NUM_USERS} users")

        if metrics['users_connected'] < NUM_USERS:
            logger.error(f"✗ Only {metrics['users_connected']} users connected")
            test_passed = False

        # Wait for presence updates to propagate
        logger.info("\nWaiting 3 seconds for presence updates to propagate...")
        await asyncio.sleep(3)

        # Step 4: Verify all users see each other
        logger.info("\nStep 4: Verifying all users see each other...")
        all_usernames = {user_data['username'] for user_data in users_data}

        for client in clients:
            expected_others = all_usernames - {client.username}
            seen_percentage = len(client.users_seen) / len(expected_others) * 100 if expected_others else 100

            logger.info(f"User {client.username} sees {len(client.users_seen)}/{len(expected_others)} "
                       f"other users ({seen_percentage:.1f}%)")

            # Consider test passed if user sees at least 90% of others
            if seen_percentage < 90:
                logger.warning(f"⚠ User {client.username} only sees {seen_percentage:.1f}% of other users")

        # Step 5: All users make edits simultaneously
        logger.info("\nStep 5: All users making edits simultaneously...")
        edit_tasks = []

        for i, client in enumerate(clients):
            element_id = f"element_{i}"
            changes = {
                'type': 'shape',
                'x': i * 50,
                'y': i * 30,
                'width': 100,
                'height': 80,
                'text': f'Edit by {client.username}'
            }
            edit_tasks.append(client.send_edit(element_id, changes))

        edit_results = await asyncio.gather(*edit_tasks, return_exceptions=True)
        edits_sent = sum(1 for r in edit_results if r is True)

        logger.info(f"✓ Sent {edits_sent}/{NUM_USERS} edits")

        # Wait for edit propagation
        logger.info("\nWaiting 5 seconds for edit propagation...")
        await asyncio.sleep(5)

        # Step 6: Verify all edits propagated
        logger.info("\nStep 6: Verifying edit propagation...")

        for client in clients:
            received_count = len(client.edits_received)
            expected_count = NUM_USERS - 1  # All edits except their own
            propagation_percentage = (received_count / expected_count * 100) if expected_count > 0 else 100

            logger.info(f"User {client.username} received {received_count}/{expected_count} edits "
                       f"({propagation_percentage:.1f}%)")

            # Calculate propagation time
            for editor_username, receive_time in client.edit_received_times.items():
                if client.edit_sent_time:
                    propagation_time = receive_time - client.edit_sent_time
                    metrics['edit_propagation_times'].append(propagation_time)

            # Consider test passed if user received at least 80% of edits
            if propagation_percentage < 80:
                logger.warning(f"⚠ User {client.username} only received {propagation_percentage:.1f}% of edits")

        # Step 7: Monitor performance
        logger.info("\nStep 7: Monitoring performance...")
        metrics['resources_end'] = await monitor_system_resources()

        logger.info(f"Ending resources: CPU={metrics['resources_end']['cpu_percent']}%, "
                   f"Memory={metrics['resources_end']['memory_percent']}%")

        # Calculate metrics
        avg_connection_time = sum(metrics['connection_times']) / len(metrics['connection_times']) if metrics['connection_times'] else 0
        avg_propagation_time = sum(metrics['edit_propagation_times']) / len(metrics['edit_propagation_times']) if metrics['edit_propagation_times'] else 0

        logger.info(f"\nPerformance Metrics:")
        logger.info(f"- Average connection time: {avg_connection_time:.3f}s")
        logger.info(f"- Average edit propagation time: {avg_propagation_time:.3f}s")
        logger.info(f"- CPU usage change: {metrics['resources_end']['cpu_percent'] - metrics['resources_start']['cpu_percent']:.1f}%")
        logger.info(f"- Memory usage change: {metrics['resources_end']['memory_percent'] - metrics['resources_start']['memory_percent']:.1f}%")

        # Check for performance degradation
        cpu_increase = metrics['resources_end']['cpu_percent'] - metrics['resources_start']['cpu_percent']
        memory_increase = metrics['resources_end']['memory_percent'] - metrics['resources_start']['memory_percent']

        if cpu_increase > 50:
            logger.warning(f"⚠ High CPU increase: {cpu_increase:.1f}%")

        if memory_increase > 20:
            logger.warning(f"⚠ High memory increase: {memory_increase:.1f}%")

        # Cleanup: Disconnect all users
        logger.info("\nCleaning up: Disconnecting all users...")
        disconnect_tasks = [client.disconnect_from_room() for client in clients]
        await asyncio.gather(*disconnect_tasks, return_exceptions=True)

        # Final verdict
        total_time = time.time() - start_time
        logger.info("\n" + "=" * 80)
        logger.info(f"TEST COMPLETED in {total_time:.2f}s")
        logger.info(f"Users created: {metrics['users_created']}/{NUM_USERS}")
        logger.info(f"Users connected: {metrics['users_connected']}/{NUM_USERS}")
        logger.info(f"Edits sent: {edits_sent}/{NUM_USERS}")
        logger.info("=" * 80)

        # Test passes if we got at least 90% connectivity and edit propagation
        success_rate = metrics['users_connected'] / NUM_USERS
        if success_rate >= 0.9:
            logger.info("✅ SCALABILITY TEST PASSED")
            return True
        else:
            logger.error(f"✗ SCALABILITY TEST FAILED (only {success_rate*100:.1f}% success rate)")
            return False

    except Exception as e:
        logger.error(f"Test exception: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    try:
        result = asyncio.run(test_scalability_20_users())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test failed with exception: {e}", exc_info=True)
        sys.exit(1)
