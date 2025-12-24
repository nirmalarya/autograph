#!/usr/bin/env python3
"""Debug script to check sessions in Redis."""

import redis
import json

# Connect to Redis
redis_client = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

print("Scanning for all session keys...")
pattern = "session:*"
sessions = []

for key in redis_client.scan_iter(match=pattern):
    # Ensure key is a string
    if isinstance(key, bytes):
        key = key.decode('utf-8')
    
    session_data_str = redis_client.get(key)
    if session_data_str:
        session_data = json.loads(session_data_str)
        sessions.append({
            "key": key,
            "user_id": session_data.get("user_id"),
            "created_at": session_data.get("created_at"),
        })
        print(f"  Key: {key[:50]}...")
        print(f"    User ID: {session_data.get('user_id')}")
        print(f"    Created: {session_data.get('created_at')}")
        print()

print(f"\nTotal sessions found: {len(sessions)}")

# Group by user
from collections import defaultdict
user_sessions = defaultdict(list)
for session in sessions:
    user_sessions[session["user_id"]].append(session)

print("\nSessions by user:")
for user_id, user_sess in user_sessions.items():
    print(f"  User {user_id}: {len(user_sess)} sessions")
