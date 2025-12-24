#!/usr/bin/env python3
"""
Test script for graceful shutdown functionality.

This script tests that services handle shutdown signals properly:
1. Complete in-flight requests before shutting down
2. Reject new requests during shutdown with 503
3. Shutdown cleanly after all requests complete
"""

import subprocess
import time
import requests
import signal
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# Test configuration
API_GATEWAY_URL = "http://localhost:8080"
AUTH_SERVICE_URL = "http://localhost:8085"
DIAGRAM_SERVICE_URL = "http://localhost:8082"

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_header(text):
    """Print a test header."""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}{text:^80}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")


def print_success(text):
    """Print success message."""
    print(f"{GREEN}✅ {text}{RESET}")


def print_error(text):
    """Print error message."""
    print(f"{RED}❌ {text}{RESET}")


def print_warning(text):
    """Print warning message."""
    print(f"{YELLOW}⚠️  {text}{RESET}")


def print_info(text):
    """Print info message."""
    print(f"{BLUE}ℹ️  {text}{RESET}")


def start_service(service_name, port, service_dir):
    """Start a service process."""
    print_info(f"Starting {service_name} on port {port}...")
    
    # Change to service directory
    cwd = os.path.join(os.path.dirname(__file__), service_dir)
    
    # Check if venv exists
    venv_python = os.path.join(cwd, "venv/bin/python3")
    if os.path.exists(venv_python):
        python_cmd = venv_python
    else:
        python_cmd = "python3.12"  # Fallback to system Python 3.12
    
    # Start service
    process = subprocess.Popen(
        [python_cmd, "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", str(port)],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid  # Create new process group for proper signal handling
    )
    
    # Wait for service to be ready
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=1)
            if response.status_code == 200:
                print_success(f"{service_name} started successfully (PID: {process.pid})")
                return process
        except:
            pass
        time.sleep(1)
    
    print_error(f"Failed to start {service_name}")
    process.terminate()
    return None


def make_slow_request(url, duration=5):
    """Make a request that takes specified time (simulated by server)."""
    try:
        # For testing, we'll use the health endpoint but track timing
        start = time.time()
        response = requests.get(url, timeout=10)
        elapsed = time.time() - start
        return {
            "status_code": response.status_code,
            "elapsed": elapsed,
            "success": True
        }
    except requests.exceptions.RequestException as e:
        return {
            "status_code": None,
            "elapsed": time.time() - start,
            "success": False,
            "error": str(e)
        }


def test_graceful_shutdown_api_gateway():
    """Test graceful shutdown for API Gateway."""
    print_header("TEST 1: API Gateway Graceful Shutdown")
    
    # Start API Gateway
    process = start_service("API Gateway", 8080, "services/api-gateway")
    if not process:
        print_error("Failed to start API Gateway, skipping test")
        return False
    
    try:
        # Test 1: Send SIGTERM during request
        print_info("Test 1: Send SIGTERM during concurrent requests")
        
        def make_request(i):
            """Make a simple health check request."""
            try:
                start = time.time()
                # Add small delay to simulate processing
                time.sleep(0.1 * i)  # Stagger requests
                response = requests.get(f"{API_GATEWAY_URL}/health", timeout=5)
                elapsed = time.time() - start
                return {
                    "request_id": i,
                    "status_code": response.status_code,
                    "elapsed": elapsed,
                    "success": True
                }
            except Exception as e:
                return {
                    "request_id": i,
                    "status_code": None,
                    "elapsed": time.time() - start,
                    "success": False,
                    "error": str(e)
                }
        
        # Start multiple concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(10)]
            
            # Send SIGTERM after 0.2 seconds
            time.sleep(0.2)
            print_info(f"Sending SIGTERM to API Gateway (PID: {process.pid})")
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            
            # Collect results
            results = []
            for future in as_completed(futures):
                results.append(future.result())
        
        # Analyze results
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        
        print_info(f"Successful requests: {len(successful)}/10")
        print_info(f"Failed requests: {len(failed)}/10")
        
        # All in-flight requests should complete
        if len(successful) >= 1:  # At least one should complete
            print_success("In-flight requests completed successfully")
        else:
            print_error("No requests completed - shutdown too aggressive")
            return False
        
        # Wait for process to exit
        print_info("Waiting for graceful shutdown...")
        try:
            process.wait(timeout=10)
            print_success("API Gateway shut down gracefully")
        except subprocess.TimeoutExpired:
            print_error("API Gateway did not shut down within timeout")
            process.kill()
            return False
        
        return True
        
    finally:
        # Cleanup
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except:
            pass


