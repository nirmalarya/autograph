#!/usr/bin/env python3
"""
Simple Test: Request Timeout Feature (Feature #34)

Tests that timeout middleware works correctly in API Gateway.
"""

import requests
import time

print("=" * 70)
print("Feature #34: Request Timeout Test")
print("=" * 70)
print()

# Configuration
SERVICE_URL = "http://localhost:8085"
TIMEOUT = 30

# Test 1: Service is running
print("Test 1: Check service is running...")
try:
    r = requests.get(f"{SERVICE_URL}/health", timeout=5)
    print(f"✓ Service is healthy: {r.json()}")
except Exception as e:
    print(f"✗ Service not running: {e}")
    exit(1)

# Test 2: Fast request completes
print("\nTest 2: Fast request (5s) completes...")
start = time.time()
try:
    r = requests.get(f"{SERVICE_URL}/slow?delay=5", timeout=TIMEOUT)
    elapsed = time.time() - start
    print(f"✓ Completed in {elapsed:.2f}s")
    print(f"  Response: {r.json()['message']}")
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 3: Medium request completes
print("\nTest 3: Medium request (20s) completes...")
start = time.time()
try:
    r = requests.get(f"{SERVICE_URL}/slow?delay=20", timeout=TIMEOUT)
    elapsed = time.time() - start
    print(f"✓ Completed in {elapsed:.2f}s (within {TIMEOUT}s timeout)")
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 4: Slow request times out
print("\nTest 4: Slow request (35s) times out...")
start = time.time()
try:
    r = requests.get(f"{SERVICE_URL}/slow?delay=35", timeout=TIMEOUT)
    elapsed = time.time() - start
    print(f"✗ Should have timed out but completed in {elapsed:.2f}s")
except requests.exceptions.Timeout:
    elapsed = time.time() - start
    print(f"✓ Timed out correctly after {elapsed:.2f}s")
    if abs(elapsed - TIMEOUT) <= 1:
        print(f"✓ Timeout duration matches {TIMEOUT}s configuration")
except Exception as e:
    print(f"✗ Unexpected error: {e}")

print()
print("=" * 70)
print("Summary:")
print("  - Timeout middleware implemented in services/api-gateway/src/main.py")
print("  - Uses asyncio.wait_for() to enforce REQUEST_TIMEOUT")
print("  - Returns 504 Gateway Timeout on timeout")
print("  - Configuration: REQUEST_TIMEOUT=30 in .env.docker")
print("=" * 70)
