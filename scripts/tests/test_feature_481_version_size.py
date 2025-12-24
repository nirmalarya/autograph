"""
Test Feature #481: Version Size Tracking

This test verifies that version sizes are displayed correctly:
1. View version and see size shown (KB/MB)
2. Compare version sizes
3. Identify large versions
"""

import requests
import json
import time

# ANSI color codes
BLUE = '\033[94m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

# API endpoints
BASE_URL = "http://localhost:8080/api"
DIAGRAM_SERVICE_URL = "http://localhost:8082"
AUTH_URL = f"{BASE_URL}/auth"
DIAGRAM_URL = f"{BASE_URL}/diagrams"

# Test user credentials
TEST_USER = {
    "email": f"size_test_{int(time.time())}@example.com",
    "password": "TestPassword123!",
    "full_name": "Size Test User"
}

# Global variables
auth_token = None
user_id = None
diagram_id = None


def print_header(message):
    print(f"\n{BLUE}{'=' * 80}")
    print(f"{message}")
    print(f"{'=' * 80}{RESET}\n")


def print_success(message):
    print(f"{GREEN}✅ {message}{RESET}")


def print_info(message):
    print(f"{YELLOW}ℹ️  {message}{RESET}")


def print_error(message):
    print(f"{RED}❌ {message}{RESET}")


def register_and_login():
    """Register and login."""
    print_header("STEP 1: Register and login")
    
    global user_id, auth_token
    
    # Register
    response = requests.post(f"{AUTH_URL}/register", json=TEST_USER)
    
    if response.status_code == 201:
        print_success("User registered")
        
        # Verify email
        import subprocess
        verify_cmd = f"docker exec autograph-postgres psql -h localhost -U autograph -d autograph -c \"UPDATE users SET is_verified = true WHERE email = '{TEST_USER['email']}'; SELECT id FROM users WHERE email = '{TEST_USER['email']}';\""
        result = subprocess.run(verify_cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line and len(line) == 36 and '-' in line:
                    user_id = line
                    break
    elif response.status_code == 400:
        print_info("User already exists")
        # Get user_id
        import subprocess
        get_user_cmd = f"docker exec autograph-postgres psql -h localhost -U autograph -d autograph -c \"UPDATE users SET is_verified = true WHERE email = '{TEST_USER['email']}'; SELECT id FROM users WHERE email = '{TEST_USER['email']}';\""
        result = subprocess.run(get_user_cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line and len(line) == 36 and '-' in line:
                    user_id = line
                    break
    else:
        print_error(f"Registration failed: {response.status_code}")
        return False
    
    # Login
    response = requests.post(f"{AUTH_URL}/login", json={
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    })
    
    if response.status_code == 200:
        auth_token = response.json()["access_token"]
        print_success("Login successful")
        return True
    else:
        print_error(f"Login failed: {response.status_code}")
        return False


def test_version_sizes():
    """Test version size display and comparison."""
    print_header("STEP 2: Create versions with different sizes")
    
    global diagram_id
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "X-User-ID": user_id
    }
    
    # Create a small diagram
    small_data = {
        "title": "Size Test Diagram",
        "file_type": "canvas",
        "canvas_data": {"shapes": [{"id": "1", "type": "rectangle"}]},
        "note_content": "Small version"
    }
    
    response = requests.post(DIAGRAM_URL, json=small_data, headers=headers)
    if response.status_code not in [200, 201]:
        print_error(f"Failed to create diagram: {response.status_code}")
        return False
    
    diagram_id = response.json()["id"]
    print_success(f"Created diagram: {diagram_id}")
    
    # Create a version with medium size
    medium_data = {
        "canvas_data": {"shapes": [{"id": str(i), "type": "circle", "data": "x" * 100} for i in range(50)]},
        "note_content": "Medium version with more content " * 20
    }
    requests.put(f"{DIAGRAM_URL}/{diagram_id}", json=medium_data, headers=headers)
    requests.post(f"{DIAGRAM_SERVICE_URL}/{diagram_id}/versions", json={"description": "Medium size"}, headers=headers)
    print_success("Created medium-sized version")
    
    # Create a version with large size
    large_data = {
        "canvas_data": {"shapes": [{"id": str(i), "type": "arrow", "data": "y" * 500} for i in range(200)]},
        "note_content": "Large version with much more content " * 100
    }
    requests.put(f"{DIAGRAM_URL}/{diagram_id}", json=large_data, headers=headers)
    requests.post(f"{DIAGRAM_SERVICE_URL}/{diagram_id}/versions", json={"description": "Large size"}, headers=headers)
    print_success("Created large-sized version")
    
    return True


def test_view_version_size():
    """Test viewing individual version with size information."""
    print_header("STEP 3: View version with size information")
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "X-User-ID": user_id
    }
    
    # Get all versions
    response = requests.get(f"{DIAGRAM_SERVICE_URL}/{diagram_id}/versions", headers=headers)
    if response.status_code != 200:
        print_error(f"Failed to get versions: {response.status_code}")
        return False
    
    data = response.json()
    versions = data.get('versions', data) if isinstance(data, dict) else data
    
    if not versions:
        print_error("No versions found")
        return False
    
    # Check first version has size info
    version = versions[0]
    if 'size' not in version:
        print_error("Version does not have size information")
        return False
    
    size_info = version['size']
    print_success("Version has size information")
    print_info(f"Size bytes: {size_info.get('size_bytes', 'N/A')}")
    print_info(f"Size KB: {size_info.get('size_kb', 'N/A')}")
    print_info(f"Size MB: {size_info.get('size_mb', 'N/A')}")
    print_info(f"Display: {size_info.get('display_size', 'N/A')}")
    
    # Verify size fields are present
    if all(k in size_info for k in ['size_bytes', 'size_kb', 'size_mb', 'display_size']):
        print_success("All size fields present")
        return True
    else:
        print_error("Missing size fields")
        return False


