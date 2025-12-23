#!/usr/bin/env python3
"""
Test script for Feature #39: Error tracking with stack traces and context
Tests that errors are logged with full stack traces, context, and correlation IDs.
"""

import requests
import json
import subprocess
import time
import sys
from typing import Dict, List, Any

# Test configuration
AUTH_SERVICE_URL = "http://localhost:8080/api/auth"
TEST_USER_ID = "test-user-789"
TEST_FILE_ID = "test-file-abc"

def run_test(test_name: str, test_func) -> bool:
    """Run a single test and return True if it passes."""
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print('='*80)
    try:
        test_func()
        print(f"✅ PASS: {test_name}")
        return True
    except AssertionError as e:
        print(f"❌ FAIL: {test_name}")
        print(f"   Error: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {test_name}")
        print(f"   Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_container_logs(correlation_id: str, tail: int = 50) -> List[Dict[str, Any]]:
    """Get logs from auth-service container and filter by correlation ID."""
    try:
        # Get logs without tail to ensure we get recent logs
        result = subprocess.run(
            ["docker", "logs", "autograph-auth-service"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        logs = []
        # Check both stdout and stderr
        for line in (result.stdout + result.stderr).split('\n'):
            if correlation_id in line:
                try:
                    log_entry = json.loads(line)
                    logs.append(log_entry)
                except json.JSONDecodeError:
                    continue
        
        return logs
    except subprocess.TimeoutExpired:
        print(f"   ⚠️  Timeout getting logs")
        return []
    except Exception as e:
        print(f"   ⚠️  Error getting logs: {e}")
        return []

# =============================================================================
# TEST 1: Error endpoint triggers error with context
# =============================================================================

def test_error_endpoint_triggers_error():
    """Test that error endpoint triggers an error and returns context."""
    response = requests.get(
        f"{AUTH_SERVICE_URL}/test/error",
        params={"user_id": TEST_USER_ID, "file_id": TEST_FILE_ID},
        timeout=10
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert "message" in data, "Response missing 'message'"
    assert "correlation_id" in data, "Response missing 'correlation_id'"
    assert "user_id" in data, "Response missing 'user_id'"
    assert "file_id" in data, "Response missing 'file_id'"
    assert "error_type" in data, "Response missing 'error_type'"
    assert "error_message" in data, "Response missing 'error_message'"
    
    assert data["user_id"] == TEST_USER_ID, f"user_id mismatch: {data['user_id']}"
    assert data["file_id"] == TEST_FILE_ID, f"file_id mismatch: {data['file_id']}"
    assert data["error_type"] == "ZeroDivisionError", f"error_type mismatch: {data['error_type']}"
    assert "division by zero" in data["error_message"], f"error_message mismatch: {data['error_message']}"
    
    print(f"   ✓ Error endpoint returned expected data")
    print(f"   ✓ Correlation ID: {data['correlation_id']}")
    
    # Store correlation_id for next test
    global LAST_CORRELATION_ID
    LAST_CORRELATION_ID = data['correlation_id']

# =============================================================================
# TEST 2: Error logged with full stack trace
# =============================================================================

def test_error_logged_with_stack_trace():
    """Test that error is logged with full stack trace."""
    # Wait for logs to propagate
    time.sleep(1)
    
    correlation_id = LAST_CORRELATION_ID
    logs = get_container_logs(correlation_id)
    
    assert len(logs) > 0, f"No logs found with correlation_id: {correlation_id}"
    print(f"   ✓ Found {len(logs)} log entries")
    
    # Find error log entry
    error_logs = [log for log in logs if log.get("level") == "ERROR"]
    assert len(error_logs) > 0, "No ERROR level logs found"
    print(f"   ✓ Found {len(error_logs)} ERROR log entries")
    
    # Check first error log has stack trace
    error_log = error_logs[0]
    assert "stack_trace" in error_log, "ERROR log missing 'stack_trace'"
    assert "error_type" in error_log, "ERROR log missing 'error_type'"
    assert "error_message" in error_log, "ERROR log missing 'error_message'"
    
    print(f"   ✓ Stack trace captured: {len(error_log['stack_trace'])} characters")
    print(f"   ✓ Error type: {error_log['error_type']}")
    print(f"   ✓ Error message: {error_log['error_message']}")

# =============================================================================
# TEST 3: Error includes request context
# =============================================================================

def test_error_includes_request_context():
    """Test that error log includes user_id, file_id, and correlation_id."""
    correlation_id = LAST_CORRELATION_ID
    logs = get_container_logs(correlation_id)
    
    # Find error log entry
    error_logs = [log for log in logs if log.get("level") == "ERROR"]
    error_log = error_logs[0]
    
    # Check context fields
    assert error_log.get("correlation_id") == correlation_id, "correlation_id mismatch in log"
    assert error_log.get("user_id") == TEST_USER_ID, "user_id missing or mismatch in log"
    assert error_log.get("file_id") == TEST_FILE_ID, "file_id missing or mismatch in log"
    
    print(f"   ✓ Correlation ID present: {error_log['correlation_id']}")
    print(f"   ✓ User ID present: {error_log['user_id']}")
    print(f"   ✓ File ID present: {error_log['file_id']}")

# =============================================================================
# TEST 4: Stack trace shows correct line numbers
# =============================================================================

def test_stack_trace_shows_line_numbers():
    """Test that stack trace includes file names and line numbers."""
    correlation_id = LAST_CORRELATION_ID
    logs = get_container_logs(correlation_id)
    
    error_logs = [log for log in logs if log.get("level") == "ERROR"]
    error_log = error_logs[0]
    stack_trace = error_log["stack_trace"]
    
    # Check for file names and line numbers in stack trace
    assert "/app/src/main.py" in stack_trace, "Stack trace missing file path"
    assert "line" in stack_trace, "Stack trace missing line numbers"
    assert "ZeroDivisionError" in stack_trace, "Stack trace missing exception type"
    
    print(f"   ✓ Stack trace includes file paths")
    print(f"   ✓ Stack trace includes line numbers")
    print(f"   ✓ Stack trace includes exception type")

# =============================================================================
# TEST 5: Multiple errors can be logged with different contexts
# =============================================================================

def test_multiple_errors_different_contexts():
    """Test that multiple errors can be logged with different contexts."""
    # Trigger first error
    response1 = requests.get(
        f"{AUTH_SERVICE_URL}/test/error",
        params={"user_id": "user-001", "file_id": "file-001"},
        timeout=10
    )
    correlation_id_1 = response1.json()["correlation_id"]
    
    time.sleep(0.5)
    
    # Trigger second error
    response2 = requests.get(
        f"{AUTH_SERVICE_URL}/test/error",
        params={"user_id": "user-002", "file_id": "file-002"},
        timeout=10
    )
    correlation_id_2 = response2.json()["correlation_id"]
    
    # Wait for logs
    time.sleep(1)
    
    # Check both errors are logged separately
    logs1 = get_container_logs(correlation_id_1)
    logs2 = get_container_logs(correlation_id_2)
    
    assert len(logs1) > 0, f"No logs for correlation_id {correlation_id_1}"
    assert len(logs2) > 0, f"No logs for correlation_id {correlation_id_2}"
    
    # Find error logs
    error_logs1 = [log for log in logs1 if log.get("level") == "ERROR"]
    error_logs2 = [log for log in logs2 if log.get("level") == "ERROR"]
    
    assert len(error_logs1) > 0, "No error logs for first request"
    assert len(error_logs2) > 0, "No error logs for second request"
    
    # Check contexts are different
    assert error_logs1[0].get("user_id") == "user-001", "First error user_id incorrect"
    assert error_logs2[0].get("user_id") == "user-002", "Second error user_id incorrect"
    
    print(f"   ✓ First error logged with user_id: user-001")
    print(f"   ✓ Second error logged with user_id: user-002")
    print(f"   ✓ Errors properly isolated by correlation_id")

# =============================================================================
# TEST 6: Nested errors show full call stack
# =============================================================================

def test_nested_errors_show_full_call_stack():
    """Test that nested errors show the full call stack."""
    response = requests.get(
        f"{AUTH_SERVICE_URL}/test/nested-error",
        timeout=10
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    correlation_id = data["correlation_id"]
    
    # Wait for logs
    time.sleep(1)
    
    logs = get_container_logs(correlation_id)
    error_logs = [log for log in logs if log.get("level") == "ERROR"]
    
    assert len(error_logs) > 0, "No error logs found"
    
    error_log = error_logs[0]
    stack_trace = error_log["stack_trace"]
    
    # Check that all three function levels are in the stack trace
    assert "level_1" in stack_trace, "Stack trace missing level_1 function"
    assert "level_2" in stack_trace, "Stack trace missing level_2 function"
    assert "level_3" in stack_trace, "Stack trace missing level_3 function"
    assert "IndexError" in stack_trace, "Stack trace missing IndexError"
    
    # Check custom context
    assert error_log.get("depth") == 3, "Missing depth context"
    assert "function_chain" in error_log, "Missing function_chain context"
    
    print(f"   ✓ Stack trace shows all 3 nested function calls")
    print(f"   ✓ Function chain: {error_log['function_chain']}")
    print(f"   ✓ Stack depth: {error_log['depth']}")

# =============================================================================
# TEST 7: Error type and message accurately captured
# =============================================================================

def test_error_type_and_message_captured():
    """Test that error type and message are accurately captured."""
    # Test ZeroDivisionError
    response1 = requests.get(f"{AUTH_SERVICE_URL}/test/error", timeout=10)
    data1 = response1.json()
    assert data1["error_type"] == "ZeroDivisionError", "Incorrect error type"
    assert "division by zero" in data1["error_message"], "Incorrect error message"
    
    # Test IndexError
    response2 = requests.get(f"{AUTH_SERVICE_URL}/test/nested-error", timeout=10)
    data2 = response2.json()
    assert data2["error_type"] == "IndexError", "Incorrect error type"
    
    print(f"   ✓ ZeroDivisionError captured correctly")
    print(f"   ✓ IndexError captured correctly")
    print(f"   ✓ Error messages accurate")

# =============================================================================
# Main test runner
# =============================================================================

def main():
    """Run all tests and report results."""
    print("="*80)
    print("FEATURE #39: ERROR TRACKING WITH STACK TRACES AND CONTEXT")
    print("="*80)
    print(f"\nTesting error tracking functionality...")
    print(f"Auth Service URL: {AUTH_SERVICE_URL}")
    
    # List of all tests
    tests = [
        ("Error endpoint triggers error with context", test_error_endpoint_triggers_error),
        ("Error logged with full stack trace", test_error_logged_with_stack_trace),
        ("Error includes request context (user_id, file_id, correlation_id)", test_error_includes_request_context),
        ("Stack trace shows correct line numbers", test_stack_trace_shows_line_numbers),
        ("Multiple errors can be logged with different contexts", test_multiple_errors_different_contexts),
        ("Nested errors show full call stack", test_nested_errors_show_full_call_stack),
        ("Error type and message accurately captured", test_error_type_and_message_captured),
    ]
    
    # Run all tests
    results = []
    for test_name, test_func in tests:
        passed = run_test(test_name, test_func)
        results.append((test_name, passed))
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed_count}/{total_count} tests passed ({passed_count/total_count*100:.1f}%)")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! Feature #39 is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
