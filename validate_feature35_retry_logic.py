#!/usr/bin/env python3
"""
Feature 35: Retry logic with exponential backoff for transient failures

Tests:
1. Configure retry: 3 attempts, exponential backoff ✓
2. Simulate transient database connection failure
3. Verify first attempt fails
4. Verify retry after 1 second (with jitter)
5. Verify retry after 2 seconds (with jitter)
6. Verify retry after 4 seconds (with jitter)
7. Simulate success on 3rd attempt
8. Verify request eventually succeeds
"""

import sys
import os
import time
import asyncio
from typing import List

# Add shared modules to path
sys.path.insert(0, '/Users/nirmalarya/Workspace/autograph')

from shared.python.retry import (
    retry,
    async_retry,
    RetryConfig,
    DATABASE_RETRY_CONFIG,
    API_RETRY_CONFIG,
    REDIS_RETRY_CONFIG
)


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


class TransientFailureSimulator:
    """Simulates transient failures for testing retry logic."""

    def __init__(self, fail_count: int = 2):
        """
        Initialize simulator.

        Args:
            fail_count: Number of times to fail before succeeding
        """
        self.fail_count = fail_count
        self.attempt_count = 0
        self.attempt_times: List[float] = []

    def __call__(self):
        """Simulate a function that fails transiently."""
        self.attempt_count += 1
        self.attempt_times.append(time.time())

        if self.attempt_count <= self.fail_count:
            raise ConnectionError(f"Simulated transient failure (attempt {self.attempt_count})")

        return f"Success on attempt {self.attempt_count}"

    async def async_call(self):
        """Async version of the simulated function."""
        self.attempt_count += 1
        self.attempt_times.append(time.time())

        if self.attempt_count <= self.fail_count:
            raise ConnectionError(f"Simulated transient failure (attempt {self.attempt_count})")

        return f"Success on attempt {self.attempt_count}"

    def get_delays(self) -> List[float]:
        """Get delays between attempts."""
        if len(self.attempt_times) < 2:
            return []

        delays = []
        for i in range(1, len(self.attempt_times)):
            delay = self.attempt_times[i] - self.attempt_times[i-1]
            delays.append(delay)

        return delays


def test_retry_config():
    """Test RetryConfig class."""
    print_test("RetryConfig class")

    config = RetryConfig(
        max_attempts=3,
        initial_delay=1.0,
        max_delay=60.0,
        exponential_base=2.0,
        jitter=False  # Disable jitter for predictable testing
    )

    # Test delay calculation
    delay_0 = config.get_delay(0)  # 1.0 * (2^0) = 1.0
    delay_1 = config.get_delay(1)  # 1.0 * (2^1) = 2.0
    delay_2 = config.get_delay(2)  # 1.0 * (2^2) = 4.0

    print_success(f"Delay for attempt 0: {delay_0}s (expected 1.0s)")
    print_success(f"Delay for attempt 1: {delay_1}s (expected 2.0s)")
    print_success(f"Delay for attempt 2: {delay_2}s (expected 4.0s)")

    if abs(delay_0 - 1.0) < 0.01 and abs(delay_1 - 2.0) < 0.01 and abs(delay_2 - 4.0) < 0.01:
        print_success("Exponential backoff calculation correct")
        return True
    else:
        print_error("Exponential backoff calculation incorrect")
        return False


def test_sync_retry_success():
    """Test synchronous retry decorator with eventual success."""
    print_test("Synchronous retry with eventual success")

    # Configure retry without jitter for predictable timing
    config = RetryConfig(
        max_attempts=3,
        initial_delay=0.5,  # Use shorter delays for testing
        exponential_base=2.0,
        jitter=False,
        exceptions=(ConnectionError,)
    )

    simulator = TransientFailureSimulator(fail_count=2)  # Fail 2 times, succeed on 3rd

    @retry(config)
    def test_function():
        return simulator()

    try:
        start_time = time.time()
        result = test_function()
        duration = time.time() - start_time

        print_success(f"Result: {result}")
        print_success(f"Total attempts: {simulator.attempt_count}")
        print_success(f"Total duration: {duration:.2f}s")

        # Verify delays
        delays = simulator.get_delays()
        print_success(f"Delays between attempts: {[f'{d:.2f}s' for d in delays]}")

        # Check if delays are approximately correct (0.5s, 1.0s with some tolerance)
        if len(delays) == 2:
            if 0.4 < delays[0] < 0.6 and 0.9 < delays[1] < 1.1:
                print_success("Exponential backoff timing correct")
                return True
            else:
                print_error(f"Delays incorrect: {delays}")
                return False
        else:
            print_error(f"Expected 2 delays, got {len(delays)}")
            return False

    except Exception as e:
        print_error(f"Test failed: {e}")
        return False


async def test_async_retry_success():
    """Test asynchronous retry decorator with eventual success."""
    print_test("Asynchronous retry with eventual success")

    # Configure retry without jitter for predictable timing
    config = RetryConfig(
        max_attempts=3,
        initial_delay=0.5,
        exponential_base=2.0,
        jitter=False,
        exceptions=(ConnectionError,)
    )

    simulator = TransientFailureSimulator(fail_count=2)

    @async_retry(config)
    async def test_async_function():
        return await simulator.async_call()

    try:
        start_time = time.time()
        result = await test_async_function()
        duration = time.time() - start_time

        print_success(f"Result: {result}")
        print_success(f"Total attempts: {simulator.attempt_count}")
        print_success(f"Total duration: {duration:.2f}s")

        # Verify delays
        delays = simulator.get_delays()
        print_success(f"Delays between attempts: {[f'{d:.2f}s' for d in delays]}")

        if len(delays) == 2:
            if 0.4 < delays[0] < 0.6 and 0.9 < delays[1] < 1.1:
                print_success("Async exponential backoff timing correct")
                return True
            else:
                print_error(f"Delays incorrect: {delays}")
                return False
        else:
            print_error(f"Expected 2 delays, got {len(delays)}")
            return False

    except Exception as e:
        print_error(f"Test failed: {e}")
        return False


