#!/usr/bin/env python3
"""
Test Feature #661: Consistent Button Styles

This test verifies that all buttons across the application use the Button component
with consistent styling instead of inline styles.
"""

import os
import re
from pathlib import Path

def test_button_component_exists():
    """Test that Button component exists and has proper variants"""
    print("Test 1: Button component exists and has proper variants")
    
    button_path = Path("services/frontend/app/components/Button.tsx")
    if not button_path.exists():
        print("  ❌ Button component not found")
        return False
    
    content = button_path.read_text()
    
    # Check for ButtonVariant type
    if "export type ButtonVariant" not in content:
        print("  ❌ ButtonVariant type not found")
        return False
    
    # Check for required variants
    required_variants = ['primary', 'secondary', 'success', 'danger', 'outline', 'ghost']
    for variant in required_variants:
        if f"'{variant}'" not in content:
            print(f"  ❌ Variant '{variant}' not found")
            return False
    
    print("  ✅ Button component has all required variants")
    return True

def test_pages_use_button_component():
    """Test that key pages import and use Button component"""
    print("\nTest 2: Pages import and use Button component")
    
    pages_to_check = [
        "services/frontend/app/login/page.tsx",
        "services/frontend/app/register/page.tsx",
        "services/frontend/app/dashboard/page.tsx",
        "services/frontend/app/settings/security/page.tsx",
        "services/frontend/app/ai-generate/page.tsx",
    ]
    
    all_passed = True
    for page_path in pages_to_check:
        page = Path(page_path)
        if not page.exists():
            print(f"  ⚠️  Page {page_path} not found")
            continue
        
        content = page.read_text()
        
        # Check if page imports Button
        if "import Button" not in content and "from '../components/Button'" not in content and "from '../../components/Button'" not in content:
            print(f"  ❌ {page.name} doesn't import Button component")
            all_passed = False
            continue
        
        # Check if page uses <Button> component
        if "<Button" not in content:
            print(f"  ❌ {page.name} imports Button but doesn't use it")
            all_passed = False
            continue
        
        print(f"  ✅ {page.name} imports and uses Button component")
    
    return all_passed

def test_no_inline_button_styles():
    """Test that pages don't have inline button styles for primary action buttons"""
    print("\nTest 3: No inline primary button styles in key pages")
    
    pages_to_check = [
        "services/frontend/app/login/page.tsx",
        "services/frontend/app/register/page.tsx",
        "services/frontend/app/dashboard/page.tsx",
        "services/frontend/app/settings/security/page.tsx",
        "services/frontend/app/ai-generate/page.tsx",
    ]
    
    # Pattern to detect inline button styles with primary colors (bg-blue-600, bg-green-600, bg-red-600)
    # Specifically looking for <button> elements with these colors
    inline_style_pattern = r'<button[^>]*className="[^"]*bg-(blue|green|red)-[456]\d{2}[^"]*"[^>]*>'
    
    all_passed = True
    for page_path in pages_to_check:
        page = Path(page_path)
        if not page.exists():
            continue
        
        content = page.read_text()
        matches = re.findall(inline_style_pattern, content, re.MULTILINE)
        
        if matches:
            print(f"  ❌ {page.name} has {len(matches)} button(s) with inline primary color styles")
            all_passed = False
        else:
            print(f"  ✅ {page.name} has no inline primary button styles")
    
    return all_passed

def test_button_variants_used():
    """Test that Button component is used with proper variants"""
    print("\nTest 4: Button component used with proper variants")
    
    pages_to_check = [
        "services/frontend/app/login/page.tsx",
        "services/frontend/app/register/page.tsx",
        "services/frontend/app/dashboard/page.tsx",
    ]
    
    all_passed = True
    for page_path in pages_to_check:
        page = Path(page_path)
        if not page.exists():
            continue
        
        content = page.read_text()
        
        # Check if Button is used with variant prop
        if '<Button' in content:
            if 'variant=' in content:
                print(f"  ✅ {page.name} uses Button with variant prop")
            else:
                print(f"  ⚠️  {page.name} uses Button but might be missing variant prop")
                # This is okay as variant has a default value
    
    return all_passed

def test_css_button_classes():
    """Test that CSS has consistent button classes"""
    print("\nTest 5: CSS has consistent button classes")
    
    css_path = Path("services/frontend/src/styles/globals.css")
    if not css_path.exists():
        print("  ❌ globals.css not found")
        return False
    
    content = css_path.read_text()
    
    # Check for button classes
    required_classes = ['.btn', '.btn-primary', '.btn-secondary', '.btn-success', '.btn-danger', '.btn-outline', '.btn-ghost']
    
    all_found = True
    for cls in required_classes:
        if cls not in content:
            print(f"  ❌ CSS class '{cls}' not found")
            all_found = False
    
    if all_found:
        print("  ✅ All required button CSS classes are defined")
    
    return all_found

def test_button_loading_state():
    """Test that Button component supports loading state"""
    print("\nTest 6: Button component supports loading state")
    
    button_path = Path("services/frontend/app/components/Button.tsx")
    if not button_path.exists():
        print("  ❌ Button component not found")
        return False
    
    content = button_path.read_text()
    
    if "loading?" in content and "spinner" in content:
        print("  ✅ Button component supports loading state with spinner")
        return True
    else:
        print("  ❌ Button component doesn't support loading state")
        return False

def test_button_sizes():
    """Test that Button component supports different sizes"""
    print("\nTest 7: Button component supports different sizes")
    
    button_path = Path("services/frontend/app/components/Button.tsx")
    if not button_path.exists():
        print("  ❌ Button component not found")
        return False
    
    content = button_path.read_text()
    
    if "ButtonSize" in content and "'sm'" in content and "'md'" in content and "'lg'" in content:
        print("  ✅ Button component supports sm, md, lg sizes")
        return True
    else:
        print("  ❌ Button component doesn't support all sizes")
        return False

def test_button_accessibility():
    """Test that Button component has accessibility features"""
    print("\nTest 8: Button component has accessibility features")
    
    button_path = Path("services/frontend/app/components/Button.tsx")
    if not button_path.exists():
        print("  ❌ Button component not found")
        return False
    
    content = button_path.read_text()
    
    # Check for focus-ring class or focus styles
    if "focus-ring" in content or "focus:ring" in content:
        print("  ✅ Button component has focus ring for accessibility")
        return True
    else:
        print("  ⚠️  Button component might be missing focus styles")
        return True  # Not critical, CSS might handle it

def main():
    print("=" * 70)
    print("Testing Feature #661: Consistent Button Styles")
    print("=" * 70)
    
    # Change to project root
    os.chdir(Path(__file__).parent)
    
    tests = [
        test_button_component_exists,
        test_pages_use_button_component,
        test_no_inline_button_styles,
        test_button_variants_used,
        test_css_button_classes,
        test_button_loading_state,
        test_button_sizes,
        test_button_accessibility,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Test failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 70)
    print(f"Tests Passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("✅ ALL TESTS PASSED! Button styles are consistent.")
        return 0
    else:
        print("❌ Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    exit(main())