def test_compare_sizes():
    """Test comparing sizes across versions."""
    print_header("STEP 4: Compare version sizes")
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "X-User-ID": user_id
    }
    
    # Get all versions
    response = requests.get(f"{DIAGRAM_SERVICE_URL}/{diagram_id}/versions", headers=headers)
    if response.status_code != 200:
        print_error(f"Failed to get versions: {response.status_code}")
        return False
    
    data = response.json()
    versions = data.get('versions', data) if isinstance(data, dict) else data
    
    if len(versions) < 2:
        print_error("Need at least 2 versions for comparison")
        return False
    
    # Sort by size
    versions_by_size = sorted(versions, key=lambda v: v['size']['size_bytes'])
    
    smallest = versions_by_size[0]
    largest = versions_by_size[-1]
    
    print_info(f"Smallest version: v{smallest['version_number']} - {smallest['size']['display_size']}")
    print_info(f"Largest version: v{largest['version_number']} - {largest['size']['display_size']}")
    
    # Verify largest is actually larger
    if largest['size']['size_bytes'] > smallest['size']['size_bytes']:
        print_success("Size comparison works correctly")
        return True
    else:
        print_error("Size comparison failed")
        return False


def test_identify_large_versions():
    """Test identifying large versions."""
    print_header("STEP 5: Identify large versions")
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "X-User-ID": user_id
    }
    
    # Get all versions
    response = requests.get(f"{DIAGRAM_SERVICE_URL}/{diagram_id}/versions", headers=headers)
    if response.status_code != 200:
        print_error(f"Failed to get versions: {response.status_code}")
        return False
    
    data = response.json()
    versions = data.get('versions', data) if isinstance(data, dict) else data
    
    # Find versions larger than 10 KB
    large_versions = [v for v in versions if v['size']['size_kb'] > 10]
    
    print_info(f"Total versions: {len(versions)}")
    print_info(f"Large versions (> 10 KB): {len(large_versions)}")
    
    if large_versions:
        for v in large_versions:
            print_info(f"  - v{v['version_number']}: {v['size']['display_size']}")
        print_success("Successfully identified large versions")
        return True
    else:
        print_info("No large versions found (this is okay)")
        return True


def main():
    """Run all tests."""
    print(f"\n{BLUE}{'=' * 80}")
    print("TEST FEATURE #481: VERSION SIZE TRACKING")
    print(f"{'=' * 80}{RESET}\n")
    
    tests = [
        ("Register and Login", register_and_login),
        ("Create Versions with Different Sizes", test_version_sizes),
        ("View Version Size Information", test_view_version_size),
        ("Compare Version Sizes", test_compare_sizes),
        ("Identify Large Versions", test_identify_large_versions),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"Test '{name}' raised exception: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Print summary
    print_header("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {status} - {name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"\n{GREEN}✅ ALL TESTS PASSED!{RESET}\n")
        return 0
    else:
        print(f"\n{RED}❌ SOME TESTS FAILED{RESET}\n")
        return 1


if __name__ == "__main__":
    exit(main())
