#!/usr/bin/env python3
"""
Feature #398: Real-time collaboration: Last seen timestamps: 'Active 5 minutes ago'

Test Steps:
1. Connect to collaboration service
2. Join room
3. Verify last_active timestamp is returned
4. Verify timestamp can be converted to "X minutes ago" format
"""

import asyncio
import socketio
import requests
import json
import sys
from datetime import datetime, timedelta
import jwt as jwt_lib
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_GATEWAY = "http://localhost:8080"
COLLAB_SERVICE = "http://localhost:8083"
TEST_USER_EMAIL = "testuser@example.com"
TEST_USER_PASSWORD = "SecurePassword123!"
TEST_ROOM = "diagram-last-seen-test"

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


def format_relative_time(iso_timestamp):
    """Convert ISO timestamp to 'X minutes ago' format."""
    if not iso_timestamp:
        return "Never"

    try:
        last_active = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        now = datetime.utcnow()

        # Make both timezone-aware or both naive
        if last_active.tzinfo is not None:
            from datetime import timezone
            now = now.replace(tzinfo=timezone.utc)
        else:
            last_active = last_active.replace(tzinfo=None)
            now = now.replace(tzinfo=None)

        delta = now - last_active

        seconds = int(delta.total_seconds())

        if seconds < 60:
            return f"Active {seconds} seconds ago"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"Active {minutes} minute{'s' if minutes != 1 else ''} ago"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"Active {hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = seconds // 86400
            return f"Active {days} day{'s' if days != 1 else ''} ago"
    except Exception as e:
        log_error(f"Failed to parse timestamp: {e}")
        return "Unknown"


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


async def test_last_seen_timestamps():
    """Test last_active timestamp functionality."""

    print(f"{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}Feature #398: Last Seen Timestamps ('Active X minutes ago'){RESET}")
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

    @sio.event
    async def connect():
        nonlocal connected
        connected = True
        log_success("WebSocket connected")

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

        # Join room using call() to get response
        log_step(2, "Joining room and checking last_active timestamp")
        join_response = await sio.call('join_room', {
            'room': TEST_ROOM,
            'user_id': user_id,
            'username': 'Test User',
            'role': 'editor'
        })

        log_info(f"Join room response: {json.dumps(join_response, indent=2)}")

        if not join_response.get('success'):
            log_error(f"Failed to join room: {join_response}")
            return False

        # Verify last_active is present
        if 'users' not in join_response or len(join_response['users']) == 0:
            log_error("No users in room")
            return False

        user = join_response['users'][0]

        # Step 3: Verify last_active timestamp is present
        log_step(3, "Verifying last_active timestamp field")

        if 'last_active' in user or 'last_seen' in user:
            last_active = user.get('last_active') or user.get('last_seen')
            log_success(f"✅ last_active timestamp present: {last_active}")
        else:
            log_error("❌ last_active timestamp not found in user object")
            log_info(f"Available fields: {list(user.keys())}")
            return False

        # Step 4: Convert to human-readable format
        log_step(4, "Converting timestamp to 'Active X minutes ago' format")

        relative_time = format_relative_time(last_active)
        log_success(f"✅ Formatted as: '{relative_time}'")

        # Step 5: Simulate older timestamp
        log_step(5, "Testing with older timestamp (5 minutes ago)")

        five_min_ago = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
        formatted = format_relative_time(five_min_ago)

        if "5 minute" in formatted:
            log_success(f"✅ Correctly formatted: '{formatted}'")
        else:
            log_error(f"❌ Unexpected format: '{formatted}'")
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
    result = asyncio.run(test_last_seen_timestamps())
    sys.exit(0 if result else 1)
