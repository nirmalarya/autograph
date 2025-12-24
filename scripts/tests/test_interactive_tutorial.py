#!/usr/bin/env python3
"""
Test Suite for Feature #669: Interactive Tutorial

This test verifies the interactive tutorial component that provides hands-on
learning for new users.

Tests:
1. Component structure and exports
2. Tutorial steps configuration
3. Keyboard navigation
4. Accessibility features
5. State persistence
6. UI components
7. Animations and transitions
8. Dark mode support
9. Responsive design
10. Layout integration
11. Settings integration
12. Documentation
"""

import os
import sys
import re
from pathlib import Path

# ANSI color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test_header(test_name: str):
    """Print a formatted test header."""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}Testing: {test_name}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")

def print_success(message: str):
    """Print a success message."""
    print(f"{GREEN}✓ {message}{RESET}")

def print_error(message: str):
    """Print an error message."""
    print(f"{RED}✗ {message}{RESET}")

def print_info(message: str):
    """Print an info message."""
    print(f"{YELLOW}ℹ {message}{RESET}")

def read_file(filepath: str) -> str:
    """Read and return file contents."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print_error(f"File not found: {filepath}")
        return ""
    except Exception as e:
        print_error(f"Error reading {filepath}: {e}")
        return ""

def test_component_structure():
    """Test 1: Verify InteractiveTutorial component structure."""
    print_test_header("Component Structure")
    
    filepath = "services/frontend/app/components/InteractiveTutorial.tsx"
    content = read_file(filepath)
    
    if not content:
        print_error("InteractiveTutorial.tsx not found")
        return False
    
    checks = [
        ("Feature comment", r"Feature #669"),
        ("Component export", r"export default function InteractiveTutorial"),
        ("Hook export", r"export function useInteractiveTutorial"),
        ("Tutorial steps array", r"const TUTORIAL_STEPS.*TutorialStep\[\]"),
        ("Storage keys", r"const STORAGE_KEY.*autograph-tutorial"),
        ("State management", r"useState"),
        ("Effect hooks", r"useEffect"),
        ("Keyboard navigation", r"handleKeyDown"),
        ("Progress tracking", r"completedSteps"),
        ("ARIA labels", r"aria-"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content, re.IGNORECASE):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print_info(f"Passed: {passed}/{len(checks)}")
    return passed == len(checks)

def test_tutorial_steps():
    """Test 2: Verify tutorial steps configuration."""
    print_test_header("Tutorial Steps Configuration")
    
    filepath = "services/frontend/app/components/InteractiveTutorial.tsx"
    content = read_file(filepath)
    
    if not content:
        return False
    
    steps = [
        ("Intro step", r"id:\s*['\"]intro['\"]"),
        ("Canvas intro", r"id:\s*['\"]canvas-intro['\"]"),
        ("Draw rectangle", r"id:\s*['\"]draw-rectangle['\"]"),
        ("Add text", r"id:\s*['\"]add-text['\"]"),
        ("Draw circle", r"id:\s*['\"]draw-circle['\"]"),
        ("Label database", r"id:\s*['\"]label-database['\"]"),
        ("Draw arrow", r"id:\s*['\"]draw-arrow['\"]"),
        ("Style shapes", r"id:\s*['\"]style-shapes['\"]"),
        ("Try AI", r"id:\s*['\"]try-ai['\"]"),
        ("Complete step", r"id:\s*['\"]complete['\"]"),
    ]
    
    passed = 0
    for step_name, pattern in steps:
        if re.search(pattern, content):
            print_success(f"{step_name} found")
            passed += 1
        else:
            print_error(f"{step_name} not found")
    
    print_info(f"Passed: {passed}/{len(steps)}")
    return passed == len(steps)

def test_keyboard_navigation():
    """Test 3: Verify keyboard navigation support."""
    print_test_header("Keyboard Navigation")
    
    filepath = "services/frontend/app/components/InteractiveTutorial.tsx"
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("Escape key handler", r"e\.key.*===.*['\"]Escape['\"]"),
        ("Arrow right handler", r"ArrowRight"),
        ("Arrow left handler", r"ArrowLeft"),
        ("Arrow down handler", r"ArrowDown"),
        ("Arrow up handler", r"ArrowUp"),
        ("Keyboard event listener", r"addEventListener.*keydown"),
        ("Keyboard hint text", r"<kbd"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print_info(f"Passed: {passed}/{len(checks)}")
    return passed == len(checks)

def test_accessibility():
    """Test 4: Verify accessibility features."""
    print_test_header("Accessibility Features")
    
    filepath = "services/frontend/app/components/InteractiveTutorial.tsx"
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("role='dialog'", r"role=['\"]dialog['\"]"),
        ("aria-labelledby", r"aria-labelledby"),
        ("aria-describedby", r"aria-describedby"),
        ("aria-modal", r"aria-modal"),
        ("aria-label attributes", r"aria-label"),
        ("Progress bar ARIA", r"role=['\"]progressbar['\"]"),
        ("aria-valuenow", r"aria-valuenow"),
        ("aria-valuemin", r"aria-valuemin"),
        ("aria-valuemax", r"aria-valuemax"),
        ("Keyboard accessible", r"aria-label.*step"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print_info(f"Passed: {passed}/{len(checks)}")
    return passed == len(checks)

def test_state_persistence():
    """Test 5: Verify state persistence with localStorage."""
    print_test_header("State Persistence")
    
    filepath = "services/frontend/app/components/InteractiveTutorial.tsx"
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("Storage key constant", r"const STORAGE_KEY"),
        ("Progress key constant", r"const PROGRESS_KEY"),
        ("localStorage.getItem", r"localStorage\.getItem"),
        ("localStorage.setItem", r"localStorage\.setItem"),
        ("localStorage.removeItem", r"localStorage\.removeItem"),
        ("Completed state", r"completed"),
        ("Skipped state", r"skipped"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print_info(f"Passed: {passed}/{len(checks)}")
    return passed == len(checks)

def test_ui_components():
    """Test 6: Verify UI components."""
    print_test_header("UI Components")
    
    filepath = "services/frontend/app/components/InteractiveTutorial.tsx"
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("Backdrop overlay", r"backdrop"),
        ("Progress bar", r"progressbar"),
        ("Close button", r"Skip tutorial"),
        ("Previous button", r"Previous"),
        ("Next button", r"Next"),
        ("Step counter", r"Step.*of"),
        ("Title heading", r"tutorial-title"),
        ("Description", r"tutorial-description"),
        ("Instructions list", r"Instructions"),
        ("Icons", r"lucide-react"),
        ("Complete button", r"Complete"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content, re.IGNORECASE):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print_info(f"Passed: {passed}/{len(checks)}")
    return passed == len(checks)

def test_animations():
    """Test 7: Verify animations and transitions."""
    print_test_header("Animations and Transitions")
    
    filepath = "services/frontend/app/components/InteractiveTutorial.tsx"
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("Animation state", r"isAnimating"),
        ("Transition classes", r"transition"),
        ("Duration classes", r"duration"),
        ("Opacity animation", r"opacity"),
        ("Scale animation", r"scale"),
        ("Ease timing", r"ease"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print_info(f"Passed: {passed}/{len(checks)}")
    return passed == len(checks)

def test_dark_mode():
    """Test 8: Verify dark mode support."""
    print_test_header("Dark Mode Support")
    
    filepath = "services/frontend/app/components/InteractiveTutorial.tsx"
    content = read_file(filepath)
    
    if not content:
        return False
    
    # Count dark mode classes
    dark_classes = len(re.findall(r'dark:', content))
    dark_bg = len(re.findall(r'dark:bg-', content))
    dark_text = len(re.findall(r'dark:text-', content))
    dark_border = len(re.findall(r'dark:border-', content))
    dark_hover = len(re.findall(r'dark:hover:', content))
    
    checks = [
        ("dark: classes", dark_classes >= 15),
        ("dark:bg- classes", dark_bg >= 5),
        ("dark:text- classes", dark_text >= 5),
        ("dark:border- classes", dark_border >= 1),
        ("dark:hover: classes", dark_hover >= 1),
    ]
    
    passed = 0
    for check_name, condition in checks:
        if condition:
            print_success(f"{check_name} found ({dark_classes} total dark: classes)")
            passed += 1
        else:
            print_error(f"{check_name} insufficient")
    
    print_info(f"Passed: {passed}/{len(checks)}")
    return passed == len(checks)

def test_responsive_design():
    """Test 9: Verify responsive design."""
    print_test_header("Responsive Design")
    
    filepath = "services/frontend/app/components/InteractiveTutorial.tsx"
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("Mobile spacing", r"mx-4"),
        ("Max width constraint", r"max-w-"),
        ("Touch target classes", r"touch-target"),
        ("Responsive padding", r"sm:p-|p-\d"),
        ("Responsive text", r"sm:text-"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print_info(f"Passed: {passed}/{len(checks)}")
    return passed == len(checks)

def test_layout_integration():
    """Test 10: Verify layout integration."""
    print_test_header("Layout Integration")
    
    filepath = "services/frontend/app/layout.tsx"
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("InteractiveTutorial import", r"import.*InteractiveTutorial"),
        ("InteractiveTutorial component", r"<InteractiveTutorial"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print_info(f"Passed: {passed}/{len(checks)}")
    return passed == len(checks)

def test_settings_integration():
    """Test 11: Verify settings page integration."""
    print_test_header("Settings Integration")
    
    filepath = "services/frontend/app/settings/page.tsx"
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("useInteractiveTutorial import", r"import.*useInteractiveTutorial"),
        ("useInteractiveTutorial hook", r"useInteractiveTutorial\(\)"),
        ("restartTutorial function", r"restartTutorial"),
        ("hasCompletedTutorial function", r"hasCompletedTutorial"),
        ("Tutorial button", r"Start Tutorial|Restart"),
        ("Tutorial status", r"tutorialCompleted"),
        ("GraduationCap icon", r"GraduationCap"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print_info(f"Passed: {passed}/{len(checks)}")
    return passed == len(checks)

def test_documentation():
    """Test 12: Verify documentation."""
    print_test_header("Documentation")
    
    filepath = "services/frontend/app/components/InteractiveTutorial.tsx"
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("Feature number", r"Feature #669"),
        ("Feature description", r"Interactive Tutorial"),
        ("Features list", r"Features:"),
        ("Step-by-step mention", r"step-by-step|Step-by-step"),
        ("Hands-on mention", r"hands-on|Hands-on"),
        ("Sample diagram mention", r"sample diagram"),
        ("Explains tools mention", r"explains.*tools|tool"),
        ("Hook documentation", r"Hook to control"),
        ("Interface documentation", r"interface.*TutorialStep"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content, re.IGNORECASE):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print_info(f"Passed: {passed}/{len(checks)}")
    return passed == len(checks)

def main():
    """Run all tests."""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}Interactive Tutorial Test Suite - Feature #669{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")
    
    tests = [
        ("Component Structure", test_component_structure),
        ("Tutorial Steps", test_tutorial_steps),
        ("Keyboard Navigation", test_keyboard_navigation),
        ("Accessibility", test_accessibility),
        ("State Persistence", test_state_persistence),
        ("UI Components", test_ui_components),
        ("Animations", test_animations),
        ("Dark Mode", test_dark_mode),
        ("Responsive Design", test_responsive_design),
        ("Layout Integration", test_layout_integration),
        ("Settings Integration", test_settings_integration),
        ("Documentation", test_documentation),
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
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}Test Summary{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{GREEN}✓ PASS{RESET}" if result else f"{RED}✗ FAIL{RESET}"
        print(f"{status} - {test_name}")
    
    print(f"\n{BLUE}{'='*80}{RESET}")
    percentage = (passed / total * 100) if total > 0 else 0
    print(f"Results: {passed}/{total} tests passed ({percentage:.1f}%)")
    print(f"{BLUE}{'='*80}{RESET}\n")
    
    if passed == total:
        print(f"{GREEN}✅ SUCCESS: All interactive tutorial tests passed!{RESET}\n")
        return 0
    else:
        print(f"{RED}❌ FAILURE: Some tests failed.{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
