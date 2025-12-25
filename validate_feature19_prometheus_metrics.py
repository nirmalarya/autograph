#!/usr/bin/env python3
"""
Feature #19 Validation: Prometheus Metrics Endpoint
Validates that Prometheus-compatible metrics are exposed for monitoring
"""
import requests
import sys
from pathlib import Path
import re

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def check_mark(passed):
    return "✅" if passed else "❌"

# Test results
results = []

print_section("FEATURE #19: PROMETHEUS METRICS ENDPOINT VALIDATION")

# Step 1: Verify /metrics endpoint is accessible
print("\n[Step 1] Verify /metrics endpoint accessibility")
try:
    response = requests.get("http://localhost:8080/metrics", timeout=5)
    accessible = response.status_code == 200
    content_type = response.headers.get("content-type", "")

    print(f"  {check_mark(accessible)} Endpoint accessible (HTTP {response.status_code})")
    print(f"  Content-Type: {content_type}")
    print(f"  Response size: {len(response.text)} bytes")

    if accessible:
        metrics_text = response.text
        results.append(("Metrics endpoint accessible", True))
    else:
        print(f"  ❌ Endpoint returned {response.status_code}")
        results.append(("Metrics endpoint accessible", False))
        sys.exit(1)
except Exception as e:
    print(f"  ❌ Error accessing endpoint: {e}")
    results.append(("Metrics endpoint accessible", False))
    sys.exit(1)

# Step 2: Verify Prometheus format
print("\n[Step 2] Verify metrics in Prometheus format")

# Check for HELP and TYPE comments
has_help = re.search(r'^# HELP', metrics_text, re.MULTILINE) is not None
has_type = re.search(r'^# TYPE', metrics_text, re.MULTILINE) is not None

# Count metric types
counters = len(re.findall(r'# TYPE \w+ counter', metrics_text))
gauges = len(re.findall(r'# TYPE \w+ gauge', metrics_text))
histograms = len(re.findall(r'# TYPE \w+ histogram', metrics_text))
summaries = len(re.findall(r'# TYPE \w+ summary', metrics_text))

print(f"  {check_mark(has_help)} Has HELP comments")
print(f"  {check_mark(has_type)} Has TYPE declarations")
print(f"  Metric types found:")
print(f"    - Counters: {counters}")
print(f"    - Gauges: {gauges}")
print(f"    - Histograms: {histograms}")
print(f"    - Summaries: {summaries}")

prometheus_format_ok = has_help and has_type and (counters + gauges + histograms + summaries) > 0
results.append(("Prometheus format", prometheus_format_ok))

# Step 3: Verify request_count metric exists
print("\n[Step 3] Check request_count metric exists")
request_count_pattern = r'api_gateway_requests_total'
has_request_count = re.search(request_count_pattern, metrics_text) is not None

if has_request_count:
    # Find example metrics
    examples = re.findall(
        r'(api_gateway_requests_total\{[^}]+\}\s+[\d.]+)',
        metrics_text
    )
    print(f"  {check_mark(has_request_count)} api_gateway_requests_total metric found")
    print(f"  Examples ({len(examples)} total):")
    for example in examples[:3]:
        print(f"    {example}")
    if len(examples) > 3:
        print(f"    ... and {len(examples) - 3} more")
else:
    print(f"  ❌ api_gateway_requests_total metric not found")

results.append(("Request count metric", has_request_count))

# Step 4: Verify request_duration metric exists
print("\n[Step 4] Check request_duration metric exists")
duration_pattern = r'api_gateway_request_duration_seconds'
has_duration = re.search(duration_pattern, metrics_text) is not None

if has_duration:
    # Check for histogram buckets
    bucket_pattern = r'api_gateway_request_duration_seconds_bucket'
    has_buckets = re.search(bucket_pattern, metrics_text) is not None

    print(f"  {check_mark(has_duration)} api_gateway_request_duration_seconds metric found")
    print(f"  {check_mark(has_buckets)} Histogram buckets present")

    # Find bucket examples
    if has_buckets:
        bucket_examples = re.findall(
            r'(api_gateway_request_duration_seconds_bucket\{le="[^"]+".+?\}\s+[\d.]+)',
            metrics_text
        )
        print(f"  Bucket examples:")
        for example in bucket_examples[:3]:
            print(f"    {example}")
else:
    print(f"  ❌ api_gateway_request_duration_seconds metric not found")

results.append(("Request duration metric", has_duration))

# Step 5: Verify active_connections metric exists
print("\n[Step 5] Check active_connections metric exists")
connections_pattern = r'api_gateway_active_connections'
has_connections = re.search(connections_pattern, metrics_text) is not None

if has_connections:
    # Find current value
    match = re.search(
        r'api_gateway_active_connections\s+([\d.]+)',
        metrics_text
    )
    if match:
        value = match.group(1)
        print(f"  {check_mark(has_connections)} api_gateway_active_connections metric found")
        print(f"  Current value: {value}")
    else:
        print(f"  {check_mark(has_connections)} api_gateway_active_connections metric found")
else:
    print(f"  ❌ api_gateway_active_connections metric not found")

results.append(("Active connections metric", has_connections))

# Step 6: Verify circuit breaker metrics exist
print("\n[Step 6] Check circuit breaker metrics exist")
cb_state_pattern = r'api_gateway_circuit_breaker_state'
cb_failures_pattern = r'api_gateway_circuit_breaker_failures_total'

has_cb_state = re.search(cb_state_pattern, metrics_text) is not None
has_cb_failures = re.search(cb_failures_pattern, metrics_text) is not None

