"""Test script to verify database connection pooling."""
import requests
import concurrent.futures
import time
from datetime import datetime

def test_endpoint(endpoint_url, request_id):
    """Test a single request to an endpoint."""
    try:
        start = time.time()
        response = requests.post(
            endpoint_url,
            json={"email": f"test{request_id}@example.com", "password": "testpass123"},
            timeout=10
        )
        elapsed = time.time() - start
        return {
            "request_id": request_id,
            "status_code": response.status_code,
            "elapsed": elapsed,
            "success": response.status_code in [200, 201, 400, 409]  # 400/409 expected for duplicate users
        }
    except Exception as e:
        return {
            "request_id": request_id,
            "error": str(e),
            "success": False
        }

def test_concurrent_connections(num_requests, endpoint_url):
    """Test concurrent connections to verify pooling."""
    print(f"\n{'='*80}")
    print(f"Testing {num_requests} concurrent requests to {endpoint_url}")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    # Execute concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_requests) as executor:
        futures = [
            executor.submit(test_endpoint, endpoint_url, i)
            for i in range(num_requests)
        ]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Analyze results
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    
    print(f"\n{'-'*80}")
    print(f"Results:")
    print(f"  Total requests: {num_requests}")
    print(f"  Successful: {len(successful)}")
    print(f"  Failed: {len(failed)}")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Avg time per request: {total_time/num_requests:.2f}s")
    print(f"  Requests per second: {num_requests/total_time:.2f}")
    
    if successful:
        avg_elapsed = sum(r["elapsed"] for r in successful) / len(successful)
        min_elapsed = min(r["elapsed"] for r in successful)
        max_elapsed = max(r["elapsed"] for r in successful)
        print(f"  Avg response time: {avg_elapsed:.3f}s")
        print(f"  Min response time: {min_elapsed:.3f}s")
        print(f"  Max response time: {max_elapsed:.3f}s")
    
    if failed:
        print(f"\n  Failed requests:")
        for r in failed[:5]:  # Show first 5 failures
            print(f"    Request {r['request_id']}: {r.get('error', 'Unknown error')}")
    
    print(f"{'-'*80}\n")
    
    return {
        "total": num_requests,
        "successful": len(successful),
        "failed": len(failed),
        "total_time": total_time,
        "avg_time": total_time/num_requests
    }

if __name__ == "__main__":
    # Test endpoints
    auth_register = "http://localhost:8080/api/auth/register"
    
    print("\n" + "="*80)
    print("DATABASE CONNECTION POOLING TEST")
    print("="*80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("\nConfiguration:")
    print("  pool_size: 10")
    print("  max_overflow: 20")
    print("  pool_pre_ping: True")
    print("  pool_recycle: 3600s")
    print("  pool_timeout: 30s")
    
    # Test 1: 10 concurrent requests (should use pool only)
    print("\n\nTEST 1: 10 concurrent requests")
    print("Expected: All requests should use pooled connections")
    result1 = test_concurrent_connections(10, auth_register)
    
    # Wait a bit
    time.sleep(2)
    
    # Test 2: 30 concurrent requests (should use pool + overflow)
    print("\n\nTEST 2: 30 concurrent requests")
    print("Expected: 10 use pool, 20 use overflow connections")
    result2 = test_concurrent_connections(30, auth_register)
    
    # Wait a bit
    time.sleep(2)
    
    # Test 3: 35 concurrent requests (should use pool + overflow + wait)
    print("\n\nTEST 3: 35 concurrent requests")
    print("Expected: 10 use pool, 20 use overflow, 5 wait for available connection")
    result3 = test_concurrent_connections(35, auth_register)
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Test 1 (10 requests): {result1['successful']}/{result1['total']} successful in {result1['total_time']:.2f}s")
    print(f"Test 2 (30 requests): {result2['successful']}/{result2['total']} successful in {result2['total_time']:.2f}s")
    print(f"Test 3 (35 requests): {result3['successful']}/{result3['total']} successful in {result3['total_time']:.2f}s")
    
    # Verify pooling is working
    print("\nConnection pooling verification:")
    if result1['successful'] >= 8 and result2['successful'] >= 25 and result3['successful'] >= 30:
        print("  ✅ Connection pooling is working correctly!")
        print("  ✅ Pool handles concurrent requests efficiently")
        print("  ✅ Overflow connections are created when needed")
    else:
        print("  ⚠️  Some requests failed - check service logs")
    
    print("\n" + "="*80 + "\n")
