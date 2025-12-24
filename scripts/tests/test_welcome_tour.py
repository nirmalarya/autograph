#!/usr/bin/env python3
"""
AutoGraph v3 - Welcome Tour Test Suite
Feature #668: Onboarding - Welcome Tour

This test suite verifies the implementation of the welcome tour feature.
"""

import os
import sys
import re
from pathlib import Path

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{text}{Colors.END}")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✅ PASS{Colors.END} {text}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}❌ FAIL{Colors.END} {text}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.YELLOW}ℹ INFO{Colors.END} {text}")

def read_file(filepath):
    """Read file contents"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return None

def count_occurrences(content, pattern, flags=0):
    """Count pattern occurrences in content"""
    if content is None:
        return 0
    return len(re.findall(pattern, content, flags))

def test_welcome_tour_component():
    """Test 1: Welcome Tour Component Exists"""
    print_header("TEST 1: Welcome Tour Component")
    
    component_path = "services/frontend/app/components/WelcomeTour.tsx"
    content = read_file(component_path)
    
    if content is None:
        print_error(f"WelcomeTour component not found at {component_path}")
        return False
    
    checks = [
        ("Feature comment", r"Feature #668", 1),
        ("Component export", r"export default function WelcomeTour", 1),
        ("Hook export", r"export function useWelcomeTour", 1),
        ("Tour steps array", r"const TOUR_STEPS.*=.*\[", 1),
        ("localStorage key", r"STORAGE_KEY.*=.*'autograph-welcome-tour", 1),
        ("State management", r"useState", 3),
        ("Effect hooks", r"useEffect", 3),
        ("Keyboard navigation", r"handleKeyDown", 1),
        ("Progress bar", r"progressbar", 1),
        ("ARIA labels", r"aria-", 10),
    ]
    
    passed = 0
    for name, pattern, min_count in checks:
        count = count_occurrences(content, pattern)
        if count >= min_count:
            print_success(f"{name} found ({count} instances)")
            passed += 1
        else:
            print_error(f"{name} not found (expected {min_count}+, found {count})")
    
    return passed == len(checks)

def test_tour_steps():
    """Test 2: Tour Steps Configuration"""
    print_header("TEST 2: Tour Steps Configuration")
    
    component_path = "services/frontend/app/components/WelcomeTour.tsx"
    content = read_file(component_path)
    
    if content is None:
        print_error("WelcomeTour component not found")
        return False
    
    # Extract tour steps
    steps_match = re.search(r'const TOUR_STEPS.*?=.*?\[(.*?)\];', content, re.DOTALL)
    if not steps_match:
        print_error("Tour steps array not found")
        return False
    
    steps_content = steps_match.group(1)
    
    checks = [
        ("Welcome step", r"Welcome to AutoGraph", 1),
        ("Dashboard step", r"Dashboard", 1),
        ("Create diagrams step", r"Create Diagrams", 1),
        ("AI generation step", r"AI-Powered Generation", 1),
        ("Canvas step", r"Canvas", 1),
        ("Mermaid step", r"Mermaid|Diagram-as-Code", 1),
        ("Collaboration step", r"Collaboration", 1),
        ("Export step", r"Export", 1),
        ("Complete step", r"All Set|Complete", 1),
    ]
    
    passed = 0
    for name, pattern, min_count in checks:
        count = count_occurrences(steps_content, pattern, re.IGNORECASE)
        if count >= min_count:
            print_success(f"{name} found")
            passed += 1
        else:
            print_error(f"{name} not found")
    
    return passed == len(checks)

def test_keyboard_navigation():
    """Test 3: Keyboard Navigation"""
    print_header("TEST 3: Keyboard Navigation")
    
    component_path = "services/frontend/app/components/WelcomeTour.tsx"
    content = read_file(component_path)
    
    if content is None:
        print_error("WelcomeTour component not found")
        return False
    
    checks = [
        ("Escape key handler", r"key.*===.*'Escape'", 1),
        ("Arrow right handler", r"key.*===.*'ArrowRight'", 1),
        ("Arrow left handler", r"key.*===.*'ArrowLeft'", 1),
        ("Arrow down handler", r"key.*===.*'ArrowDown'", 1),
        ("Arrow up handler", r"key.*===.*'ArrowUp'", 1),
        ("Keyboard event listener", r"addEventListener.*keydown", 1),
        ("Keyboard hint text", r"arrow keys|Press Esc", 1),
    ]
    
    passed = 0
    for name, pattern, min_count in checks:
        count = count_occurrences(content, pattern, re.IGNORECASE)
        if count >= min_count:
            print_success(f"{name} found ({count} instances)")
            passed += 1
        else:
            print_error(f"{name} not found")
    
    return passed == len(checks)

def test_accessibility_features():
    """Test 4: Accessibility Features"""
    print_header("TEST 4: Accessibility Features")
    
    component_path = "services/frontend/app/components/WelcomeTour.tsx"
    content = read_file(component_path)
    
    if content is None:
        print_error("WelcomeTour component not found")
        return False
    
    checks = [
        ("role='dialog'", r"role=\"dialog\"", 1),
        ("aria-labelledby", r"aria-labelledby", 1),
        ("aria-describedby", r"aria-describedby", 1),
        ("aria-modal", r"aria-modal", 1),
        ("aria-label attributes", r"aria-label", 5),
        ("Progress bar ARIA", r"role=\"progressbar\"", 1),
        ("aria-valuenow", r"aria-valuenow", 1),
        ("aria-valuemin", r"aria-valuemin", 1),
        ("aria-valuemax", r"aria-valuemax", 1),
        ("Focus management", r"focus\(\)", 1),
    ]
    
    passed = 0
    for name, pattern, min_count in checks:
        count = count_occurrences(content, pattern)
        if count >= min_count:
            print_success(f"{name} found ({count} instances)")
            passed += 1
        else:
            print_error(f"{name} not found")
    
    return passed == len(checks)

def test_state_persistence():
    """Test 5: State Persistence (localStorage)"""
    print_header("TEST 5: State Persistence")
    
    component_path = "services/frontend/app/components/WelcomeTour.tsx"
    content = read_file(component_path)
    
    if content is None:
        print_error("WelcomeTour component not found")
        return False
    
    checks = [
        ("Storage key constant", r"STORAGE_KEY", 1),
        ("localStorage.getItem", r"localStorage\.getItem", 2),
        ("localStorage.setItem", r"localStorage\.setItem", 2),
        ("localStorage.removeItem", r"localStorage\.removeItem", 1),
        ("Completed state", r"completed", 3),
        ("Skipped state", r"skipped", 1),
    ]
    
    passed = 0
    for name, pattern, min_count in checks:
        count = count_occurrences(content, pattern)
        if count >= min_count:
            print_success(f"{name} found ({count} instances)")
            passed += 1
        else:
            print_error(f"{name} not found")
    
    return passed == len(checks)

def test_ui_components():
    """Test 6: UI Components"""
    print_header("TEST 6: UI Components")
    
    component_path = "services/frontend/app/components/WelcomeTour.tsx"
    content = read_file(component_path)
    
    if content is None:
        print_error("WelcomeTour component not found")
        return False
    
    checks = [
        ("Backdrop overlay", r"backdrop|bg-black/50", 1),
        ("Progress bar", r"Progress", 2),
        ("Close button", r"Skip tour|Close", 2),
        ("Navigation buttons", r"Previous|Next", 2),
        ("Step counter", r"Step.*of", 1),
        ("Title heading", r"<h2", 1),
        ("Description paragraph", r"id=\"tour-description\"", 1),
        ("Action button", r"action\.label", 1),
        ("Icons (Lucide)", r"from 'lucide-react'", 1),
    ]
    
    passed = 0
    for name, pattern, min_count in checks:
        count = count_occurrences(content, pattern, re.IGNORECASE)
        if count >= min_count:
            print_success(f"{name} found ({count} instances)")
            passed += 1
        else:
            print_error(f"{name} not found")
    
    return passed == len(checks)

def test_animations_and_transitions():
    """Test 7: Animations and Transitions"""
    print_header("TEST 7: Animations and Transitions")
    
    component_path = "services/frontend/app/components/WelcomeTour.tsx"
    content = read_file(component_path)
    
    if content is None:
        print_error("WelcomeTour component not found")
        return False
    
    checks = [
        ("Animation state variable", r"setIsAnimating", 2),
        ("Transition classes", r"transition", 5),
        ("Duration classes", r"duration-", 3),
        ("Opacity animation", r"opacity", 2),
        ("Scale animation", r"scale", 1),
        ("Ease-in-out", r"ease-in-out|ease-out", 2),
    ]
    
    passed = 0
    for name, pattern, min_count in checks:
        count = count_occurrences(content, pattern)
        if count >= min_count:
            print_success(f"{name} found ({count} instances)")
            passed += 1
        else:
            print_error(f"{name} not found")
    
    return passed == len(checks)

def test_dark_mode_support():
    """Test 8: Dark Mode Support"""
    print_header("TEST 8: Dark Mode Support")
    
    component_path = "services/frontend/app/components/WelcomeTour.tsx"
    content = read_file(component_path)
    
    if content is None:
        print_error("WelcomeTour component not found")
        return False
    
    checks = [
        ("dark: classes", r"dark:", 15),
        ("dark:bg-", r"dark:bg-", 5),
        ("dark:text-", r"dark:text-", 5),
        ("dark:border-", r"dark:border-", 1),
        ("dark:hover:", r"dark:hover:", 2),
    ]
    
    passed = 0
    for name, pattern, min_count in checks:
        count = count_occurrences(content, pattern)
        if count >= min_count:
            print_success(f"{name} found ({count} instances)")
            passed += 1
        else:
            print_error(f"{name} not found (expected {min_count}+, found {count})")
    
    return passed == len(checks)

def test_responsive_design():
    """Test 9: Responsive Design"""
    print_header("TEST 9: Responsive Design")
    
    component_path = "services/frontend/app/components/WelcomeTour.tsx"
    content = read_file(component_path)
    
    if content is None:
        print_error("WelcomeTour component not found")
        return False
    
    checks = [
        ("Mobile spacing (mx-4)", r"mx-4", 1),
        ("Max width constraint", r"max-w-", 1),
        ("Touch target classes", r"touch-target-", 3),
        ("Responsive padding", r"p-\d+|px-\d+|py-\d+", 5),
    ]
    
    passed = 0
    for name, pattern, min_count in checks:
        count = count_occurrences(content, pattern)
        if count >= min_count:
            print_success(f"{name} found ({count} instances)")
            passed += 1
        else:
            print_error(f"{name} not found")
    
    return passed == len(checks)

def test_layout_integration():
    """Test 10: Layout Integration"""
    print_header("TEST 10: Layout Integration")
    
    layout_path = "services/frontend/app/layout.tsx"
    content = read_file(layout_path)
    
    if content is None:
        print_error("Layout file not found")
        return False
    
    checks = [
        ("WelcomeTour import", r"import.*WelcomeTour", 1),
        ("WelcomeTour component", r"<WelcomeTour.*/>", 1),
    ]
    
    passed = 0
    for name, pattern, min_count in checks:
        count = count_occurrences(content, pattern)
        if count >= min_count:
            print_success(f"{name} found")
            passed += 1
        else:
            print_error(f"{name} not found")
    
    return passed == len(checks)

def test_settings_integration():
    """Test 11: Settings Page Integration"""
    print_header("TEST 11: Settings Page Integration")
    
    settings_path = "services/frontend/app/settings/page.tsx"
    content = read_file(settings_path)
    
    if content is None:
        print_error("Settings page not found")
        return False
    
    checks = [
        ("useWelcomeTour hook import", r"import.*useWelcomeTour", 1),
        ("useWelcomeTour hook usage", r"useWelcomeTour\(\)", 1),
        ("restartTour function", r"restartTour", 2),
        ("hasCompletedTour function", r"hasCompletedTour", 2),
        ("Show tour button", r"Show Again|Start Tour", 1),
        ("Onboarding section", r"Onboarding", 1),
    ]
    
    passed = 0
    for name, pattern, min_count in checks:
        count = count_occurrences(content, pattern)
        if count >= min_count:
            print_success(f"{name} found ({count} instances)")
            passed += 1
        else:
            print_error(f"{name} not found")
    
    return passed == len(checks)

def test_documentation():
    """Test 12: Documentation"""
    print_header("TEST 12: Documentation")
    
    component_path = "services/frontend/app/components/WelcomeTour.tsx"
    content = read_file(component_path)
    
    if content is None:
        print_error("WelcomeTour component not found")
        return False
    
    checks = [
        ("Feature number reference", r"Feature #668", 1),
        ("Feature description", r"welcome tour|guided tour", 1),
        ("Features list", r"Features:", 1),
        ("Multi-step mention", r"Multi-step", 1),
        ("Keyboard navigation mention", r"Keyboard navigation", 1),
        ("Accessibility mention", r"Accessibility", 1),
        ("Dark mode mention", r"Dark mode", 1),
        ("Interface documentation", r"interface TourStep", 1),
        ("Hook documentation", r"Hook to manually trigger", 1),
    ]
    
    passed = 0
    for name, pattern, min_count in checks:
        count = count_occurrences(content, pattern, re.IGNORECASE)
        if count >= min_count:
            print_success(f"{name} found")
            passed += 1
        else:
            print_error(f"{name} not found")
    
    return passed == len(checks)

def main():
    """Run all tests"""
    print(f"{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}AutoGraph v3 - Welcome Tour Test Suite{Colors.END}")
    print(f"{Colors.BOLD}Testing Feature #668: Onboarding - Welcome Tour{Colors.END}")
    print(f"{Colors.BOLD}{'='*80}{Colors.END}")
    
    # Change to project root directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Run all tests
    tests = [
        ("Welcome Tour Component", test_welcome_tour_component),
        ("Tour Steps Configuration", test_tour_steps),
        ("Keyboard Navigation", test_keyboard_navigation),
        ("Accessibility Features", test_accessibility_features),
        ("State Persistence", test_state_persistence),
        ("UI Components", test_ui_components),
        ("Animations and Transitions", test_animations_and_transitions),
        ("Dark Mode Support", test_dark_mode_support),
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
            print_error(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print_header("SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"\nResults: {passed}/{total} tests passed ({percentage:.1f}%)\n")
    
    for test_name, result in results:
        status = f"{Colors.GREEN}✅ PASS{Colors.END}" if result else f"{Colors.RED}❌ FAIL{Colors.END}"
        print(f"{status} {test_name}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ SUCCESS: All welcome tour tests passed!{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ FAILURE: Some tests failed.{Colors.END}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
