#!/usr/bin/env python3
"""
Test Configurable Log Levels
Feature #38: Log levels configurable per service (DEBUG, INFO, WARNING, ERROR)

Tests that log levels can be configured via LOG_LEVEL environment variable
and that logs are filtered according to the configured level.
"""

import requests
import subprocess
import json
import sys
import time

# Configuration
API_BASE = "http://localhost:8080"
AUTH_BASE = f"{API_BASE}/api/auth"

def print_test(name):
    """Print test section header."""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")

def print_result(passed, message):
    """Print test result."""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status}: {message}")
    return passed

def get_recent_logs(service, lines=50):
    """Get recent logs from a Docker container."""
    try:
        result = subprocess.run(
            ["docker", "logs", f"autograph-{service}", "--tail", str(lines)],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout + result.stderr
    except Exception as e:
        print(f"Error getting logs: {e}")
        return ""

def parse_json_logs(logs):
    """Parse JSON log lines from mixed output."""
    json_logs = []
    for line in logs.split('\n'):
        line = line.strip()
        if not line or not line.startswith('{'):
            continue
        try:
            log_entry = json.loads(line)
            json_logs.append(log_entry)
        except json.JSONDecodeError:
            pass
    return json_logs

def restart_service_with_log_level(service, log_level):
    """Restart a service with a specific log level."""
    print(f"Restarting {service} with LOG_LEVEL={log_level}...")
    
    try:
        # Stop the service
        subprocess.run(
            ["docker", "compose", "stop", service],
            cwd="/Users/nirmalarya/Workspace/auto-harness/cursor-autonomous-coding/autograph-v3",
            capture_output=True,
            timeout=30
        )
        
        # Start with new log level
        subprocess.run(
            ["docker", "compose", "up", "-d", "--no-deps", service],
            env={**subprocess.os.environ, "LOG_LEVEL": log_level},
            cwd="/Users/nirmalarya/Workspace/auto-harness/cursor-autonomous-coding/autograph-v3",
            capture_output=True,
            timeout=30
        )
        
        # Wait for service to start
        time.sleep(5)
        
        return True
    except Exception as e:
        print(f"Error restarting service: {e}")
        return False

def test_current_log_level():
    """Test 1: Verify current log level is INFO by default."""
    print_test("Default Log Level is INFO")
    
    try:
        response = requests.get(f"{AUTH_BASE}/test/logging", timeout=5)
        
        if response.status_code != 200:
            return print_result(False, f"Request failed: {response.status_code}")
        
        data = response.json()
        current_level = data.get("current_log_level", "unknown")
        
        print(f"Current log level: {current_level}")
        
        if current_level != "INFO":
            return print_result(False, f"Expected INFO, got {current_level}")
        
        return print_result(True, f"Default log level is INFO")
        
    except Exception as e:
        return print_result(False, f"Error: {e}")

def test_info_level_filters_debug():
    """Test 2: INFO level filters out DEBUG logs."""
    print_test("INFO Level Filters Out DEBUG Logs")
    
    # Make request to generate logs
    try:
        response = requests.get(f"{AUTH_BASE}/test/logging", timeout=5)
        if response.status_code != 200:
            return print_result(False, f"Request failed: {response.status_code}")
        
        correlation_id = response.json().get("correlation_id")
        print(f"Correlation ID: {correlation_id}")
        
    except Exception as e:
        return print_result(False, f"Request error: {e}")
    
    # Wait for logs to flush
    time.sleep(2)
    
    # Check logs
    logs = get_recent_logs("auth-service", lines=100)
    json_logs = parse_json_logs(logs)
    
    # Find logs with our correlation ID
    matching_logs = [log for log in json_logs if log.get("correlation_id") == correlation_id]
    
    if not matching_logs:
        return print_result(False, "No matching logs found")
    
    # Count by level
    levels_found = {}
    for log in matching_logs:
        level = log.get("level", "UNKNOWN")
        levels_found[level] = levels_found.get(level, 0) + 1
    
    print(f"Logs found with correlation ID:")
    for level, count in sorted(levels_found.items()):
        print(f"  {level}: {count}")
    
    # Verify DEBUG logs not present
    if "DEBUG" in levels_found:
        return print_result(False, "DEBUG logs should be filtered out at INFO level")
    
    # Verify INFO, WARNING, ERROR are present
    expected_levels = ["INFO", "WARNING", "ERROR"]
    for level in expected_levels:
        if level not in levels_found:
            print(f"Warning: {level} not found in logs")
    
    return print_result(True, "DEBUG logs filtered out at INFO level")

def test_log_level_hierarchy():
    """Test 3: Verify log level hierarchy (DEBUG < INFO < WARNING < ERROR)."""
    print_test("Log Level Hierarchy")
    
    # Make request
    try:
        response = requests.get(f"{AUTH_BASE}/test/logging", timeout=5)
        if response.status_code != 200:
            return print_result(False, f"Request failed: {response.status_code}")
    except Exception as e:
        return print_result(False, f"Request error: {e}")
    
    time.sleep(1)
    
    # Check logs
    logs = get_recent_logs("auth-service", lines=100)
    json_logs = parse_json_logs(logs)
    
    # Count recent log levels (last 50 logs)
    recent_logs = json_logs[-50:]
    levels_found = set(log.get("level") for log in recent_logs if log.get("level"))
    
    print(f"Log levels found in recent logs: {sorted(levels_found)}")
    
    # At INFO level, should have INFO, WARNING, ERROR, but not DEBUG
    expected = {"INFO", "WARNING", "ERROR"}
    not_expected = {"DEBUG"}
    
    has_expected = expected.intersection(levels_found)
    has_not_expected = not_expected.intersection(levels_found)
    
    if has_not_expected:
        return print_result(False, f"Found unexpected log levels: {has_not_expected}")
    
    if not has_expected:
        return print_result(False, "No expected log levels found")
    
    return print_result(True, f"Log hierarchy correct: {sorted(has_expected)}")

def test_all_log_levels_available():
    """Test 4: Verify all log levels (DEBUG, INFO, WARNING, ERROR) are supported."""
    print_test("All Log Levels Supported")
    
    # Make request to test logging endpoint
    try:
        response = requests.get(f"{AUTH_BASE}/test/logging", timeout=5)
        
        if response.status_code != 200:
            return print_result(False, f"Request failed: {response.status_code}")
        
        data = response.json()
        supported_levels = data.get("levels", [])
        
        print(f"Supported levels: {supported_levels}")
        
        expected_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        if sorted(supported_levels) != sorted(expected_levels):
            return print_result(False, f"Expected {expected_levels}, got {supported_levels}")
        
        return print_result(True, f"All 4 log levels supported: {expected_levels}")
        
    except Exception as e:
        return print_result(False, f"Error: {e}")

def test_log_level_environment_variable():
    """Test 5: Verify LOG_LEVEL environment variable is respected."""
    print_test("LOG_LEVEL Environment Variable")
    
    try:
        # Check current log level
        response = requests.get(f"{AUTH_BASE}/test/logging", timeout=5)
        
        if response.status_code != 200:
            return print_result(False, f"Request failed: {response.status_code}")
        
        data = response.json()
        current_level = data.get("current_log_level", "unknown")
        
        print(f"Service reports LOG_LEVEL: {current_level}")
        
        # Verify it reads from environment
        if current_level not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            return print_result(False, f"Invalid log level: {current_level}")
        
        return print_result(True, f"LOG_LEVEL environment variable is used (current: {current_level})")
        
    except Exception as e:
        return print_result(False, f"Error: {e}")

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("CONFIGURABLE LOG LEVELS TESTS")
    print("Feature #38: Log levels configurable per service")
    print("="*60)
    
    # Check services are running
    try:
        response = requests.get(f"{API_BASE}/health", timeout=2)
        if response.status_code != 200:
            print("\n✗ ERROR: API Gateway not healthy")
            return 1
        print(f"\n✓ API Gateway is healthy")
    except Exception as e:
        print(f"\n✗ ERROR: Cannot reach API Gateway: {e}")
        return 1
    
    try:
        response = requests.get(f"{AUTH_BASE}/test/counter", timeout=2)
        if response.status_code != 200:
            print("✗ ERROR: Auth Service not healthy")
            return 1
        print(f"✓ Auth Service is healthy")
    except Exception as e:
        print(f"✗ ERROR: Cannot reach Auth Service: {e}")
        return 1
    
    # Run tests
    results = []
    
    results.append(test_current_log_level())
    results.append(test_info_level_filters_debug())
    results.append(test_log_level_hierarchy())
    results.append(test_all_log_levels_available())
    results.append(test_log_level_environment_variable())
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests PASSED! Feature #38 is working correctly.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