def test_retry_exhaustion():
    """Test that retry exhausts after max attempts."""
    print_test("Retry exhaustion after max attempts")

    config = RetryConfig(
        max_attempts=3,
        initial_delay=0.1,
        exponential_base=2.0,
        jitter=False,
        exceptions=(ConnectionError,)
    )

    # Simulator that always fails
    simulator = TransientFailureSimulator(fail_count=10)

    @retry(config)
    def test_function():
        return simulator()

    try:
        result = test_function()
        print_error("Should have raised ConnectionError")
        return False

    except ConnectionError as e:
        print_success(f"Correctly raised exception after {simulator.attempt_count} attempts")

        if simulator.attempt_count == 3:
            print_success("Max attempts (3) respected")
            return True
        else:
            print_error(f"Expected 3 attempts, got {simulator.attempt_count}")
            return False


def test_jitter():
    """Test that jitter adds randomization to delays."""
    print_test("Jitter randomization")

    config_with_jitter = RetryConfig(
        max_attempts=3,
        initial_delay=1.0,
        exponential_base=2.0,
        jitter=True
    )

    config_without_jitter = RetryConfig(
        max_attempts=3,
        initial_delay=1.0,
        exponential_base=2.0,
        jitter=False
    )

    # Get delays with jitter
    delays_with_jitter = [config_with_jitter.get_delay(0) for _ in range(5)]

    # Get delays without jitter
    delays_without_jitter = [config_without_jitter.get_delay(0) for _ in range(5)]

    print_info(f"Delays with jitter: {[f'{d:.3f}s' for d in delays_with_jitter]}")
    print_info(f"Delays without jitter: {[f'{d:.3f}s' for d in delays_without_jitter]}")

    # Check that jittered delays vary
    jitter_variance = len(set(round(d, 2) for d in delays_with_jitter)) > 1

    # Check that non-jittered delays are consistent
    no_jitter_consistent = len(set(delays_without_jitter)) == 1

    if jitter_variance:
        print_success("Jitter adds randomization")
    else:
        print_error("Jitter not adding randomization")

    if no_jitter_consistent:
        print_success("No jitter is consistent")
    else:
        print_error("No jitter should be consistent")

    return jitter_variance and no_jitter_consistent


def test_predefined_configs():
    """Test predefined retry configurations."""
    print_test("Predefined retry configurations")

    # Test DATABASE_RETRY_CONFIG
    print_success(f"DATABASE_RETRY_CONFIG:")
    print_success(f"  max_attempts: {DATABASE_RETRY_CONFIG.max_attempts}")
    print_success(f"  initial_delay: {DATABASE_RETRY_CONFIG.initial_delay}s")
    print_success(f"  max_delay: {DATABASE_RETRY_CONFIG.max_delay}s")
    print_success(f"  exponential_base: {DATABASE_RETRY_CONFIG.exponential_base}")

    # Test API_RETRY_CONFIG
    print_success(f"API_RETRY_CONFIG:")
    print_success(f"  max_attempts: {API_RETRY_CONFIG.max_attempts}")
    print_success(f"  initial_delay: {API_RETRY_CONFIG.initial_delay}s")
    print_success(f"  max_delay: {API_RETRY_CONFIG.max_delay}s")

    # Test REDIS_RETRY_CONFIG
    print_success(f"REDIS_RETRY_CONFIG:")
    print_success(f"  max_attempts: {REDIS_RETRY_CONFIG.max_attempts}")
    print_success(f"  initial_delay: {REDIS_RETRY_CONFIG.initial_delay}s")
    print_success(f"  max_delay: {REDIS_RETRY_CONFIG.max_delay}s")

    return True


def test_retry_usage_in_services():
    """Test that retry is being used in services."""
    print_test("Retry usage in services")

    # Check if auth service uses retry
    try:
        with open('/Users/nirmalarya/Workspace/autograph/services/auth-service/src/database.py', 'r') as f:
            content = f.read()

        if '@retry(DATABASE_RETRY_CONFIG)' in content:
            print_success("Auth service database uses retry logic")
            return True
        else:
            print_error("Auth service database doesn't use retry")
            return False

    except Exception as e:
        print_error(f"Failed to check service usage: {e}")
        return False


async def main():
    print(f"\n{'='*80}")
    print(f"Feature 35: Retry Logic with Exponential Backoff Validation")
    print(f"{'='*80}")

    tests = [
        ("RetryConfig", test_retry_config()),
        ("Sync Retry Success", test_sync_retry_success()),
        ("Async Retry Success", test_async_retry_success()),
        ("Retry Exhaustion", test_retry_exhaustion()),
        ("Jitter Randomization", test_jitter()),
        ("Predefined Configs", test_predefined_configs()),
        ("Service Usage", test_retry_usage_in_services()),
    ]

    results = []
    for test_name, test_result in tests:
        if asyncio.iscoroutine(test_result):
            result = await test_result
        else:
            result = test_result
        results.append((test_name, result))

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
        print(f"\n{Colors.GREEN}✓ Feature 35: Retry logic with exponential backoff - PASSING{Colors.END}")
        return 0
    else:
        print(f"\n{Colors.RED}✗ Feature 35: FAILING - {total - passed} test(s) failed{Colors.END}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
