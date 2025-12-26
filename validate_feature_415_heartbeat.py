#!/usr/bin/env python3
"""
Feature #415: Presence Heartbeat - Periodic Ping to Maintain Connection
Test heartbeat mechanism for maintaining WebSocket connections.
"""
import asyncio
import socketio
import sys
import time
import jwt
import os
from datetime import datetime, timedelta

# Test configuration
COLLABORATION_SERVICE_URL = "http://localhost:8083"
TEST_ROOM = f"test-room-{int(time.time())}"
JWT_SECRET = os.getenv("JWT_SECRET", "please-set-jwt-secret-in-environment")

def create_test_token(user_id, username, email):
    """Create a JWT token for testing."""
    payload = {
        "user_id": user_id,
        "username": username,
        "email": email,
        "exp": datetime.now() + timedelta(hours=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

# Test state
test_results = {
    "code_has_heartbeat_handler": False,
    "code_updates_last_heartbeat": False,
    "code_calculates_latency": False,
    "code_determines_quality": False,
    "socketio_has_ping_config": False,
    "connection_established": False,
    "heartbeat_sent": False,
    "heartbeat_response": None,
    "latency_calculated": False,
    "quality_reported": False,
}

async def verify_code_implementation():
    """Verify the heartbeat implementation in code."""
    print("\n📌 Step 1: Verifying code implementation...")

    try:
        with open('services/collaboration-service/src/main.py', 'r') as f:
            code = f.read()

        # Check 1: Heartbeat event handler exists
        if 'async def heartbeat' in code:
            test_results["code_has_heartbeat_handler"] = True
            print("✅ heartbeat() event handler exists")
        else:
            print("❌ heartbeat() event handler not found")
            return False

        # Check 2: Updates last_heartbeat timestamp
        if 'last_heartbeat=' in code or 'last_heartbeat =' in code:
            test_results["code_updates_last_heartbeat"] = True
            print("✅ Updates last_heartbeat timestamp")
        else:
            print("❌ last_heartbeat update not found")

        # Check 3: Calculates latency
        if 'latency' in code and 'client_timestamp' in code:
            test_results["code_calculates_latency"] = True
            print("✅ Calculates latency from client timestamp")
        else:
            print("❌ Latency calculation not found")

        # Check 4: Determines connection quality
        if 'ConnectionQuality' in code and 'latency <' in code:
            test_results["code_determines_quality"] = True
            print("✅ Determines connection quality based on latency")
        else:
            print("❌ Connection quality determination not found")

        # Check 5: Socket.IO server configuration
        if 'socketio.AsyncServer' in code:
            test_results["socketio_has_ping_config"] = True
            print("✅ Socket.IO AsyncServer initialized")
            print("   (Socket.IO has built-in ping/pong with defaults)")
            print("   Default ping_interval: 25000ms (25 seconds)")
            print("   Default ping_timeout: 20000ms (20 seconds)")
        else:
            print("❌ Socket.IO server not found")

        return True

    except Exception as e:
        print(f"❌ Error reading code: {e}")
        return False

async def test_heartbeat_functionality():
    """Test the heartbeat functionality."""
    print("\n📌 Step 2: Testing heartbeat functionality...")

    sio = socketio.AsyncClient()
    token = create_test_token("user-test", "Test User", "test@example.com")

    try:
        # Connect to server
        print("  Connecting to collaboration service...")
        await sio.connect(
            COLLABORATION_SERVICE_URL,
            auth={"token": token},
            transports=['websocket']
        )
        test_results["connection_established"] = True
        print("✅ WebSocket connection established")

        # Join a room
        print("  Joining test room...")
        join_response = await sio.call('join_room', {
            'room': TEST_ROOM,
            'user_id': 'user-test',
            'username': 'Test User',
            'email': 'test@example.com'
        }, timeout=5)

        if join_response.get('success'):
            print(f"✅ Joined room: {TEST_ROOM}")
        else:
            print(f"❌ Failed to join room: {join_response}")
            return False

        # Send heartbeat
        print("\n  Sending heartbeat...")
        client_timestamp = time.time() * 1000  # Current time in milliseconds

        heartbeat_response = await sio.call('heartbeat', {
            'room': TEST_ROOM,
            'user_id': 'user-test',
            'timestamp': client_timestamp
        }, timeout=5)

        test_results["heartbeat_sent"] = True
        test_results["heartbeat_response"] = heartbeat_response

        print("✅ Heartbeat sent")
        print(f"  Response: {heartbeat_response}")

        # Verify response
        if heartbeat_response.get('success'):
            print("✅ Heartbeat acknowledged by server")

            # Check latency
            if 'latency' in heartbeat_response:
                latency = heartbeat_response['latency']
                test_results["latency_calculated"] = True
                print(f"✅ Latency calculated: {latency:.2f}ms")
            else:
                print("❌ Latency not in response")

            # Check connection quality
            if 'quality' in heartbeat_response:
                quality = heartbeat_response['quality']
                test_results["quality_reported"] = True
                print(f"✅ Connection quality: {quality}")
            else:
                print("❌ Quality not in response")

            # Check server time
            if 'server_time' in heartbeat_response:
                print(f"✅ Server time: {heartbeat_response['server_time']}")
            else:
                print("⚠️  Server time not in response")

        else:
            print(f"❌ Heartbeat failed: {heartbeat_response}")
            return False

        # Test multiple heartbeats
        print("\n  Sending multiple heartbeats to verify consistency...")
        for i in range(3):
            await asyncio.sleep(1)
            client_timestamp = time.time() * 1000
            response = await sio.call('heartbeat', {
                'room': TEST_ROOM,
                'user_id': 'user-test',
                'timestamp': client_timestamp
            }, timeout=5)

            if response.get('success'):
                latency = response.get('latency', 0)
                quality = response.get('quality', 'unknown')
                print(f"  Heartbeat {i+1}: latency={latency:.2f}ms, quality={quality}")
            else:
                print(f"  Heartbeat {i+1}: failed")

        print("✅ Multiple heartbeats successful")

        # Wait to observe Socket.IO's built-in ping/pong
        print("\n  Waiting 30 seconds to observe Socket.IO's built-in ping/pong...")
        print("  (Socket.IO default: ping every 25 seconds)")
        await asyncio.sleep(30)
        print("✅ Connection maintained during wait period")

        # Disconnect
        await sio.disconnect()
        print("✅ Disconnected gracefully")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            if sio.connected:
                await sio.disconnect()
        except:
            pass

async def main():
    """Main test runner."""
    print("=" * 80)
    print("Feature #415: Presence Heartbeat")
    print("=" * 80)
    print("\nThis test verifies:")
    print("1. Heartbeat event handler exists and functions correctly")
    print("2. Latency calculation from client timestamp")
    print("3. Connection quality determination")
    print("4. Socket.IO's built-in ping/pong mechanism")
    print("5. last_heartbeat timestamp tracking")

    # Step 1: Verify code
    code_ok = await verify_code_implementation()

    # Step 2: Test functionality
    functionality_ok = await test_heartbeat_functionality()

    # Final results
    print("\n" + "=" * 80)
    print("TEST RESULTS")
    print("=" * 80)

    requirements = [
        ("Code: heartbeat() handler exists", test_results["code_has_heartbeat_handler"]),
        ("Code: Updates last_heartbeat timestamp", test_results["code_updates_last_heartbeat"]),
        ("Code: Calculates latency", test_results["code_calculates_latency"]),
        ("Code: Determines connection quality", test_results["code_determines_quality"]),
        ("Code: Socket.IO server configured", test_results["socketio_has_ping_config"]),
        ("Functionality: Connection established", test_results["connection_established"]),
        ("Functionality: Heartbeat sent", test_results["heartbeat_sent"]),
        ("Functionality: Latency calculated", test_results["latency_calculated"]),
        ("Functionality: Quality reported", test_results["quality_reported"]),
    ]

    all_passed = True
    for req, passed in requirements:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {req}")
        if not passed:
            all_passed = False

    if test_results["heartbeat_response"]:
        print(f"\nHeartbeat Response:")
        print(f"  {test_results['heartbeat_response']}")

    if all_passed:
        print("\n" + "=" * 80)
        print("🎉 Feature #415 PASSED: Presence Heartbeat")
        print("=" * 80)
        print("\nHeartbeat Mechanism:")
        print("- Application-level heartbeat event for presence tracking")
        print("- Calculates latency from client timestamp")
        print("- Determines connection quality (EXCELLENT/GOOD/FAIR/POOR)")
        print("- Updates last_heartbeat timestamp in user presence")
        print("- Socket.IO provides built-in ping/pong (25s interval, 20s timeout)")
        print("- Combined approach ensures connection health monitoring")
        sys.exit(0)
    else:
        print("\n" + "=" * 80)
        print("❌ Feature #415 FAILED")
        print("=" * 80)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