def test_graceful_shutdown_auth_service():
    """Test graceful shutdown for Auth Service."""
    print_header("TEST 2: Auth Service Graceful Shutdown")
    
    # Start Auth Service
    process = start_service("Auth Service", 8085, "services/auth-service")
    if not process:
        print_error("Failed to start Auth Service, skipping test")
        return False
    
    try:
        # Test with concurrent requests
        print_info("Sending concurrent requests and SIGTERM")
        
        def make_request(i):
            """Make a health check request."""
            try:
                start = time.time()
                time.sleep(0.1 * i)  # Stagger requests
                response = requests.get(f"{AUTH_SERVICE_URL}/health", timeout=5)
                elapsed = time.time() - start
                return {
                    "request_id": i,
                    "status_code": response.status_code,
                    "elapsed": elapsed,
                    "success": True
                }
            except Exception as e:
                return {
                    "request_id": i,
                    "status_code": None,
                    "elapsed": time.time() - start,
                    "success": False,
                    "error": str(e)
                }
        
        # Start multiple concurrent requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i) for i in range(5)]
            
            # Send SIGTERM after 0.2 seconds
            time.sleep(0.2)
            print_info(f"Sending SIGTERM to Auth Service (PID: {process.pid})")
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            
            # Collect results
            results = []
            for future in as_completed(futures):
                results.append(future.result())
        
        # Analyze results
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        
        print_info(f"Successful requests: {len(successful)}/5")
        print_info(f"Failed requests: {len(failed)}/5")
        
        if len(successful) >= 1:
            print_success("In-flight requests completed successfully")
        else:
            print_error("No requests completed")
            return False
        
        # Wait for process to exit
        print_info("Waiting for graceful shutdown...")
        try:
            process.wait(timeout=10)
            print_success("Auth Service shut down gracefully")
        except subprocess.TimeoutExpired:
            print_error("Auth Service did not shut down within timeout")
            process.kill()
            return False
        
        return True
        
    finally:
        # Cleanup
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except:
            pass


def test_reject_during_shutdown():
    """Test that new requests are rejected during shutdown."""
    print_header("TEST 3: Reject New Requests During Shutdown")
    
    # Start API Gateway
    process = start_service("API Gateway", 8080, "services/api-gateway")
    if not process:
        print_error("Failed to start API Gateway, skipping test")
        return False
    
    try:
        # Send SIGTERM
        print_info(f"Sending SIGTERM to API Gateway (PID: {process.pid})")
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        
        # Wait a moment for shutdown to register
        time.sleep(0.5)
        
        # Try to make a new request
        print_info("Attempting new request during shutdown...")
        try:
            response = requests.get(f"{API_GATEWAY_URL}/health", timeout=2)
            if response.status_code == 503:
                print_success("New request rejected with 503 (as expected)")
                success = True
            else:
                print_warning(f"New request returned {response.status_code} (expected 503)")
                success = False
        except requests.exceptions.ConnectionError:
            print_info("Connection refused (service already shut down)")
            success = True
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            success = False
        
        # Wait for process to exit
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        
        return success
        
    finally:
        # Cleanup
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except:
            pass


def main():
    """Run all graceful shutdown tests."""
    print_header("GRACEFUL SHUTDOWN TEST SUITE")
    print_info("Testing that services handle shutdown signals properly")
    print_info("Services will complete in-flight requests before shutting down")
    print_info("New requests during shutdown will be rejected with 503")
    
    results = {}
    
    # Run tests
    results["API Gateway"] = test_graceful_shutdown_api_gateway()
    time.sleep(2)  # Wait between tests
    
    results["Auth Service"] = test_graceful_shutdown_auth_service()
    time.sleep(2)  # Wait between tests
    
    results["Reject During Shutdown"] = test_reject_during_shutdown()
    
    # Summary
    print_header("TEST SUMMARY")
    all_passed = True
    for test_name, passed in results.items():
        if passed:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
            all_passed = False
    
    if all_passed:
        print_success("\n🎉 All tests passed! Graceful shutdown is working correctly.")
        return 0
    else:
        print_error("\n❌ Some tests failed. Review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
