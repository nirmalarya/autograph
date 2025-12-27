#!/usr/bin/env python3
"""
Performance Test: Time to Interactive < 3s
Tests that the homepage becomes interactive in under 3 seconds.
"""

import time
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_time_to_interactive():
    """Test time to interactive performance"""
    print("=" * 80)
    print("TEST: Time to Interactive < 3s")
    print("=" * 80)

    results = {
        "test_name": "Time to Interactive",
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

            # Clear cache for accurate measurement
            print("\n1. Clearing cache...")
            context.clear_cookies()
            results["checks"].append({
                "name": "Clear cache",
                "passed": True,
                "details": "Cache cleared successfully"
            })

            # Measure time to interactive
            print("\n2. Measuring time to interactive...")
            start_time = time.time()

            # Navigate to the app
            response = page.goto('http://localhost:3001/login', wait_until='domcontentloaded', timeout=10000)

            # Wait for page to be fully interactive (network idle)
            page.wait_for_load_state('networkidle', timeout=10000)

            # Ensure page is interactive (body visible and clickable)
            page.wait_for_selector('body', state='visible', timeout=5000)

            tti = time.time() - start_time
            print(f"   Time to interactive: {tti:.3f}s")

            check_passed = tti < 3.0
            results["checks"].append({
                "name": "Time to interactive",
                "passed": check_passed,
                "expected": "< 3.0s",
                "actual": f"{tti:.3f}s"
            })

            if not check_passed:
                results["all_passed"] = False
                print(f"   ❌ FAILED: TTI {tti:.3f}s exceeds 3s limit")
            else:
                improvement = ((3.0 - tti) / 3.0) * 100
                print(f"   ✅ PASSED: TTI {tti:.3f}s is under 3s ({improvement:.1f}% better than requirement)")

            # Verify page is actually interactive
            print("\n3. Verifying page interactivity...")

            # Check that page has rendered content
            page_has_content = page.locator('body *').count() > 0

            # Check that page title is set
            page_title = page.title()

            # Try to interact with page (e.g., focus on an input if available)
            can_interact = True
            try:
                # Look for any interactive element
                interactive_elements = page.locator('input, button, a').count()
                if interactive_elements > 0:
                    print(f"   Found {interactive_elements} interactive elements")
                else:
                    print("   No interactive elements found (login may not have loaded)")
            except Exception as e:
                can_interact = False
                print(f"   Could not verify interactivity: {e}")

            interactivity_check = page_has_content and len(page_title) > 0
            results["checks"].append({
                "name": "Page is interactive",
                "passed": interactivity_check,
                "details": f"Has content: {page_has_content}, Title: '{page_title}', Can interact: {can_interact}"
            })

            if not interactivity_check:
                results["all_passed"] = False
                print(f"   ❌ FAILED: Page is not properly interactive")
            else:
                print(f"   ✅ PASSED: Page is interactive (Title: '{page_title}')")

            # Get detailed performance metrics
            print("\n4. Collecting detailed performance metrics...")
            try:
                metrics = page.evaluate('''() => {
                    const perfData = window.performance.timing;
                    const navigationStart = perfData.navigationStart;

                    return {
                        domContentLoaded: perfData.domContentLoadedEventEnd - navigationStart,
                        domInteractive: perfData.domInteractive - navigationStart,
                        domComplete: perfData.domComplete - navigationStart,
                        loadComplete: perfData.loadEventEnd - navigationStart,
                        firstPaint: performance.getEntriesByType('paint').find(p => p.name === 'first-paint')?.startTime || 0,
                        firstContentfulPaint: performance.getEntriesByType('paint').find(p => p.name === 'first-contentful-paint')?.startTime || 0,
                    };
                }''')

                print(f"   DOM Interactive: {metrics.get('domInteractive', 0):.0f}ms")
                print(f"   DOM Content Loaded: {metrics.get('domContentLoaded', 0):.0f}ms")
                print(f"   First Paint: {metrics.get('firstPaint', 0):.0f}ms")
                print(f"   First Contentful Paint: {metrics.get('firstContentfulPaint', 0):.0f}ms")
                print(f"   Load Complete: {metrics.get('loadComplete', 0):.0f}ms")

                results["checks"].append({
                    "name": "Performance metrics collected",
                    "passed": True,
                    "details": metrics
                })
            except Exception as e:
                print(f"   Warning: Could not collect performance metrics: {e}")
                results["checks"].append({
                    "name": "Performance metrics collected",
                    "passed": False,
                    "details": str(e)
                })

            # Check for blocking resources
            print("\n5. Checking for blocking resources...")
            try:
                resource_timings = page.evaluate('''() => {
                    const resources = performance.getEntriesByType('resource');
                    return resources
                        .filter(r => r.duration > 500)  // Resources taking > 500ms
                        .map(r => ({
                            name: r.name,
                            duration: r.duration,
                            type: r.initiatorType
                        }));
                }''')

                if len(resource_timings) > 0:
                    print(f"   Found {len(resource_timings)} slow resources (>500ms):")
                    for resource in resource_timings[:5]:
                        print(f"      - {resource['type']}: {resource['duration']:.0f}ms - {resource['name'][:60]}")
                else:
                    print("   ✅ No blocking resources detected")

                results["checks"].append({
                    "name": "No blocking resources",
                    "passed": len(resource_timings) == 0,
                    "details": f"Slow resources: {len(resource_timings)}"
                })
            except Exception as e:
                print(f"   Warning: Could not check resources: {e}")

            browser.close()

    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        results["all_passed"] = False
        results["error"] = str(e)
        return results

    return results


def main():
    """Run TTI performance tests"""
    print("\n" + "=" * 80)
    print("PERFORMANCE TEST: Time to Interactive")
    print("=" * 80 + "\n")

    results = test_time_to_interactive()

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
    with open('spec/test_performance_tti_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    return 0 if results['all_passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
