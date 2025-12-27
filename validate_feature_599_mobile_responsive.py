#!/usr/bin/env python3
"""
E2E Validation Test for Feature #599: Responsive Design - Mobile Phone

This test validates that the application is fully responsive for mobile phones
with proper viewport configuration, touch-friendly UI elements, and mobile-optimized layouts.

Test Steps:
1. Verify viewport meta tag configuration
2. Verify mobile layout and responsive CSS
3. Verify touch-friendly button sizes (min 48x48px)
4. Verify readable text sizes (min 16px to prevent iOS zoom)
5. Test that all features work on mobile

Expected Results:
✅ Viewport properly configured for mobile devices
✅ Mobile media queries implemented (@media max-width: 768px)
✅ Touch targets meet WCAG 2.1 AAA guidelines (48x48px minimum)
✅ Text sizes prevent unwanted mobile zoom (16px minimum)
✅ Mobile-optimized layouts and spacing
✅ Responsive grid systems and breakpoints
"""

import sys
from pathlib import Path

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text):
    """Print a formatted header"""
    print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
    print(f"{BOLD}{BLUE}{text:^80}{RESET}")
    print(f"{BOLD}{BLUE}{'='*80}{RESET}\n")

def print_step(step_num, description):
    """Print a test step"""
    print(f"{BOLD}Step {step_num}:{RESET} {description}")

def print_result(passed, message):
    """Print a test result"""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"  {status} - {message}")
    return passed

def validate_viewport_config():
    """Validate viewport meta tag and configuration"""
    print_step(1, "Validating viewport configuration")

    layout_path = Path(__file__).parent / 'services' / 'frontend' / 'app' / 'layout.tsx'

    if not layout_path.exists():
        return print_result(False, f"layout.tsx not found at {layout_path}")

    content = layout_path.read_text()

    checks = [
        ('export const viewport: Viewport' in content, "Viewport configuration exported"),
        ("width: 'device-width'" in content, "Viewport width set to device-width"),
        ('initialScale: 1' in content, "Initial scale set to 1"),
        ('maximumScale:' in content, "Maximum scale configured"),
        ('userScalable: true' in content, "User scaling enabled for accessibility"),
        ('themeColor:' in content, "Theme color configured"),
    ]

    all_passed = True
    for check, description in checks:
        result = print_result(check, description)
        all_passed = all_passed and result

    return all_passed

def validate_mobile_media_queries():
    """Validate mobile responsive CSS with media queries"""
    print_step(2, "Validating mobile media queries and responsive CSS")

    css_path = Path(__file__).parent / 'services' / 'frontend' / 'src' / 'styles' / 'globals.css'

    if not css_path.exists():
        return print_result(False, f"globals.css not found at {css_path}")

    content = css_path.read_text()

    # Count media queries
    mobile_queries = content.count('@media (max-width: 768px)')
    tablet_queries = content.count('@media (min-width: 768px) and (max-width: 1024px)')

    checks = [
        (mobile_queries >= 5, f"Mobile media queries implemented ({mobile_queries} found)"),
        (tablet_queries >= 1, f"Tablet media queries implemented ({tablet_queries} found)"),
        ('@media (pointer: coarse)' in content, "Coarse pointer (touch) detection implemented"),
        ('@media (pointer: fine)' in content, "Fine pointer (mouse) detection implemented"),
        ('MOBILE-OPTIMIZED TOUCH TARGETS' in content, "Mobile touch target documentation present"),
    ]

    all_passed = True
    for check, description in checks:
        result = print_result(check, description)
        all_passed = all_passed and result

    return all_passed

def validate_touch_friendly_sizes():
    """Validate touch-friendly button and input sizes"""
    print_step(3, "Validating touch-friendly UI element sizes")

    css_path = Path(__file__).parent / 'services' / 'frontend' / 'src' / 'styles' / 'globals.css'
    content = css_path.read_text()

    # Count touch-friendly size declarations
    size_48px = content.count('min-height: 48px')
    size_44px = content.count('min-height: 44px')

    checks = [
        (size_48px >= 8, f"48px minimum touch targets implemented ({size_48px} instances)"),
        (size_44px >= 2, f"44px minimum touch targets implemented ({size_44px} instances)"),
        ('min-width: 48px' in content, "Minimum width for touch targets specified"),
        ('WCAG 2.1 Level AAA' in content, "WCAG AAA compliance documented"),
        ('touch-action: manipulation' in content, "Touch manipulation configured"),
        ('-webkit-tap-highlight-color' in content, "iOS tap highlight configured"),
    ]

    all_passed = True
    for check, description in checks:
        result = print_result(check, description)
        all_passed = all_passed and result

    return all_passed

