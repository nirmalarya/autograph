"""
Test Feature #160: Diagram version count display

This test verifies that diagrams track and display the total number of versions.

Test Steps:
1. Create diagram (version 1)
2. Update diagram 5 times
3. Verify version_count=6
4. View dashboard
5. Verify version count displayed
6. View version history
7. Verify all 6 versions listed
"""

import requests
import json
import time
from datetime import datetime

# Base URLs
AUTH_URL = "http://localhost:8085"
DIAGRAM_URL = "http://localhost:8082"

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(text)
    print("=" * 80 + "\n")

def print_step(step_num, text):
    """Print a test step."""
    print(f"\nStep {step_num}: {text}")
    print("-" * 80)

def print_success(text):
    """Print a success message."""
    print(f"✓ ✓ {text}")

def print_error(text):
    """Print an error message."""
    print(f"✗ ✗ {text}")

def register_and_login():
    """Register a new user and login."""
    print_step(1, "Registering and logging in")
    
    # Generate unique email
    timestamp = int(time.time() * 1000)
    email = f"test_version_count_{timestamp}@example.com"
    password = "SecurePass123!"
    
    # Register
    register_response = requests.post(
        f"{AUTH_URL}/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Version Count Test User"
        }
    )
    
    if register_response.status_code not in [200, 201]:
        print_error(f"Registration failed: {register_response.status_code} - {register_response.text}")
        return None, None, None
    
    print_success(f"User registered: {email}")
    
    # Login
    login_response = requests.post(
        f"{AUTH_URL}/login",
        json={
            "email": email,
            "password": password
        }
    )
    
    if login_response.status_code != 200:
        print_error(f"Login failed: {login_response.text}")
        return None, None, None
    
    login_data = login_response.json()
    access_token = login_data.get("access_token")
    
    # Decode JWT to get user_id
    import base64
    payload = access_token.split('.')[1]
    # Add padding if needed
    padding = 4 - len(payload) % 4
    if padding != 4:
        payload += '=' * padding
    decoded = json.loads(base64.b64decode(payload))
    user_id = decoded.get('sub')
    
    print_success(f"Login successful, user_id: {user_id}")
    
    return email, access_token, user_id

def create_diagram(user_id):
    """Create a new diagram."""
    print_step(2, "Creating diagram (version 1)")
    
    response = requests.post(
        f"{DIAGRAM_URL}/",
        headers={
            "X-User-ID": user_id,
            "Content-Type": "application/json"
        },
        json={
            "title": "Version Count Test Diagram",
            "file_type": "canvas",
            "canvas_data": {"shapes": [{"id": "1", "type": "rect"}]},
            "note_content": None
        }
    )
    
    if response.status_code != 200:
        print_error(f"Failed to create diagram: {response.text}")
        return None
    
    diagram = response.json()
    diagram_id = diagram.get("id")
    version_count = diagram.get("version_count", 0)
    current_version = diagram.get("current_version", 0)
    
    print_success(f"Diagram created: {diagram_id}")
    print_success(f"Initial version_count: {version_count}")
    print_success(f"Initial current_version: {current_version}")
    
    if version_count != 1:
        print_error(f"Expected version_count=1, got {version_count}")
        return None
    
    if current_version != 1:
        print_error(f"Expected current_version=1, got {current_version}")
        return None
    
    return diagram_id

def update_diagram(diagram_id, user_id, update_num):
    """Update a diagram to create a new version."""
    print(f"\nUpdating diagram (creating version {update_num + 1})...")
    
    response = requests.put(
        f"{DIAGRAM_URL}/{diagram_id}",
        headers={
            "X-User-ID": user_id,
            "Content-Type": "application/json"
        },
        json={
            "title": f"Version Count Test Diagram - Update {update_num}",
            "canvas_data": {"shapes": [{"id": str(update_num), "type": "rect"}]},
            "note_content": None,
            "description": f"Update {update_num}"
        }
    )
    
    if response.status_code != 200:
        print_error(f"Failed to update diagram: {response.text}")
        return None
    
    diagram = response.json()
    version_count = diagram.get("version_count", 0)
    current_version = diagram.get("current_version", 0)
    
    print_success(f"Update {update_num} complete: version_count={version_count}, current_version={current_version}")
    
    return diagram

def get_diagram(diagram_id, user_id):
    """Get diagram details."""
    response = requests.get(
        f"{DIAGRAM_URL}/{diagram_id}",
        headers={
            "X-User-ID": user_id
        }
    )
    
    if response.status_code != 200:
        print_error(f"Failed to get diagram: {response.text}")
        return None
    
    return response.json()

def list_diagrams(user_id):
    """List all diagrams."""
    response = requests.get(
        f"{DIAGRAM_URL}/",
        headers={
            "X-User-ID": user_id
        }
    )
    
    if response.status_code != 200:
        print_error(f"Failed to list diagrams: {response.text}")
        return None
    
    return response.json()

def get_versions(diagram_id, user_id):
    """Get version history for a diagram."""
    response = requests.get(
        f"{DIAGRAM_URL}/{diagram_id}/versions",
        headers={
            "X-User-ID": user_id
        }
    )
    
    if response.status_code != 200:
        print_error(f"Failed to get versions: {response.text}")
        return None
    
    return response.json()

