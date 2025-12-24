#!/usr/bin/env python3
"""Clear all session data from Redis to start fresh."""

import redis

# Connect to Redis
redis_client = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

print("Clearing all session data from Redis...")

# Delete all session:* keys
pattern = "session:*"
count = 0
for key in redis_client.scan_iter(match=pattern):
    redis_client.delete(key)
    count += 1

print(f"Deleted {count} session keys")

# Delete all user_sessions:* sets
pattern2 = "user_sessions:*"
count2 = 0
for key in redis_client.scan_iter(match=pattern2):
    redis_client.delete(key)
    count2 += 1

print(f"Deleted {count2} user_sessions sets")

print("\nRedis session data cleared!")
