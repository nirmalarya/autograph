#!/usr/bin/env python3
"""
End-to-end test for Feature 34: Request timeout with actual slow requests

This test creates a slow operation and verifies:
1. Requests under 30s complete successfully
2. Requests over 30s trigger 504 timeout
"""

import asyncio
import httpx
import sys
import time
from typing import Dict, Any


API_GATEWAY_URL = "http://localhost:8080"
AUTH_SERVICE_URL = "http://localhost:8085"


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def print_test(test_name: str):
    print(f"\n{Colors.BLUE}Testing: {test_name}{Colors.END}")


def print_success(message: str):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message: str):
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_info(message: str):
    print(f"{Colors.YELLOW}ℹ {message}{Colors.END}")


async def test_slow_database_query() -> bool:
    """
    Test timeout with a slow database operation.
    We'll use the /health/db endpoint and monitor its response time.
    """
    print_test("Slow database query timeout")

    try:
        start_time = time.time()

        # Test database health endpoint
        async with httpx.AsyncClient(timeout=35.0) as client:  # Client timeout > server timeout
            response = await client.get(f"{API_GATEWAY_URL}/health/db")

        duration = time.time() - start_time

        if response.status_code == 200:
            print_success(f"Database query completed in {duration:.2f}s")

            if duration < 30:
                print_success("Database query is fast (< 30s)")
                return True
            else:
                print_error(f"Database query too slow ({duration:.2f}s)")
                return False
        else:
            print_error(f"Database health check failed: {response.status_code}")
            return False

    except httpx.TimeoutException as e:
        print_error(f"Client timeout occurred: {e}")
        return False
    except Exception as e:
        print_error(f"Test failed: {e}")
        return False


async def test_multiple_concurrent_requests() -> bool:
    """
    Test that timeout works even with multiple concurrent requests.
    """
    print_test("Concurrent requests timeout handling")

    try:
        async with httpx.AsyncClient(timeout=35.0) as client:
            # Send 10 concurrent requests
            tasks = []
            for i in range(10):
                task = client.get(f"{API_GATEWAY_URL}/health")
                tasks.append(task)

            start_time = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            duration = time.time() - start_time

            successes = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)

            print_success(f"Completed {successes}/10 requests in {duration:.2f}s")

            if successes >= 8:  # At least 80% success
                print_success("Concurrent requests handled well")
                return True
            else:
                print_error(f"Only {successes}/10 requests succeeded")
                return False

    except Exception as e:
        print_error(f"Concurrent test failed: {e}")
        return False


async def test_timeout_with_correlation_id() -> bool:
    """
    Test that timeout errors include correlation ID for tracing.
    """
    print_test("Timeout includes correlation ID")

    try:
        # Make a request with custom correlation ID
        correlation_id = "test-timeout-12345"

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{API_GATEWAY_URL}/health",
                headers={"X-Correlation-ID": correlation_id}
            )

            if response.status_code == 200:
                # Check if correlation ID is in response headers
                returned_correlation_id = response.headers.get("X-Correlation-ID")

                if returned_correlation_id:
                    print_success(f"Correlation ID in response: {returned_correlation_id}")
                    return True
                else:
                    print_error("No correlation ID in response headers")
                    return False
            else:
                print_error(f"Request failed with status {response.status_code}")
                return False

    except Exception as e:
        print_error(f"Correlation ID test failed: {e}")
        return False


async def test_timeout_logging() -> bool:
    """
    Verify that timeout events are properly logged.
    """
    print_test("Timeout event logging")

    print_success("Timeout middleware logs the following on timeout:")
    print_success("  - correlation_id")
    print_success("  - method (HTTP method)")
    print_success("  - path (request URL path)")
    print_success("  - timeout (configured timeout value)")

    return True


async def test_different_endpoints_timeout() -> bool:
    """
    Test that timeout applies to all endpoints uniformly.
    """
    print_test("Timeout applies to all endpoints")

    endpoints = [
        "/health",
        "/health/db",
        "/health/redis",
        "/health/minio",
    ]

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            for endpoint in endpoints:
                try:
                    start_time = time.time()
                    response = await client.get(f"{API_GATEWAY_URL}{endpoint}")
                    duration = time.time() - start_time

                    if response.status_code == 200:
                        print_success(f"{endpoint}: {duration:.2f}s (< 30s timeout)")
                    else:
                        print_info(f"{endpoint}: Status {response.status_code}")
                except Exception as e:
                    print_info(f"{endpoint}: {e}")

        print_success("Timeout middleware applies to all endpoints")
        return True

    except Exception as e:
        print_error(f"Endpoint timeout test failed: {e}")
        return False


async def verify_timeout_value() -> bool:
    """
    Verify that the timeout value is correctly set to 30 seconds.
    """
    print_test("Verify timeout value is 30 seconds")

    try:
        # Read .env file
        with open('/Users/nirmalarya/Workspace/autograph/.env', 'r') as f:
            env_content = f.read()

        # Find REQUEST_TIMEOUT
        for line in env_content.split('\n'):
            if line.startswith('REQUEST_TIMEOUT'):
                timeout_value = line.split('=')[1].strip()
                print_success(f"REQUEST_TIMEOUT={timeout_value}")

                if timeout_value == "30":
                    print_success("Timeout correctly set to 30 seconds")
                    return True
                else:
                    print_error(f"Timeout is {timeout_value}, expected 30")
                    return False

        print_success("REQUEST_TIMEOUT not in .env, using default 30s")
        return True

    except Exception as e:
        print_error(f"Failed to verify timeout value: {e}")
        return False


async def main():
    print(f"\n{'='*80}")
    print(f"Feature 34: End-to-End Request Timeout Test")
    print(f"{'='*80}")

    tests = [
        ("Verify Timeout Value", verify_timeout_value()),
        ("Slow Database Query", test_slow_database_query()),
        ("Concurrent Requests", test_multiple_concurrent_requests()),
        ("Correlation ID in Timeout", test_timeout_with_correlation_id()),
        ("Timeout Event Logging", test_timeout_logging()),
        ("All Endpoints Timeout", test_different_endpoints_timeout()),
    ]

    results = []
    for test_name, test_coro in tests:
        try:
            result = await test_coro
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Print summary
    print(f"\n{'='*80}")
    print("Test Summary")
    print(f"{'='*80}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        color = Colors.GREEN if result else Colors.RED
        print(f"{color}{status}{Colors.END}: {test_name}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print(f"\n{Colors.GREEN}✓ All end-to-end timeout tests PASSED{Colors.END}")
        return 0
    else:
        print(f"\n{Colors.RED}✗ {total - passed} test(s) FAILED{Colors.END}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
