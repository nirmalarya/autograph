#!/usr/bin/env python3
"""
AutoGraph v3 - Mobile Touch Targets Test Suite
Feature #667: Mobile-optimized touch targets

Tests comprehensive mobile touch target optimizations including:
- Media queries for different screen sizes
- Pointer detection (coarse vs fine)
- Touch target sizes (44px minimum, 48px on mobile)
- Spacing between interactive elements
- iOS and Android specific optimizations
- Touch feedback and gestures
"""

import os
import re
from pathlib import Path

# ANSI color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text):
    """Print a formatted header"""
    print(f"\n{BOLD}{BLUE}{text}{RESET}")

def print_success(text):
    """Print a success message"""
    print(f"{GREEN}✅ PASS{RESET} {text}")

def print_error(text):
    """Print an error message"""
    print(f"{RED}❌ FAIL{RESET} {text}")

def read_file(filepath):
    """Read file contents"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return None

def count_occurrences(content, pattern, flags=0):
    """Count pattern occurrences in content"""
    if not content:
        return 0
    matches = re.findall(pattern, content, flags)
    return len(matches)

def test_mobile_media_queries():
    """Test 1: Mobile media queries for different screen sizes"""
    print_header("TEST 1: Mobile Media Queries")
    
    globals_css = read_file('services/frontend/src/styles/globals.css')
    if not globals_css:
        print_error("globals.css not found")
        return False
    
    tests = [
        (r'@media\s*\(max-width:\s*768px\)', "Mobile breakpoint (max-width: 768px)"),
        (r'@media\s*\(max-width:\s*374px\)', "Small mobile breakpoint (max-width: 374px)"),
        (r'@media\s*\(min-width:\s*768px\)\s*and\s*\(max-width:\s*1024px\)', "Tablet breakpoint (768px-1024px)"),
        (r'@media\s*\(max-width:\s*768px\)\s*and\s*\(orientation:\s*landscape\)', "Mobile landscape orientation"),
    ]
    
    all_passed = True
    for pattern, description in tests:
        count = count_occurrences(globals_css, pattern, re.IGNORECASE)
        if count > 0:
            print_success(f"{description} found ({count} instances)")
        else:
            print_error(f"{description} not found")
            all_passed = False
    
    return all_passed

def test_pointer_detection():
    """Test 2: Pointer detection (coarse vs fine)"""
    print_header("TEST 2: Pointer Detection Media Queries")
    
    globals_css = read_file('services/frontend/src/styles/globals.css')
    if not globals_css:
        print_error("globals.css not found")
        return False
    
    tests = [
        (r'@media\s*\(pointer:\s*coarse\)', "Coarse pointer detection (touch devices)"),
        (r'@media\s*\(pointer:\s*fine\)', "Fine pointer detection (mouse/trackpad)"),
    ]
    
    all_passed = True
    for pattern, description in tests:
        count = count_occurrences(globals_css, pattern, re.IGNORECASE)
        if count > 0:
            print_success(f"{description} found ({count} instances)")
        else:
            print_error(f"{description} not found")
            all_passed = False
    
    return all_passed

def test_touch_target_sizes():
    """Test 3: Touch target sizes (44px minimum, 48px on mobile)"""
    print_header("TEST 3: Touch Target Sizes")
    
    globals_css = read_file('services/frontend/src/styles/globals.css')
    if not globals_css:
        print_error("globals.css not found")
        return False
    
    tests = [
        (r'min-height:\s*44px', "44px minimum height (WCAG AAA)"),
        (r'min-width:\s*44px', "44px minimum width (WCAG AAA)"),
        (r'min-height:\s*48px', "48px height for mobile"),
        (r'min-width:\s*48px', "48px width for mobile"),
        (r'min-height:\s*52px', "52px height for small mobile"),
        (r'min-height:\s*56px', "56px height for list items"),
    ]
    
    all_passed = True
    for pattern, description in tests:
        count = count_occurrences(globals_css, pattern, re.IGNORECASE)
        if count > 0:
            print_success(f"{description} found ({count} instances)")
        else:
            print_error(f"{description} not found")
            all_passed = False
    
    return all_passed

def test_mobile_font_sizes():
    """Test 4: Mobile font sizes (16px to prevent iOS zoom)"""
    print_header("TEST 4: Mobile Font Sizes")
    
    globals_css = read_file('services/frontend/src/styles/globals.css')
    if not globals_css:
        print_error("globals.css not found")
        return False
    
    # Check for 16px font size in mobile context
    mobile_section = re.search(r'@media\s*\(max-width:\s*768px\).*?(?=@media|@layer|\Z)', globals_css, re.DOTALL)
    if not mobile_section:
        print_error("Mobile media query section not found")
        return False
    
    mobile_content = mobile_section.group(0)
    
    tests = [
        (r'font-size:\s*16px.*Prevent iOS zoom', "16px font size with iOS zoom prevention comment"),
        (r'font-size:\s*16px', "16px font size"),
        (r'font-size:\s*17px', "17px font size for small mobile"),
    ]
    
    all_passed = True
    for pattern, description in tests:
        count = count_occurrences(globals_css, pattern, re.IGNORECASE)
        if count > 0:
            print_success(f"{description} found ({count} instances)")
        else:
            print_error(f"{description} not found")
            all_passed = False
    
    return all_passed

def test_touch_spacing():
    """Test 5: Spacing between interactive elements"""
    print_header("TEST 5: Touch Spacing")
    
    globals_css = read_file('services/frontend/src/styles/globals.css')
    if not globals_css:
        print_error("globals.css not found")
        return False
    
    tests = [
        (r'margin-left:\s*12px', "12px spacing between elements"),
        (r'\.touch-spacing', "Touch spacing utility class"),
        (r'\.touch-spacing-x', "Horizontal touch spacing utility"),
        (r'\.touch-spacing-y', "Vertical touch spacing utility"),
        (r'\.touch-safe', "Touch safe utility class"),
    ]
    
    all_passed = True
    for pattern, description in tests:
        count = count_occurrences(globals_css, pattern, re.IGNORECASE)
        if count > 0:
            print_success(f"{description} found ({count} instances)")
        else:
            print_error(f"{description} not found")
            all_passed = False
    
    return all_passed

def test_touch_feedback():
    """Test 6: Touch feedback and gestures"""
    print_header("TEST 6: Touch Feedback and Gestures")
    
    globals_css = read_file('services/frontend/src/styles/globals.css')
    if not globals_css:
        print_error("globals.css not found")
        return False
    
    tests = [
        (r':active', "Active state for touch feedback"),
        (r'transform:\s*scale\(0\.98\)', "Scale transform on active"),
        (r'opacity:\s*0\.8', "Opacity change on active"),
        (r'touch-action:\s*manipulation', "Touch action manipulation"),
        (r'-webkit-tap-highlight-color', "Webkit tap highlight color"),
        (r'-webkit-user-select:\s*none', "Prevent text selection on touch"),
    ]
    
    all_passed = True
    for pattern, description in tests:
        count = count_occurrences(globals_css, pattern, re.IGNORECASE)
        if count > 0:
            print_success(f"{description} found ({count} instances)")
        else:
            print_error(f"{description} not found")
            all_passed = False
    
    return all_passed

def test_ios_optimizations():
    """Test 7: iOS-specific optimizations"""
    print_header("TEST 7: iOS-Specific Optimizations")
    
    globals_css = read_file('services/frontend/src/styles/globals.css')
    if not globals_css:
        print_error("globals.css not found")
        return False
    
    tests = [
        (r'@supports\s*\(-webkit-touch-callout:\s*none\)', "iOS detection with @supports"),
        (r'-webkit-tap-highlight-color', "Webkit tap highlight color"),
        (r'-webkit-overflow-scrolling:\s*touch', "Webkit smooth scrolling"),
        (r'font-size:\s*16px.*Prevent iOS zoom', "16px font to prevent iOS zoom"),
    ]
    
    all_passed = True
    for pattern, description in tests:
        count = count_occurrences(globals_css, pattern, re.IGNORECASE)
        if count > 0:
            print_success(f"{description} found ({count} instances)")
        else:
            print_error(f"{description} not found")
            all_passed = False
    
    return all_passed

def test_android_optimizations():
    """Test 8: Android-specific optimizations"""
    print_header("TEST 8: Android-Specific Optimizations")
    
    globals_css = read_file('services/frontend/src/styles/globals.css')
    if not globals_css:
        print_error("globals.css not found")
        return False
    
    tests = [
        (r'@supports\s*not\s*\(-webkit-touch-callout:\s*none\)', "Android detection with @supports not"),
        (r'background-color:\s*rgba\(0,\s*0,\s*0,\s*0\.05\)', "Android active state background"),
    ]
    
    all_passed = True
    for pattern, description in tests:
        count = count_occurrences(globals_css, pattern, re.IGNORECASE)
        if count > 0:
            print_success(f"{description} found ({count} instances)")
        else:
            print_error(f"{description} not found")
            all_passed = False
    
    return all_passed

def test_touch_utility_classes():
    """Test 9: Touch utility classes"""
    print_header("TEST 9: Touch Utility Classes")
    
    globals_css = read_file('services/frontend/src/styles/globals.css')
    if not globals_css:
        print_error("globals.css not found")
        return False
    
    tests = [
        (r'\.touch-target-small', "Touch target small utility"),
        (r'\.touch-target-medium', "Touch target medium utility"),
        (r'\.touch-target-large', "Touch target large utility"),
        (r'\.touch-hit-area', "Touch hit area utility"),
        (r'\.swipeable', "Swipeable utility"),
    ]
    
    all_passed = True
    for pattern, description in tests:
        count = count_occurrences(globals_css, pattern, re.IGNORECASE)
        if count > 0:
            print_success(f"{description} found ({count} instances)")
        else:
            print_error(f"{description} not found")
            all_passed = False
    
    return all_passed

def test_form_elements_mobile():
    """Test 10: Mobile-optimized form elements"""
    print_header("TEST 10: Mobile-Optimized Form Elements")
    
    globals_css = read_file('services/frontend/src/styles/globals.css')
    if not globals_css:
        print_error("globals.css not found")
        return False
    
    # Check mobile section for form elements
    mobile_section = re.search(r'@media\s*\(max-width:\s*768px\).*?(?=@media|@layer|\Z)', globals_css, re.DOTALL)
    if not mobile_section:
        print_error("Mobile media query section not found")
        return False
    
    mobile_content = mobile_section.group(0)
    
    tests = [
        (r'input\[type="text"\]', "Text input styling"),
        (r'input\[type="email"\]', "Email input styling"),
        (r'input\[type="password"\]', "Password input styling"),
        (r'input\[type="checkbox"\]', "Checkbox styling"),
        (r'input\[type="radio"\]', "Radio button styling"),
        (r'textarea', "Textarea styling"),
        (r'select', "Select dropdown styling"),
    ]
    
    all_passed = True
    for pattern, description in tests:
        count = count_occurrences(globals_css, pattern, re.IGNORECASE)
        if count > 0:
            print_success(f"{description} found ({count} instances)")
        else:
            print_error(f"{description} not found")
            all_passed = False
    
    return all_passed

def test_navigation_mobile():
    """Test 11: Mobile-optimized navigation"""
    print_header("TEST 11: Mobile-Optimized Navigation")
    
    globals_css = read_file('services/frontend/src/styles/globals.css')
    if not globals_css:
        print_error("globals.css not found")
        return False
    
    tests = [
        (r'nav\s+a', "Navigation link styling"),
        (r'nav\s+button', "Navigation button styling"),
        (r'\[role="navigation"\]', "ARIA navigation role"),
        (r'\[role="toolbar"\]', "ARIA toolbar role"),
    ]
    
    all_passed = True
    for pattern, description in tests:
        count = count_occurrences(globals_css, pattern, re.IGNORECASE)
        if count > 0:
            print_success(f"{description} found ({count} instances)")
        else:
            print_error(f"{description} not found")
            all_passed = False
    
    return all_passed

def test_feature_comment():
    """Test 12: Feature #667 documentation comment"""
    print_header("TEST 12: Feature Documentation")
    
    globals_css = read_file('services/frontend/src/styles/globals.css')
    if not globals_css:
        print_error("globals.css not found")
        return False
    
    tests = [
        (r'MOBILE-OPTIMIZED TOUCH TARGETS', "Feature title comment"),
        (r'Feature #667', "Feature number reference"),
        (r'WCAG 2\.1 Level AAA', "WCAG compliance reference"),
        (r'44x44px minimum', "Minimum size specification"),
    ]
    
    all_passed = True
    for pattern, description in tests:
        count = count_occurrences(globals_css, pattern, re.IGNORECASE)
        if count > 0:
            print_success(f"{description} found ({count} instances)")
        else:
            print_error(f"{description} not found")
            all_passed = False
    
    return all_passed

