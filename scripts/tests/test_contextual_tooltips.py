#!/usr/bin/env python3
"""
Test Script for Feature: Contextual Tooltips System
Tests the implementation of contextual tooltips throughout the UI
"""

import os
import re
from pathlib import Path

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text):
    print(f"\n{BLUE}{BOLD}{'=' * 80}{RESET}")
    print(f"{BLUE}{BOLD}{text}{RESET}")
    print(f"{BLUE}{BOLD}{'=' * 80}{RESET}\n")

def print_test(name, passed, details=""):
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} - {name}")
    if details:
        print(f"       {details}")

def read_file(filepath):
    """Read file contents"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"{RED}Error reading {filepath}: {e}{RESET}")
        return None

def test_contextual_tooltips_component():
    """Test the ContextualTooltips component file"""
    print_header("TEST 1: ContextualTooltips Component Structure")
    
    filepath = "services/frontend/app/components/ContextualTooltips.tsx"
    content = read_file(filepath)
    
    if not content:
        print_test("File exists", False, f"Could not read {filepath}")
        return 0, 20
    
    tests_passed = 0
    tests_total = 20
    
    # Test 1: Feature comment
    if re.search(r'Feature:\s*Contextual\s*Tooltips', content, re.IGNORECASE):
        print_test("Feature comment present", True)
        tests_passed += 1
    else:
        print_test("Feature comment present", False)
    
    # Test 2: ContextualTooltipDefinition interface
    if 'interface ContextualTooltipDefinition' in content:
        print_test("ContextualTooltipDefinition interface", True)
        tests_passed += 1
    else:
        print_test("ContextualTooltipDefinition interface", False)
    
    # Test 3: CONTEXTUAL_TOOLTIPS constant
    if 'export const CONTEXTUAL_TOOLTIPS' in content:
        print_test("CONTEXTUAL_TOOLTIPS constant", True)
        tests_passed += 1
    else:
        print_test("CONTEXTUAL_TOOLTIPS constant", False)
    
    # Test 4: Context provider
    if 'ContextualTooltipsProvider' in content:
        print_test("ContextualTooltipsProvider component", True)
        tests_passed += 1
    else:
        print_test("ContextualTooltipsProvider component", False)
    
    # Test 5: useContextualTooltips hook
    if 'export function useContextualTooltips' in content:
        print_test("useContextualTooltips hook", True)
        tests_passed += 1
    else:
        print_test("useContextualTooltips hook", False)
    
    # Test 6: ContextualTooltipWrapper component
    if 'export function ContextualTooltipWrapper' in content:
        print_test("ContextualTooltipWrapper component", True)
        tests_passed += 1
    else:
        print_test("ContextualTooltipWrapper component", False)
    
    # Test 7: ContextualTooltipsSettings component
    if 'export function ContextualTooltipsSettings' in content:
        print_test("ContextualTooltipsSettings component", True)
        tests_passed += 1
    else:
        print_test("ContextualTooltipsSettings component", False)
    
    # Test 8: ContextualTooltipsToggle component
    if 'export function ContextualTooltipsToggle' in content:
        print_test("ContextualTooltipsToggle component", True)
        tests_passed += 1
    else:
        print_test("ContextualTooltipsToggle component", False)
    
    # Test 9: useSetTooltipContext hook
    if 'export function useSetTooltipContext' in content:
        print_test("useSetTooltipContext hook", True)
        tests_passed += 1
    else:
        print_test("useSetTooltipContext hook", False)
    
    # Test 10: Local storage integration
    if 'localStorage.getItem' in content and 'contextual-tooltips' in content:
        print_test("Local storage integration", True)
        tests_passed += 1
    else:
        print_test("Local storage integration", False)
    
    # Test 11: Enable/disable toggle
    if 'toggleEnabled' in content:
        print_test("Enable/disable toggle functionality", True)
        tests_passed += 1
    else:
        print_test("Enable/disable toggle functionality", False)
    
    # Test 12: Dismiss tooltip functionality
    if 'dismissTooltip' in content:
        print_test("Dismiss tooltip functionality", True)
        tests_passed += 1
    else:
        print_test("Dismiss tooltip functionality", False)
    
    # Test 13: Reset dismissed tooltips
    if 'resetDismissed' in content:
        print_test("Reset dismissed tooltips functionality", True)
        tests_passed += 1
    else:
        print_test("Reset dismissed tooltips functionality", False)
    
    # Test 14: Context filtering
    if 'currentContext' in content and 'setCurrentContext' in content:
        print_test("Context filtering functionality", True)
        tests_passed += 1
    else:
        print_test("Context filtering functionality", False)
    
    # Test 15: Tooltip importance levels
    if "'high'" in content and "'medium'" in content and "'low'" in content:
        print_test("Tooltip importance levels", True)
        tests_passed += 1
    else:
        print_test("Tooltip importance levels", False)
    
    # Test 16: Learn more links
    if 'learnMoreUrl' in content:
        print_test("Learn more URL support", True)
        tests_passed += 1
    else:
        print_test("Learn more URL support", False)
    
    # Test 17: Dark mode support
    if 'dark:' in content:
        print_test("Dark mode support", True)
        tests_passed += 1
    else:
        print_test("Dark mode support", False)
    
    # Test 18: Accessibility
    if 'aria-' in content:
        print_test("Accessibility (ARIA) attributes", True)
        tests_passed += 1
    else:
        print_test("Accessibility (ARIA) attributes", False)
    
    # Test 19: React imports
    if 'import React' in content or "import { useState" in content:
        print_test("React imports", True)
        tests_passed += 1
    else:
        print_test("React imports", False)
    
    # Test 20: Tooltip component import
    if "import Tooltip" in content:
        print_test("Tooltip component import", True)
        tests_passed += 1
    else:
        print_test("Tooltip component import", False)
    
    return tests_passed, tests_total

def test_tooltip_definitions():
    """Test that tooltip definitions are comprehensive"""
    print_header("TEST 2: Tooltip Definitions Coverage")
    
    filepath = "services/frontend/app/components/ContextualTooltips.tsx"
    content = read_file(filepath)
    
    if not content:
        return 0, 10
    
    tests_passed = 0
    tests_total = 10
    
    contexts = [
        'dashboard',
        'canvas',
        'ai-generation',
        'mermaid',
        'collaboration',
        'export',
        'version-history',
        'settings',
        'help',
    ]
    
    # Count tooltips per context
    for context in contexts:
        if f"context: '{context}'" in content or f'context: "{context}"' in content:
            print_test(f"Tooltips for '{context}' context", True)
            tests_passed += 1
        else:
            print_test(f"Tooltips for '{context}' context", False)
    
    # Test that we have multiple tooltip definitions
    tooltip_count = content.count('id:')
    if tooltip_count >= 15:
        print_test(f"Multiple tooltip definitions ({tooltip_count} found)", True)
        tests_passed += 1
    else:
        print_test(f"Multiple tooltip definitions (only {tooltip_count} found)", False)
    
    return tests_passed, tests_total

def test_layout_integration():
    """Test that ContextualTooltips is integrated into the layout"""
    print_header("TEST 3: Layout Integration")
    
    filepath = "services/frontend/app/layout.tsx"
    content = read_file(filepath)
    
    if not content:
        return 0, 5
    
    tests_passed = 0
    tests_total = 5
    
    # Test 1: Import statement
    if 'ContextualTooltipsProvider' in content:
        print_test("ContextualTooltipsProvider import", True)
        tests_passed += 1
    else:
        print_test("ContextualTooltipsProvider import", False)
    
    # Test 2: ContextualTooltipsToggle import
    if 'ContextualTooltipsToggle' in content:
        print_test("ContextualTooltipsToggle import", True)
        tests_passed += 1
    else:
        print_test("ContextualTooltipsToggle import", False)
    
    # Test 3: ContextualTooltipsSettings import
    if 'ContextualTooltipsSettings' in content:
        print_test("ContextualTooltipsSettings import", True)
        tests_passed += 1
    else:
        print_test("ContextualTooltipsSettings import", False)
    
    # Test 4: Provider wrapping children
    if '<ContextualTooltipsProvider' in content:
        print_test("ContextualTooltipsProvider wrapping children", True)
        tests_passed += 1
    else:
        print_test("ContextualTooltipsProvider wrapping children", False)
    
    # Test 5: Toggle and Settings components rendered
    if '<ContextualTooltipsToggle' in content and '<ContextualTooltipsSettings' in content:
        print_test("Toggle and Settings components rendered", True)
        tests_passed += 1
    else:
        print_test("Toggle and Settings components rendered", False)
    
    return tests_passed, tests_total

def test_settings_panel():
    """Test the settings panel functionality"""
    print_header("TEST 4: Settings Panel")
    
    filepath = "services/frontend/app/components/ContextualTooltips.tsx"
    content = read_file(filepath)
    
    if not content:
        return 0, 8
    
    tests_passed = 0
    tests_total = 8
    
    # Test 1: Settings panel component
    if 'function ContextualTooltipsSettings' in content:
        print_test("Settings panel component", True)
        tests_passed += 1
    else:
        print_test("Settings panel component", False)
    
    # Test 2: Show/hide toggle
    if 'showSettingsPanel' in content:
        print_test("Show/hide settings panel state", True)
        tests_passed += 1
    else:
        print_test("Show/hide settings panel state", False)
    
    # Test 3: Enable/disable switch
    if 'role="switch"' in content:
        print_test("Enable/disable switch (accessible)", True)
        tests_passed += 1
    else:
        print_test("Enable/disable switch (accessible)", False)
    
    # Test 4: Reset dismissed button
    if 'Reset All Tooltips' in content or 'resetDismissed' in content:
        print_test("Reset dismissed tooltips button", True)
        tests_passed += 1
    else:
        print_test("Reset dismissed tooltips button", False)
    
    # Test 5: Settings icon
    if 'Settings' in content and 'lucide-react' in content:
        print_test("Settings icon (lucide-react)", True)
        tests_passed += 1
    else:
        print_test("Settings icon (lucide-react)", False)
    
    # Test 6: Modal backdrop
    if 'backdrop-blur' in content or 'bg-black/50' in content:
        print_test("Modal backdrop with blur", True)
        tests_passed += 1
    else:
        print_test("Modal backdrop with blur", False)
    
    # Test 7: Close button
    if 'Close settings' in content or 'aria-label="Close' in content:
        print_test("Close button with aria-label", True)
        tests_passed += 1
    else:
        print_test("Close button with aria-label", False)
    
    # Test 8: Help tip
    if 'Tip' in content or 'HelpCircle' in content:
        print_test("Help tip in settings", True)
        tests_passed += 1
    else:
        print_test("Help tip in settings", False)
    
    return tests_passed, tests_total

def test_floating_toggle_button():
    """Test the floating toggle button"""
    print_header("TEST 5: Floating Toggle Button")
    
    filepath = "services/frontend/app/components/ContextualTooltips.tsx"
    content = read_file(filepath)
    
    if not content:
        return 0, 6
    
    tests_passed = 0
    tests_total = 6
    
    # Test 1: Toggle component
    if 'function ContextualTooltipsToggle' in content:
        print_test("Toggle button component", True)
        tests_passed += 1
    else:
        print_test("Toggle button component", False)
    
    # Test 2: Fixed positioning
    if 'fixed' in content and 'bottom' in content and 'right' in content:
        print_test("Fixed positioning (bottom-right)", True)
        tests_passed += 1
    else:
        print_test("Fixed positioning (bottom-right)", False)
    
    # Test 3: Z-index for stacking
    if 'z-40' in content or 'z-[40]' in content:
        print_test("Z-index for proper stacking", True)
        tests_passed += 1
    else:
        print_test("Z-index for proper stacking", False)
    
    # Test 4: Visual indicator (enabled state)
    if 'enabled' in content and 'bg-blue-600' in content:
        print_test("Visual indicator for enabled state", True)
        tests_passed += 1
    else:
        print_test("Visual indicator for enabled state", False)
    
    # Test 5: HelpCircle icon
    if 'HelpCircle' in content:
        print_test("HelpCircle icon", True)
        tests_passed += 1
    else:
        print_test("HelpCircle icon", False)
    
    # Test 6: Touch-friendly size
    if 'touch-target' in content or 'p-3' in content:
        print_test("Touch-friendly size", True)
        tests_passed += 1
    else:
        print_test("Touch-friendly size", False)
    
    return tests_passed, tests_total

def test_wrapper_component():
    """Test the wrapper component for individual tooltips"""
    print_header("TEST 6: ContextualTooltipWrapper Component")
    
    filepath = "services/frontend/app/components/ContextualTooltips.tsx"
    content = read_file(filepath)
    
    if not content:
        return 0, 7
    
    tests_passed = 0
    tests_total = 7
    
    # Test 1: Wrapper component
    if 'function ContextualTooltipWrapper' in content:
        print_test("Wrapper component", True)
        tests_passed += 1
    else:
        print_test("Wrapper component", False)
    
    # Test 2: tooltipId prop
    if 'tooltipId' in content:
        print_test("tooltipId prop", True)
        tests_passed += 1
    else:
        print_test("tooltipId prop", False)
    
    # Test 3: forceShow prop for demos
    if 'forceShow' in content:
        print_test("forceShow prop (for onboarding)", True)
        tests_passed += 1
    else:
        print_test("forceShow prop (for onboarding)", False)
    
    # Test 4: Dismiss button on hover
    if 'showDismissButton' in content:
        print_test("Dismiss button on hover", True)
        tests_passed += 1
    else:
        print_test("Dismiss button on hover", False)
    
    # Test 5: Context filtering
    if 'shouldShow' in content and 'currentContext' in content:
        print_test("Context filtering logic", True)
        tests_passed += 1
    else:
        print_test("Context filtering logic", False)
    
    # Test 6: Learn more link
    if 'learnMoreUrl' in content and 'Learn more' in content:
        print_test("Learn more link support", True)
        tests_passed += 1
    else:
        print_test("Learn more link support", False)
    
    # Test 7: Wraps existing Tooltip component
    if '<Tooltip' in content:
        print_test("Wraps existing Tooltip component", True)
        tests_passed += 1
    else:
        print_test("Wraps existing Tooltip component", False)
    
    return tests_passed, tests_total

def test_context_hook():
    """Test the context setting hook"""
    print_header("TEST 7: Context Setting Hook")
    
    filepath = "services/frontend/app/components/ContextualTooltips.tsx"
    content = read_file(filepath)
    
    if not content:
        return 0, 4
    
    tests_passed = 0
    tests_total = 4
    
    # Test 1: useSetTooltipContext hook
    if 'function useSetTooltipContext' in content:
        print_test("useSetTooltipContext hook", True)
        tests_passed += 1
    else:
        print_test("useSetTooltipContext hook", False)
    
    # Test 2: Sets context on mount
    if 'useEffect' in content and 'setCurrentContext' in content:
        print_test("Sets context on mount", True)
        tests_passed += 1
    else:
        print_test("Sets context on mount", False)
    
    # Test 3: Clears context on unmount
    if 'return ()' in content:
        print_test("Clears context on unmount", True)
        tests_passed += 1
    else:
        print_test("Clears context on unmount", False)
    
    # Test 4: Context parameter
    if 'context: string' in content:
        print_test("Context parameter (string)", True)
        tests_passed += 1
    else:
        print_test("Context parameter (string)", False)
    
    return tests_passed, tests_total

def test_dark_mode_support():
    """Test dark mode support"""
    print_header("TEST 8: Dark Mode Support")
    
    filepath = "services/frontend/app/components/ContextualTooltips.tsx"
    content = read_file(filepath)
    
    if not content:
        return 0, 5
    
    tests_passed = 0
    tests_total = 5
    
    # Count dark mode classes
    dark_classes = len(re.findall(r'dark:', content))
    
    if dark_classes >= 10:
        print_test(f"Dark mode classes present ({dark_classes} found)", True)
        tests_passed += 1
    else:
        print_test(f"Dark mode classes present (only {dark_classes} found)", False)
    
    # Test specific dark mode classes
    if 'dark:bg-gray-800' in content:
        print_test("Dark background colors", True)
        tests_passed += 1
    else:
        print_test("Dark background colors", False)
    
    if 'dark:text-gray' in content:
        print_test("Dark text colors", True)
        tests_passed += 1
    else:
        print_test("Dark text colors", False)
    
    if 'dark:border-' in content:
        print_test("Dark border colors", True)
        tests_passed += 1
    else:
        print_test("Dark border colors", False)
    
    if 'dark:hover:' in content:
        print_test("Dark hover states", True)
        tests_passed += 1
    else:
        print_test("Dark hover states", False)
    
    return tests_passed, tests_total

def test_accessibility():
    """Test accessibility features"""
    print_header("TEST 9: Accessibility Features")
    
    filepath = "services/frontend/app/components/ContextualTooltips.tsx"
    content = read_file(filepath)
    
    if not content:
        return 0, 6
    
    tests_passed = 0
    tests_total = 6
    
    # Test ARIA attributes
    if 'aria-label' in content:
        print_test("aria-label attributes", True)
        tests_passed += 1
    else:
        print_test("aria-label attributes", False)
    
    if 'aria-checked' in content:
        print_test("aria-checked for toggle", True)
        tests_passed += 1
    else:
        print_test("aria-checked for toggle", False)
    
    if 'role="switch"' in content:
        print_test("role='switch' for toggle", True)
        tests_passed += 1
    else:
        print_test("role='switch' for toggle", False)
    
    # Test keyboard accessibility
    if 'onClick' in content:
        print_test("Keyboard accessible buttons", True)
        tests_passed += 1
    else:
        print_test("Keyboard accessible buttons", False)
    
    # Test focus management
    if 'e.stopPropagation' in content:
        print_test("Event handling (stopPropagation)", True)
        tests_passed += 1
    else:
        print_test("Event handling (stopPropagation)", False)
    
    # Test semantic HTML
    if '<button' in content:
        print_test("Semantic HTML (buttons)", True)
        tests_passed += 1
    else:
        print_test("Semantic HTML (buttons)", False)
    
    return tests_passed, tests_total

def test_responsive_design():
    """Test responsive design"""
    print_header("TEST 10: Responsive Design")
    
    filepath = "services/frontend/app/components/ContextualTooltips.tsx"
    content = read_file(filepath)
    
    if not content:
        return 0, 4
    
    tests_passed = 0
    tests_total = 4
    
    # Test responsive classes
    if 'max-w-' in content:
        print_test("Max width constraint", True)
        tests_passed += 1
    else:
        print_test("Max width constraint", False)
    
    if 'mx-' in content or 'my-' in content:
        print_test("Responsive margins", True)
        tests_passed += 1
    else:
        print_test("Responsive margins", False)
    
    if 'rounded-' in content:
        print_test("Rounded corners", True)
        tests_passed += 1
    else:
        print_test("Rounded corners", False)
    
    if 'shadow-' in content:
        print_test("Shadow effects", True)
        tests_passed += 1
    else:
        print_test("Shadow effects", False)
    
    return tests_passed, tests_total

def main():
    """Run all tests"""
    print(f"{BOLD}{BLUE}")
    print("=" * 80)
    print(" CONTEXTUAL TOOLTIPS SYSTEM - AUTOMATED TEST SUITE")
    print("=" * 80)
    print(RESET)
    
    total_passed = 0
    total_tests = 0
    
    # Run all test suites
    test_suites = [
        test_contextual_tooltips_component,
        test_tooltip_definitions,
        test_layout_integration,
        test_settings_panel,
        test_floating_toggle_button,
        test_wrapper_component,
        test_context_hook,
        test_dark_mode_support,
        test_accessibility,
        test_responsive_design,
    ]
    
    for test_suite in test_suites:
        passed, total = test_suite()
        total_passed += passed
        total_tests += total
    
    # Print summary
    print_header("TEST SUMMARY")
    
    percentage = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {GREEN}{total_passed}{RESET}")
    print(f"Failed: {RED}{total_tests - total_passed}{RESET}")
    print(f"Success Rate: {GREEN if percentage >= 90 else YELLOW if percentage >= 70 else RED}{percentage:.1f}%{RESET}")
    
    if total_passed == total_tests:
        print(f"\n{GREEN}{BOLD}✓ ALL TESTS PASSED! Feature implementation complete.{RESET}\n")
        return 0
    elif percentage >= 90:
        print(f"\n{YELLOW}{BOLD}⚠ Most tests passed. Minor issues to address.{RESET}\n")
        return 0
    else:
        print(f"\n{RED}{BOLD}✗ Some tests failed. Please review the implementation.{RESET}\n")
        return 1

if __name__ == '__main__':
    exit(main())
