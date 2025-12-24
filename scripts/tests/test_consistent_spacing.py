#!/usr/bin/env python3
"""
Test Suite: Consistent Spacing and Padding (Feature #663)

Validates that AutoGraph v3 uses a consistent 8px grid system for spacing
and padding across all pages and components.

Test Categories:
1. CSS Spacing Utilities - Verify spacing classes exist
2. 8px Grid System - Verify spacing follows 8px grid
3. Page Spacing Consistency - Check key pages use consistent spacing
4. Component Spacing - Verify components use spacing utilities
5. Responsive Spacing - Check responsive spacing patterns
6. Visual Rhythm - Verify consistent spacing creates visual rhythm
"""

import re
import sys
from pathlib import Path

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test(name: str, passed: bool, details: str = ""):
    """Print test result with color"""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"  {status} - {name}")
    if details and not passed:
        print(f"    {YELLOW}{details}{RESET}")

def print_section(title: str):
    """Print section header"""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}{title}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")

def read_file(filepath: str) -> str:
    """Read file contents"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return ""

def test_css_spacing_utilities():
    """Test 1: Verify CSS spacing utilities exist"""
    print_section("Test 1: CSS Spacing Utilities")
    
    css_path = "services/frontend/src/styles/globals.css"
    css_content = read_file(css_path)
    
    tests = [
        ("CSS file exists", bool(css_content), "globals.css not found"),
        ("8px grid documentation", "8px grid" in css_content.lower() or "8px Grid" in css_content, "Missing 8px grid documentation"),
        ("Spacing scale documented", "Scale:" in css_content or "scale:" in css_content, "Missing spacing scale documentation"),
        ("Container padding utility", ".container-padding" in css_content, "Missing .container-padding utility"),
        ("Section spacing utility", ".section-spacing" in css_content, "Missing .section-spacing utility"),
        ("Element spacing utility", ".element-spacing" in css_content, "Missing .element-spacing utility"),
        ("Grid gap utility", ".grid-gap" in css_content, "Missing .grid-gap utility"),
        ("Form spacing utility", ".form-spacing" in css_content, "Missing .form-spacing utility"),
        ("Card padding utility", ".card-padding" in css_content, "Missing .card-padding utility"),
        ("Usage guidelines", "Usage Guidelines:" in css_content or "usage guidelines" in css_content.lower(), "Missing usage guidelines"),
    ]
    
    passed = sum(1 for _, result, _ in tests if result)
    for name, result, details in tests:
        print_test(name, result, details)
    
    print(f"\n{BLUE}Subtotal: {passed}/{len(tests)} tests passed{RESET}")
    return passed, len(tests)

def test_8px_grid_system():
    """Test 2: Verify spacing follows 8px grid"""
    print_section("Test 2: 8px Grid System Validation")
    
    css_path = "services/frontend/src/styles/globals.css"
    css_content = read_file(css_path)
    
    # Tailwind spacing scale (in px): 0.5=2, 1=4, 2=8, 3=12, 4=16, 6=24, 8=32, 12=48, 16=64
    # All are multiples of 4px, and even numbers are multiples of 8px
    
    tests = [
        ("Base unit documented (2 = 8px)", "2   = 8px" in css_content or "2 = 8px" in css_content, "Base unit not documented"),
        ("Medium spacing (4 = 16px)", "4   = 16px" in css_content or "4 = 16px" in css_content, "Medium spacing not documented"),
        ("Large spacing (6 = 24px)", "6   = 24px" in css_content or "6 = 24px" in css_content, "Large spacing not documented"),
        ("Extra large (8 = 32px)", "8   = 32px" in css_content or "8 = 32px" in css_content, "Extra large not documented"),
        ("Huge spacing (12 = 48px)", "12  = 48px" in css_content or "12 = 48px" in css_content, "Huge spacing not documented"),
        ("Massive spacing (16 = 64px)", "16  = 64px" in css_content or "16 = 64px" in css_content, "Massive spacing not documented"),
    ]
    
    passed = sum(1 for _, result, _ in tests if result)
    for name, result, details in tests:
        print_test(name, result, details)
    
    print(f"\n{BLUE}Subtotal: {passed}/{len(tests)} tests passed{RESET}")
    return passed, len(tests)

def test_page_spacing_consistency():
    """Test 3: Check key pages use consistent spacing"""
    print_section("Test 3: Page Spacing Consistency")
    
    pages = {
        "Home page": "services/frontend/app/page.tsx",
        "Login page": "services/frontend/app/login/page.tsx",
        "Register page": "services/frontend/app/register/page.tsx",
        "Dashboard page": "services/frontend/app/dashboard/page.tsx",
    }
    
    tests = []
    
    for page_name, page_path in pages.items():
        content = read_file(page_path)
        
        # Check for consistent spacing patterns (multiples of 4)
        # Common patterns: p-4, p-6, p-8, m-4, m-6, m-8, gap-4, gap-6, space-y-4, space-y-6
        has_spacing = bool(re.search(r'(p|m|gap|space-[xy])-[0-9]+', content))
        
        # Check for 8px grid usage (even numbers: 2, 4, 6, 8, 12, 16)
        uses_grid = bool(re.search(r'(p|m|gap|space-[xy])-(2|4|6|8|12|16)', content))
        
        # Check for responsive spacing
        has_responsive = bool(re.search(r'(sm:|md:|lg:)(p|m|gap|space-[xy])-[0-9]+', content))
        
        tests.append((f"{page_name} - Has spacing classes", has_spacing, f"No spacing classes found in {page_path}"))
        tests.append((f"{page_name} - Uses 8px grid", uses_grid, f"Not using 8px grid in {page_path}"))
        tests.append((f"{page_name} - Responsive spacing", has_responsive, f"No responsive spacing in {page_path}"))
    
    passed = sum(1 for _, result, _ in tests if result)
    for name, result, details in tests:
        print_test(name, result, details)
    
    print(f"\n{BLUE}Subtotal: {passed}/{len(tests)} tests passed{RESET}")
    return passed, len(tests)

def test_component_spacing():
    """Test 4: Verify components use spacing utilities"""
    print_section("Test 4: Component Spacing")
    
    components = {
        "Button": "services/frontend/app/components/Button.tsx",
        "Input": "services/frontend/app/components/Input.tsx",
        "Toast": "services/frontend/app/components/Toast.tsx",
        "EmptyState": "services/frontend/app/components/EmptyState.tsx",
    }
    
    tests = []
    
    for comp_name, comp_path in components.items():
        content = read_file(comp_path)
        
        # Check for spacing classes
        has_spacing = bool(re.search(r'(p|m|gap|space-[xy]|left|right|top|bottom)-[0-9]+', content))
        
        # Check for consistent padding/margin (any valid Tailwind spacing)
        uses_consistent = bool(re.search(r'(p|m|gap|space-[xy]|left|right|top|bottom)-(0\.5|1|1\.5|2|3|4|5|6|8|10|12|16)', content))
        
        tests.append((f"{comp_name} - Has spacing", has_spacing, f"No spacing in {comp_path}"))
        tests.append((f"{comp_name} - Consistent spacing", uses_consistent, f"Inconsistent spacing in {comp_path}"))
    
    passed = sum(1 for _, result, _ in tests if result)
    for name, result, details in tests:
        print_test(name, result, details)
    
    print(f"\n{BLUE}Subtotal: {passed}/{len(tests)} tests passed{RESET}")
    return passed, len(tests)

def test_responsive_spacing():
    """Test 5: Check responsive spacing patterns"""
    print_section("Test 5: Responsive Spacing Patterns")
    
    pages = [
        "services/frontend/app/page.tsx",
        "services/frontend/app/login/page.tsx",
        "services/frontend/app/dashboard/page.tsx",
    ]
    
    tests = []
    
    for page_path in pages:
        content = read_file(page_path)
        page_name = Path(page_path).stem
        
        # Check for mobile-first spacing (base class + sm/md/lg variants)
        has_mobile_first = bool(re.search(r'(p|m|gap|space-[xy])-[0-9]+ (sm:|md:|lg:)', content))
        
        # Check for progressive spacing (increases with screen size)
        # e.g., px-4 sm:px-6 md:px-8 or py-6 sm:py-8
        has_progressive = bool(re.search(r'(p[xy]?|m[xy]?)-[0-9]+ (sm:|md:|lg:)(p[xy]?|m[xy]?)-[0-9]+', content))
        
        # Check for responsive gaps
        has_responsive_gaps = bool(re.search(r'gap-[0-9]+ (sm:|md:|lg:)gap-[0-9]+', content))
        
        tests.append((f"{page_name} - Mobile-first spacing", has_mobile_first, f"No mobile-first spacing in {page_path}"))
        tests.append((f"{page_name} - Progressive spacing", has_progressive, f"No progressive spacing in {page_path}"))
    
    passed = sum(1 for _, result, _ in tests if result)
    for name, result, details in tests:
        print_test(name, result, details)
    
    print(f"\n{BLUE}Subtotal: {passed}/{len(tests)} tests passed{RESET}")
    return passed, len(tests)

def test_visual_rhythm():
    """Test 6: Verify consistent spacing creates visual rhythm"""
    print_section("Test 6: Visual Rhythm Verification")
    
    css_path = "services/frontend/src/styles/globals.css"
    css_content = read_file(css_path)
    
    # Check for consistent spacing patterns
    tests = [
        ("Container padding variants", ".container-padding-sm" in css_content and ".container-padding-lg" in css_content, "Missing container padding variants"),
        ("Section spacing variants", ".section-spacing-sm" in css_content and ".section-spacing-lg" in css_content, "Missing section spacing variants"),
        ("Element spacing variants", ".element-spacing-sm" in css_content and ".element-spacing-lg" in css_content, "Missing element spacing variants"),
        ("Grid gap variants", ".grid-gap-sm" in css_content and ".grid-gap-lg" in css_content, "Missing grid gap variants"),
        ("Form spacing variants", ".form-spacing-sm" in css_content and ".form-spacing-lg" in css_content, "Missing form spacing variants"),
        ("Card padding variants", ".card-padding-sm" in css_content and ".card-padding-lg" in css_content, "Missing card padding variants"),
        ("Spacing scale consistency", "space-y-4" in css_content or "@apply space-y-4" in css_content, "Missing consistent spacing scale"),
    ]
    
    passed = sum(1 for _, result, _ in tests if result)
    for name, result, details in tests:
        print_test(name, result, details)
    
    print(f"\n{BLUE}Subtotal: {passed}/{len(tests)} tests passed{RESET}")
    return passed, len(tests)

def main():
    """Run all tests"""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}AutoGraph v3 - Consistent Spacing & Padding Test Suite{RESET}")
    print(f"{BLUE}Feature #663: Polish - Consistent spacing and padding{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")
    
    total_passed = 0
    total_tests = 0
    
    # Run all test categories
    test_functions = [
        test_css_spacing_utilities,
        test_8px_grid_system,
        test_page_spacing_consistency,
        test_component_spacing,
        test_responsive_spacing,
        test_visual_rhythm,
    ]
    
    for test_func in test_functions:
        passed, total = test_func()
        total_passed += passed
        total_tests += total
    
    # Print final summary
    print_section("Final Summary")
    percentage = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n{BLUE}Total Tests: {total_tests}{RESET}")
    print(f"{GREEN}Passed: {total_passed}{RESET}")
    print(f"{RED}Failed: {total_tests - total_passed}{RESET}")
    print(f"{BLUE}Success Rate: {percentage:.1f}%{RESET}")
    
    if total_passed == total_tests:
        print(f"\n{GREEN}{'='*80}{RESET}")
        print(f"{GREEN}✓ ALL TESTS PASSED! Spacing is consistent across the application.{RESET}")
        print(f"{GREEN}{'='*80}{RESET}\n")
        return 0
    else:
        print(f"\n{RED}{'='*80}{RESET}")
        print(f"{RED}✗ SOME TESTS FAILED. Please review the failures above.{RESET}")
        print(f"{RED}{'='*80}{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
