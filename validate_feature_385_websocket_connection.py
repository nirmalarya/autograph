#!/usr/bin/env python3
"""
Validation script for Feature #385: WebSocket connection via Socket.IO.

Tests:
1. Open diagram
2. Verify WebSocket connection established
3. Check connection to ws://localhost:8083
4. Verify Socket.IO protocol handshake
5. Verify connection stays alive
"""

import socketio
import sys
import time
import jwt
from datetime import datetime, timedelta

COLLAB_URL = "http://localhost:8083"
JWT_SECRET = "autograph-secret-key-change-in-production"

def create_test_token():
    """Create a test JWT token."""
    payload = {
        "user_id": "test-user-websocket",
        "email": "test@example.com",
        "username": "TestUser",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def test_websocket_connection():
    """Test WebSocket connection to collaboration service."""

    print("=" * 80)
    print("Feature #385: WebSocket connection via Socket.IO")
    print("=" * 80)

    # Step 1: Create Socket.IO client
    print("\n1. Creating Socket.IO client...")

    sio = socketio.Client(logger=False, engineio_logger=False)
    connected = False
    connection_error = None

    # Define event handlers
    @sio.event
    def connect():
        nonlocal connected
        connected = True
        print("✓ WebSocket connection established")

    @sio.event
    def connect_error(data):
        nonlocal connection_error
        connection_error = data
        print(f"✗ Connection error: {data}")

    @sio.event
    def disconnect():
        print("✓ Disconnected from server")

    # Step 2-3: Connect to WebSocket server
    print("\n2. Connecting to ws://localhost:8083...")

    try:
        # Create JWT token for authentication
        token = create_test_token()

        # Connect with token in auth
        sio.connect(
            COLLAB_URL,
            auth={"token": token},
            wait_timeout=10
        )

        # Wait a moment for connection to establish
        time.sleep(1)

        if not connected:
            print(f"❌ FAILED: Connection not established")
            if connection_error:
                print(f"Error: {connection_error}")
            return False

        print(f"✓ Connected to collaboration service")

    except Exception as e:
        print(f"❌ FAILED: Connection error: {e}")
        return False

    # Step 4: Verify Socket.IO protocol handshake
    print("\n3. Verifying Socket.IO protocol handshake...")

    if sio.connected:
        print(f"✓ Socket.IO handshake successful")
        print(f"✓ Client SID assigned: {sio.sid[:16]}...")
    else:
        print(f"❌ FAILED: Not connected after handshake")
        return False

    # Step 5: Verify connection stays alive
    print("\n4. Verifying connection stays alive (5 seconds)...")

    for i in range(5):
        time.sleep(1)
        if not sio.connected:
            print(f"❌ FAILED: Connection dropped after {i+1} seconds")
            return False
        print(f"  ✓ Still connected ({i+1}s)")

    print(f"✓ Connection stable for 5 seconds")

    # Clean up
    print("\n5. Disconnecting...")
    sio.disconnect()
    time.sleep(0.5)

    # Success
    print("\n" + "=" * 80)
    print("✅ Feature #385 validation PASSED")
    print("=" * 80)
    print("\nAll steps verified:")
    print("  ✓ Socket.IO client created")
    print("  ✓ WebSocket connection established to ws://localhost:8083")
    print("  ✓ Socket.IO protocol handshake completed")
    print("  ✓ Client SID assigned")
    print("  ✓ Connection stays alive (stable)")

    return True


if __name__ == "__main__":
    try:
        success = test_websocket_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
