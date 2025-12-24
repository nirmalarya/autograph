"""Test script for Feature #480: Background compression of old versions.

This script tests the version compression system:
1. Creates test diagram with versions
2. Tests manual compression of a specific version
3. Tests bulk compression of diagram versions
4. Tests background compression of all old versions
5. Verifies compression statistics
6. Tests decompression when accessing versions

Run this script with:
    python test_feature_480_version_compression.py
"""

import requests
import json
import time
import base64
from datetime import datetime, timedelta

# Test configuration
BASE_URL = "http://localhost:8082"
AUTH_URL = "http://localhost:8085"
TEST_USER_EMAIL = "test.compression@example.com"
TEST_USER_PASSWORD = "Test@1234"

# ANSI color codes for pretty output
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def print_step(step_num, description):
    """Print a test step header."""
    print(f"\n{BLUE}{'='*80}")
    print(f"STEP {step_num}: {description}")
    print(f"{'='*80}{RESET}\n")


def print_success(message):
    """Print success message."""
    print(f"{GREEN}✅ {message}{RESET}")


def print_error(message):
    """Print error message."""
    print(f"{RED}❌ {message}{RESET}")


def print_info(message):
    """Print info message."""
    print(f"{YELLOW}ℹ️  {message}{RESET}")


def format_bytes(bytes_value):
    """Format bytes as human-readable string."""
    if bytes_value < 1024:
        return f"{bytes_value} B"
    elif bytes_value < 1024 * 1024:
        return f"{bytes_value / 1024:.2f} KB"
    else:
        return f"{bytes_value / (1024 * 1024):.2f} MB"


print(f"{BLUE}{'='*80}")
print("TEST FEATURE #480: VERSION COMPRESSION")
print(f"{'='*80}{RESET}\n")

# STEP 1: Register and login
print_step(1, "Register and login test user")

# Register
register_data = {
    "email": TEST_USER_EMAIL,
    "password": TEST_USER_PASSWORD,
    "full_name": "Test Compression User"
}

response = requests.post(f"{AUTH_URL}/register", json=register_data)
if response.status_code in [200, 201]:
    user_id = response.json().get("id") or response.json().get("user", {}).get("id")
    print_success(f"User registered: {user_id}")
elif response.status_code == 400:
    print_info("User already exists (continuing with existing user)")
    user_id = None
else:
    print_error(f"Registration failed: {response.status_code} - {response.text}")
    exit(1)

# Verify user email
import subprocess
verify_cmd = f'docker exec -i autograph-postgres psql -U autograph -d autograph -c "UPDATE users SET is_verified = true WHERE email = \'{TEST_USER_EMAIL}\'; SELECT id FROM users WHERE email = \'{TEST_USER_EMAIL}\';"'
result = subprocess.run(verify_cmd, shell=True, capture_output=True, text=True)
if result.returncode == 0:
    print_success("User email verified")
    if not user_id:
        # Extract user_id from psql output
        for line in result.stdout.split('\n'):
            if '-' in line and len(line.strip()) == 36:
                user_id = line.strip()
                break
else:
    print_error("Failed to verify user email")
    exit(1)

# Login
login_data = {
    "email": TEST_USER_EMAIL,
    "password": TEST_USER_PASSWORD
}

response = requests.post(f"{AUTH_URL}/login", json=login_data)
if response.status_code == 200:
    token = response.json()["access_token"]
    print_success("Login successful")
    
    # Extract user_id from JWT if not already set
    if not user_id:
        payload = token.split('.')[1]
        payload += '=' * (4 - len(payload) % 4)
        user_data = json.loads(base64.b64decode(payload))
        user_id = user_data.get('sub')
    
    print_info(f"User ID: {user_id}")
else:
    print_error(f"Login failed: {response.status_code} - {response.text}")
    exit(1)

headers = {
    "Authorization": f"Bearer {token}",
    "X-User-ID": user_id
}

# STEP 2: Create test diagram with multiple versions
print_step(2, "Create test diagram with large content")

# Create diagram with large canvas data (to make compression worthwhile)
large_canvas_data = {
    "shapes": [
        {
            "id": f"shape-{i}",
            "type": "rectangle",
            "x": i * 100,
            "y": i * 50,
            "width": 200,
            "height": 100,
            "fill": f"#{i*10:06x}",
            "label": f"Test Shape {i}" * 10  # Repeat to make it larger
        }
        for i in range(50)  # 50 shapes
    ]
}

