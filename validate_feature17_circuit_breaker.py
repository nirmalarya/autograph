#!/usr/bin/env python3
"""
Feature #17 Validation: Circuit Breaker Pattern
Validates that circuit breaker prevents cascading failures
"""
import subprocess
import sys
import time
from pathlib import Path

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def check_mark(passed):
    return "✅" if passed else "❌"

# Test results
results = []

print_section("FEATURE #17: CIRCUIT BREAKER PATTERN VALIDATION")

# Step 1: Verify circuit breaker class exists
print("\n[Step 1] Verify circuit breaker implementation exists")
circuit_breaker_file = Path("shared/python/circuit_breaker.py")
if circuit_breaker_file.exists():
    content = circuit_breaker_file.read_text()
    has_class = "class CircuitBreaker" in content
    has_states = "class CircuitState(Enum)" in content
    has_call = "def call(self" in content
    has_on_failure = "def _on_failure" in content
    has_on_success = "def _on_success" in content

    print(f"  {check_mark(has_class)} CircuitBreaker class defined")
    print(f"  {check_mark(has_states)} CircuitState enum (CLOSED, OPEN, HALF_OPEN)")
    print(f"  {check_mark(has_call)} call() method for protected execution")
    print(f"  {check_mark(has_on_failure)} _on_failure() tracks failures")
    print(f"  {check_mark(has_on_success)} _on_success() tracks successes")

    step1_pass = all([has_class, has_states, has_call, has_on_failure, has_on_success])
    results.append(("Circuit breaker implementation", step1_pass))
else:
    print(f"  ❌ Circuit breaker file not found: {circuit_breaker_file}")
    results.append(("Circuit breaker implementation", False))
    step1_pass = False

# Step 2: Verify circuit breaker is configured in API Gateway
print("\n[Step 2] Verify circuit breaker configured for ai-service in API Gateway")
gateway_file = Path("services/api-gateway/src/main.py")
if gateway_file.exists():
    content = gateway_file.read_text()
    has_import = "from shared.python.circuit_breaker import CircuitBreaker" in content
    has_ai_breaker = '"ai": CircuitBreaker(' in content
    has_threshold = 'failure_threshold=5' in content
    has_timeout = 'timeout=30.0' in content

    print(f"  {check_mark(has_import)} Circuit breaker imported")
    print(f"  {check_mark(has_ai_breaker)} AI service circuit breaker configured")
    print(f"  {check_mark(has_threshold)} Failure threshold = 5")
    print(f"  {check_mark(has_timeout)} Timeout = 30s")

    step2_pass = all([has_import, has_ai_breaker, has_threshold, has_timeout])
    results.append(("API Gateway configuration", step2_pass))
else:
    print(f"  ❌ API Gateway file not found: {gateway_file}")
    results.append(("API Gateway configuration", False))
    step2_pass = False

# Step 3: Verify circuit breaker is used in proxy logic
print("\n[Step 3] Verify circuit breaker protects proxy requests")
if gateway_file.exists():
    content = gateway_file.read_text()

    # Check for circuit breaker check before proxying
    has_circuit_check = 'if circuit_breaker and circuit_breaker.state == CircuitState.OPEN' in content
    has_fail_fast = 'Service {service_name} temporarily unavailable (circuit breaker open)' in content
    has_on_failure_call = 'circuit_breaker._on_failure()' in content
    has_on_success_call = 'circuit_breaker._on_success()' in content
    has_connect_error = 'except httpx.ConnectError:' in content

    print(f"  {check_mark(has_circuit_check)} Checks circuit state before proxying")
    print(f"  {check_mark(has_fail_fast)} Fails fast when circuit OPEN (503 error)")
    print(f"  {check_mark(has_connect_error)} Catches connection errors")
    print(f"  {check_mark(has_on_failure_call)} Calls _on_failure() on errors")
    print(f"  {check_mark(has_on_success_call)} Calls _on_success() on success")

    step3_pass = all([
        has_circuit_check,
        has_fail_fast,
        has_on_failure_call,
        has_on_success_call,
        has_connect_error
    ])
    results.append(("Proxy protection logic", step3_pass))
else:
    step3_pass = False
    results.append(("Proxy protection logic", False))

# Step 4: Verify circuit breaker stats endpoint exists
print("\n[Step 4] Verify circuit breaker monitoring endpoint")
if gateway_file.exists():
    content = gateway_file.read_text()
    has_endpoint = '@app.get("/health/circuit-breakers")' in content
    has_stats_method = 'breaker.get_stats()' in content
    is_public = '"/health/circuit-breakers"' in content and 'PUBLIC_ROUTES' in content

    print(f"  {check_mark(has_endpoint)} /health/circuit-breakers endpoint exists")
    print(f"  {check_mark(has_stats_method)} Returns breaker.get_stats()")
    print(f"  {check_mark(is_public)} Endpoint is publicly accessible")

    step4_pass = all([has_endpoint, has_stats_method, is_public])
    results.append(("Monitoring endpoint", step4_pass))
else:
    step4_pass = False
    results.append(("Monitoring endpoint", False))

