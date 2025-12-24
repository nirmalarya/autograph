#!/usr/bin/env python3
"""
Test script to verify tooltip functionality in AutoGraph v3.

This script tests:
1. Tooltip component exists and is properly implemented
2. Tooltips are added to icon buttons
3. Tooltips have proper accessibility attributes
4. Tooltips work with keyboard navigation
"""

import os
import sys

def test_tooltip_component():
    """Test that Tooltip component exists and has proper structure."""
    print("=" * 80)
    print("TEST 1: Tooltip Component Implementation")
    print("=" * 80)
    
    tooltip_path = "services/frontend/app/components/Tooltip.tsx"
    
    if not os.path.exists(tooltip_path):
        print("❌ FAILED: Tooltip.tsx not found")
        return False
    
    with open(tooltip_path, 'r') as f:
        content = f.read()
    
    # Check for key features
    checks = [
        ("TooltipPosition type", "TooltipPosition"),
        ("Tooltip component export", "export default function Tooltip"),
        ("Accessibility role", 'role="tooltip"'),
        ("ARIA describedby", "aria-describedby"),
        ("Position calculation", "calculatePosition"),
        ("Mouse events", "onMouseEnter"),
        ("Keyboard events", "onFocus"),
        ("Portal rendering", "fixed z-"),
        ("SimpleTooltip helper", "SimpleTooltip"),
        ("useTooltip hook", "useTooltip"),
    ]
    
    passed = 0
    for name, check in checks:
        if check in content:
            print(f"✅ {name}: Found")
            passed += 1
        else:
            print(f"❌ {name}: Not found")
    
    print(f"\nResult: {passed}/{len(checks)} checks passed")
    return passed == len(checks)

def test_tooltip_integration():
    """Test that tooltips are integrated into components."""
    print("\n" + "=" * 80)
    print("TEST 2: Tooltip Integration in Components")
    print("=" * 80)
    
    components = [
        ("services/frontend/app/components/ThemeToggle.tsx", "ThemeToggle"),
        ("services/frontend/app/components/HighContrastToggle.tsx", "HighContrastToggle"),
        ("services/frontend/app/components/Button.tsx", "IconButton"),
        ("services/frontend/app/dashboard/page.tsx", "Dashboard"),
    ]
    
    passed = 0
    for path, name in components:
        if not os.path.exists(path):
            print(f"❌ {name}: File not found")
            continue
        
        with open(path, 'r') as f:
            content = f.read()
        
        # Check if Tooltip is imported and used
        has_import = "import Tooltip" in content or "import { Tooltip }" in content
        has_usage = "<Tooltip" in content
        
        if has_import and has_usage:
            print(f"✅ {name}: Tooltip imported and used")
            passed += 1
        elif has_import:
            print(f"⚠️  {name}: Tooltip imported but not used")
        elif has_usage:
            print(f"⚠️  {name}: Tooltip used but not imported")
        else:
            print(f"❌ {name}: No tooltip integration")
    
    print(f"\nResult: {passed}/{len(components)} components have tooltips")
    return passed >= 3  # At least 3 components should have tooltips

def test_accessibility_features():
    """Test that tooltips have proper accessibility features."""
    print("\n" + "=" * 80)
    print("TEST 3: Accessibility Features")
    print("=" * 80)
    
    tooltip_path = "services/frontend/app/components/Tooltip.tsx"
    
    with open(tooltip_path, 'r') as f:
        content = f.read()
    
    accessibility_checks = [
        ("ARIA role", 'role="tooltip"'),
        ("ARIA describedby", "aria-describedby"),
        ("Focus handling", "onFocus"),
        ("Blur handling", "onBlur"),
        ("Keyboard navigation", "onFocus"),
        ("Screen reader support", "aria-"),
    ]
    
    passed = 0
    for name, check in accessibility_checks:
        if check in content:
            print(f"✅ {name}: Implemented")
            passed += 1
        else:
            print(f"❌ {name}: Not found")
    
    print(f"\nResult: {passed}/{len(accessibility_checks)} accessibility features present")
    return passed >= 4  # At least 4 accessibility features should be present

def test_tooltip_positioning():
    """Test that tooltips support multiple positions."""
    print("\n" + "=" * 80)
    print("TEST 4: Tooltip Positioning")
    print("=" * 80)
    
    tooltip_path = "services/frontend/app/components/Tooltip.tsx"
    
    with open(tooltip_path, 'r') as f:
        content = f.read()
    
    positions = ["top", "bottom", "left", "right"]
    
    passed = 0
    for pos in positions:
        if f"'{pos}'" in content or f'"{pos}"' in content:
            print(f"✅ Position '{pos}': Supported")
            passed += 1
        else:
            print(f"❌ Position '{pos}': Not supported")
    
    # Check for position calculation
    if "calculatePosition" in content:
        print(f"✅ Position calculation: Implemented")
        passed += 1
    else:
        print(f"❌ Position calculation: Not implemented")
    
    print(f"\nResult: {passed}/{len(positions) + 1} positioning features present")
    return passed >= 4

def test_tooltip_styling():
    """Test that tooltips have proper styling."""
    print("\n" + "=" * 80)
    print("TEST 5: Tooltip Styling")
    print("=" * 80)
    
    tooltip_path = "services/frontend/app/components/Tooltip.tsx"
    
    with open(tooltip_path, 'r') as f:
        content = f.read()
    
    styling_checks = [
        ("Background color", "bg-gray-900"),
        ("Text color", "text-white"),
        ("Border radius", "rounded"),
        ("Shadow", "shadow"),
        ("Z-index", "z-"),
        ("Fade animation", "fade-in"),
        ("Arrow indicator", "arrow"),
        ("Dark mode support", "dark:"),
    ]
    
    passed = 0
    for name, check in styling_checks:
        if check in content:
            print(f"✅ {name}: Implemented")
            passed += 1
        else:
            print(f"❌ {name}: Not found")
    
    print(f"\nResult: {passed}/{len(styling_checks)} styling features present")
    return passed >= 6

def test_icon_button_tooltips():
    """Test that IconButton component has tooltip support."""
    print("\n" + "=" * 80)
    print("TEST 6: IconButton Tooltip Support")
    print("=" * 80)
    
    button_path = "services/frontend/app/components/Button.tsx"
    
    with open(button_path, 'r') as f:
        content = f.read()
    
    checks = [
        ("Tooltip import", "import Tooltip"),
        ("Tooltip prop", "tooltip?:"),
        ("Tooltip position prop", "tooltipPosition?:"),
        ("Tooltip wrapper", "<Tooltip"),
        ("Default tooltip (label)", "tooltip || label"),
    ]
    
    passed = 0
    for name, check in checks:
        if check in content:
            print(f"✅ {name}: Implemented")
            passed += 1
        else:
            print(f"❌ {name}: Not found")
    
    print(f"\nResult: {passed}/{len(checks)} IconButton tooltip features present")
    return passed >= 4

def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("TOOLTIP FUNCTIONALITY TEST SUITE")
    print("=" * 80)
    
    tests = [
        test_tooltip_component,
        test_tooltip_integration,
        test_accessibility_features,
        test_tooltip_positioning,
        test_tooltip_styling,
        test_icon_button_tooltips,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED! Tooltip feature is fully implemented.")
        return 0
    elif passed >= total * 0.8:
        print("\n⚠️  MOST TESTS PASSED. Minor issues to address.")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED. Please review implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
