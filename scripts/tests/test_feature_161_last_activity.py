#!/usr/bin/env python3
"""
Test Feature #161: Diagram Last Activity Timestamp

This test verifies that the last_activity timestamp is properly tracked and updated
when diagrams are created, viewed, edited, or commented on.

Test Steps:
1. Register and login a test user
2. Create a diagram and verify last_activity is set
3. View the diagram and verify last_activity is updated
4. Edit the diagram and verify last_activity is updated
5. Add a comment and verify last_activity is updated
6. Sort diagrams by last_activity
7. Verify most recently active diagrams appear first
8. Cleanup test data
"""

import requests
import time
from datetime import datetime
import json

# Configuration
BASE_URL = "http://localhost:8085"  # Auth service
DIAGRAM_URL = "http://localhost:8082"  # Diagram service
TEST_EMAIL = f"test_feature_161_{int(time.time())}@example.com"
TEST_PASSWORD = "TestPassword123!"

def print_step(step_num, description):
    """Print a test step with formatting."""
    print(f"\n{'='*80}")
    print(f"STEP {step_num}: {description}")
    print('='*80)

def print_result(success, message):
    """Print test result with formatting."""
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"{status}: {message}")
    return success

def test_feature_161():
    """Test Feature #161: Diagram Last Activity Timestamp."""
    
    print("\n" + "="*80)
    print("FEATURE #161: DIAGRAM LAST ACTIVITY TIMESTAMP TEST")
    print("="*80)
    
    results = []
    user_id = None
    access_token = None
    diagram_id = None
    diagram2_id = None
    
    try:
        # Step 1: Register and login
        print_step(1, "Register and login test user")
        
        # Register
        response = requests.post(
            f"{BASE_URL}/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "full_name": "Test User Feature 161"
            }
        )
        
        if response.status_code == 201:
            data = response.json()
            user_id = data.get("id")  # User ID is directly in the response
            results.append(print_result(True, f"User registered successfully (ID: {user_id})"))
            
            # Now login to get access token
            login_response = requests.post(
                f"{BASE_URL}/login",
                json={
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD
                }
            )
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                access_token = login_data.get("access_token")
                results.append(print_result(True, "Login successful"))
            else:
                results.append(print_result(False, f"Login failed: {login_response.status_code}"))
                return False
        else:
            results.append(print_result(False, f"Registration failed: {response.status_code} - {response.text}"))
            return False
        
        # Step 2: Create a diagram and verify last_activity is set
        print_step(2, "Create diagram and verify last_activity is set")
        
        response = requests.post(
            f"{DIAGRAM_URL}/",
            json={
                "title": "Test Diagram - Last Activity",
                "file_type": "canvas",
                "canvas_data": {"shapes": []},
                "note_content": "Test note content"
            },
            headers={
                "X-User-ID": user_id,
                "Authorization": f"Bearer {access_token}"
            }
        )
        
        if response.status_code in [200, 201]:
            diagram = response.json()
            diagram_id = diagram.get("id")
            last_activity_1 = diagram.get("last_activity")
            
            if last_activity_1:
                results.append(print_result(True, f"Diagram created with last_activity: {last_activity_1}"))
            else:
                print(f"DEBUG: Diagram response: {json.dumps(diagram, indent=2)}")
                results.append(print_result(False, "Diagram created but last_activity is missing"))
        else:
            results.append(print_result(False, f"Diagram creation failed: {response.status_code} - {response.text}"))
            return False
        
        # Wait a moment to ensure timestamps are different
        time.sleep(2)
        
        # Step 3: View the diagram and verify last_activity is updated
        print_step(3, "View diagram and verify last_activity is updated")
        
        response = requests.get(
            f"{DIAGRAM_URL}/{diagram_id}",
            headers={
                "X-User-ID": user_id,
                "Authorization": f"Bearer {access_token}"
            }
        )
        
        if response.status_code == 200:
            diagram = response.json()
            last_activity_2 = diagram.get("last_activity")
            
            if last_activity_2 and last_activity_2 > last_activity_1:
                results.append(print_result(True, f"last_activity updated on view: {last_activity_2}"))
            elif last_activity_2:
                results.append(print_result(False, f"last_activity not updated on view (still {last_activity_2})"))
            else:
                results.append(print_result(False, "last_activity is missing after view"))
        else:
            results.append(print_result(False, f"Failed to get diagram: {response.status_code} - {response.text}"))
        
        # Wait a moment to ensure timestamps are different
        time.sleep(2)
        
        # Step 4: Edit the diagram and verify last_activity is updated
        print_step(4, "Edit diagram and verify last_activity is updated")
        
        response = requests.put(
            f"{DIAGRAM_URL}/{diagram_id}",
            json={
                "title": "Test Diagram - Last Activity (Updated)",
                "canvas_data": {"shapes": [{"type": "rectangle"}]},
                "note_content": "Updated note content"
            },
            headers={
                "X-User-ID": user_id,
                "Authorization": f"Bearer {access_token}"
            }
        )
        
        if response.status_code == 200:
            diagram = response.json()
            last_activity_3 = diagram.get("last_activity")
            
            if last_activity_3 and last_activity_3 > last_activity_2:
                results.append(print_result(True, f"last_activity updated on edit: {last_activity_3}"))
            elif last_activity_3:
                results.append(print_result(False, f"last_activity not updated on edit (still {last_activity_3})"))
            else:
                results.append(print_result(False, "last_activity is missing after edit"))
        else:
            results.append(print_result(False, f"Failed to update diagram: {response.status_code} - {response.text}"))
        
        # Wait a moment to ensure timestamps are different
        time.sleep(2)
        
        # Step 5: Add a comment and verify last_activity is updated
        print_step(5, "Add comment and verify last_activity is updated")
        
        response = requests.post(
            f"{DIAGRAM_URL}/{diagram_id}/comments",
            json={
                "content": "Test comment"
            },
            headers={
                "X-User-ID": user_id,
                "Authorization": f"Bearer {access_token}"
            }
        )
        
        if response.status_code == 200:
            # Get the diagram again to check last_activity
            response = requests.get(
                f"{DIAGRAM_URL}/{diagram_id}",
                headers={
                    "X-User-ID": user_id,
                    "Authorization": f"Bearer {access_token}"
                }
            )
            
            if response.status_code == 200:
                diagram = response.json()
                last_activity_4 = diagram.get("last_activity")
                
                if last_activity_4 and last_activity_4 > last_activity_3:
                    results.append(print_result(True, f"last_activity updated on comment: {last_activity_4}"))
                elif last_activity_4:
                    results.append(print_result(False, f"last_activity not updated on comment (still {last_activity_4})"))
                else:
                    results.append(print_result(False, "last_activity is missing after comment"))
            else:
                results.append(print_result(False, f"Failed to get diagram after comment: {response.status_code}"))
        else:
            results.append(print_result(False, f"Failed to add comment: {response.status_code} - {response.text}"))
        
        # Step 6: Create another diagram with older activity
        print_step(6, "Create second diagram for sorting test")
        
        response = requests.post(
            f"{DIAGRAM_URL}/",
            json={
                "title": "Test Diagram 2 - Older Activity",
                "file_type": "canvas",
                "canvas_data": {"shapes": []},
                "note_content": "Older diagram"
            },
            headers={
                "X-User-ID": user_id,
                "Authorization": f"Bearer {access_token}"
            }
        )
        
        if response.status_code in [200, 201]:
            diagram2 = response.json()
            diagram2_id = diagram2.get("id")
            results.append(print_result(True, f"Second diagram created (ID: {diagram2_id})"))
        else:
            results.append(print_result(False, f"Failed to create second diagram: {response.status_code}"))
        
        # Wait a moment
        time.sleep(2)
        
        # Step 7: Sort diagrams by last_activity
        print_step(7, "Sort diagrams by last_activity and verify order")
        
        response = requests.get(
            f"{DIAGRAM_URL}/?sort_by=last_activity&sort_order=desc",
            headers={
                "X-User-ID": user_id,
                "Authorization": f"Bearer {access_token}"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            diagrams = data.get("diagrams", [])
            
            if len(diagrams) >= 2:
                # First diagram should be the one we just created (diagram2)
                # Second should be the one we've been updating (diagram1)
                first_diagram = diagrams[0]
                second_diagram = diagrams[1]
                
                first_activity = first_diagram.get("last_activity")
                second_activity = second_diagram.get("last_activity")
                
                if first_activity and second_activity and first_activity >= second_activity:
                    results.append(print_result(True, f"Diagrams sorted correctly by last_activity"))
                    print(f"  First: {first_diagram.get('title')} - {first_activity}")
                    print(f"  Second: {second_diagram.get('title')} - {second_activity}")
                else:
                    results.append(print_result(False, "Diagrams not sorted correctly by last_activity"))
            else:
                results.append(print_result(False, f"Expected at least 2 diagrams, got {len(diagrams)}"))
        else:
            results.append(print_result(False, f"Failed to list diagrams: {response.status_code} - {response.text}"))
        
        # Step 8: Cleanup
        print_step(8, "Cleanup test data")
        
        # Delete diagrams
        if diagram_id:
            response = requests.delete(
                f"{DIAGRAM_URL}/{diagram_id}",
                headers={
                    "X-User-ID": user_id,
                    "Authorization": f"Bearer {access_token}"
                }
            )
            if response.status_code == 200:
                results.append(print_result(True, "Test diagram 1 deleted"))
            else:
                results.append(print_result(False, f"Failed to delete diagram 1: {response.status_code}"))
        
        if diagram2_id:
            response = requests.delete(
                f"{DIAGRAM_URL}/{diagram2_id}",
                headers={
                    "X-User-ID": user_id,
                    "Authorization": f"Bearer {access_token}"
                }
            )
            if response.status_code == 200:
                results.append(print_result(True, "Test diagram 2 deleted"))
            else:
                results.append(print_result(False, f"Failed to delete diagram 2: {response.status_code}"))
        
    except Exception as e:
        print(f"\n✗ EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(False)
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r)
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests == 0:
        print("\n🎉 ALL TESTS PASSED!")
        return True
    else:
        print(f"\n❌ {failed_tests} TEST(S) FAILED")
        return False

if __name__ == "__main__":
    success = test_feature_161()
    exit(0 if success else 1)
