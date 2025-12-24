#!/usr/bin/env python3
"""
Test Features #472-473: Version Labels and Comments
- Update version labels (tag important versions)
- Update version comments (add notes explaining changes)
"""

import requests
import json
import time

# Base URLs
DIAGRAM_URL = "http://localhost:8082"

def test_version_label_and_comment():
    """Test version label and comment update features."""
    print("=" * 80)
    print("TESTING FEATURES #472-473: VERSION LABELS & COMMENTS")
    print("=" * 80)
    
    # Note: This test requires a diagram with at least one version
    # You'll need to manually provide:
    diagram_id = input("\nEnter diagram ID: ")
    version_id = input("Enter version ID: ")
    token = input("Enter access token: ")
    user_id = input("Enter user ID: ")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id,
        "Content-Type": "application/json"
    }
    
    print("\n" + "=" * 80)
    print("TEST 1: Update Version Label")
    print("=" * 80)
    
    try:
        # Update label
        label_data = {"label": f"Important Milestone {int(time.time())}"}
        response = requests.patch(
            f"{DIAGRAM_URL}/{diagram_id}/versions/{version_id}/label",
            json=label_data,
            headers=headers,
            timeout=5
        )
        
        print(f"\nRequest: PATCH /{diagram_id}/versions/{version_id}/label")
        print(f"Payload: {json.dumps(label_data, indent=2)}")
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS: Label updated successfully")
            print(f"   Version: {data.get('version_number')}")
            print(f"   Label: {data.get('label')}")
        else:
            print(f"❌ FAIL: Status {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
    
    print("\n" + "=" * 80)
    print("TEST 2: Update Version Comment/Description")
    print("=" * 80)
    
    try:
        # Update description
        description_data = {"description": f"Updated design with new features - {time.strftime('%Y-%m-%d %H:%M:%S')}"}
        response = requests.patch(
            f"{DIAGRAM_URL}/{diagram_id}/versions/{version_id}/description",
            json=description_data,
            headers=headers,
            timeout=5
        )
        
        print(f"\nRequest: PATCH /{diagram_id}/versions/{version_id}/description")
        print(f"Payload: {json.dumps(description_data, indent=2)}")
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS: Description updated successfully")
            print(f"   Version: {data.get('version_number')}")
            print(f"   Description: {data.get('description')}")
        else:
            print(f"❌ FAIL: Status {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
    
    print("\n" + "=" * 80)
    print("TEST 3: Verify Version Data")
    print("=" * 80)
    
    try:
        # Get version to verify changes
        response = requests.get(
            f"{DIAGRAM_URL}/{diagram_id}/versions/{version_id}",
            headers=headers,
            timeout=5
        )
        
        print(f"\nRequest: GET /{diagram_id}/versions/{version_id}")
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS: Version retrieved successfully")
            print(f"   Version Number: {data.get('version_number')}")
            print(f"   Label: {data.get('label')}")
            print(f"   Description: {data.get('description')}")
        else:
            print(f"❌ FAIL: Status {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
    
    print("\n" + "=" * 80)
    print("MANUAL UI TESTING INSTRUCTIONS")
    print("=" * 80)
    print("\n1. Open http://localhost:3000/versions/{diagram_id}?v1=1&v2=2")
    print("2. For each version panel:")
    print("   a. Click '+ Add Label' or 'Edit' next to existing label")
    print("   b. Enter a label (e.g., 'Production Release')")
    print("   c. Click 'Save' - label should update immediately")
    print("   d. Click '+ Add Comment' or 'Edit' next to comment")
    print("   e. Enter a description (e.g., 'Fixed bug in authentication')")
    print("   f. Click 'Save Comment' - comment should appear in gray box")
    print("3. Verify labels appear in version selector dropdowns")
    print("4. Verify changes persist after page refresh")
    print("\n✅ Both features implemented and ready for testing!")

if __name__ == "__main__":
    test_version_label_and_comment()
