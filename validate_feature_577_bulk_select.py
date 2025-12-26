#!/usr/bin/env python3
"""
Feature #577 Validation: Bulk Operations - Select Multiple Diagrams

Tests:
1. Check 5 diagram checkboxes
2. Verify selection count: '5 selected'
3. Verify bulk actions enabled
"""

import os
import sys
import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

# Configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
API_GATEWAY = os.getenv("API_GATEWAY_URL", "http://localhost:8080")
TEST_EMAIL = "bulkselect577@test.com"
TEST_PASSWORD = "TestPassword123!"
TEST_USERNAME = "bulkselect577"

def setup_chrome():
    """Setup Chrome WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=chrome_options)

def create_test_user():
    """Create test user via API"""
    print(f"Creating test user: {TEST_EMAIL}")

    response = requests.post(
        f"{API_GATEWAY}/auth/register",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "username": TEST_USERNAME
        },
        timeout=10
    )

    if response.status_code in [200, 201]:
        print("✅ Test user created successfully")
        return True
    elif response.status_code == 400 and "already exists" in response.text.lower():
        print("ℹ️  Test user already exists")
        return True
    else:
        print(f"❌ Failed to create user: {response.status_code} - {response.text}")
        return False

def login_user(driver):
    """Login to the application"""
    print(f"\n=== Logging in as {TEST_EMAIL} ===")

    driver.get(f"{FRONTEND_URL}/login")
    wait = WebDriverWait(driver, 20)

    # Wait for and fill email
    email_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))
    email_input.clear()
    email_input.send_keys(TEST_EMAIL)

    # Fill password
    password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
    password_input.clear()
    password_input.send_keys(TEST_PASSWORD)

    # Click login button
    login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    login_button.click()

    # Wait for redirect to dashboard
    wait.until(EC.url_contains("/dashboard"))
    print("✅ Login successful")

    # Wait for dashboard to load
    time.sleep(2)

def create_test_diagrams(driver, count=7):
    """Create test diagrams for bulk selection"""
    print(f"\n=== Creating {count} test diagrams ===")

    wait = WebDriverWait(driver, 20)

    for i in range(count):
        try:
            # Click New Diagram button
            new_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'New Diagram')]")))
            new_btn.click()
            time.sleep(0.5)

            # Find and click Canvas option
            canvas_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Canvas')]")))
            canvas_option.click()
            time.sleep(1)

            # Wait for dialog with name input
            name_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='name']")))
            diagram_name = f"Bulk Test Diagram {i+1}"
            name_input.clear()
            name_input.send_keys(diagram_name)

            # Click Create button
            create_btn = driver.find_element(By.XPATH, "//button[contains(., 'Create')]")
            create_btn.click()

            # Wait for redirect to editor
            wait.until(EC.url_contains("/diagram/"))
            print(f"  ✅ Created: {diagram_name}")

            # Go back to dashboard
            driver.get(f"{FRONTEND_URL}/dashboard")
            time.sleep(1)

        except Exception as e:
            print(f"  ⚠️  Error creating diagram {i+1}: {e}")
            continue

    print(f"✅ Created {count} test diagrams")
    time.sleep(2)

def test_bulk_selection(driver):
    """Test bulk selection functionality"""
    print("\n=== Testing Bulk Selection (Feature #577) ===")

    wait = WebDriverWait(driver, 20)

    # Ensure we're on dashboard
    driver.get(f"{FRONTEND_URL}/dashboard")
    time.sleep(2)

    # Step 1: Find and check 5 diagram checkboxes
    print("\nStep 1: Checking 5 diagram checkboxes...")
    checkboxes = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[type='checkbox']")))

    # Filter out the "Select All" checkbox - we want individual diagram checkboxes
    diagram_checkboxes = [cb for cb in checkboxes if not cb.get_attribute("checked")]

    if len(diagram_checkboxes) < 5:
        print(f"❌ Not enough diagrams found. Found {len(diagram_checkboxes)}, need at least 5")
        return False

    # Click 5 checkboxes
    checked_count = 0
    for i, checkbox in enumerate(diagram_checkboxes[:5]):
        try:
            # Scroll into view
            driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
            time.sleep(0.3)

            # Click checkbox
            checkbox.click()
            checked_count += 1
            print(f"  ✅ Checked checkbox {checked_count}")
            time.sleep(0.3)
        except Exception as e:
            print(f"  ⚠️  Error clicking checkbox {i+1}: {e}")

    if checked_count < 5:
        print(f"❌ Only checked {checked_count} checkboxes, need 5")
        return False

    print(f"✅ Successfully checked {checked_count} checkboxes")
    time.sleep(1)

    # Step 2: Verify selection count displays "5 selected"
    print("\nStep 2: Verifying selection count shows '5 selected'...")
    try:
        selection_count = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '5 diagram')]")))
        count_text = selection_count.text
        print(f"  Found selection count: '{count_text}'")

        if '5' in count_text and 'selected' in count_text.lower():
            print("✅ Selection count verified: '5 selected'")
        else:
            print(f"❌ Selection count incorrect. Expected '5 selected', got '{count_text}'")
            return False
    except TimeoutException:
        print("❌ Selection count not found")
        return False

    # Step 3: Verify bulk actions are enabled
    print("\nStep 3: Verifying bulk actions are enabled...")

    bulk_actions_found = []

    # Check for bulk action buttons
    bulk_action_labels = ["Export Selected", "Move Selected", "Delete Selected", "Clear Selection"]

    for label in bulk_action_labels:
        try:
            button = driver.find_element(By.XPATH, f"//button[contains(., '{label}')]")
            if button.is_displayed():
                bulk_actions_found.append(label)
                print(f"  ✅ Found bulk action: {label}")
        except:
            print(f"  ⚠️  Bulk action not found: {label}")

    if len(bulk_actions_found) >= 2:
        print(f"✅ Bulk actions enabled ({len(bulk_actions_found)} actions found)")
        return True
    else:
        print(f"❌ Insufficient bulk actions found. Need at least 2, found {len(bulk_actions_found)}")
        return False

def main():
    """Main test execution"""
    print("=" * 80)
    print("FEATURE #577 VALIDATION: Bulk Operations - Select Multiple")
    print("=" * 80)

    driver = None
    try:
        # Skip API user creation - user created via SQL
        print("\nℹ️  Test user already created via SQL")

        # Setup browser
        print("\n=== Setting up Chrome WebDriver ===")
        driver = setup_chrome()
        print("✅ Chrome WebDriver ready")

        # Login
        login_user(driver)

        # Create test diagrams
        create_test_diagrams(driver, count=7)

        # Test bulk selection
        success = test_bulk_selection(driver)

        if success:
            print("\n" + "=" * 80)
            print("✅ FEATURE #577 VALIDATION PASSED")
            print("=" * 80)
            print("\nAll steps completed successfully:")
            print("  ✅ Checked 5 diagram checkboxes")
            print("  ✅ Verified selection count: '5 selected'")
            print("  ✅ Verified bulk actions enabled")
            return True
        else:
            print("\n" + "=" * 80)
            print("❌ FEATURE #577 VALIDATION FAILED")
            print("=" * 80)
            return False

    except Exception as e:
        print(f"\n❌ VALIDATION ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if driver:
            driver.quit()
            print("\n✅ Browser closed")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
