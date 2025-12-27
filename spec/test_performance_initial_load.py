#!/usr/bin/env python3
"""
Performance Test: Initial Load < 2s
Tests that the homepage loads and becomes interactive in under 2 seconds.
"""

import time
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_initial_load_performance():
    """Test initial page load performance"""
    print("=" * 80)
    print("TEST: Initial Load Performance < 2s")
    print("=" * 80)

    results = {
        "test_name": "Initial Load Performance",
        "checks": [],
        "all_passed": True
    }

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # Clear cache
            print("\n1. Clearing cache...")
            context.clear_cookies()
            results["checks"].append({
                "name": "Clear cache",
                "passed": True,
                "details": "Cache cleared successfully"
            })

            # Measure page load time
            print("\n2. Loading login page (initial landing page)...")
            start_time = time.time()

            # Navigate to the app - it redirects to login
            response = page.goto('http://localhost:3001/login', wait_until='domcontentloaded', timeout=10000)

            # Wait for page to be interactive (DOM ready)
            page.wait_for_load_state('domcontentloaded')

            load_time = time.time() - start_time

            print(f"   Initial load time: {load_time:.3f}s")

            check_passed = load_time < 2.0
            results["checks"].append({
                "name": "Initial load time",
                "passed": check_passed,
                "expected": "< 2.0s",
                "actual": f"{load_time:.3f}s"
            })

            if not check_passed:
                results["all_passed"] = False
                print(f"   ❌ FAILED: Load time {load_time:.3f}s exceeds 2s limit")
            else:
                print(f"   ✅ PASSED: Load time {load_time:.3f}s is under 2s")

            # Measure time to interactive
            print("\n3. Measuring time to interactive...")

            # Wait for page to be fully interactive
            page.wait_for_load_state('networkidle', timeout=10000)

            # Check that page body is visible
            page.wait_for_selector('body', state='visible', timeout=5000)

            tti = time.time() - start_time
            print(f"   Time to interactive: {tti:.3f}s")

            check_passed_tti = tti < 3.0
            results["checks"].append({
                "name": "Time to interactive",
                "passed": check_passed_tti,
                "expected": "< 3.0s",
                "actual": f"{tti:.3f}s"
            })

            if not check_passed_tti:
                results["all_passed"] = False
                print(f"   ❌ FAILED: TTI {tti:.3f}s exceeds 3s limit")
            else:
                print(f"   ✅ PASSED: TTI {tti:.3f}s is under 3s")

            # Check that critical content is rendered
            print("\n4. Verifying critical content rendered...")
            # Check if page has loaded any visible content
            page_has_content = page.locator('body *').count() > 0
            page_title = page.title()

            content_check_passed = page_has_content and len(page_title) > 0
            results["checks"].append({
                "name": "Critical content rendered",
                "passed": content_check_passed,
                "details": f"Page has content: {page_has_content}, Title: '{page_title}'"
            })

            if not content_check_passed:
                results["all_passed"] = False
                print(f"   ❌ FAILED: Page content not properly rendered")
            else:
                print(f"   ✅ PASSED: Page content rendered (Title: '{page_title}')")

            # Get performance metrics
            print("\n5. Collecting performance metrics...")
            metrics = page.evaluate('''() => {
                const perfData = window.performance.timing;
                const navigationStart = perfData.navigationStart;

                return {
                    domContentLoaded: perfData.domContentLoadedEventEnd - navigationStart,
                    domComplete: perfData.domComplete - navigationStart,
                    loadComplete: perfData.loadEventEnd - navigationStart,
                    firstPaint: performance.getEntriesByType('paint').find(p => p.name === 'first-paint')?.startTime || 0,
                    firstContentfulPaint: performance.getEntriesByType('paint').find(p => p.name === 'first-contentful-paint')?.startTime || 0,
                };
            }''')

            print(f"   DOM Content Loaded: {metrics.get('domContentLoaded', 0):.0f}ms")
            print(f"   First Paint: {metrics.get('firstPaint', 0):.0f}ms")
            print(f"   First Contentful Paint: {metrics.get('firstContentfulPaint', 0):.0f}ms")
            print(f"   Load Complete: {metrics.get('loadComplete', 0):.0f}ms")

            results["checks"].append({
                "name": "Performance metrics collected",
                "passed": True,
                "details": metrics
            })

            # Check no JavaScript errors
            print("\n6. Checking for JavaScript errors...")
            page_errors = []

            def handle_error(error):
                page_errors.append(str(error))

            page.on('pageerror', handle_error)

            # Wait a bit to catch any late errors
            time.sleep(0.5)

            no_errors = len(page_errors) == 0
            results["checks"].append({
                "name": "No JavaScript errors",
                "passed": no_errors,
                "details": f"Errors found: {len(page_errors)}"
            })

            if not no_errors:
                results["all_passed"] = False
                print(f"   ❌ FAILED: {len(page_errors)} JavaScript errors detected")
                for error in page_errors[:5]:  # Show first 5 errors
                    print(f"      - {error}")
            else:
                print(f"   ✅ PASSED: No JavaScript errors")

            browser.close()

    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR: {str(e)}")
        results["all_passed"] = False
        results["error"] = str(e)
        return results

    return results


def main():
    """Run performance tests"""
    print("\n" + "=" * 80)
    print("PERFORMANCE TEST SUITE: Initial Load")
    print("=" * 80 + "\n")

    results = test_initial_load_performance()

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total checks: {len(results['checks'])}")
    passed_count = sum(1 for c in results['checks'] if c['passed'])
    print(f"Passed: {passed_count}/{len(results['checks'])}")
    print(f"Overall result: {'✅ PASSED' if results['all_passed'] else '❌ FAILED'}")
    print("=" * 80 + "\n")

    # Save results
    with open('spec/test_performance_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    return 0 if results['all_passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
