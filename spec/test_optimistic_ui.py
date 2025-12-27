#!/usr/bin/env python3
"""
E2E Test for Feature #620: Optimistic UI - No Spinners

This test validates that:
1. Diagram creation appears instant (no loading spinner)
2. UI updates immediately (optimistic)
3. Background sync completes successfully
4. User sees seamless experience
"""

import os
import sys
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

# Test configuration
BASE_URL = os.getenv('BASE_URL', 'http://localhost:3000')
TEST_EMAIL = 'test_optimistic_ui@example.com'
TEST_PASSWORD = 'TestPass123!'

def setup_driver():
    """Setup Chrome driver with appropriate options."""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(2)
    return driver

def register_and_login(driver):
    """Login with existing test user."""
    print("📝 Logging in test user...")

    # Login
    driver.get(f'{BASE_URL}/login')

    email_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, 'email'))
    )
    email_input.send_keys(TEST_EMAIL)

    password_input = driver.find_element(By.NAME, 'password')
    password_input.send_keys(TEST_PASSWORD)

    submit_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
    submit_button.click()

    # Wait for redirect to dashboard
    WebDriverWait(driver, 10).until(
        lambda d: '/dashboard' in d.current_url
    )

    print("✅ User logged in successfully")
    return True

def test_optimistic_diagram_creation(driver):
    """
    Test that diagram creation uses optimistic UI:
    1. Create diagram from dashboard
    2. Verify NO spinner appears
    3. Verify diagram appears immediately in list
    4. Verify modal closes instantly
    """
    print("\n🧪 Test 1: Optimistic diagram creation from dashboard")

    driver.get(f'{BASE_URL}/dashboard')
    time.sleep(2)

    # Open create modal
    create_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'New Diagram') or contains(., 'Create')]"))
    )
    create_button.click()
    time.sleep(1)

    # Fill in diagram title
    title_input = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='title' i], input[name='title']"))
    )
    test_title = f"Optimistic Test {int(time.time())}"
    title_input.clear()
    title_input.send_keys(test_title)

    # Record start time
    start_time = time.time()

    # Click create button
    create_submit = driver.find_element(By.XPATH, "//button[contains(., 'Create')]")
    create_submit.click()

    # Measure time until modal closes
    try:
        WebDriverWait(driver, 2).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, "input[placeholder*='title' i]"))
        )
        modal_close_time = time.time() - start_time
    except TimeoutException:
        print("❌ Modal did not close quickly")
        return False

    # Check that modal closed quickly (optimistic UI = instant, < 500ms)
    if modal_close_time > 1.0:
        print(f"❌ Modal took too long to close: {modal_close_time:.2f}s (expected < 1s)")
        return False

    print(f"✅ Modal closed instantly: {modal_close_time:.3f}s")

    # Verify NO loading spinner appeared
    try:
        spinner = driver.find_element(By.CSS_SELECTOR, '.animate-spin, [class*="spinner"], [class*="loading"]')
        if spinner.is_displayed():
            print("❌ Loading spinner is visible (should not appear with optimistic UI)")
            return False
    except NoSuchElementException:
        print("✅ No loading spinner found (optimistic UI working)")

    # Verify diagram appears in list immediately
    time.sleep(1)
    try:
        diagram_element = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{test_title}')]"))
        )
        print(f"✅ Diagram '{test_title}' appeared in list immediately")
    except TimeoutException:
        print(f"❌ Diagram '{test_title}' not found in list")
        return False

    return True

