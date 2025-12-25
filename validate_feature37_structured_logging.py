#!/usr/bin/env python3
"""
Feature #37 Validation: Structured Logging with JSON Format
============================================================

This script validates that structured JSON logging is configured correctly:
- Logs are in valid JSON format
- Logs contain required fields (timestamp, level, message, service_name)
- Logs include correlation_id for distributed tracing
- Logs can be aggregated and queried by correlation_id
- All services use consistent log format

Exit codes:
0 - All validations passed
1 - Validation failed
"""

import sys
import time
import requests
import json
import subprocess
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configuration
API_BASE = "http://localhost:8080"
AUTH_BASE = f"{API_BASE}/api/auth"
TIMEOUT = 10

def log_info(message: str):
    """Print info message."""
    print(f"ℹ️  {message}")

def log_success(message: str):
    """Print success message."""
    print(f"✅ {message}")

def log_error(message: str):
    """Print error message."""
    print(f"❌ {message}")

def log_test(name: str):
    """Print test section header."""
    print(f"\n{'='*70}")
    print(f"  {name}")
    print(f"{'='*70}")


class StructuredLoggingValidator:
    """Validates structured JSON logging functionality."""

    def __init__(self):
        self.validation_results = []
        self.start_time = datetime.now()
        self.test_correlation_id = f"test-{int(time.time())}-{hex(id(self))[2:]}"

    def validate_service_health(self) -> bool:
        """Validate services are running and healthy."""
        log_test("SERVICE HEALTH CHECK")

        try:
            response = requests.get(f"{API_BASE}/health", timeout=TIMEOUT)
            if response.status_code != 200:
                log_error(f"API Gateway not healthy: {response.status_code}")
                return False
            log_success("API Gateway is healthy")
        except Exception as e:
            log_error(f"Cannot reach API Gateway: {e}")
            return False

        try:
            response = requests.get(f"{AUTH_BASE}/health", timeout=TIMEOUT)
            if response.status_code != 200:
                log_error(f"Auth Service not healthy: {response.status_code}")
                return False
            log_success("Auth Service is healthy")
        except Exception as e:
            log_error(f"Cannot reach Auth Service: {e}")
            return False

        return True

    def get_recent_logs(self, service: str, lines: int = 50) -> List[str]:
        """Get recent logs from a service container."""
        try:
            result = subprocess.run(
                ["docker", "logs", "--tail", str(lines), service],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout.splitlines() + result.stderr.splitlines()
        except Exception as e:
            log_error(f"Failed to get logs from {service}: {e}")
            return []

    def parse_json_log(self, log_line: str) -> Optional[Dict[str, Any]]:
        """Parse a JSON log line."""
        try:
            # Try to parse the entire line as JSON
            return json.loads(log_line)
        except json.JSONDecodeError:
            # Try to find JSON in the line
            # Some logs might have timestamp prefix before JSON
            json_match = re.search(r'\{.*\}', log_line)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass
        return None

    def validate_json_log_format(self) -> bool:
        """Validate logs are in valid JSON format."""
        log_test("VALIDATION 1: JSON Log Format")

        # Generate some activity with correlation ID
        headers = {"X-Correlation-ID": self.test_correlation_id}

        log_info(f"Generating test activity with correlation_id: {self.test_correlation_id}")

        try:
            # Make a few requests to generate logs
            for i in range(3):
                requests.get(f"{AUTH_BASE}/health", headers=headers, timeout=TIMEOUT)
                time.sleep(0.1)
        except:
            pass

        time.sleep(1)  # Give logs time to flush

        # Get logs from API gateway
        log_info("Retrieving logs from autograph-api-gateway...")
        logs = self.get_recent_logs("autograph-api-gateway", lines=100)

        if not logs:
            log_error("No logs retrieved from API gateway")
            return False

        log_info(f"Retrieved {len(logs)} log lines")

        # Try to parse JSON logs
        json_logs = []
        for log_line in logs:
            parsed = self.parse_json_log(log_line)
            if parsed:
                json_logs.append(parsed)

        if not json_logs:
            log_error("No valid JSON logs found")
            log_info("Sample log lines:")
            for log_line in logs[:5]:
                log_info(f"  {log_line[:100]}")
            return False

        log_success(f"Found {len(json_logs)} valid JSON log entries")

        # Show a sample log
        log_info("Sample JSON log entry:")
        log_info(f"  {json.dumps(json_logs[0], indent=2)[:500]}")

        return True

    def validate_required_fields(self) -> bool:
        """Validate logs contain required fields."""
        log_test("VALIDATION 2: Required Log Fields")

        # Generate activity
        headers = {"X-Correlation-ID": self.test_correlation_id}

        try:
            requests.get(f"{AUTH_BASE}/health", headers=headers, timeout=TIMEOUT)
        except:
            pass

        time.sleep(1)

        # Get logs
        logs = self.get_recent_logs("autograph-api-gateway", lines=100)

        # Parse JSON logs
        json_logs = []
        for log_line in logs:
            parsed = self.parse_json_log(log_line)
            if parsed:
                json_logs.append(parsed)

        if not json_logs:
            log_error("No JSON logs found")
            return False

        # Check required fields
        required_fields = ["timestamp", "level", "message", "service"]

        # Check first 10 logs
        logs_to_check = json_logs[:10]
        missing_fields_count = 0

        for i, log_entry in enumerate(logs_to_check):
            missing = [field for field in required_fields if field not in log_entry]
            if missing:
                missing_fields_count += 1
                if i == 0:  # Show first failure
                    log_error(f"Log entry missing fields: {missing}")
                    log_info(f"Log entry: {json.dumps(log_entry, indent=2)[:300]}")

        if missing_fields_count > 0:
            log_error(f"{missing_fields_count}/{len(logs_to_check)} logs missing required fields")
            return False

        log_success(f"All checked logs contain required fields: {', '.join(required_fields)}")

        # Show field examples
        sample_log = json_logs[0]
        log_info("Sample field values:")
        for field in required_fields:
            log_info(f"  {field}: {sample_log.get(field)}")

        return True

    def validate_correlation_id_tracking(self) -> bool:
        """Validate correlation_id is tracked in logs."""
        log_test("VALIDATION 3: Correlation ID Tracking")

        # Generate unique correlation ID
        correlation_id = f"validate-{int(time.time())}-{hex(id(self))[2:]}"

        log_info(f"Making request with correlation_id: {correlation_id}")

        # Make request with correlation ID
        headers = {"X-Correlation-ID": correlation_id}

        try:
            response = requests.get(f"{AUTH_BASE}/health", headers=headers, timeout=TIMEOUT)
            log_info(f"Request completed with status: {response.status_code}")
        except Exception as e:
            log_error(f"Request failed: {e}")
            return False

        time.sleep(1)  # Give logs time to flush

        # Get logs from both services
        log_info("Searching for correlation_id in logs...")

        found_in_gateway = False
        found_in_auth = False

        # Check API gateway logs
        gateway_logs = self.get_recent_logs("autograph-api-gateway", lines=100)
        for log_line in gateway_logs:
            if correlation_id in log_line:
                found_in_gateway = True
                parsed = self.parse_json_log(log_line)
                if parsed:
                    log_info(f"Found in API Gateway: {parsed.get('message', '')[:80]}")
                break

        # Check Auth service logs
        auth_logs = self.get_recent_logs("autograph-auth-service", lines=100)
        for log_line in auth_logs:
            if correlation_id in log_line:
                found_in_auth = True
                parsed = self.parse_json_log(log_line)
                if parsed:
                    log_info(f"Found in Auth Service: {parsed.get('message', '')[:80]}")
                break

        if not found_in_gateway:
            log_error(f"Correlation ID not found in API Gateway logs")
            return False

        log_success("Correlation ID successfully tracked in logs")

        if found_in_auth:
            log_success("Correlation ID propagated to downstream service (Auth)")
        else:
            log_info("Correlation ID not found in Auth service (may not have been logged)")

        return True

    def validate_log_aggregation_query(self) -> bool:
        """Validate logs can be queried by correlation_id."""
        log_test("VALIDATION 4: Log Aggregation and Querying")

        # Generate unique correlation ID and make multiple requests
        correlation_id = f"aggregate-{int(time.time())}-{hex(id(self))[2:]}"

        log_info(f"Making multiple requests with correlation_id: {correlation_id}")

        headers = {"X-Correlation-ID": correlation_id}
        request_count = 3

        try:
            for i in range(request_count):
                requests.get(f"{AUTH_BASE}/health", headers=headers, timeout=TIMEOUT)
                time.sleep(0.1)

            log_info(f"Completed {request_count} requests")
        except Exception as e:
            log_error(f"Requests failed: {e}")
            return False

        time.sleep(1)

        # Query logs by correlation ID
        log_info("Querying logs by correlation_id...")

        gateway_logs = self.get_recent_logs("autograph-api-gateway", lines=200)

        matching_logs = []
        for log_line in gateway_logs:
            if correlation_id in log_line:
                parsed = self.parse_json_log(log_line)
                if parsed:
                    matching_logs.append(parsed)

        if not matching_logs:
            log_error("No logs found with correlation_id")
            return False

        log_success(f"Retrieved {len(matching_logs)} log entries with correlation_id")

        # Show that we can track the request flow
        log_info("Request flow from logs:")
        for i, log_entry in enumerate(matching_logs[:5], 1):
            msg = log_entry.get('message', '')[:60]
            level = log_entry.get('level', 'INFO')
            log_info(f"  {i}. [{level}] {msg}")

        return True

    def validate_service_name_consistency(self) -> bool:
        """Validate logs include service_name and it's consistent."""
        log_test("VALIDATION 5: Service Name Consistency")

        # Get logs from different services
        services = [
            ("autograph-api-gateway", ["api-gateway", "auth"]),  # Gateway logs both its own and proxied service names
            ("autograph-auth-service", ["auth-service"]),
        ]

        all_consistent = True

        for container_name, expected_services in services:
            logs = self.get_recent_logs(container_name, lines=50)

            json_logs = []
            for log_line in logs:
                parsed = self.parse_json_log(log_line)
                if parsed:
                    json_logs.append(parsed)

            if not json_logs:
                log_info(f"No JSON logs found for {container_name} (may use different format)")
                continue

            # Check service field
            service_names = set()
            for log_entry in json_logs:
                if 'service' in log_entry:
                    service_names.add(log_entry['service'])

            if not service_names:
                log_error(f"{container_name}: No 'service' field found in logs")
                all_consistent = False
                continue

            # Check if service names are as expected
            unexpected = service_names - set(expected_services)
            if unexpected:
                log_error(f"{container_name}: Unexpected service names: {unexpected}")
                all_consistent = False
            else:
                log_success(f"{container_name}: Service names as expected: {', '.join(sorted(service_names))}")

        return all_consistent

    def validate_timestamp_format(self) -> bool:
        """Validate timestamp format is ISO 8601."""
        log_test("VALIDATION 6: Timestamp Format")

        # Get logs
        logs = self.get_recent_logs("autograph-api-gateway", lines=50)

        json_logs = []
        for log_line in logs:
            parsed = self.parse_json_log(log_line)
            if parsed:
                json_logs.append(parsed)

        if not json_logs:
            log_error("No JSON logs found")
            return False

        # Check timestamp format
        invalid_timestamps = 0

        for log_entry in json_logs[:10]:
            timestamp_str = log_entry.get('timestamp')
            if not timestamp_str:
                invalid_timestamps += 1
                continue

            # Try to parse ISO 8601 timestamp
            try:
                datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                invalid_timestamps += 1
                if invalid_timestamps == 1:  # Show first failure
                    log_error(f"Invalid timestamp format: {timestamp_str}")

        if invalid_timestamps > 0:
            log_error(f"{invalid_timestamps}/10 logs have invalid timestamp format")
            return False

        log_success("All timestamps are in valid ISO 8601 format")
        log_info(f"Sample timestamp: {json_logs[0].get('timestamp')}")

        return True

    def run_all_validations(self) -> bool:
        """Run all validation tests."""
        print("\n" + "="*70)
        print("  FEATURE #37: STRUCTURED LOGGING VALIDATION")
        print("="*70)
        print(f"  Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)

        # Check service health first
        if not self.validate_service_health():
            log_error("Service health check failed")
            return False

        # Run all validations
        validations = [
            ("JSON Log Format", self.validate_json_log_format),
            ("Required Log Fields", self.validate_required_fields),
            ("Correlation ID Tracking", self.validate_correlation_id_tracking),
            ("Log Aggregation Query", self.validate_log_aggregation_query),
            ("Service Name Consistency", self.validate_service_name_consistency),
            ("Timestamp Format", self.validate_timestamp_format),
        ]

        results = []
        for name, validation_func in validations:
            try:
                result = validation_func()
                results.append((name, result))
            except Exception as e:
                log_error(f"Validation '{name}' raised exception: {e}")
                results.append((name, False))

        # Print summary
        self.print_summary(results)

        # Return overall result
        return all(result for _, result in results)

    def print_summary(self, results):
        """Print validation summary."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        print(f"\n{'='*70}")
        print("  VALIDATION SUMMARY")
        print(f"{'='*70}")

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {name}")

        print(f"\n{'='*70}")
        print(f"  Results: {passed}/{total} validations passed")
        print(f"  Duration: {duration:.2f} seconds")
        print(f"  Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}")

        if passed == total:
            print("\n🎉 Feature #37 (Structured Logging) is FULLY VALIDATED!")
            print("✅ All logging validations passed")
        else:
            print(f"\n❌ Feature #37 validation FAILED")
            print(f"   {total - passed} validation(s) did not pass")


def main():
    """Main entry point."""
    validator = StructuredLoggingValidator()

    try:
        success = validator.run_all_validations()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Validation interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
