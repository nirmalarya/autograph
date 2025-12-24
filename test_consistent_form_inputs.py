#!/usr/bin/env python3
"""
Test Suite: Consistent Form Inputs (Feature #662)

Verifies that all form inputs across the application use the consistent Input component
instead of inline styles. This ensures a uniform look and feel, better maintainability,
and consistent accessibility features.

Test Coverage:
1. Input component exists and has proper structure
2. Key pages import and use Input component
3. No inline input styles remain (checking for common patterns)
4. Input component supports all necessary features (label, error, helper text, icons)
5. CSS classes for inputs are defined
6. Accessibility features are present
"""

import os
import re
import json
from pathlib import Path

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test(name, passed, details=""):
    """Print test result with color coding"""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} - {name}")
    if details:
        print(f"  {details}")

def read_file(filepath):
    """Read file content safely"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return None

def test_input_component_exists():
    """Test 1: Verify Input component exists with proper structure"""
    print(f"\n{BLUE}Test 1: Input Component Structure{RESET}")
    
    input_path = "services/frontend/app/components/Input.tsx"
    content = read_file(input_path)
    
    if not content:
        print_test("Input component file exists", False, f"File not found: {input_path}")
        return False
    
    print_test("Input component file exists", True)
    
    # Check for essential features
    tests = [
        ("Input component export", "export default function Input" in content or "const Input = " in content),
        ("Label support", "label?" in content or "label:" in content),
        ("Error state support", "error?" in content or "error:" in content),
        ("Success state support", "success?" in content or "success:" in content),
        ("Helper text support", "helperText?" in content or "helperText:" in content),
        ("Icon support", "icon?" in content or "icon:" in content),
        ("Full width support", "fullWidth?" in content or "fullWidth:" in content),
        ("Textarea component", "export const Textarea" in content or "Textarea = " in content),
        ("forwardRef usage", "forwardRef" in content),
        ("Accessibility (aria-invalid)", "aria-invalid" in content),
        ("Accessibility (aria-describedby)", "aria-describedby" in content),
    ]
    
    all_passed = True
    for test_name, result in tests:
        print_test(test_name, result)
        if not result:
            all_passed = False
    
    return all_passed

def test_pages_import_input():
    """Test 2: Verify key pages import Input component"""
    print(f"\n{BLUE}Test 2: Pages Import Input Component{RESET}")
    
    pages_to_check = [
        "services/frontend/app/login/page.tsx",
        "services/frontend/app/register/page.tsx",
        "services/frontend/app/dashboard/page.tsx",
        "services/frontend/app/settings/security/page.tsx",
    ]
    
    all_passed = True
    for page_path in pages_to_check:
        content = read_file(page_path)
        if not content:
            print_test(f"{os.path.basename(page_path)} exists", False)
            all_passed = False
            continue
        
        # Check for Input import
        has_import = (
            "import Input from" in content or
            "import { Input }" in content or
            "import Input," in content
        )
        
        page_name = os.path.basename(os.path.dirname(page_path)) if "settings" in page_path else os.path.basename(page_path).replace(".tsx", "")
        print_test(f"{page_name} imports Input", has_import)
        
        if not has_import:
            all_passed = False
    
    return all_passed

def test_pages_use_input_component():
    """Test 3: Verify pages use <Input> component instead of inline styles"""
    print(f"\n{BLUE}Test 3: Pages Use Input Component{RESET}")
    
    pages_to_check = [
        ("services/frontend/app/login/page.tsx", "login"),
        ("services/frontend/app/register/page.tsx", "register"),
        ("services/frontend/app/dashboard/page.tsx", "dashboard"),
        ("services/frontend/app/settings/security/page.tsx", "security"),
    ]
    
    all_passed = True
    for page_path, page_name in pages_to_check:
        content = read_file(page_path)
        if not content:
            continue
        
        # Check for <Input usage
        has_input_usage = "<Input" in content
        print_test(f"{page_name} uses <Input> component", has_input_usage)
        
        if not has_input_usage:
            all_passed = False
    
    return all_passed

def test_no_inline_input_styles():
    """Test 4: Verify no inline input styles remain in key pages"""
    print(f"\n{BLUE}Test 4: No Inline Input Styles{RESET}")
    
    pages_to_check = [
        ("services/frontend/app/login/page.tsx", "login"),
        ("services/frontend/app/register/page.tsx", "register"),
        ("services/frontend/app/dashboard/page.tsx", "dashboard"),
        ("services/frontend/app/settings/security/page.tsx", "security"),
    ]
    
    # Patterns that indicate inline input styling (not using Input component)
    inline_patterns = [
        (r'<input[^>]*className="[^"]*w-full[^"]*px-[34][^"]*py-[23][^"]*border[^"]*border-gray', 
         "Full inline input styles"),
    ]
    
    all_passed = True
    for page_path, page_name in pages_to_check:
        content = read_file(page_path)
        if not content:
            continue
        
        page_clean = True
        for pattern, pattern_name in inline_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            if matches:
                print_test(f"{page_name} has no {pattern_name}", False, 
                          f"Found {len(matches)} instances")
                page_clean = False
                all_passed = False
        
        if page_clean:
            print_test(f"{page_name} has no inline input styles", True)
    
    return all_passed

def test_css_input_classes():
    """Test 5: Verify CSS input classes are defined"""
    print(f"\n{BLUE}Test 5: CSS Input Classes{RESET}")
    
    css_path = "services/frontend/src/styles/globals.css"
    content = read_file(css_path)
    
    if not content:
        print_test("globals.css exists", False)
        return False
    
    print_test("globals.css exists", True)
    
    # Check for input class definitions
    tests = [
        (".input base class", ".input {" in content or ".input{" in content),
        (".input-error class", ".input-error {" in content or ".input-error{" in content),
        (".input-success class", ".input-success {" in content or ".input-success{" in content),
        ("Input focus styles", "focus:ring" in content and ".input" in content),
        ("Input dark mode", "dark:bg-gray" in content and ".input" in content),
        ("Input disabled state", "disabled:opacity" in content or "disabled:cursor-not-allowed" in content),
    ]
    
    all_passed = True
    for test_name, result in tests:
        print_test(test_name, result)
        if not result:
            all_passed = False
    
    return all_passed

def test_input_features():
    """Test 6: Verify Input component has all necessary features"""
    print(f"\n{BLUE}Test 6: Input Component Features{RESET}")
    
    input_path = "services/frontend/app/components/Input.tsx"
    content = read_file(input_path)
    
    if not content:
        return False
    
    tests = [
        ("Label rendering", 'label &&' in content or 'label?' in content),
        ("Error message display", 'error &&' in content or 'error?' in content),
        ("Success message display", 'success &&' in content or 'success?' in content),
        ("Helper text display", 'helperText &&' in content or 'helperText?' in content),
        ("Icon positioning (left)", 'iconPosition === "left"' in content or "iconPosition === 'left'" in content),
        ("Icon positioning (right)", 'iconPosition === "right"' in content or "iconPosition === 'right'" in content),
        ("Required indicator", 'required &&' in content or 'props.required' in content),
        ("Error icon", 'error && !icon' in content),
        ("Success icon", 'success && !icon' in content),
    ]
    
    all_passed = True
    for test_name, result in tests:
        print_test(test_name, result)
        if not result:
            all_passed = False
    
    return all_passed

def test_accessibility():
    """Test 7: Verify accessibility features"""
    print(f"\n{BLUE}Test 7: Accessibility Features{RESET}")
    
    input_path = "services/frontend/app/components/Input.tsx"
    content = read_file(input_path)
    
    if not content:
        return False
    
    tests = [
        ("aria-invalid attribute", "aria-invalid" in content),
        ("aria-describedby attribute", "aria-describedby" in content),
        ("Label htmlFor attribute", "htmlFor" in content),
        ("Input id generation", "inputId" in content or "id ||" in content),
        ("Error message id", "error" in content and "id=" in content),
        ("Helper text id", "helper" in content and "id=" in content),
    ]
    
    all_passed = True
    for test_name, result in tests:
        print_test(test_name, result)
        if not result:
            all_passed = False
    
    return all_passed

def test_form_validation():
    """Test 8: Verify forms have proper validation"""
    print(f"\n{BLUE}Test 8: Form Validation{RESET}")
    
    pages_to_check = [
        ("services/frontend/app/login/page.tsx", "login", ["email", "password"]),
        ("services/frontend/app/register/page.tsx", "register", ["email", "password"]),
    ]
    
    all_passed = True
    for page_path, page_name, required_fields in pages_to_check:
        content = read_file(page_path)
        if not content:
            continue
        
        for field in required_fields:
            # Check if field has required attribute
            has_required = f'name="{field}"' in content and "required" in content
            print_test(f"{page_name} - {field} is required", has_required)
            if not has_required:
                all_passed = False
    
    return all_passed

def run_all_tests():
    """Run all tests and report results"""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}CONSISTENT FORM INPUTS TEST SUITE{RESET}")
    print(f"{BLUE}Feature #662: Polish - Consistent form inputs{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")
    
    tests = [
        ("Input Component Structure", test_input_component_exists),
        ("Pages Import Input", test_pages_import_input),
        ("Pages Use Input Component", test_pages_use_input_component),
        ("No Inline Input Styles", test_no_inline_input_styles),
        ("CSS Input Classes", test_css_input_classes),
        ("Input Component Features", test_input_features),
        ("Accessibility Features", test_accessibility),
        ("Form Validation", test_form_validation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n{RED}Error running {test_name}: {str(e)}{RESET}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}TEST SUMMARY{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{GREEN}✓{RESET}" if result else f"{RED}✗{RESET}"
        print(f"{status} {test_name}")
    
    print(f"\n{BLUE}Results: {passed}/{total} tests passed{RESET}")
    
    if passed == total:
        print(f"\n{GREEN}{'='*80}{RESET}")
        print(f"{GREEN}✓ ALL TESTS PASSED! Form inputs are consistent.{RESET}")
        print(f"{GREEN}{'='*80}{RESET}")
        return True
    else:
        print(f"\n{YELLOW}{'='*80}{RESET}")
        print(f"{YELLOW}⚠ {total - passed} test(s) failed. Please review the failures above.{RESET}")
        print(f"{YELLOW}{'='*80}{RESET}")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
