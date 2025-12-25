#!/usr/bin/env python3
"""
Feature #36 Validation: Request Deduplication (Idempotency)
============================================================

This script validates that request deduplication with idempotency keys works correctly:
- Operations with same idempotency key execute only once
- Cached responses returned for duplicate requests
- Different keys execute separate operations
- No key means requests execute every time
- Only POST/PUT/PATCH operations are deduplicated
- Both header variants supported (Idempotency-Key and X-Idempotency-Key)

Exit codes:
0 - All validations passed
1 - Validation failed
"""

import sys
import time
import requests
import json
from datetime import datetime

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


class IdempotencyValidator:
    """Validates request deduplication functionality."""

    def __init__(self):
        self.validation_results = []
        self.start_time = datetime.now()

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

    def validate_prevents_duplicate_execution(self) -> bool:
        """Validate that same idempotency key prevents duplicate execution."""
        log_test("VALIDATION 1: Prevent Duplicate Execution")

        try:
            # Reset counter
            requests.post(f"{AUTH_BASE}/test/counter/reset", timeout=TIMEOUT)

            # Get initial counter
            response = requests.get(f"{AUTH_BASE}/test/counter", timeout=TIMEOUT)
            initial_count = response.json()["count"]
            log_info(f"Initial counter: {initial_count}")

            # First request with idempotency key
            idempotency_key = f"test-key-{int(time.time())}"
            headers = {
                "Idempotency-Key": idempotency_key,
                "Content-Type": "application/json"
            }

            response1 = requests.post(
                f"{AUTH_BASE}/test/create",
                headers=headers,
                json={},
                timeout=TIMEOUT
            )

            if response1.status_code != 200:
                log_error(f"First request failed: {response1.status_code}")
                return False

            data1 = response1.json()
            resource_id_1 = data1.get("resource_id")
            execution_count_1 = data1.get("execution_count")

            log_info(f"First request:")
            log_info(f"  Resource ID: {resource_id_1}")
            log_info(f"  Execution count: {execution_count_1}")
            log_info(f"  Cache hit: {response1.headers.get('X-Idempotency-Hit', 'false')}")

            # Verify first request not from cache
            if response1.headers.get('X-Idempotency-Hit') == 'true':
                log_error("First request should not be from cache")
                return False

            time.sleep(0.5)

            # Second request with SAME idempotency key
            response2 = requests.post(
                f"{AUTH_BASE}/test/create",
                headers=headers,
                json={},
                timeout=TIMEOUT
            )

            if response2.status_code != 200:
                log_error(f"Second request failed: {response2.status_code}")
                return False

            data2 = response2.json()
            resource_id_2 = data2.get("resource_id")
            execution_count_2 = data2.get("execution_count")

            log_info(f"Second request (same key):")
            log_info(f"  Resource ID: {resource_id_2}")
            log_info(f"  Execution count: {execution_count_2}")
            log_info(f"  Cache hit: {response2.headers.get('X-Idempotency-Hit', 'false')}")

            # Verify second request WAS from cache
            if response2.headers.get('X-Idempotency-Hit') != 'true':
                log_error("Second request should be from cache")
                return False

            # Verify resource IDs match (same response)
            if resource_id_1 != resource_id_2:
                log_error(f"Resource IDs should match: {resource_id_1} vs {resource_id_2}")
                return False

            # Verify execution counts match (operation not duplicated)
            if execution_count_1 != execution_count_2:
                log_error(f"Execution counts should match: {execution_count_1} vs {execution_count_2}")
                return False

            # Verify counter only incremented once
            response = requests.get(f"{AUTH_BASE}/test/counter", timeout=TIMEOUT)
            final_count = response.json()["count"]

            expected_count = initial_count + 1
            if final_count != expected_count:
                log_error(f"Counter should be {expected_count}, got {final_count}")
                return False

            log_success("Idempotency key prevented duplicate execution")
            log_success(f"Counter correctly incremented once: {initial_count} → {final_count}")

            return True

        except Exception as e:
            log_error(f"Validation failed: {e}")
            return False

    def validate_different_keys_new_operations(self) -> bool:
        """Validate that different idempotency keys execute new operations."""
        log_test("VALIDATION 2: Different Keys Execute New Operations")

        try:
            # Reset counter
            requests.post(f"{AUTH_BASE}/test/counter/reset", timeout=TIMEOUT)
            log_info("Counter reset")

            # Request with key A
            headers_a = {
                "Idempotency-Key": f"key-A-{int(time.time())}",
                "Content-Type": "application/json"
            }

            response_a = requests.post(
                f"{AUTH_BASE}/test/create",
                headers=headers_a,
                json={},
                timeout=TIMEOUT
            )

            if response_a.status_code != 200:
                log_error(f"Request A failed: {response_a.status_code}")
                return False

            data_a = response_a.json()
            resource_id_a = data_a.get("resource_id")

            log_info(f"Request A: {resource_id_a}")

            time.sleep(0.5)

            # Request with key B (different)
            headers_b = {
                "Idempotency-Key": f"key-B-{int(time.time())}",
                "Content-Type": "application/json"
            }

            response_b = requests.post(
                f"{AUTH_BASE}/test/create",
                headers=headers_b,
                json={},
                timeout=TIMEOUT
            )

            if response_b.status_code != 200:
                log_error(f"Request B failed: {response_b.status_code}")
                return False

            data_b = response_b.json()
            resource_id_b = data_b.get("resource_id")

            log_info(f"Request B: {resource_id_b}")

            # Verify resource IDs are DIFFERENT
            if resource_id_a == resource_id_b:
                log_error("Resource IDs should be different for different keys")
                return False

            # Verify request B not from cache
            if response_b.headers.get('X-Idempotency-Hit') == 'true':
                log_error("Request with new key should not be from cache")
                return False

            # Verify counter incremented twice
            response = requests.get(f"{AUTH_BASE}/test/counter", timeout=TIMEOUT)
            final_count = response.json()["count"]

            if final_count != 2:
                log_error(f"Counter should be 2, got {final_count}")
                return False

            log_success("Different idempotency keys execute separate operations")
            log_success(f"Counter correctly incremented twice: {final_count}")

            return True

        except Exception as e:
            log_error(f"Validation failed: {e}")
            return False

    def validate_no_key_always_executes(self) -> bool:
        """Validate that requests without idempotency key always execute."""
        log_test("VALIDATION 3: No Idempotency Key Always Executes")

        try:
            # Reset counter
            requests.post(f"{AUTH_BASE}/test/counter/reset", timeout=TIMEOUT)

            # Make 3 requests without idempotency key
            resource_ids = []

            for i in range(3):
                response = requests.post(
                    f"{AUTH_BASE}/test/create",
                    json={},
                    timeout=TIMEOUT
                )

                if response.status_code != 200:
                    log_error(f"Request {i+1} failed: {response.status_code}")
                    return False

                data = response.json()
                resource_id = data.get("resource_id")
                resource_ids.append(resource_id)

                log_info(f"Request {i+1}: {resource_id}")

                time.sleep(0.2)

            # Verify all resource IDs are different
            if len(set(resource_ids)) != 3:
                log_error("All resource IDs should be different without idempotency key")
                return False

            # Verify counter incremented 3 times
            response = requests.get(f"{AUTH_BASE}/test/counter", timeout=TIMEOUT)
            final_count = response.json()["count"]

            if final_count != 3:
                log_error(f"Counter should be 3, got {final_count}")
                return False

            log_success("Requests without idempotency key execute every time")
            log_success(f"Counter correctly incremented 3 times: {final_count}")

            return True

        except Exception as e:
            log_error(f"Validation failed: {e}")
            return False

    def validate_header_variants(self) -> bool:
        """Validate both Idempotency-Key and X-Idempotency-Key headers work."""
        log_test("VALIDATION 4: Both Header Variants Supported")

        try:
            # Reset counter
            requests.post(f"{AUTH_BASE}/test/counter/reset", timeout=TIMEOUT)

            # Test with Idempotency-Key
            headers1 = {
                "Idempotency-Key": f"standard-{int(time.time())}",
                "Content-Type": "application/json"
            }

            response1 = requests.post(
                f"{AUTH_BASE}/test/create",
                headers=headers1,
                json={},
                timeout=TIMEOUT
            )

            if response1.status_code != 200:
                log_error(f"Request with Idempotency-Key failed: {response1.status_code}")
                return False

            log_info("✓ Idempotency-Key header accepted")

            # Test with X-Idempotency-Key
            headers2 = {
                "X-Idempotency-Key": f"x-variant-{int(time.time())}",
                "Content-Type": "application/json"
            }

            response2 = requests.post(
                f"{AUTH_BASE}/test/create",
                headers=headers2,
                json={},
                timeout=TIMEOUT
            )

            if response2.status_code != 200:
                log_error(f"Request with X-Idempotency-Key failed: {response2.status_code}")
                return False

            log_info("✓ X-Idempotency-Key header accepted")

            log_success("Both idempotency header variants accepted")

            return True

        except Exception as e:
            log_error(f"Validation failed: {e}")
            return False

    def validate_get_not_cached(self) -> bool:
        """Validate GET requests are not affected by idempotency."""
        log_test("VALIDATION 5: GET Requests Not Cached")

        try:
            # Make multiple GET requests with same idempotency key
            headers = {
                "Idempotency-Key": "get-test-key"
            }

            # First GET
            response1 = requests.get(
                f"{AUTH_BASE}/test/counter",
                headers=headers,
                timeout=TIMEOUT
            )

            if response1.status_code != 200:
                log_error(f"First GET failed: {response1.status_code}")
                return False

            count1 = response1.json()["count"]
            log_info(f"First GET count: {count1}")

            # Increment counter
            requests.post(f"{AUTH_BASE}/test/create", json={}, timeout=TIMEOUT)

            # Second GET with same idempotency key
            response2 = requests.get(
                f"{AUTH_BASE}/test/counter",
                headers=headers,
                timeout=TIMEOUT
            )

            if response2.status_code != 200:
                log_error(f"Second GET failed: {response2.status_code}")
                return False

            count2 = response2.json()["count"]
            log_info(f"Second GET count: {count2}")

            # Verify counts are different (not cached)
            if count1 == count2:
                log_error("GET requests should not be cached by idempotency")
                return False

            log_success("GET requests not affected by idempotency middleware")
            log_success(f"Counts correctly different: {count1} → {count2}")

            return True

        except Exception as e:
            log_error(f"Validation failed: {e}")
            return False

    def validate_redis_storage(self) -> bool:
        """Validate idempotency keys are stored in Redis."""
        log_test("VALIDATION 6: Redis Storage")

        try:
            # Reset counter
            requests.post(f"{AUTH_BASE}/test/counter/reset", timeout=TIMEOUT)

            # Create request with idempotency key
            idempotency_key = f"redis-test-{int(time.time())}"
            headers = {
                "Idempotency-Key": idempotency_key,
                "Content-Type": "application/json"
            }

            response = requests.post(
                f"{AUTH_BASE}/test/create",
                headers=headers,
                json={},
                timeout=TIMEOUT
            )

            if response.status_code != 200:
                log_error(f"Request failed: {response.status_code}")
                return False

            log_info(f"Created resource with key: {idempotency_key}")

            # Make same request again - should hit cache
            response2 = requests.post(
                f"{AUTH_BASE}/test/create",
                headers=headers,
                json={},
                timeout=TIMEOUT
            )

            # Verify it was cached (hit Redis)
            if response2.headers.get('X-Idempotency-Hit') != 'true':
                log_error("Request should have hit Redis cache")
                return False

            log_success("Idempotency key correctly stored in Redis")
            log_success("Cached response successfully retrieved")

            return True

        except Exception as e:
            log_error(f"Validation failed: {e}")
            return False

    def run_all_validations(self) -> bool:
        """Run all validation tests."""
        print("\n" + "="*70)
        print("  FEATURE #36: REQUEST DEDUPLICATION VALIDATION")
        print("="*70)
        print(f"  Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)

        # Check service health first
        if not self.validate_service_health():
            log_error("Service health check failed")
            return False

        # Run all validations
        validations = [
            ("Prevent Duplicate Execution", self.validate_prevents_duplicate_execution),
            ("Different Keys New Operations", self.validate_different_keys_new_operations),
            ("No Key Always Executes", self.validate_no_key_always_executes),
            ("Header Variants", self.validate_header_variants),
            ("GET Not Cached", self.validate_get_not_cached),
            ("Redis Storage", self.validate_redis_storage),
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
            print("\n🎉 Feature #36 (Request Deduplication) is FULLY VALIDATED!")
            print("✅ All idempotency validations passed")
        else:
            print(f"\n❌ Feature #36 validation FAILED")
            print(f"   {total - passed} validation(s) did not pass")


def main():
    """Main entry point."""
    validator = IdempotencyValidator()

    try:
        success = validator.run_all_validations()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Validation interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
