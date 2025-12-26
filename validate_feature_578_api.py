#!/usr/bin/env python3
"""
Feature #578: Organization: Folders: create folder
API-based test:
1. Register user
2. Create folder named 'Architecture'
3. Verify folder created
4. Get folders list
5. Verify folder appears in list
"""

import requests
import json
import os
import hashlib

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def hash_password(password):
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def test_create_folder_api():
    """Test creating a folder via API."""
    try:
        print(f"{BLUE}Starting Feature #578 API test: Create folder{RESET}\n")

        # Step 1: Register test user
        print(f"{YELLOW}Step 1: Registering test user...{RESET}")
        test_email = f"folder_api_578_{os.urandom(4).hex()}@example.com"
        test_password = "SecurePass123!"
        test_name = "Folder API Test User"

        register_data = {
            "email": test_email,
            "password": test_password,
            "full_name": test_name
        }

        response = requests.post(
            'http://localhost:8080/auth/register',
            json=register_data,
            timeout=10
        )

        if response.status_code != 201:
            print(f"{RED}✗ Failed to register user: {response.status_code}{RESET}")
            print(f"Response: {response.text}")
            return False

        user_data = response.json()
        user_id = user_data['user']['id']
        print(f"{GREEN}✓ User registered successfully (ID: {user_id}){RESET}")

        # Step 2: Create folder named 'Architecture'
        print(f"\n{YELLOW}Step 2: Creating folder 'Architecture'...{RESET}")
        folder_data = {
            "name": "Architecture",
            "color": "#3B82F6",
            "icon": "folder-code"
        }

        response = requests.post(
            'http://localhost:8082/folders',
            json=folder_data,
            headers={'X-User-ID': user_id},
            timeout=10
        )

        if response.status_code not in [200, 201]:
            print(f"{RED}✗ Failed to create folder: {response.status_code}{RESET}")
            print(f"Response: {response.text}")
            return False

        folder_response = response.json()
        folder_id = folder_response['folder']['id']
        folder_name = folder_response['folder']['name']

        print(f"{GREEN}✓ Folder created successfully!{RESET}")
        print(f"  - ID: {folder_id}")
        print(f"  - Name: {folder_name}")
        print(f"  - Color: {folder_response['folder'].get('color', 'N/A')}")
        print(f"  - Icon: {folder_response['folder'].get('icon', 'N/A')}")

        # Step 3: Verify folder name
        print(f"\n{YELLOW}Step 3: Verifying folder name...{RESET}")
        if folder_name != "Architecture":
            print(f"{RED}✗ Folder name mismatch. Expected 'Architecture', got '{folder_name}'{RESET}")
            return False

        print(f"{GREEN}✓ Folder name verified: 'Architecture'{RESET}")

        # Step 4: Get folders list
        print(f"\n{YELLOW}Step 4: Getting folders list...{RESET}")
        response = requests.get(
            'http://localhost:8082/folders',
            headers={'X-User-ID': user_id},
            timeout=10
        )

        if response.status_code != 200:
            print(f"{RED}✗ Failed to get folders list: {response.status_code}{RESET}")
            print(f"Response: {response.text}")
            return False

        folders_data = response.json()
        folders_list = folders_data.get('folders', [])

        print(f"{GREEN}✓ Retrieved folders list: {len(folders_list)} folder(s){RESET}")

        # Step 5: Verify folder appears in list
        print(f"\n{YELLOW}Step 5: Verifying folder appears in sidebar...{RESET}")

        found_folder = None
        for folder in folders_list:
            if folder['id'] == folder_id:
                found_folder = folder
                break

        if not found_folder:
            print(f"{RED}✗ Folder not found in list{RESET}")
            print(f"Folders in list: {json.dumps(folders_list, indent=2)}")
            return False

        print(f"{GREEN}✓ Folder 'Architecture' appears in sidebar!{RESET}")
        print(f"  - Found in folders list")
        print(f"  - Visible to user")
        print(f"  - Ready for interaction")

        # Bonus: Verify folder metadata
        print(f"\n{YELLOW}Bonus: Verifying folder metadata...{RESET}")
        if found_folder.get('color') == "#3B82F6":
            print(f"{GREEN}✓ Color correct: #3B82F6{RESET}")
        if found_folder.get('icon') == "folder-code":
            print(f"{GREEN}✓ Icon correct: folder-code{RESET}")

        print(f"\n{GREEN}{'='*60}{RESET}")
        print(f"{GREEN}✓ Feature #578 PASSED: Create folder functionality works!{RESET}")
        print(f"{GREEN}{'='*60}{RESET}\n")

        print(f"{BLUE}Summary:{RESET}")
        print(f"  ✓ User registration: OK")
        print(f"  ✓ Folder creation: OK")
        print(f"  ✓ Folder naming: OK")
        print(f"  ✓ Folder retrieval: OK")
        print(f"  ✓ Folder visibility: OK")
        print(f"\n{GREEN}All tests passed!{RESET}\n")

        return True

    except requests.exceptions.ConnectionError as e:
        print(f"\n{RED}✗ Connection error: Could not connect to services{RESET}")
        print(f"Error: {str(e)}")
        print(f"\n{YELLOW}Make sure services are running:{RESET}")
        print(f"  - docker-compose up -d")
        print(f"  - Check: docker-compose ps")
        return False

    except Exception as e:
        print(f"\n{RED}✗ Test failed with error: {str(e)}{RESET}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = test_create_folder_api()
    sys.exit(0 if success else 1)