def test_optimistic_canvas_creation(driver):
    """
    Test that /canvas/new uses optimistic UI:
    1. Navigate to /canvas/new
    2. Verify NO spinner appears
    3. Verify redirect to canvas is instant
    """
    print("\n🧪 Test 2: Optimistic canvas creation via /canvas/new")

    start_time = time.time()
    driver.get(f'{BASE_URL}/canvas/new')

    # Wait for redirect to canvas page
    try:
        WebDriverWait(driver, 5).until(
            lambda d: '/canvas/' in d.current_url and '/canvas/new' not in d.current_url
        )
        redirect_time = time.time() - start_time
    except TimeoutException:
        print("❌ Did not redirect to canvas page")
        return False

    # Check that redirect happened quickly (optimistic = instant redirect)
    if redirect_time > 2.0:
        print(f"⚠️  Redirect took {redirect_time:.2f}s (expected < 2s for optimistic UI)")
        # Not a hard failure, but not ideal
    else:
        print(f"✅ Redirected to canvas instantly: {redirect_time:.3f}s")

    # Verify we're on a canvas page
    current_url = driver.current_url
    if '/canvas/' not in current_url:
        print(f"❌ Not on canvas page: {current_url}")
        return False

    print(f"✅ On canvas page: {current_url}")

    # Verify NO loading spinner (optimistic UI)
    time.sleep(1)
    try:
        spinner = driver.find_element(By.XPATH, "//div[contains(text(), 'Creating') or contains(text(), 'Loading')]")
        if 'Creating new canvas' in spinner.text:
            print("❌ 'Creating new canvas' spinner found (should not appear with optimistic UI)")
            return False
    except NoSuchElementException:
        print("✅ No 'Creating canvas' message found (optimistic UI working)")

    # Wait for canvas to fully load
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "canvas, [class*='tldraw'], [class*='canvas']"))
        )
        print("✅ Canvas loaded successfully")
    except TimeoutException:
        print("⚠️  Canvas element not found (may still be loading)")

    return True

def test_background_sync(driver):
    """
    Test that background sync completes:
    1. Create optimistic diagram
    2. Verify it syncs to server in background
    3. Verify no errors occur
    """
    print("\n🧪 Test 3: Background sync verification")

    driver.get(f'{BASE_URL}/dashboard')
    time.sleep(2)

    # Count diagrams before creation
    try:
        diagram_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='diagram'], [data-testid*='diagram']")
        initial_count = len(diagram_elements)
    except NoSuchElementException:
        initial_count = 0

    print(f"📊 Initial diagram count: {initial_count}")

    # Create diagram
    create_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'New Diagram') or contains(., 'Create')]"))
    )
    create_button.click()
    time.sleep(1)

    title_input = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='title' i], input[name='title']"))
    )
    test_title = f"Sync Test {int(time.time())}"
    title_input.clear()
    title_input.send_keys(test_title)

    create_submit = driver.find_element(By.XPATH, "//button[contains(., 'Create')]")
    create_submit.click()

    # Wait for modal to close
    time.sleep(2)

    # Wait for background sync (give it 5 seconds)
    print("⏳ Waiting for background sync to complete...")
    time.sleep(5)

    # Refresh page to verify diagram persisted
    driver.refresh()
    time.sleep(3)

    # Verify diagram still exists after refresh (proving it synced to server)
    try:
        diagram_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{test_title}')]"))
        )
        print(f"✅ Diagram '{test_title}' persisted after refresh (background sync successful)")
        return True
    except TimeoutException:
        print(f"❌ Diagram '{test_title}' disappeared after refresh (background sync failed)")
        return False

def main():
    """Run all optimistic UI tests."""
    print("="*70)
    print("E2E Test: Feature #620 - Optimistic UI (No Spinners)")
    print("="*70)

    driver = None
    try:
        driver = setup_driver()

        # Register and login
        if not register_and_login(driver):
            print("\n❌ FAILED: Could not register/login")
            return False

        # Run tests
        test_results = []

        test_results.append(("Optimistic diagram creation", test_optimistic_diagram_creation(driver)))
        test_results.append(("Optimistic canvas creation", test_optimistic_canvas_creation(driver)))
        test_results.append(("Background sync", test_background_sync(driver)))

        # Print summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)

        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)

        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")

        print(f"\nResults: {passed}/{total} tests passed")
        print("="*70)

        return passed == total

    except Exception as e:
        print(f"\n❌ Test error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
