#!/usr/bin/env python3
"""
Test Request Deduplication (Idempotency)
Feature #36: Request deduplication prevents duplicate operations

Tests that operations with the same idempotency key are executed only once,
and subsequent requests return the cached response.
"""

import requests
import time
import sys

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

def test_idempotency_prevents_duplicate():
    """Test 1: Operations with same idempotency key execute only once."""
    print_test("Idempotency Key Prevents Duplicate Execution")
    
    # Reset counter
    try:
        requests.post(f"{AUTH_BASE}/test/counter/reset")
    except:
        pass
    
    # Get initial counter value
    try:
        response = requests.get(f"{AUTH_BASE}/test/counter")
        initial_count = response.json()["count"]
        print(f"Initial counter: {initial_count}")
    except Exception as e:
        return print_result(False, f"Failed to get initial counter: {e}")
    
    # First request with idempotency key
    idempotency_key = "test-key-12345"
    headers = {
        "Idempotency-Key": idempotency_key,
        "Content-Type": "application/json"
    }
    
    try:
        response1 = requests.post(
            f"{AUTH_BASE}/test/create",
            headers=headers,
            json={}
        )
        
        if response1.status_code != 200:
            return print_result(False, f"First request failed: {response1.status_code}")
        
        data1 = response1.json()
        resource_id_1 = data1.get("resource_id")
        execution_count_1 = data1.get("execution_count")
        
        print(f"First request:")
        print(f"  Resource ID: {resource_id_1}")
        print(f"  Execution count: {execution_count_1}")
        print(f"  Idempotency hit: {response1.headers.get('X-Idempotency-Hit', 'N/A')}")
        
        # Verify first request was not from cache
        if response1.headers.get('X-Idempotency-Hit') == 'true':
            return print_result(False, "First request should not be from cache")
        
    except Exception as e:
        return print_result(False, f"First request error: {e}")
    
    # Small delay
    time.sleep(0.5)
    
    # Second request with SAME idempotency key
    try:
        response2 = requests.post(
            f"{AUTH_BASE}/test/create",
            headers=headers,
            json={}
        )
        
        if response2.status_code != 200:
            return print_result(False, f"Second request failed: {response2.status_code}")
        
        data2 = response2.json()
        resource_id_2 = data2.get("resource_id")
        execution_count_2 = data2.get("execution_count")
        
        print(f"\nSecond request (same idempotency key):")
        print(f"  Resource ID: {resource_id_2}")
        print(f"  Execution count: {execution_count_2}")
        print(f"  Idempotency hit: {response2.headers.get('X-Idempotency-Hit', 'N/A')}")
        
        # Verify second request was from cache
        if response2.headers.get('X-Idempotency-Hit') != 'true':
            return print_result(False, "Second request should be from cache")
        
        # Verify resource IDs are the same (same response)
        if resource_id_1 != resource_id_2:
            return print_result(False, f"Resource IDs should match: {resource_id_1} vs {resource_id_2}")
        
        # Verify execution counts are the same (operation not duplicated)
        if execution_count_1 != execution_count_2:
            return print_result(False, f"Execution counts should match: {execution_count_1} vs {execution_count_2}")
        
    except Exception as e:
        return print_result(False, f"Second request error: {e}")
    
    # Verify counter only incremented once
    try:
        response = requests.get(f"{AUTH_BASE}/test/counter")
        final_count = response.json()["count"]
        print(f"\nFinal counter: {final_count}")
        
        expected_count = initial_count + 1
        if final_count != expected_count:
            return print_result(False, f"Counter should be {expected_count}, got {final_count}")
        
    except Exception as e:
        return print_result(False, f"Failed to verify counter: {e}")
    
    return print_result(True, "Idempotency key prevented duplicate execution")