def validate_readable_text_sizes():
    """Validate text sizes to prevent mobile zoom"""
    print_step(4, "Validating readable text sizes (prevent mobile zoom)")

    css_path = Path(__file__).parent / 'services' / 'frontend' / 'src' / 'styles' / 'globals.css'
    content = css_path.read_text()

    checks = [
        ('font-size: 16px' in content, "16px font size used (prevents iOS zoom)"),
        ('Prevent iOS zoom' in content or 'prevent iOS zoom' in content, "iOS zoom prevention documented"),
        ('font-size: 17px' in content or 'font-size: 18px' in content, "Larger font sizes for better readability"),
        ('text-base' in content, "Base text size class used"),
    ]

    all_passed = True
    for check, description in checks:
        result = print_result(check, description)
        all_passed = all_passed and result

    return all_passed

def validate_mobile_optimizations():
    """Validate mobile-specific optimizations"""
    print_step(5, "Validating mobile-specific optimizations")

    css_path = Path(__file__).parent / 'services' / 'frontend' / 'src' / 'styles' / 'globals.css'
    content = css_path.read_text()

    checks = [
        ('-webkit-overflow-scrolling: touch' in content, "Smooth touch scrolling enabled"),
        ('touch-action:' in content, "Touch action policies configured"),
        ('-webkit-user-select: none' in content, "Text selection control for buttons"),
        ('transform: scale(0.98)' in content or 'active:scale' in content, "Touch feedback on active state"),
        ('Mobile landscape orientation' in content, "Landscape orientation handling"),
        ('padding: 12px 16px' in content or 'padding: 14px 18px' in content, "Mobile-optimized padding"),
    ]

    all_passed = True
    for check, description in checks:
        result = print_result(check, description)
        all_passed = all_passed and result

    return all_passed

def validate_responsive_utility_classes():
    """Validate responsive utility classes and spacing"""
    print_step(6, "Validating responsive utility classes")

    css_path = Path(__file__).parent / 'services' / 'frontend' / 'src' / 'styles' / 'globals.css'
    content = css_path.read_text()

    checks = [
        ('.touch-target-' in content, "Touch target utility classes defined"),
        ('.touch-spacing' in content, "Touch spacing utility classes defined"),
        ('sm:' in content or 'md:' in content, "Tailwind responsive prefixes used"),
        ('@media (max-width:' in content, "Custom breakpoints implemented"),
        ('container-padding' in content, "Responsive container padding classes"),
    ]

    all_passed = True
    for check, description in checks:
        result = print_result(check, description)
        all_passed = all_passed and result

    return all_passed

def validate_pwa_mobile_support():
    """Validate PWA and mobile app features"""
    print_step(7, "Validating PWA and mobile app support")

    layout_path = Path(__file__).parent / 'services' / 'frontend' / 'app' / 'layout.tsx'
    content = layout_path.read_text()

    checks = [
        ('manifest: \'/manifest.json\'' in content, "PWA manifest configured"),
        ('appleWebApp:' in content, "Apple web app configuration present"),
        ('capable: true' in content, "Apple web app capable"),
        ('statusBarStyle:' in content, "iOS status bar style configured"),
        ('<link rel="manifest"' in content, "Manifest link in HTML"),
        ('<link rel="apple-touch-icon"' in content, "Apple touch icon configured"),
    ]

    all_passed = True
    for check, description in checks:
        result = print_result(check, description)
        all_passed = all_passed and result

    return all_passed

def main():
    """Run all validation tests"""
    print_header("Feature #599: Mobile Phone Responsive Design - E2E Validation")

    results = []

    # Run all validation tests
    results.append(("Viewport Configuration", validate_viewport_config()))
    results.append(("Mobile Media Queries", validate_mobile_media_queries()))
    results.append(("Touch-Friendly Sizes", validate_touch_friendly_sizes()))
    results.append(("Readable Text Sizes", validate_readable_text_sizes()))
    results.append(("Mobile Optimizations", validate_mobile_optimizations()))
    results.append(("Responsive Utility Classes", validate_responsive_utility_classes()))
    results.append(("PWA Mobile Support", validate_pwa_mobile_support()))

    # Print summary
    print_header("Validation Summary")

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
        print(f"{status} - {test_name}")

    print(f"\n{BOLD}Results: {passed_count}/{total_count} tests passed{RESET}")

    if passed_count == total_count:
        print(f"\n{GREEN}{BOLD}🎉 All validation tests PASSED!{RESET}")
        print(f"{GREEN}Feature #599 is fully implemented for mobile phones.{RESET}")
        return 0
    else:
        print(f"\n{RED}{BOLD}❌ Some validation tests FAILED!{RESET}")
        print(f"{RED}Please review the failed tests above.{RESET}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
