#!/usr/bin/env python3
"""
Feature #399: Real-time collaboration: Activity feed: 'User A created shape'

Test Steps:
1. User A joins room
2. User A creates a shape
3. Verify activity feed shows "User A created shape" event
4. Test via WebSocket event and REST API
"""

import asyncio
import socketio
import requests
import json
import sys
from datetime import datetime
import jwt as jwt_lib
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_GATEWAY = "http://localhost:8080"
COLLAB_SERVICE = "http://localhost:8083"
TEST_USER_EMAIL = "testuser@example.com"
TEST_USER_PASSWORD = "SecurePassword123!"
TEST_ROOM = "diagram-activity-test"

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def log_step(step_num, description):
    """Log a test step."""
    print(f"\n{BLUE}[Step {step_num}]{RESET} {description}")


def log_success(message):
    """Log a success message."""
    print(f"{GREEN}✓{RESET} {message}")


def log_error(message):
    """Log an error message."""
    print(f"{RED}✗{RESET} {message}")


def log_info(message):
    """Log an info message."""
    print(f"{YELLOW}ℹ{RESET} {message}")


def authenticate():
    """Authenticate and get JWT token."""
    import psycopg2
    import os

    log_step(0, "Authenticating user")

    # Try to login
    response = requests.post(
        f"{API_GATEWAY}/api/auth/login",
        json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
    )

    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        payload = jwt_lib.decode(token, options={"verify_signature": False})
        user_id = payload.get('sub')
        log_success(f"Authenticated as user {user_id}")
        return token, user_id
    elif response.status_code == 403:
        # Email not verified - verify it directly in database
        log_info("Email not verified - verifying in database...")

        try:
            conn = psycopg2.connect(
                host='localhost',
                port=int(os.getenv('POSTGRES_PORT', '5432')),
                database=os.getenv('POSTGRES_DB', 'autograph'),
                user=os.getenv('POSTGRES_USER', 'autograph'),
                password=os.getenv('POSTGRES_PASSWORD', 'autograph')
            )
            cur = conn.cursor()
            cur.execute("UPDATE users SET is_email_verified = true WHERE email = %s", (TEST_USER_EMAIL,))
            conn.commit()
            cur.close()
            conn.close()
            log_success("Email verified in database")

            # Retry login
            return authenticate()
        except Exception as e:
            log_error(f"Database error: {e}")
            return None, None
    else:
        log_error(f"Authentication failed: {response.status_code}")
        return None, None


async def test_activity_feed():
    """Test activity feed for shape creation."""

    print(f"{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}Feature #399: Activity Feed - 'User A created shape'{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}")

    # Authenticate
    token, user_id = authenticate()
    if not token:
        log_error("Authentication failed")
        return False

    # Create socket.io client
    log_step(1, "Connecting to collaboration service via WebSocket")
    sio = socketio.AsyncClient()

    connected = False
    activity_events = []

    @sio.event
    async def connect():
        nonlocal connected
        connected = True
        log_success("WebSocket connected")

    @sio.event
    async def activity(data):
        """Capture activity feed events."""
        nonlocal activity_events
        activity_events.append(data)
        log_info(f"Activity event received: {data}")

    try:
        # Connect with auth token
        await sio.connect(
            COLLAB_SERVICE,
            auth={'token': token},
            transports=['websocket']
        )

        # Wait for connection
        await asyncio.sleep(1)

        if not connected:
            log_error("Failed to connect to WebSocket")
            return False

        # Join room
        log_step(2, "Joining room")
        join_response = await sio.call('join_room', {
            'room': TEST_ROOM,
            'user_id': user_id,
            'username': 'Test User',
            'role': 'editor'
        })

        if not join_response.get('success'):
            log_error(f"Failed to join room: {join_response}")
            return False

        log_success(f"Joined room: {TEST_ROOM}")

        # Wait for join activity event
        await asyncio.sleep(0.5)

        # Step 3: Create a shape
        log_step(3, "Creating a shape via WebSocket")

        await sio.emit('shape_created', {
            'room': TEST_ROOM,
            'user_id': user_id,
            'username': 'Test User',
            'shape_type': 'rectangle',
            'shape_id': 'shape-123'
        })

        # Wait for activity event
        await asyncio.sleep(1)

        # Step 4: Verify activity event was broadcast
        log_step(4, "Verifying activity event was received")

        # Find shape creation event
        shape_created_event = None
        for event in activity_events:
            if 'created' in event.get('action', '') and 'rectangle' in event.get('action', ''):
                shape_created_event = event
                break

        if shape_created_event:
            log_success(f"✅ Activity event received: {shape_created_event}")

            # Verify event structure
            if shape_created_event.get('user_id') == user_id:
                log_success("✅ User ID matches")
            else:
                log_error(f"User ID mismatch: {shape_created_event.get('user_id')} != {user_id}")
                return False

            if 'rectangle' in shape_created_event.get('action', ''):
                log_success("✅ Action contains 'rectangle'")
            else:
                log_error(f"Action doesn't mention rectangle: {shape_created_event.get('action')}")
                return False

            if 'Test User' in shape_created_event.get('username', ''):
                log_success("✅ Username matches")
            else:
                log_error(f"Username mismatch: {shape_created_event.get('username')}")
                return False
        else:
            log_error("❌ No shape creation event received")
            log_info(f"Received events: {json.dumps(activity_events, indent=2)}")
            return False

        # Step 5: Verify activity feed via REST API
        log_step(5, "Verifying activity feed via REST API")

        response = requests.get(f"{COLLAB_SERVICE}/rooms/{TEST_ROOM}/activity")

        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])

            log_info(f"Activity feed has {len(events)} events")

            # Find our shape creation event
            found = False
            for event in events:
                if 'created' in event.get('action', '') and 'rectangle' in event.get('action', ''):
                    log_success(f"✅ Found in feed: {event.get('action')} by {event.get('username')}")
                    found = True
                    break

            if not found:
                log_error("❌ Shape creation not found in activity feed")
                log_info(f"Events: {json.dumps(events, indent=2)}")
                return False
        else:
            log_error(f"Failed to get activity feed: {response.status_code}")
            return False

        # Disconnect
        await sio.disconnect()

        print(f"\n{BLUE}{'=' * 80}{RESET}")
        print(f"{GREEN}✅ ALL TESTS PASSED{RESET}")
        print(f"{BLUE}{'=' * 80}{RESET}")

        return True

    except Exception as e:
        log_error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if sio.connected:
            await sio.disconnect()


if __name__ == "__main__":
    result = asyncio.run(test_activity_feed())
    sys.exit(0 if result else 1)
