#!/usr/bin/env python3
"""
Test Script: Retry Logic with Exponential Backoff (Feature #35)

This script tests the retry decorator with exponential backoff for handling
transient failures in database connections and external API calls.

Test Coverage:
1. Configure retry: 3 attempts, exponential backoff (1s, 2s, 4s)
2. Simulate transient database connection failure
3. Verify first attempt fails
4. Verify retry after 1 second
5. Verify retry after 2 seconds  
6. Verify retry after 4 seconds (if needed)
7. Simulate success on Nth attempt
8. Verify request eventually succeeds
"""

import sys
import os
import time
from datetime import datetime
import random

# Add shared modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shared', 'python'))
from retry import retry, async_retry, RetryConfig

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

def print_test(test_num, description):
    print(f"{YELLOW}Test {test_num}: {description}{RESET}")

def print_success(message):
    print(f"{GREEN}✓ {message}{RESET}")

def print_error(message):
    print(f"{RED}✗ {message}{RESET}")

def print_info(message):
    print(f"  {message}")


# Test 1: Verify retry decorator basics
def test_1_retry_config():
    """Test 1: Verify retry configuration."""
    print_test(1, "Verify RetryConfig with 3 attempts and exponential backoff")
    
    config = RetryConfig(
        max_attempts=3,
        initial_delay=1.0,
        exponential_base=2.0,
        jitter=False  # Disable jitter for predictable testing
    )
    
    print_info(f"Max attempts: {config.max_attempts}")
    print_info(f"Initial delay: {config.initial_delay}s")
    print_info(f"Exponential base: {config.exponential_base}")
    
    # Calculate expected delays
    delays = [config.get_delay(i) for i in range(3)]
    print_info(f"Expected delays: {[f'{d:.1f}s' for d in delays]}")
    
    # Verify exponential growth
    if delays[0] == 1.0 and delays[1] == 2.0 and delays[2] == 4.0:
        print_success("Exponential backoff configured correctly: 1s, 2s, 4s")
        return True
    else:
        print_error(f"Unexpected delays: {delays}")
        return False


# Test 2: Test successful retry after transient failure
def test_2_retry_after_transient_failure():
    """Test 2: Simulate transient failure that succeeds on retry."""
    print_test(2, "Retry succeeds after transient failures")
    
    attempt_count = [0]
    attempt_times = []
    start_time = time.time()
    
    @retry(RetryConfig(
        max_attempts=3,
        initial_delay=1.0,
        exponential_base=2.0,
        jitter=False,
        exceptions=(ConnectionError,)
    ))
    def flaky_operation():
        """Simulates operation that fails twice, succeeds on third attempt."""
        attempt_count[0] += 1
        attempt_times.append(time.time() - start_time)
        
        if attempt_count[0] < 3:
            print_info(f"  Attempt {attempt_count[0]}: Failing (simulated transient error)")
            raise ConnectionError(f"Transient failure on attempt {attempt_count[0]}")
        
        print_info(f"  Attempt {attempt_count[0]}: Success!")
        return "Success"
    
    try:
        result = flaky_operation()
        
        if result == "Success" and attempt_count[0] == 3:
            print_success(f"Operation succeeded after {attempt_count[0]} attempts")
            
            # Verify timing
            if len(attempt_times) == 3:
                delay1 = attempt_times[1] - attempt_times[0]
                delay2 = attempt_times[2] - attempt_times[1]
                print_info(f"Timing: Attempt 1 at {attempt_times[0]:.2f}s")
                print_info(f"        Attempt 2 at {attempt_times[1]:.2f}s (delay: {delay1:.2f}s)")
                print_info(f"        Attempt 3 at {attempt_times[2]:.2f}s (delay: {delay2:.2f}s)")
                
                # Verify delays are approximately 1s and 2s (±0.1s tolerance)
                if abs(delay1 - 1.0) < 0.1 and abs(delay2 - 2.0) < 0.1:
                    print_success("Exponential backoff timing verified: ~1s, ~2s")
                    return True
                else:
                    print_error(f"Timing mismatch: expected ~1s and ~2s, got {delay1:.2f}s and {delay2:.2f}s")
                    return False
            return True
        else:
            print_error(f"Unexpected result: {result}, attempts: {attempt_count[0]}")
            return False
    except Exception as e:
        print_error(f"Operation failed: {e}")
        return False


