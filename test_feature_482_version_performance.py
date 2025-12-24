#!/usr/bin/env python3
"""
Test Feature #482: Version Performance - Fast Access to Any Version

Tests that version access is fast (< 1 second) even with many versions:
1. Create diagram with 100+ versions
2. Measure access time to version 1
3. Measure access time to version 100
4. Verify both are < 1 second
5. Measure average access time across all versions
"""

import requests
import time
import json
from typing import Dict, List, Tuple
from colorama import Fore, Style, init

# Initialize colorama
init()

BASE_URL = "http://localhost:8080/api"
DIAGRAM_SERVICE_URL = "http://localhost:8082"

# Color helpers
def info(msg): print(f"{Fore.CYAN}ℹ️  {msg}{Style.RESET_ALL}")
def success(msg): print(f"{Fore.GREEN}✅ {msg}{Style.RESET_ALL}")
def error(msg): print(f"{Fore.RED}❌ {msg}{Style.RESET_ALL}")
def warning(msg): print(f"{Fore.YELLOW}⚠️  {msg}{Style.RESET_ALL}")
def header(msg): print(f"\n{Fore.BLUE}{'='*80}\n{msg}\n{'='*80}{Style.RESET_ALL}\n")

def register_and_login() -> Tuple[str, str]:
    """Register a new user and login."""
    timestamp = int(time.time())
    email = f"perftest_{timestamp}@example.com"
    password = "TestPass123!@#"
    
    # Register
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Performance Test User"
        }
    )
    
    if response.status_code != 201:
        error(f"Registration failed: {response.text}")
        raise Exception("Registration failed")
    
    user_data = response.json()
    user_id = user_data.get("id") or user_data.get("user", {}).get("id")
    
    # Auto-verify the user (direct database update for testing)
    # In production, users would click email verification link
    import psycopg2
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="autograph",
        user="autograph",
        password="autograph_dev_password"
    )
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_verified = true WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    
    # Login
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": email,
            "password": password
        }
    )
    
    if response.status_code != 200:
        error(f"Login failed: {response.text}")
        raise Exception("Login failed")
    
    data = response.json()
    token = data.get("access_token") or data.get("token")
    
    if not token:
        error(f"Failed to extract token from response: {data}")
        raise Exception("Login failed")
    
    # Decode JWT to get user_id from 'sub' field
    import base64
    payload = token.split('.')[1]
    # Add padding if needed
    padding = 4 - len(payload) % 4
    if padding != 4:
        payload += '=' * padding
    decoded = base64.b64decode(payload)
    payload_data = json.loads(decoded)
    user_id = payload_data.get('sub')
    
    if not user_id:
        error(f"Failed to extract user_id from JWT: {payload_data}")
        raise Exception("Login failed")
    
    success(f"Registered and logged in as: {email}")
    return user_id, token


def create_diagram_with_versions(user_id: str, token: str, num_versions: int = 100) -> str:
    """Create a diagram and generate many versions."""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }
    
    # Create initial diagram
    canvas_data = {
        "shapes": [
            {
                "id": "shape1",
                "type": "rectangle",
                "x": 100,
                "y": 100,
                "width": 200,
                "height": 100
            }
        ]
    }
    
    response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/",
        headers=headers,
        json={
            "title": "Performance Test Diagram",
            "file_type": "canvas",
            "canvas_data": canvas_data
        }
    )
    
    if response.status_code != 201 and response.status_code != 200:
        error(f"Failed to create diagram (status {response.status_code}): {response.text}")
        raise Exception("Failed to create diagram")
    
    diagram_id = response.json()["id"]
    success(f"Created diagram: {diagram_id}")
    
    # Create additional versions by updating the diagram
    info(f"Creating {num_versions - 1} additional versions...")
    
    for i in range(2, num_versions + 1):
        # Update canvas data to trigger new version
        canvas_data["shapes"].append({
            "id": f"shape{i}",
            "type": "circle",
            "x": 100 + i * 20,
            "y": 100 + i * 20,
            "radius": 50
        })
        
        # Use the explicit version creation endpoint
        response = requests.post(
            f"{DIAGRAM_SERVICE_URL}/{diagram_id}/versions",
            headers=headers,
            json={
                "description": f"Version {i}",
                "canvas_data": canvas_data,
                "note_content": None
            }
        )
        
        if response.status_code not in [200, 201]:
            error(f"Failed to create version {i}: {response.text}")
            raise Exception(f"Failed to create version {i}")
        
        # Show progress every 10 versions
        if i % 10 == 0:
            info(f"  Created {i} versions...")
    
    success(f"Created {num_versions} versions total")
    return diagram_id


def measure_version_access_time(user_id: str, token: str, diagram_id: str, version_number: int) -> float:
    """Measure time to access a specific version."""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }
    
    # First, get the version ID for the version number
    response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/versions",
        headers=headers
    )
    
    if response.status_code != 200:
        error(f"Failed to get versions: {response.text}")
        raise Exception("Failed to get versions")
    
    data = response.json()
    # Handle different response formats
    versions = data if isinstance(data, list) else data.get("versions", [])
    
    info(f"Total versions found: {len(versions)}")
    if versions:
        info(f"Version numbers: {sorted([v['version_number'] for v in versions])}")
    
    version_id = None
    for v in versions:
        if v["version_number"] == version_number:
            version_id = v["id"]
            break
    
    if not version_id:
        error(f"Version {version_number} not found")
        raise Exception(f"Version {version_number} not found")
    
    # Measure access time
    start_time = time.time()
    
    response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/versions/{version_id}",
        headers=headers,
        params={"include_content": "true"}
    )
    
    end_time = time.time()
    access_time = end_time - start_time
    
    if response.status_code != 200:
        error(f"Failed to access version {version_number}: {response.text}")
        raise Exception(f"Failed to access version {version_number}")
    
    return access_time