def main():
    """Run all tests"""
    print(f"\n{BOLD}{'='*80}{RESET}")
    print(f"{BOLD}AutoGraph v3 - Mobile Touch Targets Test Suite{RESET}")
    print(f"{BOLD}Testing Feature #667: Mobile-optimized touch targets{RESET}")
    print(f"{BOLD}{'='*80}{RESET}")
    
    tests = [
        test_mobile_media_queries,
        test_pointer_detection,
        test_touch_target_sizes,
        test_mobile_font_sizes,
        test_touch_spacing,
        test_touch_feedback,
        test_ios_optimizations,
        test_android_optimizations,
        test_touch_utility_classes,
        test_form_elements_mobile,
        test_navigation_mobile,
        test_feature_comment,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print_error(f"Test failed with exception: {e}")
            results.append(False)
    
    # Print summary
    passed = sum(results)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"\n{BOLD}{'='*80}{RESET}")
    print(f"{BOLD}Results: {passed}/{total} tests passed ({percentage:.1f}%){RESET}")
    print(f"{BOLD}{'='*80}{RESET}\n")
    
    if passed == total:
        print(f"{GREEN}{BOLD}✅ SUCCESS: All mobile touch target tests passed!{RESET}\n")
        return 0
    else:
        print(f"{RED}{BOLD}❌ FAILURE: Some tests failed. Please review the output above.{RESET}\n")
        return 1

if __name__ == "__main__":
    exit(main())