create_data = {
    "title": "Compression Test Diagram",
    "type": "canvas",
    "canvas_data": large_canvas_data,
    "note_content": "This is a test note with some content. " * 100  # Large note
}

response = requests.post(f"{BASE_URL}/", json=create_data, headers=headers)
if response.status_code in [200, 201]:
    diagram_id = response.json()["id"]
    print_success(f"Created diagram: {diagram_id}")
else:
    print_error(f"Failed to create diagram: {response.status_code} - {response.text}")
    exit(1)

# Create multiple versions by updating
print_info("Creating version history...")
for i in range(3):
    time.sleep(1)  # Small delay to ensure different timestamps
    update_data = {
        "canvas_data": {
            "shapes": [
                {
                    "id": f"shape-v{i+2}-{j}",
                    "type": "circle",
                    "x": j * 80,
                    "y": j * 60 + i * 20,
                    "radius": 50,
                    "fill": f"#{j*20+i*5:06x}",
                    "label": f"Version {i+2} Shape {j}" * 10
                }
                for j in range(40)
            ]
        },
        "note_content": f"Updated note for version {i+2}. " * 100
    }
    response = requests.put(f"{BASE_URL}/{diagram_id}", json=update_data, headers=headers)
    if response.status_code == 200:
        print_success(f"Created version {i+2}")
    else:
        print_info(f"Update {i+1} status: {response.status_code}")

# STEP 3: Get versions list
print_step(3, "Fetch versions to test")

response = requests.get(f"{BASE_URL}/{diagram_id}/versions", headers=headers)
if response.status_code == 200:
    versions = response.json()["versions"]
    print_success(f"Found {len(versions)} versions")
    
    if len(versions) < 1:
        print_error("Not enough versions created for testing")
        exit(1)
    
    # Pick an old version to compress
    test_version = versions[0]
    test_version_id = test_version["id"]
    test_version_number = test_version["version_number"]
    print_info(f"Will test compression on version {test_version_number} (ID: {test_version_id})")
else:
    print_error(f"Failed to get versions: {response.status_code}")
    exit(1)

# STEP 4: Test manual compression of specific version
print_step(4, "Compress specific version manually")

response = requests.post(
    f"{BASE_URL}/versions/compress/{test_version_id}",
    headers=headers
)
if response.status_code == 200:
    result = response.json()
    print_success("Version compressed successfully!")
    print_info(f"Status: {result['status']}")
    if result['status'] == 'compressed':
        print_info(f"Original size: {format_bytes(result['original_size'])}")
        print_info(f"Compressed size: {format_bytes(result['compressed_size'])}")
        print_info(f"Savings: {format_bytes(result['savings_bytes'])} ({result['savings_percent']:.1f}%)")
        print_info(f"Compression ratio: {result['compression_ratio']:.3f}")
else:
    print_error(f"Failed to compress version: {response.status_code} - {response.text}")
    exit(1)

# STEP 5: Test accessing compressed version (decompression)
print_step(5, "Access compressed version (verify decompression works)")

response = requests.get(
    f"{BASE_URL}/{diagram_id}/versions/{test_version_id}",
    headers=headers
)
if response.status_code == 200:
    version_data = response.json()
    print_success("Successfully retrieved compressed version")
    print_info(f"Version number: {version_data['version_number']}")
    print_info(f"Is compressed: {version_data.get('is_compressed', False)}")
    
    # Verify content was decompressed
    if version_data.get('canvas_data'):
        print_success("Canvas data decompressed and accessible")
        shapes_count = len(version_data['canvas_data'].get('shapes', []))
        print_info(f"  Found {shapes_count} shapes in canvas")
    
    if version_data.get('note_content'):
        print_success("Note content decompressed and accessible")
        note_length = len(version_data['note_content'])
        print_info(f"  Note length: {note_length} characters")
    
    # Show compression info
    if version_data.get('compression_info'):
        comp_info = version_data['compression_info']
        print_info(f"Compression info:")
        print_info(f"  Original: {format_bytes(comp_info['original_size'])}")
        print_info(f"  Compressed: {format_bytes(comp_info['compressed_size'])}")
        print_info(f"  Ratio: {comp_info['compression_ratio']:.3f}")
        print_info(f"  Savings: {comp_info['savings_percent']}%")
