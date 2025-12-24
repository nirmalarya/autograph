#!/usr/bin/env python3
"""
Test script for Feature #23: PostgreSQL versions table with auto-incrementing version numbers

This script tests:
1. Create file with initial version
2. Verify version_number = 1
3. Update file to create version 2
4. Verify version_number auto-increments to 2
5. Create 10 more versions
6. Verify version_number reaches 12
7. Test version ordering by version_number
"""

import requests
import json
import sys
from typing import Dict, Any

# Service URLs
API_GATEWAY_URL = "http://localhost:8080"
DIAGRAM_SERVICE_URL = "http://localhost:8082"

# Test configuration
TEST_USER_EMAIL = "version-test@example.com"
TEST_USER_PASSWORD = "SecurePass123!"
TEST_USER_NAME = "Version Test User"

def print_step(step_num: int, description: str):
    """Print test step header."""
    print(f"\n{'='*70}")
    print(f"Step {step_num}: {description}")
    print('='*70)

def print_result(passed: bool, message: str):
    """Print test result."""
    status = "✓ PASSED" if passed else "✗ FAILED"
    print(f"{status}: {message}")

def register_and_login() -> Dict[str, Any]:
    """Register a test user and login to get access token and user_id."""
    user_id = None
    
    # Register
    register_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
        "full_name": TEST_USER_NAME
    }
    
    response = requests.post(
        f"{API_GATEWAY_URL}/api/auth/register",
        json=register_data
    )
    
    if response.status_code == 201 or response.status_code == 200:
        user_data = response.json()
        user_id = user_data.get("id")
        print(f"Registered user: {user_id}")
    else:
        # User might already exist, try to login
        print("User already exists, logging in...")
    
    # Login
    login_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }
    
    response = requests.post(
        f"{API_GATEWAY_URL}/api/auth/login",
        json=login_data
    )
    
    if response.status_code != 200:
        raise Exception(f"Login failed: {response.text}")
    
    login_response = response.json()
    access_token = login_response["access_token"]
    
    # If we don't have user_id from registration, we need to get it another way
    # For now, the auth service should return it in the login response
    # Let's check what's in the response
    print(f"Login response keys: {login_response.keys()}")
    
    # Try to get user_id from various places
    if "user_id" in login_response:
        user_id = login_response["user_id"]
    elif "id" in login_response:
        user_id = login_response["id"]
    elif user_id is None:
        # If still None, make a request to get current user
        headers = {"Authorization": f"Bearer {access_token}"}
        me_response = requests.get(f"{API_GATEWAY_URL}/api/auth/me", headers=headers)
        if me_response.status_code == 200:
            user_data = me_response.json()
            user_id = user_data["id"]
        else:
            raise Exception("Could not determine user_id")
    
    print(f"Logged in successfully as user: {user_id}")
    
    return {
        "access_token": access_token,
        "user_id": user_id
    }

