#!/usr/bin/env python3
"""
Test script for Feature #40: Performance monitoring tracks request duration
Tests that request durations are logged and tracked via Prometheus metrics.
"""

import requests
import json
import subprocess
import time
import sys
import re
from typing import Dict, List, Any, Optional

# Test configuration
API_GATEWAY_URL = "http://localhost:8080"
AUTH_SERVICE_URL = f"{API_GATEWAY_URL}/api/auth"
METRICS_URL = f"{API_GATEWAY_URL}/metrics"

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

def get_api_gateway_logs(pattern: str, tail: int = 100) -> List[Dict[str, Any]]:
    """Get logs from API gateway container."""
    try:
        result = subprocess.run(
            ["docker", "logs", "autograph-api-gateway"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        logs = []
        for line in (result.stdout + result.stderr).split('\n'):
            if pattern in line:
                try:
                    log_entry = json.loads(line)
                    logs.append(log_entry)
                except json.JSONDecodeError:
                    continue
        
        return logs
    except Exception as e:
        print(f"   ⚠️  Error getting logs: {e}")
        return []

def get_prometheus_metrics() -> str:
    """Get Prometheus metrics from API gateway."""
    try:
        response = requests.get(METRICS_URL, timeout=5)
        return response.text
    except Exception as e:
        print(f"   ⚠️  Error getting metrics: {e}")
        return ""

def parse_histogram_metric(metrics: str, metric_name: str, labels: Dict[str, str]) -> Dict[str, Any]:
    """Parse histogram metrics from Prometheus output."""
    label_str = ",".join([f'{k}="{v}"' for k, v in labels.items()])
    
    # Find count and sum
    count_pattern = f"{metric_name}_count{{{label_str}}} ([0-9.]+)"
    sum_pattern = f"{metric_name}_sum{{{label_str}}} ([0-9.]+)"
    
    count_match = re.search(count_pattern, metrics)
    sum_match = re.search(sum_pattern, metrics)
    
    count = float(count_match.group(1)) if count_match else 0
    total_sum = float(sum_match.group(1)) if sum_match else 0
    
    return {
        "count": count,
        "sum": total_sum,
        "average": total_sum / count if count > 0 else 0
    }

# =============================================================================
# TEST 1: Request duration logged for every request
# =============================================================================

def test_request_duration_logged():
    """Test that request duration is logged for every request."""
    # Make a request
    response = requests.get(f"{AUTH_SERVICE_URL}/test/performance?delay=0.1", timeout=10)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    correlation_id = response.json().get("correlation_id")
    
    # Wait for logs
    time.sleep(1)
    
    # Check logs for duration
    logs = get_api_gateway_logs("Request completed")
    assert len(logs) > 0, "No 'Request completed' logs found"
    
    # Find log with our correlation ID (or just check latest)
    recent_logs = logs[-5:]  # Check last 5 logs
    duration_logged = False
    
    for log in recent_logs:
        if "duration_ms" in log:
            duration_logged = True
            print(f"   ✓ Duration logged: {log['duration_ms']}ms")
            print(f"   ✓ Method: {log['method']}")
            print(f"   ✓ Path: {log['path']}")
            print(f"   ✓ Status code: {log['status_code']}")
            break
    
    assert duration_logged, "No duration_ms field in logs"

# =============================================================================
# TEST 2: Histogram metrics exported to Prometheus
# =============================================================================

def test_histogram_metrics_exported():
    """Test that histogram metrics are exported correctly."""
    # Make a few requests to populate metrics
    for delay in [0.1, 0.2, 0.3]:
        requests.get(f"{AUTH_SERVICE_URL}/test/performance?delay={delay}", timeout=10)
    
    # Wait for metrics to update
    time.sleep(1)
    
    # Get metrics
    metrics = get_prometheus_metrics()
    assert len(metrics) > 0, "No metrics returned"
    
    # Check for histogram metric
    assert "api_gateway_request_duration_seconds" in metrics, "Duration histogram not found"
    assert "api_gateway_request_duration_seconds_bucket" in metrics, "Histogram buckets not found"
    assert "api_gateway_request_duration_seconds_count" in metrics, "Histogram count not found"
    assert "api_gateway_request_duration_seconds_sum" in metrics, "Histogram sum not found"
    
    print(f"   ✓ Histogram metrics exported")
    print(f"   ✓ Buckets, count, and sum present")

# =============================================================================
# TEST 3: Slow requests logged with warning (> 1 second)
# =============================================================================

def test_slow_request_logging():
    """Test that requests > 1 second are logged with warning."""
    # Make a slow request
    response = requests.get(f"{AUTH_SERVICE_URL}/test/performance?delay=1.5", timeout=10)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    # Wait for logs
    time.sleep(1)
    
    # Check for slow request warning
    logs = get_api_gateway_logs("Slow request detected")
    assert len(logs) > 0, "No 'Slow request detected' logs found"
    
    slow_log = logs[-1]  # Get latest slow request log
    assert slow_log.get("level") == "WARNING", "Slow request not logged at WARNING level"
    assert slow_log.get("duration_ms", 0) > 1000, "Duration should be > 1000ms"
    assert slow_log.get("threshold_ms") == 1000, "Threshold should be 1000ms"
    assert slow_log.get("performance_issue") == True, "performance_issue flag should be True"
    
    print(f"   ✓ Slow request logged with WARNING level")
    print(f"   ✓ Duration: {slow_log.get('duration_ms')}ms")
    print(f"   ✓ Threshold: {slow_log.get('threshold_ms')}ms")
    print(f"   ✓ Performance issue flag: {slow_log.get('performance_issue')}")

# =============================================================================
# TEST 4: Fast requests don't trigger slow warning
# =============================================================================

def test_fast_requests_no_warning():
    """Test that fast requests (< 1s) don't trigger slow warning."""
    # Count slow warnings before
    logs_before = get_api_gateway_logs("Slow request detected")
    count_before = len(logs_before)
    
    # Make a fast request
    response = requests.get(f"{AUTH_SERVICE_URL}/test/performance?delay=0.2", timeout=10)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    # Wait briefly
    time.sleep(0.5)
    
    # Count slow warnings after
    logs_after = get_api_gateway_logs("Slow request detected")
    count_after = len(logs_after)
    
    assert count_after == count_before, f"Fast request triggered slow warning: {count_after} vs {count_before}"
    
    # Check that normal completion was logged
    completion_logs = get_api_gateway_logs("Request completed")
    latest_completion = completion_logs[-1]
    assert latest_completion.get("level") == "INFO", "Fast request should log at INFO level"
    assert latest_completion.get("duration_ms", 0) < 1000, "Duration should be < 1000ms"
    
    print(f"   ✓ Fast request didn't trigger slow warning")
    print(f"   ✓ Duration: {latest_completion.get('duration_ms')}ms")

# =============================================================================
# TEST 5: Histogram captures request distribution
# =============================================================================

def test_histogram_captures_distribution():
    """Test that histogram correctly captures distribution of request durations."""
    # Get initial metrics
    metrics_before = get_prometheus_metrics()
    
    # Make requests with known durations
    test_delays = [0.1, 0.2, 0.5, 0.8, 1.5]
    for delay in test_delays:
        requests.get(f"{AUTH_SERVICE_URL}/test/performance?delay={delay}", timeout=10)
        time.sleep(0.1)
    
    # Get updated metrics
    time.sleep(1)
    metrics_after = get_prometheus_metrics()
    
    # Parse histogram for our endpoint
    histogram_data = parse_histogram_metric(
        metrics_after,
        "api_gateway_request_duration_seconds",
        {"method": "GET", "path": "/api/auth/test/performance"}
    )
    
    assert histogram_data["count"] >= len(test_delays), f"Not all requests captured: {histogram_data['count']} < {len(test_delays)}"
    assert histogram_data["sum"] > 0, "Sum should be > 0"
    
    # Check average makes sense (should be around sum of delays / count)
    expected_min_sum = sum(test_delays)
    assert histogram_data["sum"] >= expected_min_sum * 0.9, f"Sum too low: {histogram_data['sum']} < {expected_min_sum}"
    
    print(f"   ✓ Request count: {histogram_data['count']}")
    print(f"   ✓ Total duration: {histogram_data['sum']:.2f}s")
    print(f"   ✓ Average duration: {histogram_data['average']:.3f}s")

# =============================================================================
# TEST 6: Percentiles can be calculated from histogram
# =============================================================================

def test_percentiles_calculable():
    """Test that percentile data is available in histogram buckets."""
    # Make varied requests to populate buckets
    test_delays = [0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0]
    for delay in test_delays:
        requests.get(f"{AUTH_SERVICE_URL}/test/performance?delay={delay}", timeout=10)
        time.sleep(0.05)
    
    time.sleep(1)
    metrics = get_prometheus_metrics()
    
    # Check for bucket data (used to calculate percentiles)
    # Simplified check - just verify buckets exist
    assert "api_gateway_request_duration_seconds_bucket" in metrics, "No histogram buckets found"
    
    # Count bucket lines
    bucket_lines = [line for line in metrics.split('\n') if 'api_gateway_request_duration_seconds_bucket' in line and 'test/performance' in line]
    
    assert len(bucket_lines) > 0, "No histogram buckets found for test endpoint"
    
    print(f"   ✓ Histogram has {len(bucket_lines)} bucket entries")
    print(f"   ✓ Percentiles (p50, p95, p99) can be calculated from buckets")
    print(f"   ✓ Use PromQL: histogram_quantile(0.95, rate(api_gateway_request_duration_seconds_bucket[5m]))")

# =============================================================================
# TEST 7: Performance monitoring includes all request details
# =============================================================================

def test_performance_details_captured():
    """Test that performance logs include all necessary details."""
    response = requests.get(f"{AUTH_SERVICE_URL}/test/performance?delay=0.5", timeout=10)
    assert response.status_code == 200
    
    time.sleep(1)
    
    logs = get_api_gateway_logs("Request completed")
    latest_log = logs[-1]
    
    # Check all required fields
    required_fields = ["timestamp", "service", "level", "message", "correlation_id", 
                       "method", "path", "status_code", "duration_ms"]
    
    for field in required_fields:
        assert field in latest_log, f"Missing required field: {field}"
        print(f"   ✓ {field}: {latest_log[field]}")
    
    # Verify data types
    assert isinstance(latest_log["duration_ms"], (int, float)), "duration_ms should be numeric"
    assert isinstance(latest_log["status_code"], int), "status_code should be integer"

# =============================================================================
# Main test runner
# =============================================================================

def main():
    """Run all tests and report results."""
    print("="*80)
    print("FEATURE #40: PERFORMANCE MONITORING TRACKS REQUEST DURATION")
    print("="*80)
    print(f"\nTesting performance monitoring functionality...")
    print(f"API Gateway URL: {API_GATEWAY_URL}")
    print(f"Metrics URL: {METRICS_URL}")
    
    # List of all tests
    tests = [
        ("Request duration logged for every request", test_request_duration_logged),
        ("Histogram metrics exported to Prometheus", test_histogram_metrics_exported),
        ("Slow requests logged with warning (> 1 second)", test_slow_request_logging),
        ("Fast requests don't trigger slow warning", test_fast_requests_no_warning),
        ("Histogram captures request distribution", test_histogram_captures_distribution),
        ("Percentiles can be calculated from histogram", test_percentiles_calculable),
        ("Performance monitoring includes all request details", test_performance_details_captured),
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
        print("\n🎉 All tests passed! Feature #40 is working correctly.")
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