print(f"  {check_mark(has_cb_state)} api_gateway_circuit_breaker_state metric")
print(f"  {check_mark(has_cb_failures)} api_gateway_circuit_breaker_failures_total metric")

if has_cb_state:
    # Find service-specific metrics
    cb_examples = re.findall(
        r'(api_gateway_circuit_breaker_state\{service="[^"]+"\}\s+[\d.]+)',
        metrics_text
    )
    print(f"  Circuit breaker states ({len(cb_examples)} services):")
    for example in cb_examples[:5]:
        print(f"    {example}")

cb_metrics_ok = has_cb_state and has_cb_failures
results.append(("Circuit breaker metrics", cb_metrics_ok))

# Step 7: Verify rate limit metrics exist
print("\n[Step 7] Check rate limit metrics exist")
rate_limit_pattern = r'api_gateway_rate_limit_exceeded_total'
has_rate_limit = re.search(rate_limit_pattern, metrics_text) is not None

if has_rate_limit:
    print(f"  {check_mark(has_rate_limit)} api_gateway_rate_limit_exceeded_total metric found")

    # Find examples
    rl_examples = re.findall(
        r'(api_gateway_rate_limit_exceeded_total\{[^}]+\}\s+[\d.]+)',
        metrics_text
    )
    if rl_examples:
        print(f"  Examples:")
        for example in rl_examples[:3]:
            print(f"    {example}")
else:
    print(f"  ❌ api_gateway_rate_limit_exceeded_total metric not found")

results.append(("Rate limit metrics", has_rate_limit))

# Step 8: Verify resource monitoring metrics (memory, CPU)
print("\n[Step 8] Check resource monitoring metrics exist")
memory_pattern = r'api_gateway_memory_usage'
cpu_pattern = r'api_gateway_cpu_usage'

has_memory = re.search(memory_pattern, metrics_text) is not None
has_cpu = re.search(cpu_pattern, metrics_text) is not None

print(f"  {check_mark(has_memory)} Memory usage metrics")
print(f"  {check_mark(has_cpu)} CPU usage metrics")

if has_memory:
    # Find memory metrics
    memory_metrics = re.findall(
        r'(api_gateway_memory_[a-z_]+\s+[\d.]+)',
        metrics_text
    )
    print(f"  Memory metrics ({len(memory_metrics)}):")
    for metric in memory_metrics[:5]:
        print(f"    {metric}")

if has_cpu:
    # Find CPU metrics
    cpu_metrics = re.findall(
        r'(api_gateway_cpu_[a-z_]+\s+[\d.]+)',
        metrics_text
    )
    print(f"  CPU metrics ({len(cpu_metrics)}):")
    for metric in cpu_metrics[:5]:
        print(f"    {metric}")

resource_metrics_ok = has_memory and has_cpu
results.append(("Resource monitoring metrics", resource_metrics_ok))

# Step 9: Verify prometheus_client library usage in code
print("\n[Step 9] Verify prometheus_client library usage in code")
gateway_file = Path("services/api-gateway/src/main.py")
if gateway_file.exists():
    content = gateway_file.read_text()

    has_import = "from prometheus_client import" in content
    has_counter = "Counter(" in content
    has_histogram = "Histogram(" in content
    has_gauge = "Gauge(" in content
    has_registry = "CollectorRegistry()" in content
    has_generate = "generate_latest" in content

    print(f"  {check_mark(has_import)} prometheus_client imported")
    print(f"  {check_mark(has_counter)} Counter metrics defined")
    print(f"  {check_mark(has_histogram)} Histogram metrics defined")
    print(f"  {check_mark(has_gauge)} Gauge metrics defined")
    print(f"  {check_mark(has_registry)} CollectorRegistry created")
    print(f"  {check_mark(has_generate)} generate_latest() used")

    code_check_ok = all([
        has_import, has_counter, has_histogram,
        has_gauge, has_registry, has_generate
    ])
    results.append(("Prometheus client library", code_check_ok))
else:
    print(f"  ❌ API Gateway file not found")
    results.append(("Prometheus client library", False))

# Summary
print_section("VALIDATION SUMMARY")

all_passed = all(passed for _, passed in results)

for test_name, passed in results:
    print(f"  {check_mark(passed)} {test_name}")

# Count total metrics
total_metrics = len(re.findall(r'^[a-z_]+ ', metrics_text, re.MULTILINE))
print(f"\n  Total metrics exposed: {total_metrics}")

print("\n" + "=" * 80)
if all_passed:
    print("✅ FEATURE #19: PROMETHEUS METRICS ENDPOINT - FULLY IMPLEMENTED")
    print("\nPrometheus metrics are correctly exposed with:")
    print(f"  • /metrics endpoint accessible (HTTP 200)")
    print(f"  • Proper Prometheus format (HELP, TYPE comments)")
    print(f"  • {counters} counter metrics")
    print(f"  • {gauges} gauge metrics")
    print(f"  • {histograms} histogram metrics")
    print(f"  • Request count: api_gateway_requests_total")
    print(f"  • Request duration: api_gateway_request_duration_seconds (histogram)")
    print(f"  • Active connections: api_gateway_active_connections")
    print(f"  • Circuit breaker state and failures")
    print(f"  • Rate limit exceeded counts")
    print(f"  • Memory and CPU usage")
    print(f"\nTotal metrics: {total_metrics}")
    print("\nThese metrics can be scraped by Prometheus for monitoring and alerting.")
    sys.exit(0)
else:
    print("❌ SOME VALIDATIONS FAILED")
    sys.exit(1)

print("=" * 80 + "\n")