def test_version_autoincrement():
    """Main test function."""
    print("="*70)
    print("Feature #23: PostgreSQL versions table with auto-incrementing version numbers")
    print("="*70)
    
    results = {
        "passed": 0,
        "failed": 0,
        "tests": []
    }
    
    try:
        # Login to get credentials
        auth = register_and_login()
        access_token = auth["access_token"]
        user_id = auth["user_id"]
        
        # Headers for authenticated requests
        headers = {
            "X-User-ID": user_id,
            "Authorization": f"Bearer {access_token}"
        }
        
        # =================================================================
        # Step 1: Create file with initial version
        # =================================================================
        print_step(1, "Create file with initial version")
        
        create_data = {
            "title": "Version Test Diagram",
            "file_type": "canvas",
            "canvas_data": {
                "version": "1.0",
                "shapes": []
            }
        }
        
        response = requests.post(
            f"{DIAGRAM_SERVICE_URL}/",
            json=create_data,
            headers=headers
        )
        
        if response.status_code == 200:
            diagram = response.json()
            diagram_id = diagram["id"]
            current_version = diagram["current_version"]
            
            if current_version == 1:
                print_result(True, f"Diagram created with initial version = 1 (Diagram ID: {diagram_id})")
                results["passed"] += 1
                results["tests"].append({"step": 1, "passed": True, "message": "Initial version = 1"})
            else:
                print_result(False, f"Expected version 1, got {current_version}")
                results["failed"] += 1
                results["tests"].append({"step": 1, "passed": False, "message": f"Expected version 1, got {current_version}"})
        else:
            print_result(False, f"Failed to create diagram: {response.text}")
            results["failed"] += 1
            results["tests"].append({"step": 1, "passed": False, "message": "Failed to create diagram"})
            return results
        
        # =================================================================
        # Step 2: Verify version_number = 1 in database
        # =================================================================
        print_step(2, "Verify version_number = 1")
        
        response = requests.get(
            f"{DIAGRAM_SERVICE_URL}/{diagram_id}/versions",
            headers=headers
        )
        
        if response.status_code == 200:
            versions = response.json()
            
            if len(versions) == 1 and versions[0]["version_number"] == 1:
                print_result(True, f"Version 1 found in database with correct version_number")
                print(f"  Version ID: {versions[0]['id']}")
                print(f"  Description: {versions[0]['description']}")
                results["passed"] += 1
                results["tests"].append({"step": 2, "passed": True, "message": "Version 1 in database"})
            else:
                print_result(False, f"Expected 1 version with version_number=1, got {len(versions)} versions")
                results["failed"] += 1
                results["tests"].append({"step": 2, "passed": False, "message": "Version count or number incorrect"})
        else:
            print_result(False, f"Failed to get versions: {response.text}")
            results["failed"] += 1
            results["tests"].append({"step": 2, "passed": False, "message": "Failed to get versions"})
        
        # =================================================================
        # Step 3: Update file to create version 2
        # =================================================================
        print_step(3, "Update file to create version 2")
        
        update_data = {
            "canvas_data": {
                "version": "2.0",
                "shapes": [{"id": "shape1", "type": "rectangle"}]
            },
            "description": "Added first shape"
        }
        
        response = requests.put(
            f"{DIAGRAM_SERVICE_URL}/{diagram_id}",
            json=update_data,
            headers=headers
        )
        
        if response.status_code == 200:
            diagram = response.json()
            current_version = diagram["current_version"]
            
            if current_version == 2:
                print_result(True, f"Diagram updated to version 2")
                results["passed"] += 1
                results["tests"].append({"step": 3, "passed": True, "message": "Version auto-incremented to 2"})
            else:
                print_result(False, f"Expected version 2, got {current_version}")
                results["failed"] += 1
                results["tests"].append({"step": 3, "passed": False, "message": f"Expected version 2, got {current_version}"})
        else:
            print_result(False, f"Failed to update diagram: {response.text}")
            results["failed"] += 1
            results["tests"].append({"step": 3, "passed": False, "message": "Failed to update diagram"})
        
        # =================================================================
        # Step 4: Verify version_number auto-increments to 2
        # =================================================================
        print_step(4, "Verify version_number auto-increments to 2")
        
        response = requests.get(
            f"{DIAGRAM_SERVICE_URL}/{diagram_id}/versions",
            headers=headers
        )
        
        if response.status_code == 200:
            versions = response.json()
            
            if len(versions) == 2:
                version_numbers = [v["version_number"] for v in versions]
                if version_numbers == [1, 2]:
                    print_result(True, f"Version numbers are correctly [1, 2]")
                    results["passed"] += 1
                    results["tests"].append({"step": 4, "passed": True, "message": "Version auto-increment working"})
                else:
                    print_result(False, f"Expected version numbers [1, 2], got {version_numbers}")
                    results["failed"] += 1
                    results["tests"].append({"step": 4, "passed": False, "message": f"Wrong version numbers: {version_numbers}"})
            else:
                print_result(False, f"Expected 2 versions, got {len(versions)}")
                results["failed"] += 1
                results["tests"].append({"step": 4, "passed": False, "message": f"Wrong version count: {len(versions)}"})
        else:
            print_result(False, f"Failed to get versions: {response.text}")
            results["failed"] += 1
            results["tests"].append({"step": 4, "passed": False, "message": "Failed to get versions"})
        
        # =================================================================
        # Step 5: Create 10 more versions (versions 3-12)
        # =================================================================
        print_step(5, "Create 10 more versions (versions 3-12)")
        
        for i in range(3, 13):
            update_data = {
                "canvas_data": {
                    "version": f"{i}.0",
                    "shapes": [{"id": f"shape{j}", "type": "rectangle"} for j in range(1, i)]
                },
                "description": f"Version {i} - added more shapes"
            }
            
            response = requests.put(
                f"{DIAGRAM_SERVICE_URL}/{diagram_id}",
                json=update_data,
                headers=headers
            )
            
            if response.status_code != 200:
                print_result(False, f"Failed to create version {i}: {response.text}")
                results["failed"] += 1
                results["tests"].append({"step": 5, "passed": False, "message": f"Failed at version {i}"})
                break
        else:
            # All versions created successfully
            response = requests.get(
                f"{DIAGRAM_SERVICE_URL}/{diagram_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                diagram = response.json()
                current_version = diagram["current_version"]
                
                if current_version == 12:
                    print_result(True, f"Created versions 3-12 successfully, current_version = 12")
                    results["passed"] += 1
                    results["tests"].append({"step": 5, "passed": True, "message": "Created 10 more versions"})
                else:
                    print_result(False, f"Expected current_version 12, got {current_version}")
                    results["failed"] += 1
                    results["tests"].append({"step": 5, "passed": False, "message": f"Wrong final version: {current_version}"})
            else:
                print_result(False, f"Failed to get diagram: {response.text}")
                results["failed"] += 1
                results["tests"].append({"step": 5, "passed": False, "message": "Failed to get diagram"})
        
        # =================================================================
        # Step 6: Verify version_number reaches 12
        # =================================================================
        print_step(6, "Verify version_number reaches 12")
        
        response = requests.get(
            f"{DIAGRAM_SERVICE_URL}/{diagram_id}/versions",
            headers=headers
        )
        
        if response.status_code == 200:
            versions = response.json()
            
            if len(versions) == 12:
                version_numbers = [v["version_number"] for v in versions]
                expected = list(range(1, 13))
                
                if version_numbers == expected:
                    print_result(True, f"All 12 versions with correct version_numbers [1..12]")
                    print(f"  Total versions: {len(versions)}")
                    print(f"  Version numbers: {version_numbers}")
                    results["passed"] += 1
                    results["tests"].append({"step": 6, "passed": True, "message": "All 12 versions present"})
                else:
                    print_result(False, f"Version numbers incorrect. Expected {expected}, got {version_numbers}")
                    results["failed"] += 1
                    results["tests"].append({"step": 6, "passed": False, "message": "Version numbers incorrect"})
            else:
                print_result(False, f"Expected 12 versions, got {len(versions)}")
                results["failed"] += 1
                results["tests"].append({"step": 6, "passed": False, "message": f"Wrong version count: {len(versions)}"})
        else:
            print_result(False, f"Failed to get versions: {response.text}")
            results["failed"] += 1
            results["tests"].append({"step": 6, "passed": False, "message": "Failed to get versions"})
        
        # =================================================================
        # Step 7: Test version ordering by version_number
        # =================================================================
        print_step(7, "Test version ordering by version_number")
        
        response = requests.get(
            f"{DIAGRAM_SERVICE_URL}/{diagram_id}/versions",
            headers=headers
        )
        
        if response.status_code == 200:
            versions = response.json()
            version_numbers = [v["version_number"] for v in versions]
            
            # Check if ordered
            is_ordered = all(version_numbers[i] < version_numbers[i+1] for i in range(len(version_numbers)-1))
            
            if is_ordered:
                print_result(True, f"Versions are correctly ordered by version_number")
                print(f"  Ordered sequence: {version_numbers}")
                results["passed"] += 1
                results["tests"].append({"step": 7, "passed": True, "message": "Versions ordered correctly"})
            else:
                print_result(False, f"Versions not ordered correctly: {version_numbers}")
                results["failed"] += 1
                results["tests"].append({"step": 7, "passed": False, "message": "Versions not ordered"})
        else:
            print_result(False, f"Failed to get versions: {response.text}")
            results["failed"] += 1
            results["tests"].append({"step": 7, "passed": False, "message": "Failed to get versions"})
        
    except Exception as e:
        print(f"\n✗ Test execution error: {str(e)}")
        import traceback
        traceback.print_exc()
        results["failed"] += 1
        return results
    
    return results

if __name__ == "__main__":
    results = test_version_autoincrement()
    
    print("\n" + "="*70)
    print("Test Results Summary")
    print("="*70)
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Total:  {results['passed'] + results['failed']}")
    
    if results['failed'] == 0:
        print("\n✓ All tests PASSED - Feature #23 is fully functional!")
        sys.exit(0)
    else:
        print("\n✗ Some tests FAILED - Feature #23 needs fixes")
        sys.exit(1)
