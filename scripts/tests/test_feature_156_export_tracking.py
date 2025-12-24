"""
Test Feature #156: Diagram export count tracking

This test verifies:
1. Create diagram
2. Export as PNG
3. Verify export_count=1 in database
4. Export as SVG
5. Verify export_count=2
6. Export as PDF
7. Verify export_count=3
8. View diagram metadata
9. Verify export count displayed
"""

import requests
import json
import time
from datetime import datetime

# Configuration
AUTH_SERVICE_URL = "http://localhost:8085"
DIAGRAM_SERVICE_URL = "http://localhost:8082"
EXPORT_SERVICE_URL = "http://localhost:8097"
API_GATEWAY_URL = "http://localhost:8080"

# Test data
TEST_EMAIL = f"exporttest_{int(time.time())}@example.com"
TEST_PASSWORD = "TestPassword123!"

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(text)
    print("=" * 80 + "\n")

def print_test(text):
    """Print a test step."""
    print(f"[Test] {text}")

def print_success(text):
    """Print a success message."""
    print(f"✅ {text}")

def print_error(text):
    """Print an error message."""
    print(f"❌ {text}")

def register_user():
    """Register a new test user."""
    print_test("User registration...")
    
    response = requests.post(
        f"{AUTH_SERVICE_URL}/register",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "full_name": "Export Test User"
        }
    )
    
    if response.status_code in [200, 201]:
        user_data = response.json()
        print_success(f"User registered: {TEST_EMAIL} (ID: {user_data['id']})")
        return user_data
    else:
        print_error(f"Registration failed: {response.status_code} - {response.text}")
        return None

def login_user():
    """Login and get access token."""
    print_test("User login...")
    
    response = requests.post(
        f"{AUTH_SERVICE_URL}/login",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print_success("User logged in successfully")
        return token
    else:
        print_error(f"Login failed: {response.status_code} - {response.text}")
        return None

def create_diagram(token, user_id):
    """Create a test diagram."""
    print_test("Creating diagram...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }
    
    canvas_data = {
        "shapes": [
            {"id": "shape1", "type": "rectangle", "x": 100, "y": 100, "width": 200, "height": 150}
        ]
    }
    
    response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/",
        headers=headers,
        json={
            "title": "Export Test Diagram",
            "file_type": "canvas",
            "canvas_data": canvas_data
        }
    )
    
    if response.status_code == 200:
        diagram = response.json()
        print_success(f"Diagram created: {diagram['id']}")
        return diagram
    else:
        print_error(f"Diagram creation failed: {response.status_code} - {response.text}")
        return None

def export_diagram(token, user_id, diagram_id, format_type):
    """Export diagram and increment export count."""
    print_test(f"Exporting diagram as {format_type.upper()}...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }
    
    # First, call the export service
    export_response = requests.post(
        f"{EXPORT_SERVICE_URL}/export/{format_type}",
        headers=headers,
        json={
            "diagram_id": diagram_id,
            "canvas_data": {"shapes": []},
            "format": format_type,
            "width": 1920,
            "height": 1080
        }
    )
    
    if export_response.status_code == 200:
        print_success(f"{format_type.upper()} export generated")
        
        # Now increment the export count in diagram service
        increment_response = requests.post(
            f"{DIAGRAM_SERVICE_URL}/{diagram_id}/export",
            headers=headers
        )
        
        if increment_response.status_code == 200:
            data = increment_response.json()
            print_success(f"Export count incremented to {data['export_count']}")
            return data['export_count']
        else:
            print_error(f"Failed to increment export count: {increment_response.status_code}")
            return None
    else:
        print_error(f"Export failed: {export_response.status_code}")
        return None

def get_diagram(token, user_id, diagram_id):
    """Get diagram details."""
    print_test("Fetching diagram details...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }
    
    response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        diagram = response.json()
        print_success(f"Diagram fetched: {diagram['title']}")
        return diagram
    else:
        print_error(f"Failed to fetch diagram: {response.status_code}")
        return None

def verify_export_count(diagram, expected_count):
    """Verify the export count matches expected value."""
    print_test(f"Verifying export count is {expected_count}...")
    
    actual_count = diagram.get('export_count', 0)
    
    if actual_count == expected_count:
        print_success(f"Export count is correct: {actual_count}")
        return True
    else:
        print_error(f"Export count mismatch: expected {expected_count}, got {actual_count}")
        return False

def main():
    """Run all tests."""
    print_header("Testing Feature #156: Diagram export count tracking")
    
    # Test 1: Register user
    user = register_user()
    if not user:
        print_error("Failed to register user")
        return False
    
    user_id = user['id']
    
    # Test 2: Login
    token = login_user()
    if not token:
        print_error("Failed to login")
        return False
    
    # Test 3: Create diagram
    diagram = create_diagram(token, user_id)
    if not diagram:
        print_error("Failed to create diagram")
        return False
    
    diagram_id = diagram['id']
    
    # Verify initial export count is 0
    print_test("Verifying initial export count is 0...")
    if diagram.get('export_count', 0) == 0:
        print_success("Initial export count is 0")
    else:
        print_error(f"Initial export count is not 0: {diagram.get('export_count')}")
    
    # Test 4: Export as PNG
    export_count = export_diagram(token, user_id, diagram_id, 'png')
    if export_count != 1:
        print_error(f"Expected export count 1, got {export_count}")
        return False
    
    # Verify export count in database
    diagram = get_diagram(token, user_id, diagram_id)
    if not verify_export_count(diagram, 1):
        return False
    
    # Test 5: Export as SVG
    export_count = export_diagram(token, user_id, diagram_id, 'svg')
    if export_count != 2:
        print_error(f"Expected export count 2, got {export_count}")
        return False
    
    # Verify export count in database
    diagram = get_diagram(token, user_id, diagram_id)
    if not verify_export_count(diagram, 2):
        return False
    
    # Test 6: Export as PDF
    export_count = export_diagram(token, user_id, diagram_id, 'pdf')
    if export_count != 3:
        print_error(f"Expected export count 3, got {export_count}")
        return False
    
    # Verify export count in database
    diagram = get_diagram(token, user_id, diagram_id)
    if not verify_export_count(diagram, 3):
        return False
    
    # Test 7: Verify export count is displayed in diagram metadata
    print_test("Verifying export count in diagram metadata...")
    if 'export_count' in diagram:
        print_success(f"Export count field exists: {diagram['export_count']}")
    else:
        print_error("Export count field missing from diagram metadata")
        return False
    
    # Test 8: Export multiple times and verify increment
    print_test("Exporting 2 more times to verify continued increment...")
    
    export_diagram(token, user_id, diagram_id, 'png')
    export_diagram(token, user_id, diagram_id, 'svg')
    
    diagram = get_diagram(token, user_id, diagram_id)
    if not verify_export_count(diagram, 5):
        return False
    
    print_header("✅ All tests passed! Feature #156 is working correctly.")
    return True

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print_error(f"Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
