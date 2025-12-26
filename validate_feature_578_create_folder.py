#!/usr/bin/env python3
"""
Feature #578: Organization: Folders: create folder
Test Steps:
1. Click 'New Folder'
2. Name: 'Architecture'
3. Create
4. Verify folder created
5. Verify appears in sidebar
"""

import asyncio
import sys
from pyppeteer import launch
import os

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

async def test_create_folder():
    """Test creating a folder in the dashboard."""
    browser = None
    try:
        print(f"{BLUE}Starting Feature #578 test: Create folder{RESET}")

        # Launch browser
        browser = await launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security',
            ]
        )

        page = await browser.newPage()
        await page.setViewport({'width': 1280, 'height': 720})

        # Step 1: Register and login
        print(f"{YELLOW}Step 1: Registering test user...{RESET}")
        test_email = f"folder_test_578_{os.urandom(4).hex()}@example.com"
        test_password = "SecurePass123!"

        await page.goto('http://localhost:3000/auth/register', {'waitUntil': 'networkidle0', 'timeout': 60000})
        await page.waitForSelector('input[type="email"]', {'timeout': 10000})

        await page.type('input[type="email"]', test_email)
        await page.type('input[type="password"]', test_password)
        await page.type('input[placeholder*="Name"]', 'Folder Test User')

        await page.click('button[type="submit"]')
        await asyncio.sleep(3)

        # Navigate to dashboard
        print(f"{YELLOW}Step 2: Navigating to dashboard...{RESET}")
        await page.goto('http://localhost:3000/dashboard', {'waitUntil': 'networkidle0', 'timeout': 60000})
        await asyncio.sleep(2)

        # Step 3: Click 'New Folder' button (+ icon in folder sidebar)
        print(f"{YELLOW}Step 3: Looking for 'New Folder' button...{RESET}")

        # Wait for the folder sidebar to load
        await page.waitForSelector('.w-64', {'timeout': 10000})

        # Look for the "Create new folder" button (+ icon)
        new_folder_button = await page.querySelector('button[title="Create new folder"]')
        if not new_folder_button:
            print(f"{RED}✗ Could not find 'New Folder' button{RESET}")
            return False

        print(f"{GREEN}✓ Found 'New Folder' button{RESET}")
        await new_folder_button.click()
        await asyncio.sleep(1)

        # Step 4: Verify modal appeared
        print(f"{YELLOW}Step 4: Verifying create folder modal...{RESET}")
        modal = await page.querySelector('.fixed.inset-0')
        if not modal:
            print(f"{RED}✗ Create folder modal did not appear{RESET}")
            return False

        print(f"{GREEN}✓ Create folder modal appeared{RESET}")

        # Step 5: Enter folder name 'Architecture'
        print(f"{YELLOW}Step 5: Entering folder name 'Architecture'...{RESET}")
        folder_name_input = await page.querySelector('input[placeholder*="Folder"]')
        if not folder_name_input:
            print(f"{RED}✗ Could not find folder name input{RESET}")
            return False

        await folder_name_input.type('Architecture')
        await asyncio.sleep(0.5)

        print(f"{GREEN}✓ Entered folder name{RESET}")

        # Step 6: Click Create button
        print(f"{YELLOW}Step 6: Clicking Create button...{RESET}")

        # Find the Create button (it's the blue button in the modal)
        create_buttons = await page.querySelectorAll('button')
        create_button = None
        for btn in create_buttons:
            text_content = await page.evaluate('(element) => element.textContent', btn)
            if 'Create' in text_content and 'Creating' not in text_content:
                create_button = btn
                break

        if not create_button:
            print(f"{RED}✗ Could not find Create button{RESET}")
            return False

        await create_button.click()
        await asyncio.sleep(2)

        print(f"{GREEN}✓ Clicked Create button{RESET}")

        # Step 7: Verify modal closed
        print(f"{YELLOW}Step 7: Verifying modal closed...{RESET}")
        modal_after = await page.querySelector('.fixed.inset-0')
        if modal_after:
            print(f"{RED}✗ Modal did not close after creation{RESET}")
            return False

        print(f"{GREEN}✓ Modal closed successfully{RESET}")

        # Step 8: Verify folder appears in sidebar
        print(f"{YELLOW}Step 8: Verifying folder appears in sidebar...{RESET}")
        await asyncio.sleep(2)  # Wait for folder to load

        # Search for the folder name in the sidebar
        page_content = await page.content()
        if 'Architecture' not in page_content:
            print(f"{RED}✗ Folder 'Architecture' not found in sidebar{RESET}")
            return False

        # More specific check: look for folder in the tree
        folder_elements = await page.querySelectorAll('.w-64 button')
        folder_found = False
        for elem in folder_elements:
            text = await page.evaluate('(element) => element.textContent', elem)
            if 'Architecture' in text:
                folder_found = True
                break

        if not folder_found:
            print(f"{RED}✗ Folder 'Architecture' not visible in folder tree{RESET}")
            return False

        print(f"{GREEN}✓ Folder 'Architecture' appears in sidebar!{RESET}")

        # Bonus: Verify folder is clickable
        print(f"{YELLOW}Bonus: Testing folder is clickable...{RESET}")
        for elem in folder_elements:
            text = await page.evaluate('(element) => element.textContent', elem)
            if 'Architecture' in text:
                await elem.click()
                await asyncio.sleep(1)
                print(f"{GREEN}✓ Folder is clickable and interactive{RESET}")
                break

        print(f"\n{GREEN}{'='*60}{RESET}")
        print(f"{GREEN}✓ Feature #578 PASSED: Create folder functionality works!{RESET}")
        print(f"{GREEN}{'='*60}{RESET}\n")

        return True

    except Exception as e:
        print(f"\n{RED}✗ Test failed with error: {str(e)}{RESET}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if browser:
            await browser.close()

async def main():
    """Main test runner."""
    success = await test_create_folder()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