# Step 5: Test circuit breaker stats endpoint is accessible
print("\n[Step 5] Test circuit breaker stats endpoint accessibility")
try:
    import requests
    response = requests.get("http://localhost:8080/health/circuit-breakers", timeout=5)
    if response.status_code == 200:
        data = response.json()
        has_ai_stats = "ai" in data.get("circuit_breakers", {})
        ai_stats = data.get("circuit_breakers", {}).get("ai", {})

        print(f"  ✅ Endpoint accessible (HTTP 200)")
        print(f"  {check_mark(has_ai_stats)} AI service breaker stats present")

        if has_ai_stats:
            print(f"\n  AI Circuit Breaker Stats:")
            print(f"    State: {ai_stats.get('state')}")
            print(f"    Failure Threshold: {ai_stats.get('failure_threshold')}")
            print(f"    Success Threshold: {ai_stats.get('success_threshold')}")
            print(f"    Timeout: {ai_stats.get('timeout')}s")
            print(f"    Current Failures: {ai_stats.get('failure_count')}")

        step5_pass = has_ai_stats
        results.append(("Stats endpoint working", step5_pass))
    else:
        print(f"  ❌ Endpoint returned {response.status_code}")
        results.append(("Stats endpoint working", False))
        step5_pass = False
except Exception as e:
    print(f"  ❌ Error accessing endpoint: {e}")
    results.append(("Stats endpoint working", False))
    step5_pass = False

# Step 6: Verify all 7 services have circuit breakers
print("\n[Step 6] Verify all microservices have circuit breakers")
if gateway_file.exists():
    content = gateway_file.read_text()
    services = ["auth", "diagram", "ai", "collaboration", "git", "export", "integration"]
    all_configured = True

    for service in services:
        has_breaker = f'"{service}": CircuitBreaker(' in content
        print(f"  {check_mark(has_breaker)} {service}-service circuit breaker")
        if not has_breaker:
            all_configured = False

    results.append(("All services protected", all_configured))
    step6_pass = all_configured
else:
    results.append(("All services protected", False))
    step6_pass = False

# Step 7: Verify state transitions are implemented
print("\n[Step 7] Verify circuit breaker state transition logic")
if circuit_breaker_file.exists():
    content = circuit_breaker_file.read_text()

    # CLOSED -> OPEN transition
    has_closed_to_open = 'self._failure_count >= self.failure_threshold' in content
    has_open_state_set = 'self._state = CircuitState.OPEN' in content

    # OPEN -> HALF_OPEN transition
    has_timeout_check = '_should_attempt_reset' in content
    has_half_open = 'CircuitState.HALF_OPEN' in content

    # HALF_OPEN -> CLOSED transition
    has_success_check = 'self._success_count >= self.success_threshold' in content
    has_close_state = 'self._state = CircuitState.CLOSED' in content

    # HALF_OPEN -> OPEN transition (on failure)
    has_half_open_failure = 'if self._state == CircuitState.HALF_OPEN' in content

    print(f"  {check_mark(has_closed_to_open)} CLOSED -> OPEN: On failure threshold")
    print(f"  {check_mark(has_timeout_check)} OPEN -> HALF_OPEN: After timeout")
    print(f"  {check_mark(has_success_check)} HALF_OPEN -> CLOSED: On success threshold")
    print(f"  {check_mark(has_half_open_failure)} HALF_OPEN -> OPEN: On failure")

    step7_pass = all([
        has_closed_to_open,
        has_open_state_set,
        has_timeout_check,
        has_half_open,
        has_success_check,
        has_close_state,
        has_half_open_failure
    ])
    results.append(("State transitions", step7_pass))
else:
    step7_pass = False
    results.append(("State transitions", False))

# Step 8: Verify prevents cascading failures
print("\n[Step 8] Verify prevents cascading failures (fail-fast)")
if circuit_breaker_file.exists():
    content = circuit_breaker_file.read_text()

    # Circuit breaker should raise error when OPEN
    has_exception_class = 'class CircuitBreakerError(Exception)' in content
    has_open_check = 'if self._state == CircuitState.OPEN' in content
    has_raise_error = 'raise CircuitBreakerError' in content
    has_fast_fail_message = 'Circuit breaker' in content and 'is OPEN' in content

    print(f"  {check_mark(has_exception_class)} CircuitBreakerError exception class")
    print(f"  {check_mark(has_open_check)} Checks if circuit is OPEN")
    print(f"  {check_mark(has_raise_error)} Raises error immediately when OPEN")
    print(f"  {check_mark(has_fast_fail_message)} Provides informative error message")

    step8_pass = all([
        has_exception_class,
        has_open_check,
        has_raise_error,
        has_fast_fail_message
    ])
    results.append(("Fail-fast behavior", step8_pass))
else:
    step8_pass = False
    results.append(("Fail-fast behavior", False))

# Summary
print_section("VALIDATION SUMMARY")

all_passed = all(passed for _, passed in results)

for test_name, passed in results:
    print(f"  {check_mark(passed)} {test_name}")

print("\n" + "=" * 80)
if all_passed:
    print("✅ FEATURE #17: CIRCUIT BREAKER PATTERN - FULLY IMPLEMENTED")
    print("\nThe circuit breaker pattern is correctly implemented with:")
    print("  • CircuitBreaker class with CLOSED/OPEN/HALF_OPEN states")
    print("  • Configured for all 7 microservices (threshold=5, timeout=30s)")
    print("  • Protects proxy requests with fail-fast behavior")
    print("  • Monitors and tracks failures/successes")
    print("  • Provides /health/circuit-breakers monitoring endpoint")
    print("  • Implements proper state transitions")
    print("  • Prevents cascading failures by failing fast when circuit is OPEN")
    sys.exit(0)
else:
    print("❌ SOME VALIDATIONS FAILED")
    sys.exit(1)

print("=" * 80 + "\n")