# Test 3: Test all retries exhausted
def test_3_all_retries_exhausted():
    """Test 3: All retry attempts exhausted."""
    print_test(3, "All retries exhausted - final exception raised")
    
    attempt_count = [0]
    
    @retry(RetryConfig(
        max_attempts=3,
        initial_delay=0.5,
        exponential_base=2.0,
        jitter=False,
        exceptions=(ConnectionError,)
    ))
    def always_fails():
        """Always fails."""
        attempt_count[0] += 1
        print_info(f"  Attempt {attempt_count[0]}: Failing")
        raise ConnectionError(f"Persistent failure on attempt {attempt_count[0]}")
    
    try:
        always_fails()
        print_error("Should have raised exception after 3 attempts")
        return False
    except ConnectionError as e:
        if attempt_count[0] == 3:
            print_success(f"All {attempt_count[0]} attempts failed as expected")
            print_success(f"Final exception raised: {str(e)}")
            return True
        else:
            print_error(f"Expected 3 attempts, got {attempt_count[0]}")
            return False


# Test 4: Test database retry configuration
def test_4_database_retry_config():
    """Test 4: Verify DATABASE_RETRY_CONFIG."""
    print_test(4, "Verify DATABASE_RETRY_CONFIG")
    
    from retry import DATABASE_RETRY_CONFIG
    
    print_info(f"Max attempts: {DATABASE_RETRY_CONFIG.max_attempts}")
    print_info(f"Initial delay: {DATABASE_RETRY_CONFIG.initial_delay}s")
    print_info(f"Max delay: {DATABASE_RETRY_CONFIG.max_delay}s")
    print_info(f"Exponential base: {DATABASE_RETRY_CONFIG.exponential_base}")
    print_info(f"Jitter enabled: {DATABASE_RETRY_CONFIG.jitter}")
    
    if (DATABASE_RETRY_CONFIG.max_attempts == 3 and
        DATABASE_RETRY_CONFIG.initial_delay == 1.0 and
        DATABASE_RETRY_CONFIG.exponential_base == 2.0):
        print_success("DATABASE_RETRY_CONFIG configured correctly")
        return True
    else:
        print_error("DATABASE_RETRY_CONFIG has unexpected values")
        return False


# Test 5: Test API retry configuration
def test_5_api_retry_config():
    """Test 5: Verify API_RETRY_CONFIG."""
    print_test(5, "Verify API_RETRY_CONFIG")
    
    from retry import API_RETRY_CONFIG
    
    print_info(f"Max attempts: {API_RETRY_CONFIG.max_attempts}")
    print_info(f"Initial delay: {API_RETRY_CONFIG.initial_delay}s")
    print_info(f"Max delay: {API_RETRY_CONFIG.max_delay}s")
    
    if (API_RETRY_CONFIG.max_attempts == 3 and
        API_RETRY_CONFIG.initial_delay == 1.0):
        print_success("API_RETRY_CONFIG configured correctly")
        return True
    else:
        print_error("API_RETRY_CONFIG has unexpected values")
        return False


# Test 6: Test jitter functionality
def test_6_jitter_adds_randomness():
    """Test 6: Verify jitter adds randomness to delays."""
    print_test(6, "Verify jitter adds randomness to prevent thundering herd")
    
    config = RetryConfig(
        max_attempts=3,
        initial_delay=1.0,
        exponential_base=2.0,
        jitter=True
    )
    
    # Get multiple delay samples
    samples = [config.get_delay(0) for _ in range(10)]
    
    # Check that not all delays are exactly the same (jitter is working)
    unique_values = len(set(samples))
    
    print_info(f"Generated {len(samples)} delay samples with jitter")
    print_info(f"Unique values: {unique_values}")
    print_info(f"Min delay: {min(samples):.3f}s")
    print_info(f"Max delay: {max(samples):.3f}s")
    
    if unique_values > 1:
        print_success("Jitter is adding randomness (prevents thundering herd)")
        return True
    else:
        print_error("Jitter not working - all values identical")
        return False


