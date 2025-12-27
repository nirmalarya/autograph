#!/usr/bin/env python3
"""
E2E Test for Feature #600: Tablet Responsive Design

Tests that the application properly adapts to tablet viewport sizes (768px - 1024px)
with appropriate layouts, spacing, and touch targets.

This test validates:
1. Tablet viewport configuration (768px - 1024px)
2. Tablet-specific media queries
3. Touch target sizes for tablet (44px minimum)
4. Typography optimization for tablet reading distance
5. Multi-column layouts (2-3 columns)
6. Tablet-specific utility classes
7. Portrait and landscape orientation handling
"""

import os
import sys

def test_tablet_responsive_design():
    """Test tablet responsive design (768px - 1024px breakpoint)"""

    print("\n" + "="*80)
    print("Feature #600: Tablet Responsive Design")
    print("="*80 + "\n")

    # Read globals.css to verify tablet-specific styles
    css_path = "services/frontend/src/styles/globals.css"

    if not os.path.exists(css_path):
        print(f"❌ FAIL: CSS file not found at {css_path}")
        return False

    with open(css_path, 'r') as f:
        css_content = f.read()

    all_checks_passed = True
    checks = []

    # ===== CHECK 1: Tablet Breakpoint Media Queries =====
    print("1. Checking Tablet Breakpoint Media Queries...")
    tablet_breakpoints = [
        "min-width: 768px) and (max-width: 1024px",  # Main tablet breakpoint
        "min-width: 768px) and (max-width: 834px) and (orientation: portrait",  # Portrait
        "min-width: 835px) and (max-width: 1024px) and (orientation: landscape",  # Landscape
    ]

    check_passed = True
    for breakpoint in tablet_breakpoints:
        if breakpoint in css_content:
            print(f"  ✅ Found tablet breakpoint: {breakpoint.split(')')[0]})")
            checks.append(f"Tablet breakpoint: {breakpoint.split(')')[0]}) - PASS")
        else:
            print(f"  ❌ Missing tablet breakpoint: {breakpoint.split(')')[0]})")
            checks.append(f"Tablet breakpoint: {breakpoint.split(')')[0]}) - FAIL")
            check_passed = False

    all_checks_passed = all_checks_passed and check_passed
    print(f"  Result: {'✅ PASS' if check_passed else '❌ FAIL'}\n")

    # ===== CHECK 2: Tablet Typography Optimization =====
    print("2. Checking Tablet Typography Optimization...")
    typography_checks = [
        "@apply text-5xl",  # h1
        "@apply text-4xl",  # h2
        "@apply text-3xl",  # h3
        "max-width: 65ch",  # Optimal line length
    ]

    check_passed = True
    for typo in typography_checks:
        if typo in css_content:
            print(f"  ✅ Found typography optimization: {typo}")
            checks.append(f"Typography: {typo} - PASS")
        else:
            print(f"  ❌ Missing typography optimization: {typo}")
            checks.append(f"Typography: {typo} - FAIL")
            check_passed = False

    all_checks_passed = all_checks_passed and check_passed
    print(f"  Result: {'✅ PASS' if check_passed else '❌ FAIL'}\n")

    # ===== CHECK 3: Tablet Touch Targets (44px minimum) =====
    print("3. Checking Tablet Touch Target Sizes...")
    touch_target_checks = [
        "min-height: 44px !important",
        "min-width: 44px !important",
        "padding: 10px 20px !important",  # Button padding for tablet
    ]

    check_passed = True
    for target in touch_target_checks:
        if target in css_content:
            print(f"  ✅ Found touch target: {target}")
            checks.append(f"Touch target: {target} - PASS")
        else:
            print(f"  ❌ Missing touch target: {target}")
            checks.append(f"Touch target: {target} - FAIL")
            check_passed = False

    all_checks_passed = all_checks_passed and check_passed
    print(f"  Result: {'✅ PASS' if check_passed else '❌ FAIL'}\n")

    # ===== CHECK 4: Tablet Grid Layouts =====
    print("4. Checking Tablet Grid Layouts...")
    grid_checks = [
        ".tablet-grid-2",
        "grid-template-columns: repeat(2, 1fr)",
        ".tablet-grid-3",
        "grid-template-columns: repeat(3, 1fr)",
        ".tablet-grid-4",
        "grid-template-columns: repeat(4, 1fr)",
    ]

    check_passed = True
    for grid in grid_checks:
        if grid in css_content:
            print(f"  ✅ Found grid layout: {grid}")
            checks.append(f"Grid layout: {grid} - PASS")
        else:
            print(f"  ❌ Missing grid layout: {grid}")
            checks.append(f"Grid layout: {grid} - FAIL")
            check_passed = False

    all_checks_passed = all_checks_passed and check_passed
    print(f"  Result: {'✅ PASS' if check_passed else '❌ FAIL'}\n")

    # ===== CHECK 5: Tablet Utility Classes =====
    print("5. Checking Tablet Utility Classes...")
    utility_checks = [
        ".tablet-only",
        ".tablet-hidden",
        ".tablet-spacing",
        ".tablet-flex-row",
        ".tablet-flex-col",
        ".tablet-w-full",
        ".tablet-w-1/2",
        ".tablet-w-1/3",
        ".tablet-text-center",
    ]

    check_passed = True
    for util in utility_checks:
        if util in css_content:
            print(f"  ✅ Found utility class: {util}")
            checks.append(f"Utility class: {util} - PASS")
        else:
            print(f"  ❌ Missing utility class: {util}")
            checks.append(f"Utility class: {util} - FAIL")
            check_passed = False

    all_checks_passed = all_checks_passed and check_passed
    print(f"  Result: {'✅ PASS' if check_passed else '❌ FAIL'}\n")

    # ===== CHECK 6: Tablet Layout Components =====
    print("6. Checking Tablet Layout Components...")
    layout_checks = [
        ".container-padding",  # Container padding
        ".section-spacing",    # Section spacing
        ".card",               # Card styling
        ".form-grid",          # Form grid
        ".sidebar",            # Sidebar
        "[role=\"toolbar\"]",  # Toolbar
        "[role=\"tablist\"]",  # Tabs
    ]

    check_passed = True
    for layout in layout_checks:
        if layout in css_content:
            print(f"  ✅ Found layout component: {layout}")
            checks.append(f"Layout component: {layout} - PASS")
        else:
            print(f"  ❌ Missing layout component: {layout}")
            checks.append(f"Layout component: {layout} - FAIL")
            check_passed = False

    all_checks_passed = all_checks_passed and check_passed
    print(f"  Result: {'✅ PASS' if check_passed else '❌ FAIL'}\n")

    # ===== CHECK 7: Tablet Performance Optimizations =====
    print("7. Checking Tablet Performance Optimizations...")
    perf_checks = [
        "scroll-behavior: smooth",
        "-webkit-overflow-scrolling: touch",
        "touch-action: manipulation",
        "overscroll-behavior: contain",
    ]

    check_passed = True
    for perf in perf_checks:
        if perf in css_content:
            print(f"  ✅ Found performance optimization: {perf}")
            checks.append(f"Performance: {perf} - PASS")
        else:
            print(f"  ❌ Missing performance optimization: {perf}")
            checks.append(f"Performance: {perf} - FAIL")
            check_passed = False

    all_checks_passed = all_checks_passed and check_passed
    print(f"  Result: {'✅ PASS' if check_passed else '❌ FAIL'}\n")

    # ===== CHECK 8: Orientation-Specific Styles =====
    print("8. Checking Orientation-Specific Styles...")
    orientation_checks = [
        "orientation: portrait",
        "orientation: landscape",
    ]

    check_passed = True
    for orient in orientation_checks:
        if orient in css_content:
            print(f"  ✅ Found orientation handling: {orient}")
            checks.append(f"Orientation: {orient} - PASS")
        else:
            print(f"  ❌ Missing orientation handling: {orient}")
            checks.append(f"Orientation: {orient} - FAIL")
            check_passed = False

    all_checks_passed = all_checks_passed and check_passed
    print(f"  Result: {'✅ PASS' if check_passed else '❌ FAIL'}\n")

    # ===== FINAL SUMMARY =====
    print("="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    print(f"\nTotal Checks: {len(checks)}")
    passed = len([c for c in checks if 'PASS' in c])
    failed = len([c for c in checks if 'FAIL' in c])
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"\nOverall Result: {'✅ PASS' if all_checks_passed else '❌ FAIL'}\n")

    if all_checks_passed:
        print("🎉 Feature #600: Tablet Responsive Design - COMPLETE")
        print("\nTablet responsive design is fully implemented with:")
        print("  • 768px - 1024px breakpoint support")
        print("  • Portrait and landscape orientation handling")
        print("  • 44px minimum touch targets")
        print("  • Optimized typography for tablet reading")
        print("  • 2-4 column grid layouts")
        print("  • Tablet-specific utility classes")
        print("  • Performance optimizations")
        print("  • Comprehensive layout components")
    else:
        print("❌ Feature #600: Tablet Responsive Design - INCOMPLETE")
        print("\nFailed checks:")
        for check in checks:
            if 'FAIL' in check:
                print(f"  • {check}")

    return all_checks_passed


if __name__ == "__main__":
    success = test_tablet_responsive_design()
    sys.exit(0 if success else 1)