def delete_diagram(diagram_id, user_id):
    """Delete a diagram."""
    response = requests.delete(
        f"{DIAGRAM_URL}/{diagram_id}",
        headers={
            "X-User-ID": user_id
        }
    )
    
    if response.status_code != 200:
        print_error(f"Failed to delete diagram: {response.text}")
        return False
    
    return True

def main():
    """Run all tests."""
    print_header("TEST FEATURE #160: DIAGRAM VERSION COUNT DISPLAY")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Register and login
    email, access_token, user_id = register_and_login()
    if not user_id:
        print_error("Failed to register/login")
        return False
    
    # Step 2: Create diagram
    diagram_id = create_diagram(user_id)
    if not diagram_id:
        print_error("Failed to create diagram")
        return False
    
    # Step 3: Update diagram 5 times (to create versions 2-6)
    print_step(3, "Updating diagram 5 times (creating versions 2-6)")
    
    for i in range(1, 6):
        diagram = update_diagram(diagram_id, user_id, i)
        if not diagram:
            print_error(f"Failed to create version {i + 1}")
            return False
        
        expected_version = i + 1
        if diagram.get("version_count") != expected_version:
            print_error(f"Expected version_count={expected_version}, got {diagram.get('version_count')}")
            return False
        
        if diagram.get("current_version") != expected_version:
            print_error(f"Expected current_version={expected_version}, got {diagram.get('current_version')}")
            return False
        
        # Small delay between updates
        time.sleep(0.1)
    
    print_success("All 5 updates completed successfully")
    
    # Step 4: Verify final version_count=6
    print_step(4, "Verifying final version_count=6")
    
    diagram = get_diagram(diagram_id, user_id)
    if not diagram:
        print_error("Failed to get diagram")
        return False
    
    version_count = diagram.get("version_count", 0)
    current_version = diagram.get("current_version", 0)
    
    print(f"Final version_count: {version_count}")
    print(f"Final current_version: {current_version}")
    
    if version_count != 6:
        print_error(f"Expected version_count=6, got {version_count}")
        return False
    
    if current_version != 6:
        print_error(f"Expected current_version=6, got {current_version}")
        return False
    
    print_success("version_count=6 (correct)")
    print_success("current_version=6 (correct)")
    
    # Step 5: View dashboard and verify version count displayed
    print_step(5, "Viewing dashboard and verifying version count displayed")
    
    diagrams_data = list_diagrams(user_id)
    if not diagrams_data:
        print_error("Failed to list diagrams")
        return False
    
    diagrams = diagrams_data.get("diagrams", [])
    
    # Find our test diagram
    test_diagram = None
    for d in diagrams:
        if d.get("id") == diagram_id:
            test_diagram = d
            break
    
    if not test_diagram:
        print_error("Test diagram not found in dashboard")
        return False
    
    dashboard_version_count = test_diagram.get("version_count", 0)
    
    print(f"Dashboard shows version_count: {dashboard_version_count}")
    
    if dashboard_version_count != 6:
        print_error(f"Dashboard shows version_count={dashboard_version_count}, expected 6")
        return False
    
    print_success("Dashboard displays version_count correctly")
    
    # Step 6: View version history
    print_step(6, "Viewing version history")
    
    versions_data = get_versions(diagram_id, user_id)
    if not versions_data:
        print_error("Failed to get version history")
        return False
    
    # Handle both list and dict responses
    if isinstance(versions_data, list):
        versions = versions_data
    else:
        versions = versions_data.get("versions", [])
    
    print(f"Number of versions in history: {len(versions)}")
    
    if len(versions) != 6:
        print_error(f"Expected 6 versions in history, got {len(versions)}")
        return False
    
    print_success("Version history shows all 6 versions")
    
    # Verify version numbers
    version_numbers = sorted([v.get("version_number") for v in versions])
    expected_numbers = [1, 2, 3, 4, 5, 6]
    
    if version_numbers != expected_numbers:
        print_error(f"Version numbers mismatch: {version_numbers} != {expected_numbers}")
        return False
    
    print_success("All version numbers correct (1-6)")
    
    # Display version details
    print("\nVersion History:")
    for v in sorted(versions, key=lambda x: x.get("version_number")):
        print(f"  - Version {v.get('version_number')}: {v.get('description', 'No description')}")
    
    # Cleanup
    print_header("Cleanup")
    print_step(1, "Deleting test diagram")
    
    if delete_diagram(diagram_id, user_id):
        print_success("Test diagram deleted")
    else:
        print_error("Failed to delete test diagram")
    
    # Final summary
    print_header("TEST SUMMARY")
    print("✅ ALL TESTS PASSED!")
    print("\nFeature #160 Status: ✅ READY FOR PRODUCTION")
    print("\nVerified:")
    print("  1. ✓ New diagrams start with version_count=1")
    print("  2. ✓ version_count increments with each update")
    print("  3. ✓ version_count matches number of versions (6)")
    print("  4. ✓ Dashboard displays version_count correctly")
    print("  5. ✓ Version history shows all versions")
    print("  6. ✓ Version numbers are sequential (1-6)")
    
    print(f"\n{'=' * 80}")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 80}\n")
    
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