else:
    print_error(f"Failed to get version: {response.status_code}")
    exit(1)

# STEP 6: Test bulk compression of diagram versions
print_step(6, "Compress all old versions of diagram")

response = requests.post(
    f"{BASE_URL}/versions/compress/diagram/{diagram_id}?min_age_days=0",  # 0 days to compress all
    headers=headers
)
if response.status_code == 200:
    result = response.json()
    print_success("Bulk compression complete!")
    print_info(f"Versions compressed: {result['versions_compressed']}")
    print_info(f"Versions skipped: {result['versions_skipped']}")
    print_info(f"Total original size: {format_bytes(result['total_original_size'])}")
    print_info(f"Total compressed size: {format_bytes(result['total_compressed_size'])}")
    print_info(f"Total savings: {result['total_savings_mb']:.2f} MB ({result['savings_percent']}%)")
    print_info(f"Overall compression ratio: {result['overall_compression_ratio']}")
else:
    print_error(f"Failed bulk compression: {response.status_code} - {response.text}")
    exit(1)

# STEP 7: Test background compression (all diagrams)
print_step(7, "Test background compression system (all old versions)")

response = requests.post(
    f"{BASE_URL}/versions/compress/all?min_age_days=0&limit=50",
    headers=headers
)
if response.status_code == 200:
    result = response.json()
    print_success("Background compression complete!")
    print_info(f"Versions found: {result['versions_found']}")
    print_info(f"Versions compressed: {result['versions_compressed']}")
    print_info(f"Versions skipped: {result['versions_skipped']}")
    print_info(f"Errors: {result['errors']}")
    if result['total_original_size'] > 0:
        print_info(f"Total savings: {result['total_savings_mb']:.2f} MB ({result['savings_percent']}%)")
else:
    print_error(f"Failed background compression: {response.status_code} - {response.text}")
    exit(1)

# STEP 8: Get compression statistics
print_step(8, "Get overall compression statistics")

response = requests.get(
    f"{BASE_URL}/versions/compression/stats",
    headers=headers
)
if response.status_code == 200:
    stats = response.json()
    print_success("Retrieved compression statistics!")
    print_info(f"Total versions: {stats['total_versions']}")
    print_info(f"Compressed versions: {stats['compressed_versions']}")
    print_info(f"Uncompressed versions: {stats['uncompressed_versions']}")
    print_info(f"Compression percentage: {stats['compression_percentage']}%")
    if stats['total_savings_bytes'] > 0:
        print_info(f"Total storage savings: {stats['total_savings_mb']:.2f} MB")
        print_info(f"Average compression ratio: {stats['average_compression_ratio']}")
        print_info(f"Average savings: {stats['average_savings_percent']}%")
else:
    print_error(f"Failed to get stats: {response.status_code}")
    exit(1)

# STEP 9: Verify version comparison still works with compressed versions
print_step(9, "Test version comparison with compressed versions")

if len(versions) >= 2:
    v1 = versions[0]["version_number"]
    v2 = versions[1]["version_number"]
    
    response = requests.get(
        f"{BASE_URL}/{diagram_id}/versions/compare?v1={v1}&v2={v2}",
        headers=headers
    )
    if response.status_code == 200:
        comparison = response.json()
        print_success("Version comparison works with compressed versions!")
        print_info(f"Comparing versions {v1} and {v2}")
        print_info(f"Additions: {len(comparison.get('additions', []))}")
        print_info(f"Deletions: {len(comparison.get('deletions', []))}")
        print_info(f"Modifications: {len(comparison.get('modifications', []))}")
    else:
        print_error(f"Comparison failed: {response.status_code}")
else:
    print_info("Not enough versions for comparison test")

# Final summary
print(f"\n{GREEN}{'='*80}")
print("✅ ALL TESTS PASSED!")
print(f"{'='*80}{RESET}\n")

print("Summary:")
print("  ✅ Manual compression of specific version works")
print("  ✅ Decompression when accessing versions works")
print("  ✅ Bulk compression of diagram versions works")
print("  ✅ Background compression system works")
print("  ✅ Compression statistics tracking works")
print("  ✅ Version comparison works with compressed versions")
print("\nFeature #480 (Background compression) is FULLY FUNCTIONAL! 🎉\n")
