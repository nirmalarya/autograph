#!/usr/bin/env python3
"""
Test Suite for Feature #670: Polish: Onboarding: Example Diagrams

This test suite verifies the implementation of the example diagrams gallery feature.
It checks that users can view pre-made diagrams, duplicate them, and learn from examples.

Test Coverage:
- Component structure and exports
- Example diagram data structure
- Category filtering
- Search functionality
- Duplicate functionality
- UI components (buttons, cards, modal)
- Accessibility features
- Dark mode support
- Responsive design
- Integration with dashboard
"""

import os
import re
import sys

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_test_header(test_name):
    """Print a formatted test header."""
    print(f"\n{BLUE}{BOLD}{'='*80}{RESET}")
    print(f"{BLUE}{BOLD}TEST: {test_name}{RESET}")
    print(f"{BLUE}{BOLD}{'='*80}{RESET}\n")

def print_success(message):
    """Print a success message."""
    print(f"{GREEN}✓ {message}{RESET}")

def print_error(message):
    """Print an error message."""
    print(f"{RED}✗ {message}{RESET}")

def print_info(message):
    """Print an info message."""
    print(f"{YELLOW}ℹ {message}{RESET}")

def read_file(filepath):
    """Read and return file contents."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print_error(f"File not found: {filepath}")
        return None

def test_component_structure():
    """Test 1: Verify component structure and exports."""
    print_test_header("Component Structure and Exports")
    
    filepath = 'services/frontend/app/components/ExampleDiagrams.tsx'
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("Feature comment", r"Feature #670"),
        ("Component export", r"export default function ExampleDiagrams"),
        ("Hook export", r"export function useExampleDiagrams"),
        ("Props interface", r"interface ExampleDiagramsProps"),
        ("Example interface", r"interface ExampleDiagram"),
        ("isOpen prop", r"isOpen.*boolean"),
        ("onClose prop", r"onClose.*\(\)"),
        ("useState imports", r"import.*useState.*from.*react"),
        ("useCallback import", r"import.*useCallback.*from.*react"),
        ("useRouter import", r"import.*useRouter.*from.*next/navigation"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print(f"\n{BOLD}Result: {passed}/{len(checks)} checks passed{RESET}")
    return passed == len(checks)

def test_example_diagrams_data():
    """Test 2: Verify example diagrams data structure."""
    print_test_header("Example Diagrams Data Structure")
    
    filepath = 'services/frontend/app/components/ExampleDiagrams.tsx'
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("EXAMPLE_DIAGRAMS array", r"const EXAMPLE_DIAGRAMS.*ExampleDiagram\[\]"),
        ("Microservices example", r"microservices-arch"),
        ("3-tier architecture", r"three-tier-arch"),
        ("Serverless example", r"serverless-arch"),
        ("User registration flow", r"user-registration"),
        ("E-commerce order flow", r"order-processing"),
        ("E-commerce ERD", r"ecommerce-erd"),
        ("Blog ERD", r"blog-erd"),
        ("API authentication sequence", r"api-authentication"),
        ("Payment processing sequence", r"payment-processing"),
        ("Design patterns class", r"oop-design-patterns"),
        ("Order state machine", r"order-state-machine"),
        ("Canvas data property", r"canvasData"),
        ("Mermaid code property", r"mermaidCode"),
        ("Category property", r"category.*architecture.*flowchart.*erd.*sequence"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print(f"\n{BOLD}Result: {passed}/{len(checks)} checks passed{RESET}")
    return passed == len(checks)

def test_category_system():
    """Test 3: Verify category filtering system."""
    print_test_header("Category Filtering System")
    
    filepath = 'services/frontend/app/components/ExampleDiagrams.tsx'
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("CATEGORY_INFO constant", r"const CATEGORY_INFO"),
        ("Architecture category", r"architecture.*label.*icon.*color"),
        ("Flowchart category", r"flowchart.*label.*icon.*color"),
        ("ERD category", r"erd.*label.*icon.*color"),
        ("Sequence category", r"sequence.*label.*icon.*color"),
        ("Class category", r"class.*label.*icon.*color"),
        ("State category", r"state.*label.*icon.*color"),
        ("Category filter state", r"selectedCategory.*useState"),
        ("Filter by category", r"filteredExamples.*filter.*category"),
        ("Category buttons", r"setSelectedCategory"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print(f"\n{BOLD}Result: {passed}/{len(checks)} checks passed{RESET}")
    return passed == len(checks)

def test_search_functionality():
    """Test 4: Verify search functionality."""
    print_test_header("Search Functionality")
    
    filepath = 'services/frontend/app/components/ExampleDiagrams.tsx'
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("Search query state", r"searchQuery.*useState"),
        ("Search input field", r"input.*type.*text.*searchQuery"),
        ("Search placeholder", r"Search examples"),
        ("Filter by search", r"filteredExamples.*filter.*search"),
        ("Search in title", r"title.*toLowerCase.*includes"),
        ("Search in description", r"description.*toLowerCase.*includes"),
        ("Search in tags", r"tags.*some.*includes"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print(f"\n{BOLD}Result: {passed}/{len(checks)} checks passed{RESET}")
    return passed == len(checks)

def test_duplicate_functionality():
    """Test 5: Verify duplicate functionality."""
    print_test_header("Duplicate Functionality")
    
    filepath = 'services/frontend/app/components/ExampleDiagrams.tsx'
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("handleDuplicate function", r"const handleDuplicate.*useCallback"),
        ("Duplicating state", r"duplicating.*useState"),
        ("Get user token", r"localStorage\.getItem.*access_token"),
        ("Parse JWT", r"JSON\.parse.*atob"),
        ("Create diagram API call", r"fetch.*http://localhost:8082"),
        ("POST method", r"method.*POST"),
        ("Canvas data in body", r"canvas_data.*canvasData"),
        ("Mermaid code in body", r"note_content.*mermaidCode"),
        ("Navigate to canvas", r"router\.push.*canvas"),
        ("Navigate to mermaid", r"router\.push.*mermaid"),
        ("Error handling", r"catch.*err"),
        ("Duplicate button", r"Duplicate.*Edit"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print(f"\n{BOLD}Result: {passed}/{len(checks)} checks passed{RESET}")
    return passed == len(checks)

def test_ui_components():
    """Test 6: Verify UI components."""
    print_test_header("UI Components")
    
    filepath = 'services/frontend/app/components/ExampleDiagrams.tsx'
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("Modal backdrop", r"fixed inset-0.*bg-black"),
        ("Modal dialog", r"role.*dialog"),
        ("Modal title", r"Example Diagrams"),
        ("Close button", r"onClick.*onClose"),
        ("Search input", r"input.*Search examples"),
        ("Category filter buttons", r"Category.*button"),
        ("Example cards grid", r"grid.*grid-cols"),
        ("Thumbnail display", r"h-40.*bg-gradient"),
        ("Example title", r"text-lg.*font-semibold"),
        ("Example description", r"text-sm.*line-clamp"),
        ("Tags display", r"tags.*map"),
        ("Duplicate button", r"Duplicate.*Edit.*button"),
        ("Loading state", r"isDuplicating.*Duplicating"),
        ("Empty state", r"No examples found"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print(f"\n{BOLD}Result: {passed}/{len(checks)} checks passed{RESET}")
    return passed == len(checks)

def test_accessibility_features():
    """Test 7: Verify accessibility features."""
    print_test_header("Accessibility Features")
    
    filepath = 'services/frontend/app/components/ExampleDiagrams.tsx'
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("role='dialog'", r"role.*dialog"),
        ("aria-modal", r"aria-modal.*true"),
        ("aria-labelledby", r"aria-labelledby.*examples-title"),
        ("aria-label on close", r"aria-label.*Close"),
        ("Touch target classes", r"touch-target"),
        ("Keyboard accessible buttons", r"button.*onClick"),
        ("Disabled state handling", r"disabled.*isDuplicating"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print(f"\n{BOLD}Result: {passed}/{len(checks)} checks passed{RESET}")
    return passed == len(checks)

def test_dark_mode_support():
    """Test 8: Verify dark mode support."""
    print_test_header("Dark Mode Support")
    
    filepath = 'services/frontend/app/components/ExampleDiagrams.tsx'
    content = read_file(filepath)
    
    if not content:
        return False
    
    # Count dark: classes
    dark_classes = re.findall(r'dark:[a-z-]+', content)
    
    checks = [
        ("dark: prefix classes", len(dark_classes) >= 20),
        ("dark:bg- classes", bool(re.search(r'dark:bg-gray-\d+', content))),
        ("dark:text- classes", bool(re.search(r'dark:text-gray-\d+', content))),
        ("dark:border- classes", bool(re.search(r'dark:border-gray-\d+', content))),
        ("dark:hover: classes", bool(re.search(r'dark:hover:', content))),
    ]
    
    passed = 0
    for check_name, condition in checks:
        if condition:
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    if dark_classes:
        print_info(f"Found {len(dark_classes)} dark mode classes")
    
    print(f"\n{BOLD}Result: {passed}/{len(checks)} checks passed{RESET}")
    return passed == len(checks)

def test_responsive_design():
    """Test 9: Verify responsive design."""
    print_test_header("Responsive Design")
    
    filepath = 'services/frontend/app/components/ExampleDiagrams.tsx'
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("Mobile padding (p-4)", r"p-4"),
        ("Max width constraint", r"max-w-6xl"),
        ("Responsive grid", r"grid-cols-1.*md:grid-cols-2.*lg:grid-cols-3"),
        ("Flex wrap", r"flex-wrap"),
        ("Overflow handling", r"overflow-y-auto"),
        ("Touch target classes", r"touch-target"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content, re.IGNORECASE):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print(f"\n{BOLD}Result: {passed}/{len(checks)} checks passed{RESET}")
    return passed == len(checks)

def test_dashboard_integration():
    """Test 10: Verify dashboard integration."""
    print_test_header("Dashboard Integration")
    
    filepath = 'services/frontend/app/dashboard/page.tsx'
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("ExampleDiagrams import", r"(import.*ExampleDiagrams.*from.*components/ExampleDiagrams|dynamic.*import.*components/ExampleDiagrams)"),
        ("showExamples state", r"showExamples.*useState"),
        ("View Examples button", r"View Examples"),
        ("Button onClick handler", r"onClick.*setShowExamples.*true"),
        ("ExampleDiagrams component", r"<ExampleDiagrams"),
        ("isOpen prop", r"isOpen.*showExamples"),
        ("onClose prop", r"onClose.*setShowExamples.*false"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print(f"\n{BOLD}Result: {passed}/{len(checks)} checks passed{RESET}")
    return passed == len(checks)

def test_hook_functionality():
    """Test 11: Verify useExampleDiagrams hook."""
    print_test_header("useExampleDiagrams Hook")
    
    filepath = 'services/frontend/app/components/ExampleDiagrams.tsx'
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("Hook export", r"export function useExampleDiagrams"),
        ("isOpen state", r"isOpen.*useState.*false"),
        ("open function", r"const open.*useCallback.*setIsOpen.*true"),
        ("close function", r"const close.*useCallback.*setIsOpen.*false"),
        ("toggle function", r"const toggle.*useCallback.*setIsOpen.*prev"),
        ("Return object", r"return.*isOpen.*open.*close.*toggle"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print(f"\n{BOLD}Result: {passed}/{len(checks)} checks passed{RESET}")
    return passed == len(checks)

def test_documentation():
    """Test 12: Verify documentation."""
    print_test_header("Documentation")
    
    filepath = 'services/frontend/app/components/ExampleDiagrams.tsx'
    content = read_file(filepath)
    
    if not content:
        return False
    
    checks = [
        ("Feature number", r"Feature #670"),
        ("Feature description", r"example diagrams"),
        ("Features list", r"Features:"),
        ("Gallery mention", r"gallery"),
        ("Pre-made mention", r"pre-made"),
        ("Duplicate mention", r"duplicate"),
        ("Learn mention", r"learn"),
        ("Categories mention", r"Categories:"),
        ("Architecture mention", r"Architecture"),
        ("Flowchart mention", r"Flowchart"),
        ("ERD mention", r"ERD"),
        ("Sequence mention", r"Sequence"),
    ]
    
    passed = 0
    for check_name, pattern in checks:
        if re.search(pattern, content, re.IGNORECASE):
            print_success(f"{check_name} found")
            passed += 1
        else:
            print_error(f"{check_name} not found")
    
    print(f"\n{BOLD}Result: {passed}/{len(checks)} checks passed{RESET}")
    return passed == len(checks)

def main():
    """Run all tests and report results."""
    print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
    print(f"{BOLD}{BLUE}EXAMPLE DIAGRAMS FEATURE TEST SUITE{RESET}")
    print(f"{BOLD}{BLUE}Feature #670: Polish: Onboarding: Example Diagrams{RESET}")
    print(f"{BOLD}{BLUE}{'='*80}{RESET}\n")
    
    tests = [
        ("Component Structure", test_component_structure),
        ("Example Diagrams Data", test_example_diagrams_data),
        ("Category System", test_category_system),
        ("Search Functionality", test_search_functionality),
        ("Duplicate Functionality", test_duplicate_functionality),
        ("UI Components", test_ui_components),
        ("Accessibility Features", test_accessibility_features),
        ("Dark Mode Support", test_dark_mode_support),
        ("Responsive Design", test_responsive_design),
        ("Dashboard Integration", test_dashboard_integration),
        ("Hook Functionality", test_hook_functionality),
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
    print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
    print(f"{BOLD}{BLUE}TEST SUMMARY{RESET}")
    print(f"{BOLD}{BLUE}{'='*80}{RESET}\n")
    
    passed_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    for test_name, result in results:
        status = f"{GREEN}✓ PASS{RESET}" if result else f"{RED}✗ FAIL{RESET}"
        print(f"{status} - {test_name}")
    
    print(f"\n{BOLD}Results: {passed_count}/{total_count} tests passed ({passed_count/total_count*100:.1f}%){RESET}\n")
    
    if passed_count == total_count:
        print(f"{GREEN}{BOLD}✅ SUCCESS: All example diagrams tests passed!{RESET}\n")
        return 0
    else:
        print(f"{RED}{BOLD}❌ FAILURE: Some tests failed. Please review the output above.{RESET}\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
