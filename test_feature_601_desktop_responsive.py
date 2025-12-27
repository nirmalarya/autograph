#!/usr/bin/env python3
"""
Feature #601: Desktop Responsive Design Test
Tests desktop responsive design with full layout, 3-column grid, and all panels visible.

Acceptance Criteria:
- Open on desktop (>1024px)
- Verify full layout
- Verify 3-column grid
- Verify all panels visible

Test Coverage:
- Desktop breakpoints (1025px, 1441px, 1921px)
- Typography scaling
- 3-column grid layouts
- Panel visibility
- Navigation layout
- Touch target sizes
- Form layouts
- Modal sizes
- Table display
- Spacing utilities
- Flexbox utilities
- Performance optimizations
"""

import re


def test_desktop_responsive_design():
    """Test desktop responsive design implementation"""

    css_file = 'services/frontend/src/styles/globals.css'

    with open(css_file, 'r') as f:
        content = f.read()

    print("Testing Feature #601: Desktop Responsive Design")
    print("=" * 60)

    tests_passed = 0
    tests_failed = 0

    # Test 1: Desktop breakpoint media query exists
    print("\n1. Testing desktop breakpoint (min-width: 1025px)...")
    if '@media (min-width: 1025px)' in content:
        print("   ✅ Desktop breakpoint defined")
        tests_passed += 1
    else:
        print("   ❌ Desktop breakpoint missing")
        tests_failed += 1

    # Test 2: Large desktop breakpoint
    print("\n2. Testing large desktop breakpoint (min-width: 1441px)...")
    if '@media (min-width: 1441px)' in content:
        print("   ✅ Large desktop breakpoint defined")
        tests_passed += 1
    else:
        print("   ❌ Large desktop breakpoint missing")
        tests_failed += 1

    # Test 3: Ultra-wide desktop breakpoint
    print("\n3. Testing ultra-wide breakpoint (min-width: 1921px)...")
    if '@media (min-width: 1921px)' in content:
        print("   ✅ Ultra-wide breakpoint defined")
        tests_passed += 1
    else:
        print("   ❌ Ultra-wide breakpoint missing")
        tests_failed += 1

    # Test 4: Desktop typography
    print("\n4. Testing desktop typography...")
    typography_tests = [
        ('h1', '2.5rem'),
        ('h2', '2rem'),
        ('h3', '1.5rem'),
        ('h4', '1.25rem'),
        ('body', '16px'),
    ]
    typography_passed = 0
    for element, size in typography_tests:
        if f'{element} {{' in content and size in content:
            print(f"   ✅ {element} typography defined ({size})")
            typography_passed += 1
        else:
            print(f"   ❌ {element} typography missing or incorrect")

    if typography_passed == len(typography_tests):
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 5: Container max-width
    print("\n5. Testing container max-width...")
    if '.container {' in content and 'max-width: 1920px' in content:
        print("   ✅ Container max-width defined")
        tests_passed += 1
    else:
        print("   ❌ Container max-width missing")
        tests_failed += 1

    # Test 6: 3-column grid system
    print("\n6. Testing 3-column grid system...")
    if '.desktop-grid-3 {' in content and 'grid-template-columns: repeat(3, 1fr)' in content:
        print("   ✅ 3-column grid defined")
        tests_passed += 1
    else:
        print("   ❌ 3-column grid missing")
        tests_failed += 1

    # Test 7: 2-column and 4-column grids
    print("\n7. Testing additional grid layouts...")
    grid_tests = [
        ('.desktop-grid-2', 'repeat(2, 1fr)'),
        ('.desktop-grid-4', 'repeat(4, 1fr)'),
    ]
    grid_passed = 0
    for grid_class, columns in grid_tests:
        if grid_class in content and columns in content:
            print(f"   ✅ {grid_class} defined")
            grid_passed += 1
        else:
            print(f"   ❌ {grid_class} missing")

    if grid_passed == len(grid_tests):
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 8: 3-panel layout (Sidebar + Main + Aside)
    print("\n8. Testing 3-panel layout...")
    if '.desktop-layout-3col {' in content and 'grid-template-columns: 280px 1fr 320px' in content:
        print("   ✅ 3-panel layout defined")
        tests_passed += 1
    else:
        print("   ❌ 3-panel layout missing")
        tests_failed += 1

    # Test 9: Panel visibility classes
    print("\n9. Testing panel visibility...")
    panel_tests = [
        '.desktop-panel',
        '.desktop-sidebar',
        '.desktop-main',
        '.desktop-aside',
    ]
    panel_passed = 0
    for panel_class in panel_tests:
        if panel_class in content:
            print(f"   ✅ {panel_class} defined")
            panel_passed += 1
        else:
            print(f"   ❌ {panel_class} missing")

    if panel_passed == len(panel_tests):
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 10: Desktop navigation
    print("\n10. Testing desktop navigation...")
    if 'nav.desktop-nav {' in content and 'flex-direction: row' in content:
        print("   ✅ Desktop navigation defined")
        tests_passed += 1
    else:
        print("   ❌ Desktop navigation missing")
        tests_failed += 1

    # Test 11: Desktop cards
    print("\n11. Testing desktop card styles...")
    if '.desktop-card {' in content and 'padding: 2rem' in content:
        print("   ✅ Desktop cards defined")
        tests_passed += 1
    else:
        print("   ❌ Desktop cards missing")
        tests_failed += 1

    # Test 12: Touch targets for desktop (smaller than mobile)
    print("\n12. Testing touch target sizes...")
    if 'min-height: 40px' in content and 'min-width: 40px' in content:
        print("   ✅ Desktop touch targets defined (40px)")
        tests_passed += 1
    else:
        print("   ❌ Desktop touch targets missing")
        tests_failed += 1

    # Test 13: Multi-column forms
    print("\n13. Testing multi-column form layouts...")
    form_tests = [
        ('.desktop-form-2col', 'repeat(2, 1fr)'),
        ('.desktop-form-3col', 'repeat(3, 1fr)'),
    ]
    form_passed = 0
    for form_class, columns in form_tests:
        if form_class in content and columns in content:
            print(f"   ✅ {form_class} defined")
            form_passed += 1
        else:
            print(f"   ❌ {form_class} missing")

    if form_passed == len(form_tests):
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 14: Desktop modals
    print("\n14. Testing desktop modal sizes...")
    modal_tests = [
        ('.desktop-modal', 'max-width: 800px'),
        ('.desktop-modal-lg', 'max-width: 1200px'),
    ]
    modal_passed = 0
    for modal_class, width in modal_tests:
        if modal_class in content and width in content:
            print(f"   ✅ {modal_class} defined")
            modal_passed += 1
        else:
            print(f"   ❌ {modal_class} missing")

    if modal_passed == len(modal_tests):
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 15: Desktop table layout
    print("\n15. Testing desktop table layout...")
    if '.desktop-table {' in content and 'overflow-x: visible' in content:
        print("   ✅ Desktop table layout defined")
        tests_passed += 1
    else:
        print("   ❌ Desktop table layout missing")
        tests_failed += 1

    # Test 16: Spacing utilities
    print("\n16. Testing spacing utilities...")
    spacing_tests = [
        '.desktop-space-y-sm',
        '.desktop-space-y-md',
        '.desktop-space-y-lg',
    ]
    spacing_passed = 0
    for spacing_class in spacing_tests:
        if spacing_class in content:
            print(f"   ✅ {spacing_class} defined")
            spacing_passed += 1
        else:
            print(f"   ❌ {spacing_class} missing")

    if spacing_passed == len(spacing_tests):
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 17: Hover effects
    print("\n17. Testing desktop hover effects...")
    if '.desktop-hover:hover' in content and 'transform: translateY(-2px)' in content:
        print("   ✅ Desktop hover effects defined")
        tests_passed += 1
    else:
        print("   ❌ Desktop hover effects missing")
        tests_failed += 1

    # Test 18: Tooltips
    print("\n18. Testing desktop tooltips...")
    if '.desktop-tooltip' in content and 'attr(data-tooltip)' in content:
        print("   ✅ Desktop tooltips defined")
        tests_passed += 1
    else:
        print("   ❌ Desktop tooltips missing")
        tests_failed += 1

    # Test 19: Display utilities
    print("\n19. Testing display utilities...")
    display_tests = [
        '.desktop-hidden',
        '.desktop-visible',
        '.desktop-flex',
        '.desktop-grid',
        '.desktop-inline-flex',
    ]
    display_passed = 0
    for display_class in display_tests:
        if display_class in content:
            print(f"   ✅ {display_class} defined")
            display_passed += 1
        else:
            print(f"   ❌ {display_class} missing")

    if display_passed == len(display_tests):
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 20: Flexbox utilities
    print("\n20. Testing flexbox utilities...")
    flex_tests = [
        '.desktop-flex-row',
        '.desktop-flex-col',
        '.desktop-flex-wrap',
        '.desktop-justify-start',
        '.desktop-justify-center',
        '.desktop-justify-between',
        '.desktop-items-center',
    ]
    flex_passed = 0
    for flex_class in flex_tests:
        if flex_class in content:
            print(f"   ✅ {flex_class} defined")
            flex_passed += 1
        else:
            print(f"   ❌ {flex_class} missing")

    if flex_passed == len(flex_tests):
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 21: Width utilities
    print("\n21. Testing width utilities...")
    width_tests = [
        '.desktop-w-full',
        '.desktop-w-1/2',
        '.desktop-w-1/3',
        '.desktop-w-2/3',
        '.desktop-w-1/4',
        '.desktop-w-3/4',
    ]
    width_passed = 0
    for width_class in width_tests:
        if width_class in content:
            print(f"   ✅ {width_class} defined")
            width_passed += 1
        else:
            print(f"   ❌ {width_class} missing")

    if width_passed == len(width_tests):
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 22: Text alignment utilities
    print("\n22. Testing text alignment utilities...")
    text_tests = [
        '.desktop-text-left',
        '.desktop-text-center',
        '.desktop-text-right',
    ]
    text_passed = 0
    for text_class in text_tests:
        if text_class in content:
            print(f"   ✅ {text_class} defined")
            text_passed += 1
        else:
            print(f"   ❌ {text_class} missing")

    if text_passed == len(text_tests):
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 23: Padding utilities
    print("\n23. Testing padding utilities...")
    padding_tests = [
        '.desktop-p-0',
        '.desktop-p-2',
        '.desktop-p-4',
        '.desktop-p-8',
    ]
    padding_passed = 0
    for padding_class in padding_tests:
        if padding_class in content:
            print(f"   ✅ {padding_class} defined")
            padding_passed += 1
        else:
            print(f"   ❌ {padding_class} missing")

    if padding_passed == len(padding_tests):
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 24: Margin utilities
    print("\n24. Testing margin utilities...")
    margin_tests = [
        '.desktop-m-0',
        '.desktop-m-4',
        '.desktop-mt-4',
        '.desktop-mb-4',
    ]
    margin_passed = 0
    for margin_class in margin_tests:
        if margin_class in content:
            print(f"   ✅ {margin_class} defined")
            margin_passed += 1
        else:
            print(f"   ❌ {margin_class} missing")

    if margin_passed == len(margin_tests):
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 25: Performance optimizations
    print("\n25. Testing performance optimizations...")
    if '.desktop-gpu-accelerate' in content and 'translateZ(0)' in content:
        print("   ✅ GPU acceleration defined")
        tests_passed += 1
    else:
        print("   ❌ GPU acceleration missing")
        tests_failed += 1

    # Test 26: Smooth scrolling
    print("\n26. Testing smooth scrolling...")
    if 'scroll-behavior: smooth' in content:
        print("   ✅ Smooth scrolling enabled")
        tests_passed += 1
    else:
        print("   ❌ Smooth scrolling missing")
        tests_failed += 1

    # Test 27: Transition optimization
    print("\n27. Testing transition optimization...")
    if 'transition-duration: 0.2s' in content and 'transition-timing-function: ease' in content:
        print("   ✅ Transitions optimized")
        tests_passed += 1
    else:
        print("   ❌ Transition optimization missing")
        tests_failed += 1

    # Test 28: High refresh rate support
    print("\n28. Testing high refresh rate monitor support...")
    if '@media (min-resolution: 120dpi)' in content and 'transition-duration: 0.15s' in content:
        print("   ✅ High refresh rate support added")
        tests_passed += 1
    else:
        print("   ❌ High refresh rate support missing")
        tests_failed += 1

    # Test 29: Focus visible for keyboard navigation
    print("\n29. Testing keyboard navigation focus...")
    if '*:focus-visible' in content and 'outline: 2px solid' in content:
        print("   ✅ Keyboard focus visible defined")
        tests_passed += 1
    else:
        print("   ❌ Keyboard focus missing")
        tests_failed += 1

    # Test 30: Custom scrollbar
    print("\n30. Testing custom scrollbar...")
    if '.desktop-scrollable::-webkit-scrollbar' in content:
        print("   ✅ Custom scrollbar defined")
        tests_passed += 1
    else:
        print("   ❌ Custom scrollbar missing")
        tests_failed += 1

    # Test 31: Scrollbar width
    print("\n31. Testing scrollbar styling...")
    if 'scrollbar-width: thin' in content and 'scrollbar-color:' in content:
        print("   ✅ Scrollbar styling defined")
        tests_passed += 1
    else:
        print("   ❌ Scrollbar styling missing")
        tests_failed += 1

    # Test 32: Large desktop grid adjustments
    print("\n32. Testing large desktop grid adjustments (>1440px)...")
    if 'grid-template-columns: 320px 1fr 380px' in content:
        print("   ✅ Large desktop grid spacing defined")
        tests_passed += 1
    else:
        print("   ❌ Large desktop grid spacing missing")
        tests_failed += 1

    # Test 33: Ultra-wide grid support
    print("\n33. Testing ultra-wide grid (6-column)...")
    if '.desktop-grid-6' in content and 'repeat(6, 1fr)' in content:
        print("   ✅ 6-column ultra-wide grid defined")
        tests_passed += 1
    else:
        print("   ❌ 6-column grid missing")
        tests_failed += 1

    # Test 34: 4K display typography
    print("\n34. Testing 4K display typography...")
    if 'font-size: 3rem' in content:  # 4K h1 size
        print("   ✅ 4K typography scaling defined")
        tests_passed += 1
    else:
        print("   ❌ 4K typography missing")
        tests_failed += 1

    # Test 35: Wide container support
    print("\n35. Testing wide container (>1920px)...")
    if 'max-width: 2560px' in content:
        print("   ✅ Wide container defined")
        tests_passed += 1
    else:
        print("   ❌ Wide container missing")
        tests_failed += 1

    # Test 36: Sticky positioning for panels
    print("\n36. Testing sticky panel positioning...")
    if 'position: sticky' in content and 'top: 4rem' in content:
        print("   ✅ Sticky panel positioning defined")
        tests_passed += 1
    else:
        print("   ❌ Sticky positioning missing")
        tests_failed += 1

    # Test 37: Panel height calculations
    print("\n37. Testing panel height calculations...")
    if 'calc(100vh - 6rem)' in content:
        print("   ✅ Panel height calculations defined")
        tests_passed += 1
    else:
        print("   ❌ Panel height calculations missing")
        tests_failed += 1

    # Test 38: Image preview sizes
    print("\n38. Testing desktop image preview sizes...")
    if '.desktop-img-preview' in content and 'max-width: 600px' in content:
        print("   ✅ Desktop image previews defined")
        tests_passed += 1
    else:
        print("   ❌ Desktop image previews missing")
        tests_failed += 1

    # Final summary
    print("\n" + "=" * 60)
    print(f"FINAL RESULTS: {tests_passed}/{tests_passed + tests_failed} tests passed")
    print("=" * 60)

    if tests_failed == 0:
        print("✅ All desktop responsive design tests PASSED!")
        print("\nFeature #601 Implementation Summary:")
        print("- Desktop breakpoint (>1024px) ✅")
        print("- 3-column grid system ✅")
        print("- Full panel visibility ✅")
        print("- Large desktop support (>1440px) ✅")
        print("- Ultra-wide support (>1920px) ✅")
        print("- 4K display optimization ✅")
        print("- Performance optimizations ✅")
        print("- Accessibility features ✅")
        return True
    else:
        print(f"❌ {tests_failed} tests FAILED")
        return False


if __name__ == '__main__':
    success = test_desktop_responsive_design()
    exit(0 if success else 1)
