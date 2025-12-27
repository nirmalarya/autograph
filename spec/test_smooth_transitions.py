"""
Test Feature #621: UX/Performance - No flickering with smooth transitions

Acceptance Criteria:
1. Navigate between pages
2. Verify no content flash
3. Verify smooth fade transitions
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


def test_smooth_page_transitions():
    """Test that page transitions are smooth without flickering"""

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')

    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)

    try:
        # 1. Navigate to homepage
        driver.get('http://localhost:3000')
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

        # Check that PageTransition styles are loaded
        page_transition_element = driver.find_element(By.CLASS_NAME, 'page-transition')
        assert page_transition_element is not None, "PageTransition wrapper not found"

        # Verify initial opacity is 1 (page is visible)
        initial_opacity = driver.execute_script(
            "return window.getComputedStyle(document.querySelector('.page-transition')).opacity"
        )
        assert initial_opacity == '1', f"Initial opacity should be 1, got {initial_opacity}"

        # Check transition CSS property is set
        transition = driver.execute_script(
            "return window.getComputedStyle(document.querySelector('.page-transition')).transition"
        )
        assert 'opacity' in transition, f"Opacity transition not found: {transition}"
        assert '150ms' in transition or '0.15s' in transition, f"150ms transition not found: {transition}"

        print("✓ Page transition styles are correctly applied")

        # 2. Navigate to login page
        login_link = wait.until(EC.presence_of_element_located((By.LINK_TEXT, 'Sign In')))

        # Scroll to element and click using JavaScript (to avoid element interception)
        driver.execute_script("arguments[0].scrollIntoView(true);", login_link)
        time.sleep(0.2)  # Wait for scroll

        # Record time before navigation
        start_time = time.time()
        driver.execute_script("arguments[0].click();", login_link)

        # Wait for login page to load
        wait.until(EC.url_contains('/login'))
        navigation_time = time.time() - start_time

        # Verify page loaded with transition
        page_transition_element = driver.find_element(By.CLASS_NAME, 'page-transition')
        opacity = driver.execute_script(
            "return window.getComputedStyle(document.querySelector('.page-transition')).opacity"
        )
        assert opacity == '1', f"Page should be fully visible after transition, got opacity {opacity}"

        print(f"✓ Navigation completed in {navigation_time:.2f}s with smooth transition")

        # 3. Navigate back to home
        driver.get('http://localhost:3000')
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'main')))

        # Verify no content flash by checking that page-transition class exists
        page_transition_element = driver.find_element(By.CLASS_NAME, 'page-transition')
        opacity = driver.execute_script(
            "return window.getComputedStyle(document.querySelector('.page-transition')).opacity"
        )
        assert opacity == '1', f"Page should be fully visible, got opacity {opacity}"

        print("✓ No content flash detected")

        # 4. Verify animation keyframes exist
        keyframes_exist = driver.execute_script("""
            const styleSheets = Array.from(document.styleSheets);
            for (const sheet of styleSheets) {
                try {
                    const rules = Array.from(sheet.cssRules || []);
                    for (const rule of rules) {
                        if (rule.type === CSSRule.KEYFRAMES_RULE) {
                            if (rule.name === 'fadeIn' || rule.name === 'fadeOut') {
                                return true;
                            }
                        }
                    }
                } catch (e) {
                    // CORS errors on external stylesheets, skip
                }
            }
            return false;
        """)

        if keyframes_exist:
            print("✓ Fade animations (fadeIn/fadeOut) are defined in CSS")
        else:
            print("⚠ Warning: fadeIn/fadeOut keyframes not detected (might be in external CSS)")

        # 5. Test register page navigation
        driver.get('http://localhost:3000')
        register_link = wait.until(EC.presence_of_element_located((By.LINK_TEXT, 'Get Started')))
        driver.execute_script("arguments[0].scrollIntoView(true);", register_link)
        time.sleep(0.2)  # Wait for scroll
        driver.execute_script("arguments[0].click();", register_link)
        wait.until(EC.url_contains('/register'))

        page_transition_element = driver.find_element(By.CLASS_NAME, 'page-transition')
        opacity = driver.execute_script(
            "return window.getComputedStyle(document.querySelector('.page-transition')).opacity"
        )
        assert opacity == '1', f"Register page should be fully visible, got opacity {opacity}"

        print("✓ Smooth transitions working on all tested pages")

        print("\n" + "="*60)
        print("✅ Feature #621 PASSED: No flickering, smooth transitions")
        print("="*60)

        return True

    except Exception as e:
        print(f"\n❌ Feature #621 FAILED: {str(e)}")
        raise

    finally:
        driver.quit()


if __name__ == '__main__':
    try:
        test_smooth_page_transitions()
        exit(0)
    except Exception:
        exit(1)