def test_different_key_new_operation():
    """Test 2: Different idempotency key executes new operation."""
    print_test("Different Idempotency Key Executes New Operation")
    
    # Reset counter
    try:
        response = requests.post(f"{AUTH_BASE}/test/counter/reset")
        print("Counter reset")
    except Exception as e:
        return print_result(False, f"Failed to reset counter: {e}")
    
    # First request with key A
    headers_a = {
        "Idempotency-Key": "key-A",
        "Content-Type": "application/json"
    }
    
    try:
        response_a = requests.post(
            f"{AUTH_BASE}/test/create",
            headers=headers_a,
            json={}
        )
        
        if response_a.status_code != 200:
            return print_result(False, f"Request A failed: {response_a.status_code}")
        
        data_a = response_a.json()
        resource_id_a = data_a.get("resource_id")
        
        print(f"Request with key A:")
        print(f"  Resource ID: {resource_id_a}")
        print(f"  Execution count: {data_a.get('execution_count')}")
        
    except Exception as e:
        return print_result(False, f"Request A error: {e}")
    
    time.sleep(0.5)
    
    # Second request with key B (different)
    headers_b = {
        "Idempotency-Key": "key-B",
        "Content-Type": "application/json"
    }
    
    try:
        response_b = requests.post(
            f"{AUTH_BASE}/test/create",
            headers=headers_b,
            json={}
        )
        
        if response_b.status_code != 200:
            return print_result(False, f"Request B failed: {response_b.status_code}")
        
        data_b = response_b.json()
        resource_id_b = data_b.get("resource_id")
        
        print(f"\nRequest with key B:")
        print(f"  Resource ID: {resource_id_b}")
        print(f"  Execution count: {data_b.get('execution_count')}")
        
        # Verify resource IDs are DIFFERENT (new operation)
        if resource_id_a == resource_id_b:
            return print_result(False, "Resource IDs should be different for different keys")
        
        # Verify this was not from cache
        if response_b.headers.get('X-Idempotency-Hit') == 'true':
            return print_result(False, "Request with new key should not be from cache")
        
    except Exception as e:
        return print_result(False, f"Request B error: {e}")
    
    # Verify counter incremented twice (two operations)
    try:
        response = requests.get(f"{AUTH_BASE}/test/counter")
        final_count = response.json()["count"]
        print(f"\nFinal counter: {final_count}")
        
        if final_count != 2:
            return print_result(False, f"Counter should be 2, got {final_count}")
        
    except Exception as e:
        return print_result(False, f"Failed to verify counter: {e}")
    
    return print_result(True, "Different idempotency keys execute separate operations")


def test_no_key_executes_every_time():
    """Test 3: Requests without idempotency key execute every time."""
    print_test("No Idempotency Key Executes Every Time")
    
    # Reset counter
    try:
        requests.post(f"{AUTH_BASE}/test/counter/reset")
    except:
        pass
    
    # Make 3 requests without idempotency key
    resource_ids = []
    
    for i in range(3):
        try:
            response = requests.post(
                f"{AUTH_BASE}/test/create",
                json={}
            )
            
            if response.status_code != 200:
                return print_result(False, f"Request {i+1} failed: {response.status_code}")
            
            data = response.json()
            resource_id = data.get("resource_id")
            resource_ids.append(resource_id)
            
            print(f"Request {i+1}:")
            print(f"  Resource ID: {resource_id}")
            print(f"  Execution count: {data.get('execution_count')}")
            
        except Exception as e:
            return print_result(False, f"Request {i+1} error: {e}")
        
        time.sleep(0.2)
    
    # Verify all resource IDs are different
    if len(set(resource_ids)) != 3:
        return print_result(False, "All resource IDs should be different without idempotency key")
    
    # Verify counter incremented 3 times
    try:
        response = requests.get(f"{AUTH_BASE}/test/counter")
        final_count = response.json()["count"]
        print(f"\nFinal counter: {final_count}")
        
        if final_count != 3:
            return print_result(False, f"Counter should be 3, got {final_count}")
        
    except Exception as e:
        return print_result(False, f"Failed to verify counter: {e}")
    
    return print_result(True, "Requests without idempotency key execute every time")


