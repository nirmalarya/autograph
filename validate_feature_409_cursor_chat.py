#!/usr/bin/env python3
"""
Feature #409: Collaborative cursor chat - click cursor to send message

Tests that users can send messages to each other's cursors.

Test Scenarios:
1. User A and User B join collaboration room
2. User A sends cursor message to User B
3. Verify User B receives the message
4. Verify message includes cursor position
5. Verify message includes sender info (username, color)
"""

import socketio
import asyncio
import time
import json
import jwt
import os
from datetime import datetime, timedelta

# Test configuration
COLLABORATION_SERVICE_URL = "http://localhost:8083"
TEST_ROOM = "test_room_cursor_chat"

# Generate JWT tokens
JWT_SECRET = "please-set-jwt-secret-in-environment"  # Must match container JWT_SECRET
JWT_ALGORITHM = 'HS256'

def generate_token(user_id, username, email):
    """Generate a JWT token for a test user."""
    payload = {
        'sub': user_id,
        'user_id': user_id,
        'username': username,
        'email': email,
        'exp': datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

TOKEN_A = generate_token('user_a', 'Alice', 'alice@test.com')
TOKEN_B = generate_token('user_b', 'Bob', 'bob@test.com')


async def test_cursor_chat():
    """Test cursor chat messaging."""

    print("=" * 80)
    print("Feature #409: Collaborative Cursor Chat")
    print("=" * 80)

    # Create two clients
    client_a = socketio.AsyncClient()
    client_b = socketio.AsyncClient()

    # Track received messages
    messages_a = []
    messages_b = []

    # Message handlers
    async def message_handler_a(data):
        print(f"[User A] Received cursor message: {data}")
        messages_a.append(data)

    async def message_handler_b(data):
        print(f"[User B] Received cursor message: {data}")
        messages_b.append(data)

    client_a.on('cursor_message_received', message_handler_a)
    client_b.on('cursor_message_received', message_handler_b)

    try:
        # Step 1: Connect clients
        print("\n1. Connecting clients...")
        await client_a.connect(COLLABORATION_SERVICE_URL, auth={'token': TOKEN_A})
        await client_b.connect(COLLABORATION_SERVICE_URL, auth={'token': TOKEN_B})
        print("✓ Clients connected")

        # Step 2: Join room
        print("\n2. Joining room...")
        await client_a.emit('join_room', {
            'room': TEST_ROOM,
            'user_id': 'user_a',
            'username': 'Alice'
        })
        await client_b.emit('join_room', {
            'room': TEST_ROOM,
            'user_id': 'user_b',
            'username': 'Bob'
        })
        await asyncio.sleep(0.5)
        print("✓ Joined room")

        # Step 3: User A updates cursor position
        print("\n3. User A updates cursor position to (150, 250)...")
        await client_a.emit('cursor_move', {
            'room': TEST_ROOM,
            'user_id': 'user_a',
            'x': 150,
            'y': 250
        })
        await asyncio.sleep(0.2)

        # Step 4: User A sends cursor message to User B
        print("\n4. User A sends cursor message to User B...")
        await client_a.emit('cursor_message', {
            'room': TEST_ROOM,
            'from_user_id': 'user_a',
            'to_user_id': 'user_b',
            'message': 'Check this component',
            'cursor_x': 150,
            'cursor_y': 250
        })

        # Wait for message to propagate
        await asyncio.sleep(1)

        # Verification
        print("\n" + "=" * 80)
        print("VERIFICATION")
        print("=" * 80)

        print(f"\nMessages received by User A: {len(messages_a)}")
        print(f"Messages received by User B: {len(messages_b)}")

        # Test 1: At least one message should be received
        test1_pass = len(messages_a) > 0 or len(messages_b) > 0
        print(f"\nTest 1: Message broadcast - {'✓ PASS' if test1_pass else '✗ FAIL'}")

        # Test 2: Message should contain required fields
        test2_pass = False
        received_message = None

        # Check messages received by either user
        all_messages = messages_a + messages_b
        if all_messages:
            received_message = all_messages[0]
            has_from_user = 'from_user_id' in received_message
            has_to_user = 'to_user_id' in received_message
            has_message = 'message' in received_message
            has_cursor_x = 'cursor_x' in received_message
            has_cursor_y = 'cursor_y' in received_message
            has_username = 'from_username' in received_message
            has_color = 'from_color' in received_message

            test2_pass = all([has_from_user, has_to_user, has_message,
                             has_cursor_x, has_cursor_y, has_username, has_color])

            print(f"\nTest 2: Message structure - {'✓ PASS' if test2_pass else '✗ FAIL'}")
            if not test2_pass:
                print(f"  Missing fields - from_user: {has_from_user}, to_user: {has_to_user}, "
                      f"message: {has_message}, cursor_x: {has_cursor_x}, cursor_y: {has_cursor_y}, "
                      f"username: {has_username}, color: {has_color}")
        else:
            print(f"\nTest 2: Message structure - ✗ FAIL (no messages received)")

        # Test 3: Message content should be correct
        test3_pass = False
        if received_message:
            correct_from = received_message.get('from_user_id') == 'user_a'
            correct_to = received_message.get('to_user_id') == 'user_b'
            correct_text = received_message.get('message') == 'Check this component'
            correct_cursor_x = received_message.get('cursor_x') == 150
            correct_cursor_y = received_message.get('cursor_y') == 250

            test3_pass = all([correct_from, correct_to, correct_text,
                             correct_cursor_x, correct_cursor_y])

            print(f"\nTest 3: Message content - {'✓ PASS' if test3_pass else '✗ FAIL'}")
            if test3_pass:
                print(f"  From: {received_message.get('from_user_id')} ({received_message.get('from_username')})")
                print(f"  To: {received_message.get('to_user_id')}")
                print(f"  Message: '{received_message.get('message')}'")
                print(f"  Cursor position: ({received_message.get('cursor_x')}, {received_message.get('cursor_y')})")
                print(f"  Color: {received_message.get('from_color')}")
        else:
            print(f"\nTest 3: Message content - ✗ FAIL (no messages to verify)")

        # Test 4: Both users should receive the message (broadcast)
        test4_pass = len(messages_a) > 0 and len(messages_b) > 0
        print(f"\nTest 4: Message broadcast to all users - {'✓ PASS' if test4_pass else '✗ FAIL'}")

        all_pass = test1_pass and test2_pass and test3_pass and test4_pass

        print("\n" + "=" * 80)
        if all_pass:
            print("✓ ALL TESTS PASSED - Feature #409 Working!")
        else:
            print("✗ SOME TESTS FAILED")
        print("=" * 80)

        return all_pass

    finally:
        # Cleanup
        await client_a.disconnect()
        await client_b.disconnect()


if __name__ == "__main__":
    try:
        result = asyncio.run(test_cursor_chat())
        exit(0 if result else 1)
    except Exception as e:
        print(f"\n✗ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