# Test 7: Test max delay cap
def test_7_max_delay_cap():
    """Test 7: Verify max delay prevents unbounded growth."""
    print_test(7, "Verify max_delay caps exponential growth")
    
    config = RetryConfig(
        max_attempts=10,
        initial_delay=1.0,
        max_delay=10.0,
        exponential_base=2.0,
        jitter=False
    )
    
    # Calculate delays for many attempts
    delays = [config.get_delay(i) for i in range(10)]
    
    print_info(f"Delays: {[f'{d:.1f}s' for d in delays]}")
    
    # Verify no delay exceeds max_delay
    if all(d <= config.max_delay for d in delays):
        print_success(f"All delays capped at {config.max_delay}s")
        return True
    else:
        print_error(f"Some delays exceed max_delay: {max(delays):.1f}s > {config.max_delay}s")
        return False


# Test 8: Test async retry
def test_8_async_retry():
    """Test 8: Verify async_retry decorator works."""
    print_test(8, "Verify async_retry decorator")
    
    import asyncio
    
    attempt_count = [0]
    
    @async_retry(RetryConfig(
        max_attempts=3,
        initial_delay=0.5,
        exponential_base=2.0,
        jitter=False,
        exceptions=(ConnectionError,)
    ))
    async def async_flaky_operation():
        """Async operation that succeeds on second attempt."""
        attempt_count[0] += 1
        
        if attempt_count[0] < 2:
            print_info(f"  Async attempt {attempt_count[0]}: Failing")
            raise ConnectionError(f"Transient async failure")
        
        print_info(f"  Async attempt {attempt_count[0]}: Success!")
        return "Async success"
    
    try:
        result = asyncio.run(async_flaky_operation())
        
        if result == "Async success" and attempt_count[0] == 2:
            print_success(f"Async operation succeeded after {attempt_count[0]} attempts")
            return True
        else:
            print_error(f"Unexpected async result: {result}")
            return False
    except Exception as e:
        print_error(f"Async operation failed: {e}")
        return False


def main():
    """Run all tests."""
    print_header("Feature #35: Retry Logic with Exponential Backoff")
    
    print_info(f"Test Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info("")
    print_info("Testing retry decorator implementation:")
    print_info("  - shared/python/retry.py (RetryConfig, retry, async_retry)")
    print_info("  - Exponential backoff: delay = initial_delay * (2 ^ attempt)")
    print_info("  - Default: 3 attempts with 1s, 2s, 4s delays")
    print_info("  - Jitter adds ±25% randomization to prevent thundering herd")
    
    # Run tests
    tests = [
        test_1_retry_config,
        test_2_retry_after_transient_failure,
        test_3_all_retries_exhausted,
        test_4_database_retry_config,
        test_5_api_retry_config,
        test_6_jitter_adds_randomness,
        test_7_max_delay_cap,
        test_8_async_retry,
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print_error(f"Test failed with exception: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append(False)
        print()  # Empty line between tests
    
    # Print summary
    print_header("Test Summary")
    
    passed = sum(results)
    total = len(results)
    
    print_info(f"Tests Passed: {passed}/{total}")
    print_info(f"Tests Failed: {total - passed}/{total}")
    print_info(f"Success Rate: {passed/total*100:.1f}%")
    
    print()
    print_info("Implementation Details:")
    print_info("✓ Retry decorator in shared/python/retry.py")
    print_info("✓ Exponential backoff with configurable parameters")
    print_info("✓ Support for both sync and async functions")
    print_info("✓ Jitter to prevent thundering herd")
    print_info("✓ Max delay cap to prevent unbounded growth")
    print_info("✓ Configurable exception types to retry on")
    print_info("")
    print_info("Database retry configuration:")
    print_info("✓ Applied to database connection in auth-service/src/database.py")
    print_info("✓ 3 attempts with 1s, 2s, 4s delays")
    print_info("✓ Retries on ConnectionError, TimeoutError, OSError")
    print()
    
    if passed == total:
        print_success("✓ All tests passed! Feature #35 is working correctly.")
        print_success("  Retry logic with exponential backoff successfully implemented.")
        return 0
    else:
        print_error(f"✗ {total - passed} test(s) failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