def test_idempotency_header_variants():
    """Test 4: Both Idempotency-Key and X-Idempotency-Key headers work."""
    print_test("Idempotency Header Variants")
    
    # Reset counter
    try:
        requests.post(f"{AUTH_BASE}/test/counter/reset")
    except:
        pass
    
    # Test with Idempotency-Key header
    headers1 = {
        "Idempotency-Key": "test-variant-key",
        "Content-Type": "application/json"
    }
    
    try:
        response1 = requests.post(
            f"{AUTH_BASE}/test/create",
            headers=headers1,
            json={}
        )
        
        if response1.status_code != 200:
            return print_result(False, f"Request with Idempotency-Key failed: {response1.status_code}")
        
        data1 = response1.json()
        resource_id_1 = data1.get("resource_id")
        
        print(f"Request with 'Idempotency-Key' header:")
        print(f"  Resource ID: {resource_id_1}")
        
    except Exception as e:
        return print_result(False, f"First request error: {e}")
    
    time.sleep(0.5)
    
    # Test with X-Idempotency-Key header (same key value)
    headers2 = {
        "X-Idempotency-Key": "test-variant-key-2",
        "Content-Type": "application/json"
    }
    
    try:
        response2 = requests.post(
            f"{AUTH_BASE}/test/create",
            headers=headers2,
            json={}
        )
        
        if response2.status_code != 200:
            return print_result(False, f"Request with X-Idempotency-Key failed: {response2.status_code}")
        
        data2 = response2.json()
        resource_id_2 = data2.get("resource_id")
        
        print(f"\nRequest with 'X-Idempotency-Key' header:")
        print(f"  Resource ID: {resource_id_2}")
        
    except Exception as e:
        return print_result(False, f"Second request error: {e}")
    
    return print_result(True, "Both idempotency header variants accepted")


def test_get_requests_not_cached():
    """Test 5: GET requests are not affected by idempotency (only POST/PUT/PATCH)."""
    print_test("GET Requests Not Affected by Idempotency")
    
    # Make multiple GET requests with same idempotency key
    headers = {
        "Idempotency-Key": "get-test-key"
    }
    
    try:
        # First GET request
        response1 = requests.get(
            f"{AUTH_BASE}/test/counter",
            headers=headers
        )
        
        if response1.status_code != 200:
            return print_result(False, f"First GET failed: {response1.status_code}")
        
        count1 = response1.json()["count"]
        
        print(f"First GET request count: {count1}")
        
        # Increment counter
        requests.post(f"{AUTH_BASE}/test/create", json={})
        
        # Second GET request with same idempotency key
        response2 = requests.get(
            f"{AUTH_BASE}/test/counter",
            headers=headers
        )
        
        if response2.status_code != 200:
            return print_result(False, f"Second GET failed: {response2.status_code}")
        
        count2 = response2.json()["count"]
        
        print(f"Second GET request count: {count2}")
        
        # Verify counts are different (not cached)
        if count1 == count2:
            return print_result(False, "GET requests should not be cached by idempotency")
        
    except Exception as e:
        return print_result(False, f"GET request error: {e}")
    
    return print_result(True, "GET requests not affected by idempotency middleware")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("REQUEST DEDUPLICATION (IDEMPOTENCY) TESTS")
    print("Feature #36: Request deduplication prevents duplicate operations")
    print("="*60)
    
    # Check services are running
    try:
        response = requests.get(f"{API_BASE}/health", timeout=2)
        if response.status_code != 200:
            print("\n✗ ERROR: API Gateway not healthy")
            print("Please start services with: docker-compose up -d")
            return 1
        print(f"\n✓ API Gateway is healthy")
    except Exception as e:
        print(f"\n✗ ERROR: Cannot reach API Gateway: {e}")
        print("Please start services with: docker-compose up -d")
        return 1
    
    try:
        response = requests.get(f"{AUTH_BASE}/health", timeout=2)
        if response.status_code != 200:
            print("✗ ERROR: Auth Service not healthy")
            return 1
        print(f"✓ Auth Service is healthy")
    except Exception as e:
        print(f"✗ ERROR: Cannot reach Auth Service: {e}")
        return 1
    
    # Run tests
    results = []
    
    results.append(test_idempotency_prevents_duplicate())
    results.append(test_different_key_new_operation())
    results.append(test_no_key_executes_every_time())
    results.append(test_idempotency_header_variants())
    results.append(test_get_requests_not_cached())
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests PASSED! Feature #36 is working correctly.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