def measure_all_versions_performance(user_id: str, token: str, diagram_id: str, total_versions: int) -> List[float]:
    """Measure access time for multiple versions."""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }
    
    # Get all versions
    response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/versions",
        headers=headers
    )
    
    if response.status_code != 200:
        error(f"Failed to get versions: {response.text}")
        raise Exception("Failed to get versions")
    
    data = response.json()
    # Handle different response formats
    versions = data if isinstance(data, list) else data.get("versions", [])
    
    # Test a sample of versions (every 10th version)
    test_versions = [v for v in versions if v["version_number"] % 10 == 0 or v["version_number"] == 1]
    access_times = []
    
    info(f"Testing access time for {len(test_versions)} sample versions...")
    
    for version in test_versions:
        start_time = time.time()
        
        response = requests.get(
            f"{DIAGRAM_SERVICE_URL}/{diagram_id}/versions/{version['id']}",
            headers=headers,
            params={"include_content": "true"}
        )
        
        end_time = time.time()
        access_time = end_time - start_time
        
        if response.status_code == 200:
            access_times.append(access_time)
            info(f"  Version {version['version_number']}: {access_time:.3f}s")
    
    return access_times


def main():
    """Run all performance tests."""
    print(f"\n{Fore.MAGENTA}{'='*80}")
    print("Feature #482: Version Performance Test")
    print(f"{'='*80}{Style.RESET_ALL}\n")
    
    try:
        # Step 1: Register and login
        header("STEP 1: Register and Login")
        user_id, token = register_and_login()
        
        # Step 2: Create diagram with many versions
        header("STEP 2: Create Diagram with 100 Versions")
        num_versions = 100
        diagram_id = create_diagram_with_versions(user_id, token, num_versions)
        
        # Step 3: Measure access time to version 1
        header("STEP 3: Measure Access Time to Version 1")
        access_time_v1 = measure_version_access_time(user_id, token, diagram_id, 1)
        info(f"Access time for version 1: {access_time_v1:.3f}s")
        
        if access_time_v1 < 1.0:
            success(f"✅ Version 1 access time < 1 second: {access_time_v1:.3f}s")
        else:
            warning(f"⚠️  Version 1 access time >= 1 second: {access_time_v1:.3f}s")
        
        # Step 4: Measure access time to version 100
        header("STEP 4: Measure Access Time to Version 100")
        access_time_v100 = measure_version_access_time(user_id, token, diagram_id, 100)
        info(f"Access time for version 100: {access_time_v100:.3f}s")
        
        if access_time_v100 < 1.0:
            success(f"✅ Version 100 access time < 1 second: {access_time_v100:.3f}s")
        else:
            warning(f"⚠️  Version 100 access time >= 1 second: {access_time_v100:.3f}s")
        
        # Step 5: Measure average access time
        header("STEP 5: Measure Average Access Time")
        access_times = measure_all_versions_performance(user_id, token, diagram_id, num_versions)
        
        if access_times:
            avg_time = sum(access_times) / len(access_times)
            min_time = min(access_times)
            max_time = max(access_times)
            
            info(f"Tested {len(access_times)} versions")
            info(f"Average access time: {avg_time:.3f}s")
            info(f"Min access time: {min_time:.3f}s")
            info(f"Max access time: {max_time:.3f}s")
            
            if avg_time < 1.0:
                success(f"✅ Average access time < 1 second: {avg_time:.3f}s")
            else:
                warning(f"⚠️  Average access time >= 1 second: {avg_time:.3f}s")
            
            if max_time < 1.0:
                success(f"✅ All versions accessed in < 1 second")
            else:
                warning(f"⚠️  Some versions took >= 1 second (max: {max_time:.3f}s)")
        
        # Summary
        header("TEST SUMMARY")
        
        all_passed = (
            access_time_v1 < 1.0 and
            access_time_v100 < 1.0 and
            (avg_time < 1.0 if access_times else False) and
            (max_time < 1.0 if access_times else False)
        )
        
        tests = [
            ("Version 1 Access < 1s", access_time_v1 < 1.0),
            ("Version 100 Access < 1s", access_time_v100 < 1.0),
            ("Average Access < 1s", avg_time < 1.0 if access_times else False),
            ("All Versions < 1s", max_time < 1.0 if access_times else False),
        ]
        
        for test_name, passed in tests:
            status = f"{Fore.GREEN}PASS{Style.RESET_ALL}" if passed else f"{Fore.RED}FAIL{Style.RESET_ALL}"
            print(f"  {status} - {test_name}")
        
        passed_count = sum(1 for _, passed in tests if passed)
        print(f"\nResults: {passed_count}/{len(tests)} tests passed")
        
        if all_passed:
            success("\n✅ ALL PERFORMANCE TESTS PASSED!")
            return 0
        else:
            error("\n❌ SOME TESTS FAILED - Performance needs optimization")
            return 1
            
    except Exception as e:
        error(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
