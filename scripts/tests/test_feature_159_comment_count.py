"""
Test Feature #159: Diagram Comment Count Badge

This test verifies:
1. Diagrams start with comment_count=0
2. Adding comments increments comment_count
3. Deleting comments decrements comment_count
4. Comment count is displayed on dashboard
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8080/api"
AUTH_URL = "http://localhost:8085"
DIAGRAM_URL = "http://localhost:8082"

def print_header(title):
    """Print a formatted test header."""
    print("\n" + "="*80)
    print(title)
    print("="*80)

def print_step(step_num, description):
    """Print a test step."""
    print(f"\nStep {step_num}: {description}")

def print_success(message):
    """Print success message."""
    print(f"✓ {message}")

def print_error(message):
    """Print error message."""
    print(f"✗ {message}")

def print_info(key, value):
    """Print info message."""
    print(f"  - {key}: {value}")


def test_comment_count():
    """Test Feature #159: Diagram comment count badge."""
    
    print_header("TEST: Feature #159 - Diagram Comment Count Badge")
    
    # Generate unique email for this test run
    timestamp = int(time.time())
    test_email = f"test_comments_{timestamp}@example.com"
    test_password = "SecurePass123!"
    
    # =========================================================================
    # TEST 1: Register and login
    # =========================================================================
    print_header("TEST 1: Register Test User")
    print_step(1, f"Registering user: {test_email}")
    
    register_response = requests.post(
        f"{AUTH_URL}/register",
        json={
            "email": test_email,
            "password": test_password,
            "full_name": "Test User"
        }
    )
    
    if register_response.status_code not in [200, 201]:
        print_error(f"Registration failed: {register_response.status_code}")
        print_error(f"Response: {register_response.text}")
        return False
    
    print_success("User registered successfully")
    
    # Login
    print_step(2, "Logging in")
    login_response = requests.post(
        f"{AUTH_URL}/login",
        json={
            "email": test_email,
            "password": test_password
        }
    )
    
    if login_response.status_code != 200:
        print_error(f"Login failed: {login_response.status_code}")
        print_error(f"Response: {login_response.text}")
        return False
    
    login_data = login_response.json()
    access_token = login_data.get("access_token")
    
    if not access_token:
        print_error("Missing access_token in login response")
        return False
    
    # Decode JWT to get user_id (from 'sub' claim)
    import base64
    try:
        # Split token and decode payload
        parts = access_token.split('.')
        if len(parts) != 3:
            print_error("Invalid JWT format")
            return False
        
        # Add padding if needed
        payload = parts[1]
        padding = len(payload) % 4
        if padding:
            payload += '=' * (4 - padding)
        
        decoded = base64.b64decode(payload)
        payload_data = json.loads(decoded)
        user_id = payload_data.get("sub")
        
        if not user_id:
            print_error("Missing 'sub' claim in JWT")
            return False
    except Exception as e:
        print_error(f"Failed to decode JWT: {e}")
        return False
    
    print_success("Login successful")
    print_info("User ID", user_id)
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-User-ID": user_id
    }
    
    # =========================================================================
    # TEST 2: Create diagram and verify comment_count=0
    # =========================================================================
    print_header("TEST 2: Create Diagram and Verify comment_count=0")
    print_step(1, "Creating test diagram")
    
    create_response = requests.post(
        f"{DIAGRAM_URL}/",
        headers=headers,
        json={
            "title": "Test Diagram for Comments",
            "file_type": "canvas",
            "canvas_data": {"elements": []},
            "note_content": ""
        }
    )
    
    if create_response.status_code not in [200, 201]:
        print_error(f"Create diagram failed: {create_response.status_code}")
        print_error(f"Response: {create_response.text}")
        return False
    
    diagram_data = create_response.json()
    diagram_id = diagram_data.get("id")
    
    if not diagram_id:
        print_error("No diagram ID in response")
        return False
    
    print_success(f"Diagram created with ID: {diagram_id}")
    
    print_step(2, "Verifying comment_count=0")
    
    # Get diagram details
    get_response = requests.get(
        f"{DIAGRAM_URL}/{diagram_id}",
        headers=headers
    )
    
    if get_response.status_code != 200:
        print_error(f"Get diagram failed: {get_response.status_code}")
        return False
    
    diagram = get_response.json()
    comment_count = diagram.get("comment_count", None)
    
    if comment_count is None:
        print_error("comment_count field not in response")
        print_info("Response fields", list(diagram.keys()))
        return False
    
    if comment_count != 0:
        print_error(f"Expected comment_count=0, got {comment_count}")
        return False
    
    print_success("✓ comment_count=0 (correct)")
    
    # =========================================================================
    # TEST 3: Add comment and verify comment_count=1
    # =========================================================================
    print_header("TEST 3: Add Comment and Verify comment_count=1")
    print_step(1, "Adding first comment")
    
    comment_response = requests.post(
        f"{DIAGRAM_URL}/{diagram_id}/comments",
        headers=headers,
        params={"content": "First comment"}
    )
    
    if comment_response.status_code not in [200, 201]:
        print_error(f"Add comment failed: {comment_response.status_code}")
        print_error(f"Response: {comment_response.text}")
        return False
    
    comment_data = comment_response.json()
    print_success("Comment added successfully")
    print_info("New comment_count", comment_data.get("comment_count"))
    
    if comment_data.get("comment_count") != 1:
        print_error(f"Expected comment_count=1, got {comment_data.get('comment_count')}")
        return False
    
    print_success("✓ comment_count=1 (correct)")
    
    # =========================================================================
    # TEST 4: Add 5 more comments and verify comment_count=6
    # =========================================================================
    print_header("TEST 4: Add 5 More Comments and Verify comment_count=6")
    
    for i in range(2, 7):
        print_step(i-1, f"Adding comment #{i}")
        
        comment_response = requests.post(
            f"{DIAGRAM_URL}/{diagram_id}/comments",
            headers=headers,
            params={"content": f"Comment #{i}"}
        )
        
        if comment_response.status_code not in [200, 201]:
            print_error(f"Add comment failed: {comment_response.status_code}")
            return False
        
        comment_data = comment_response.json()
        print_success(f"Comment #{i} added (count={comment_data.get('comment_count')})")
    
    print_step(6, "Verifying final comment_count=6")
    
    # Get diagram details
    get_response = requests.get(
        f"{DIAGRAM_URL}/{diagram_id}",
        headers=headers
    )
    
    if get_response.status_code != 200:
        print_error(f"Get diagram failed: {get_response.status_code}")
        return False
    
    diagram = get_response.json()
    final_count = diagram.get("comment_count", 0)
    
    if final_count != 6:
        print_error(f"Expected comment_count=6, got {final_count}")
        return False
    
    print_success("✓ comment_count=6 (correct)")
    
    # =========================================================================
    # TEST 5: View dashboard and verify comment count displayed
    # =========================================================================
    print_header("TEST 5: View Dashboard and Verify Comment Count Displayed")
    print_step(1, "Fetching diagrams from dashboard")
    
    list_response = requests.get(
        f"{DIAGRAM_URL}/",
        headers=headers,
        params={"page": 1, "page_size": 10}
    )
    
    if list_response.status_code != 200:
        print_error(f"List diagrams failed: {list_response.status_code}")
        return False
    
    list_data = list_response.json()
    diagrams = list_data.get("diagrams", [])
    
    # Find our test diagram
    test_diagram = None
    for d in diagrams:
        if d.get("id") == diagram_id:
            test_diagram = d
            break
    
    if not test_diagram:
        print_error("Test diagram not found in list")
        return False
    
    print_success("Test diagram found in list")
    
    dashboard_count = test_diagram.get("comment_count", None)
    
    if dashboard_count is None:
        print_error("comment_count not in dashboard response")
        return False
    
    if dashboard_count != 6:
        print_error(f"Dashboard shows comment_count={dashboard_count}, expected 6")
        return False
    
    print_success("✓ Comment count badge displayed correctly on dashboard (6 comments)")
    
    # =========================================================================
    # TEST 6: Delete 2 comments and verify comment_count=4
    # =========================================================================
    print_header("TEST 6: Delete 2 Comments and Verify comment_count=4")
    
    print_step(1, "Deleting first comment")
    
    delete_response = requests.delete(
        f"{DIAGRAM_URL}/{diagram_id}/comments/comment-1",
        headers=headers
    )
    
    if delete_response.status_code not in [200, 204]:
        print_error(f"Delete comment failed: {delete_response.status_code}")
        # Continue anyway - the endpoint might not store actual comment IDs
    else:
        delete_data = delete_response.json()
        print_success(f"Comment deleted (count={delete_data.get('comment_count')})")
    
    print_step(2, "Deleting second comment")
    
    delete_response = requests.delete(
        f"{DIAGRAM_URL}/{diagram_id}/comments/comment-2",
        headers=headers
    )
    
    if delete_response.status_code not in [200, 204]:
        print_error(f"Delete comment failed: {delete_response.status_code}")
    else:
        delete_data = delete_response.json()
        print_success(f"Comment deleted (count={delete_data.get('comment_count')})")
    
    print_step(3, "Verifying final comment_count=4")
    
    # Get diagram details
    get_response = requests.get(
        f"{DIAGRAM_URL}/{diagram_id}",
        headers=headers
    )
    
    if get_response.status_code != 200:
        print_error(f"Get diagram failed: {get_response.status_code}")
        return False
    
    diagram = get_response.json()
    final_count = diagram.get("comment_count", 0)
    
    if final_count != 4:
        print_error(f"Expected comment_count=4, got {final_count}")
        return False
    
    print_success("✓ comment_count=4 after deleting 2 comments (correct)")
    
    # =========================================================================
    # Cleanup
    # =========================================================================
    print_header("Cleanup")
    print_step(1, "Deleting test diagram")
    
    delete_response = requests.delete(
        f"{DIAGRAM_URL}/{diagram_id}",
        headers=headers
    )
    
    if delete_response.status_code in [200, 204]:
        print_success("Test diagram deleted")
    else:
        print_error(f"Failed to delete diagram: {delete_response.status_code}")
    
    return True


def main():
    """Main test function."""
    print("\n")
    print("="*80)
    print("FEATURE #159: DIAGRAM COMMENT COUNT BADGE - COMPREHENSIVE TEST")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    try:
        success = test_comment_count()
        
        print("\n")
        print("="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        if success:
            print("✅ ALL TESTS PASSED!")
            print("\nFeature #159 Status: ✅ READY FOR PRODUCTION")
            print("\nVerified:")
            print("  1. ✓ Diagrams start with comment_count=0")
            print("  2. ✓ Adding comments increments comment_count")
            print("  3. ✓ Comment count updates correctly (1, 6)")
            print("  4. ✓ Comment count displayed on dashboard")
            print("  5. ✓ Deleting comments decrements comment_count")
            print("  6. ✓ Final count correct after deletions (4)")
            return 0
        else:
            print("❌ TESTS FAILED")
            print("\nPlease fix the issues above and rerun the test.")
            return 1
            
    except Exception as e:
        print("\n")
        print("="*80)
        print("UNEXPECTED ERROR")
        print("="*80)
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        print("\n" + "="*80)
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)


if __name__ == "__main__":
    exit(main())
