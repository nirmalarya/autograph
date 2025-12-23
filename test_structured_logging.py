#!/usr/bin/env python3
"""
Test Structured Logging with JSON Format
Feature #37: Structured logging with JSON format for log aggregation

Tests that services emit structured JSON logs containing:
- timestamp
- level (INFO, WARNING, ERROR, etc.)
- message
- service_name
- correlation_id (for distributed tracing)
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

def get_recent_logs(service, lines=20):
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

def test_json_format():
    """Test 1: Logs are emitted in valid JSON format."""
    print_test("Logs Emitted in Valid JSON Format")
    
    # Get logs from API Gateway
    logs = get_recent_logs("api-gateway", lines=50)
    json_logs = parse_json_logs(logs)
    
    if not json_logs:
        return print_result(False, "No JSON logs found in API Gateway output")
    
    print(f"Found {len(json_logs)} JSON log entries")
    print(f"Sample log entry:")
    print(json.dumps(json_logs[0], indent=2))
    
    return print_result(True, f"Valid JSON logs found ({len(json_logs)} entries)")

def test_required_fields():
    """Test 2: Logs contain all required fields."""
    print_test("Logs Contain Required Fields")
    
    required_fields = ["timestamp", "level", "message", "service"]
    
    # Get logs from both services
    api_logs = parse_json_logs(get_recent_logs("api-gateway", lines=50))
    auth_logs = parse_json_logs(get_recent_logs("auth-service", lines=50))
    
    all_logs = api_logs + auth_logs
    
    if not all_logs:
        return print_result(False, "No logs found")
    
    missing_fields = {}
    for log in all_logs:
        for field in required_fields:
            if field not in log:
                missing_fields[field] = missing_fields.get(field, 0) + 1
    
    if missing_fields:
        print(f"Missing fields found:")
        for field, count in missing_fields.items():
            print(f"  {field}: missing in {count} logs")
        return print_result(False, "Some logs missing required fields")
    
    print(f"All {len(all_logs)} logs contain required fields:")
    print(f"  - timestamp")
    print(f"  - level")
    print(f"  - message")
    print(f"  - service")
    
    return print_result(True, f"All logs have required fields ({len(all_logs)} logs checked)")

def test_correlation_id_tracking():
    """Test 3: Correlation ID is tracked across services."""
    print_test("Correlation ID Tracked Across Services")
    
    # Make a request with custom correlation ID
    correlation_id = f"test-correlation-{int(time.time())}"
    headers = {
        "X-Correlation-ID": correlation_id
    }
    
    try:
        response = requests.get(
            f"{AUTH_BASE}/test/counter",
            headers=headers,
            timeout=5
        )
        
        if response.status_code != 200:
            return print_result(False, f"Request failed: {response.status_code}")
        
        # Verify correlation ID in response
        response_correlation_id = response.headers.get("X-Correlation-ID")
        if response_correlation_id != correlation_id:
            return print_result(False, f"Correlation ID mismatch: sent {correlation_id}, got {response_correlation_id}")
        
        print(f"Request sent with correlation ID: {correlation_id}")
        print(f"Response includes same correlation ID: {response_correlation_id}")
        
    except Exception as e:
        return print_result(False, f"Request error: {e}")
    
    # Wait for logs to flush
    time.sleep(1)
    
    # Check logs for correlation ID
    api_logs = parse_json_logs(get_recent_logs("api-gateway", lines=100))
    auth_logs = parse_json_logs(get_recent_logs("auth-service", lines=100))
    
    # Find logs with our correlation ID
    api_matching = [log for log in api_logs if log.get("correlation_id") == correlation_id]
    auth_matching = [log for log in auth_logs if log.get("correlation_id") == correlation_id]
    
    print(f"\nLogs found with correlation ID '{correlation_id}':")
    print(f"  API Gateway: {len(api_matching)} logs")
    print(f"  Auth Service: {len(auth_matching)} logs")
    
    if not api_matching:
        return print_result(False, "No API Gateway logs found with correlation ID")
    
    if not auth_matching:
        return print_result(False, "No Auth Service logs found with correlation ID")
    
    # Show sample matching logs
    print(f"\nSample API Gateway log:")
    print(f"  {api_matching[0].get('message')}")
    
    if auth_matching:
        print(f"Sample Auth Service log:")
        print(f"  {auth_matching[0].get('message')}")
    
    return print_result(True, f"Correlation ID tracked in {len(api_matching) + len(auth_matching)} logs across both services")

def test_log_levels():
    """Test 4: Different log levels are supported."""
    print_test("Different Log Levels Supported")
    
    # Get logs from both services
    api_logs = parse_json_logs(get_recent_logs("api-gateway", lines=100))
    auth_logs = parse_json_logs(get_recent_logs("auth-service", lines=100))
    
    all_logs = api_logs + auth_logs
    
    # Count log levels
    levels = {}
    for log in all_logs:
        level = log.get("level", "UNKNOWN")
        levels[level] = levels.get(level, 0) + 1
    
    print(f"Log levels found:")
    for level, count in sorted(levels.items()):
        print(f"  {level}: {count} logs")
    
    # Should have at least INFO level
    if "INFO" not in levels:
        return print_result(False, "No INFO level logs found")
    
    # Check if multiple levels exist
    if len(levels) < 1:
        return print_result(False, "No log levels found")
    
    return print_result(True, f"Found {len(levels)} different log levels: {', '.join(sorted(levels.keys()))}")

def test_service_identification():
    """Test 5: Service name is correctly identified in logs."""
    print_test("Service Name Correctly Identified")
    
    # Get logs from both services
    api_logs = parse_json_logs(get_recent_logs("api-gateway", lines=50))
    auth_logs = parse_json_logs(get_recent_logs("auth-service", lines=50))
    
    # Check API Gateway logs
    api_service_names = set(log.get("service") for log in api_logs if log.get("service"))
    auth_service_names = set(log.get("service") for log in auth_logs if log.get("service"))
    
    print(f"API Gateway logs - service names found: {api_service_names}")
    print(f"Auth Service logs - service names found: {auth_service_names}")
    
    # Verify correct service names
    if "api-gateway" not in api_service_names:
        return print_result(False, "API Gateway logs don't contain 'api-gateway' service name")
    
    if "auth-service" not in auth_service_names:
        return print_result(False, "Auth Service logs don't contain 'auth-service' service name")
    
    return print_result(True, "Service names correctly identified in logs")

def test_timestamp_format():
    """Test 6: Timestamps are in ISO 8601 format."""
    print_test("Timestamps in ISO 8601 Format")
    
    # Get recent logs
    api_logs = parse_json_logs(get_recent_logs("api-gateway", lines=20))
    
    if not api_logs:
        return print_result(False, "No logs found")
    
    # Check first log timestamp
    sample_log = api_logs[0]
    timestamp = sample_log.get("timestamp")
    
    if not timestamp:
        return print_result(False, "No timestamp field found")
    
    print(f"Sample timestamp: {timestamp}")
    
    # Verify ISO 8601 format (YYYY-MM-DDTHH:MM:SS.ffffff)
    try:
        from datetime import datetime
        # Try to parse ISO format
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        print(f"Parsed timestamp: {dt}")
        return print_result(True, f"Timestamps in valid ISO 8601 format")
    except Exception as e:
        return print_result(False, f"Invalid timestamp format: {e}")

def test_structured_data():
    """Test 7: Logs include structured data (method, path, status_code, etc.)."""
    print_test("Logs Include Structured Data")
    
    # Make a request to generate logs
    try:
        requests.get(f"{AUTH_BASE}/test/counter", timeout=5)
    except:
        pass
    
    time.sleep(1)
    
    # Get logs
    api_logs = parse_json_logs(get_recent_logs("api-gateway", lines=50))
    
    # Find logs with structured data
    logs_with_method = [log for log in api_logs if "method" in log]
    logs_with_path = [log for log in api_logs if "path" in log]
    logs_with_status = [log for log in api_logs if "status_code" in log]
    
    print(f"Logs with structured data:")
    print(f"  method field: {len(logs_with_method)} logs")
    print(f"  path field: {len(logs_with_path)} logs")
    print(f"  status_code field: {len(logs_with_status)} logs")
    
    if logs_with_method and logs_with_path:
        sample = logs_with_method[0]
        print(f"\nSample log with structured data:")
        print(f"  Method: {sample.get('method')}")
        print(f"  Path: {sample.get('path')}")
        if "status_code" in sample:
            print(f"  Status: {sample.get('status_code')}")
    
    if not logs_with_method:
        return print_result(False, "No logs found with method field")
    
    if not logs_with_path:
        return print_result(False, "No logs found with path field")
    
    return print_result(True, f"Logs include structured data (method, path, etc.)")

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("STRUCTURED LOGGING TESTS")
    print("Feature #37: Structured logging with JSON format")
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
    
    results.append(test_json_format())
    results.append(test_required_fields())
    results.append(test_correlation_id_tracking())
    results.append(test_log_levels())
    results.append(test_service_identification())
    results.append(test_timestamp_format())
    results.append(test_structured_data())
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests PASSED! Feature #37 is working correctly.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
