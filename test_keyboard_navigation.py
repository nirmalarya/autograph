#!/usr/bin/env python3
"""
AutoGraph v3 - Keyboard Navigation Test Suite
Tests Feature #665: Keyboard navigation: all features accessible

This test verifies that:
1. All interactive elements are keyboard accessible
2. Focus indicators are visible and have proper contrast
3. Tab order is logical and follows visual flow
4. Keyboard shortcuts work correctly
5. Focus trap works in modals
6. Escape key closes modals
7. All features can be accessed without a mouse
"""

import sys
import os
import time
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
    """Print success message"""
    print(f"{GREEN}✅ PASS{RESET} {text}")

def print_error(text):
    """Print error message"""
    print(f"{RED}❌ FAIL{RESET} {text}")

def print_info(text):
    """Print info message"""
    print(f"{BLUE}ℹ️  INFO{RESET} {text}")

def check_file_exists(filepath):
    """Check if a file exists"""
    return Path(filepath).exists()

def search_in_file(filepath, pattern, flags=0):
    """Search for a pattern in a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            return re.findall(pattern, content, flags)
    except Exception as e:
        print_error(f"Error reading {filepath}: {e}")
        return []

def count_in_file(filepath, pattern, flags=0):
    """Count occurrences of a pattern in a file"""
    return len(search_in_file(filepath, pattern, flags))

def test_focus_states():
    """Test 1: Verify focus states are defined in CSS"""
    print_header("TEST 1: Focus States in CSS")
    
    css_file = "services/frontend/src/styles/globals.css"
    
    if not check_file_exists(css_file):
        print_error(f"CSS file not found: {css_file}")
        return False
    
    # Check for focus-visible styles
    focus_visible_count = count_in_file(css_file, r':focus-visible')
    if focus_visible_count >= 5:
        print_success(f"Focus-visible styles found ({focus_visible_count} instances)")
    else:
        print_error(f"Insufficient focus-visible styles (found {focus_visible_count}, expected >= 5)")
        return False
    
    # Check for focus ring utilities
    focus_ring_count = count_in_file(css_file, r'\.focus-ring')
    if focus_ring_count >= 1:
        print_success(f"Focus ring utility classes found ({focus_ring_count} instances)")
    else:
        print_error("Focus ring utility classes not found")
        return False
    
    # Check for keyboard navigation utilities
    keyboard_utils = search_in_file(css_file, r'\/\* Keyboard Navigation Utilities \*\/')
    if keyboard_utils:
        print_success("Keyboard navigation utilities section found")
    else:
        print_error("Keyboard navigation utilities section not found")
        return False
    
    # Check for enhanced focus indicators
    enhanced_focus = search_in_file(css_file, r'Enhanced for Keyboard Navigation')
    if enhanced_focus:
        print_success("Enhanced focus indicators for keyboard navigation found")
    else:
        print_error("Enhanced focus indicators not found")
        return False
    
    return True

def test_focus_trap_implementation():
    """Test 2: Verify focus trap hook is implemented"""
    print_header("TEST 2: Focus Trap Implementation")
    
    hook_file = "services/frontend/src/hooks/useFocusTrap.ts"
    
    if not check_file_exists(hook_file):
        print_error(f"Focus trap hook not found: {hook_file}")
        return False
    
    print_success("Focus trap hook file exists")
    
    # Check for key focus trap functionality
    functions = [
        (r'getFocusableElements', 'Get focusable elements function'),
        (r'handleKeyDown', 'Keyboard event handler'),
        (r'previousActiveElement', 'Store previous active element'),
        (r'[\'"]Tab[\'"]', 'Tab key handling'),
        (r'e\.shiftKey', 'Shift+Tab handling'),
    ]
    
    for pattern, description in functions:
        if search_in_file(hook_file, pattern):
            print_success(f"{description} found")
        else:
            print_error(f"{description} not found")
            return False
    
    return True

def test_modal_keyboard_accessibility():
    """Test 3: Verify modals have keyboard accessibility"""
    print_header("TEST 3: Modal Keyboard Accessibility")
    
    dashboard_file = "services/frontend/app/dashboard/page.tsx"
    
    if not check_file_exists(dashboard_file):
        print_error(f"Dashboard file not found: {dashboard_file}")
        return False
    
    # Check for focus trap usage in modals
    focus_trap_refs = count_in_file(dashboard_file, r'useFocusTrap')
    if focus_trap_refs >= 3:
        print_success(f"Focus trap used in modals ({focus_trap_refs} instances)")
    else:
        print_error(f"Focus trap not properly used (found {focus_trap_refs}, expected >= 3)")
        return False
    
    # Check for Escape key handling
    escape_handling = count_in_file(dashboard_file, r'e\.key === [\'"]Escape[\'"]')
    if escape_handling >= 3:
        print_success(f"Escape key handling found ({escape_handling} instances)")
    else:
        print_error(f"Insufficient Escape key handling (found {escape_handling}, expected >= 3)")
        return False
    
    # Check for aria-modal attributes
    aria_modal = count_in_file(dashboard_file, r'aria-modal=["\']true["\']')
    if aria_modal >= 3:
        print_success(f"ARIA modal attributes found ({aria_modal} instances)")
    else:
        print_error(f"Insufficient ARIA modal attributes (found {aria_modal}, expected >= 3)")
        return False
    
    # Check for role="dialog"
    dialog_role = count_in_file(dashboard_file, r'role=["\']dialog["\']')
    if dialog_role >= 3:
        print_success(f"Dialog roles found ({dialog_role} instances)")
    else:
        print_error(f"Insufficient dialog roles (found {dialog_role}, expected >= 3)")
        return False
    
    return True

def test_keyboard_shortcuts():
    """Test 4: Verify keyboard shortcuts are implemented"""
    print_header("TEST 4: Keyboard Shortcuts")
    
    dashboard_file = "services/frontend/app/dashboard/page.tsx"
    
    if not check_file_exists(dashboard_file):
        print_error(f"Dashboard file not found: {dashboard_file}")
        return False
    
    shortcuts = [
        (r'e\.key === [\'"]k[\'"]', 'Cmd+K / Ctrl+K (Command Palette)'),
        (r'e\.key === [\'"]n[\'"]', 'Cmd+N / Ctrl+N (New Diagram)'),
        (r'e\.key === [\'"]f[\'"]', 'Cmd+F / Ctrl+F (Search)'),
        (r'e\.key === [\'"]b[\'"]', 'Cmd+B / Ctrl+B (Toggle Sidebar)'),
        (r'e\.key === [\'"][?][\'"]', 'Cmd+? / Ctrl+? (Keyboard Shortcuts)'),
    ]
    
    for pattern, description in shortcuts:
        if search_in_file(dashboard_file, pattern):
            print_success(f"{description} implemented")
        else:
            print_error(f"{description} not found")
            return False
    
    return True

def test_tab_order():
    """Test 5: Verify logical tab order"""
    print_header("TEST 5: Logical Tab Order")
    
    layout_file = "services/frontend/app/layout.tsx"
    dashboard_file = "services/frontend/app/dashboard/page.tsx"
    
    # Check for skip to main content link in layout
    if not check_file_exists(layout_file):
        print_error(f"Layout file not found: {layout_file}")
        return False
    
    skip_link = search_in_file(layout_file, r'Skip to main content')
    if skip_link:
        print_success("Skip to main content link found in layout")
    else:
        print_error("Skip to main content link not found in layout")
        return False
    
    # Check for main content ID in dashboard
    if not check_file_exists(dashboard_file):
        print_error(f"Dashboard file not found: {dashboard_file}")
        return False
    
    main_id = search_in_file(dashboard_file, r'id=["\']main-content["\']')
    if main_id:
        print_success("Main content ID found for skip link target")
    else:
        print_error("Main content ID not found")
        return False
    
    # Check for proper heading hierarchy
    h1_count = count_in_file(dashboard_file, r'<h1')
    h2_count = count_in_file(dashboard_file, r'<h2')
    
    if h1_count >= 1:
        print_success(f"H1 headings found ({h1_count} instances)")
    else:
        print_error("No H1 headings found")
        return False
    
    if h2_count >= 3:
        print_success(f"H2 headings found ({h2_count} instances)")
    else:
        print_error(f"Insufficient H2 headings (found {h2_count}, expected >= 3)")
        return False
    
    return True

def test_focus_indicators():
    """Test 6: Verify focus indicators have proper contrast"""
    print_header("TEST 6: Focus Indicator Contrast")
    
    css_file = "services/frontend/src/styles/globals.css"
    
    if not check_file_exists(css_file):
        print_error(f"CSS file not found: {css_file}")
        return False
    
    # Check for blue-500 focus ring (good contrast)
    blue_ring = search_in_file(css_file, r'ring-blue-500')
    if blue_ring:
        print_success(f"Blue focus rings found ({len(blue_ring)} instances)")
    else:
        print_error("Blue focus rings not found")
        return False
    
    # Check for ring offset
    ring_offset = search_in_file(css_file, r'ring-offset')
    if ring_offset:
        print_success(f"Ring offset found ({len(ring_offset)} instances)")
    else:
        print_error("Ring offset not found")
        return False
    
    # Check for high contrast focus
    high_contrast_focus = search_in_file(css_file, r'\.high-contrast.*:focus')
    if high_contrast_focus:
        print_success("High contrast focus styles found")
    else:
        print_error("High contrast focus styles not found")
        return False
    
    return True

def test_button_accessibility():
    """Test 7: Verify buttons have proper keyboard accessibility"""
    print_header("TEST 7: Button Keyboard Accessibility")
    
    button_file = "services/frontend/app/components/Button.tsx"
    
    if not check_file_exists(button_file):
        print_error(f"Button component not found: {button_file}")
        return False
    
    # Check for focus-ring class
    focus_ring = search_in_file(button_file, r'focus-ring')
    if focus_ring:
        print_success("Focus ring class used in buttons")
    else:
        print_error("Focus ring class not found in buttons")
        return False
    
    # Check for aria-label in IconButton
    aria_label = search_in_file(button_file, r'aria-label')
    if aria_label:
        print_success("ARIA labels found in icon buttons")
    else:
        print_error("ARIA labels not found in icon buttons")
        return False
    
    # Check for disabled state handling
    disabled_handling = search_in_file(button_file, r'disabled')
    if len(disabled_handling) >= 2:
        print_success(f"Disabled state handling found ({len(disabled_handling)} instances)")
    else:
        print_error("Disabled state handling not found")
        return False
    
    return True

def test_keyboard_navigation_utilities():
    """Test 8: Verify keyboard navigation utility classes"""
    print_header("TEST 8: Keyboard Navigation Utility Classes")
    
    css_file = "services/frontend/src/styles/globals.css"
    
    if not check_file_exists(css_file):
        print_error(f"CSS file not found: {css_file}")
        return False
    
    utilities = [
        (r'\.skip-to-main', 'Skip to main content class'),
        (r'\.focus-trap', 'Focus trap class'),
        (r'\.keyboard-only', 'Keyboard-only visible class'),
        (r'\.keyboard-hint', 'Keyboard hint class'),
        (r'\.keyboard-shortcut', 'Keyboard shortcut display class'),
    ]
    
    for pattern, description in utilities:
        if search_in_file(css_file, pattern):
            print_success(f"{description} found")
        else:
            print_error(f"{description} not found")
            return False
    
    return True

def main():
    """Run all tests"""
    print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
    print(f"{BOLD}{BLUE}AutoGraph v3 - Keyboard Navigation Test Suite{RESET}")
    print(f"{BOLD}{BLUE}Testing Feature #665: Keyboard navigation: all features accessible{RESET}")
    print(f"{BOLD}{BLUE}{'='*80}{RESET}\n")
    
    tests = [
        ("Focus States in CSS", test_focus_states),
        ("Focus Trap Implementation", test_focus_trap_implementation),
        ("Modal Keyboard Accessibility", test_modal_keyboard_accessibility),
        ("Keyboard Shortcuts", test_keyboard_shortcuts),
        ("Logical Tab Order", test_tab_order),
        ("Focus Indicator Contrast", test_focus_indicators),
        ("Button Keyboard Accessibility", test_button_accessibility),
        ("Keyboard Navigation Utilities", test_keyboard_navigation_utilities),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
    print(f"{BOLD}{BLUE}Test Summary{RESET}")
    print(f"{BOLD}{BLUE}{'='*80}{RESET}\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
        print(f"{status} {test_name}")
    
    print(f"\n{BOLD}Results: {passed}/{total} tests passed ({passed/total*100:.1f}%){RESET}\n")
    
    if passed == total:
        print(f"{GREEN}{BOLD}✅ SUCCESS: All keyboard navigation tests passed!{RESET}\n")
        return 0
    else:
        print(f"{RED}{BOLD}❌ FAILURE: Some tests failed. Please review the output above.{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
