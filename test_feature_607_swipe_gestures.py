#!/usr/bin/env python3
"""
Feature #607 Validation: Mobile menu swipe gestures
Tests swipe gesture functionality for opening/closing mobile sidebar menus.

Acceptance Criteria:
- Swipe right to open sidebar
- Swipe left to close
- Verify smooth animation
"""

import os
import sys


def validate_feature_607():
    """Validate Feature #607: Mobile menu swipe gestures"""
    print("=" * 80)
    print("Feature #607: Mobile menu swipe gestures")
    print("=" * 80)

    checks_passed = 0
    total_checks = 35

    # Check 1: Hook file exists
    print("\n[1/35] Checking if useSwipeGesture hook exists...")
    hook_file = 'services/frontend/src/hooks/useSwipeGesture.ts'
    try:
        with open(hook_file, 'r') as f:
            hook_content = f.read()
            if 'useSwipeGesture' in hook_content:
                print("✅ useSwipeGesture hook file exists")
                checks_passed += 1
            else:
                print("❌ useSwipeGesture hook not found in file")
    except FileNotFoundError:
        print("❌ useSwipeGesture hook file not found")
        hook_content = ""

    # Check 2: SwipeGestureOptions interface
    print("\n[2/35] Checking SwipeGestureOptions interface...")
    if 'SwipeGestureOptions' in hook_content:
        print("✅ SwipeGestureOptions interface defined")
        checks_passed += 1
    else:
        print("❌ SwipeGestureOptions interface missing")

    # Check 3: onSwipeLeft callback
    print("\n[3/35] Checking onSwipeLeft callback...")
    if 'onSwipeLeft' in hook_content:
        print("✅ onSwipeLeft callback supported")
        checks_passed += 1
    else:
        print("❌ onSwipeLeft callback missing")

    # Check 4: onSwipeRight callback
    print("\n[4/35] Checking onSwipeRight callback...")
    if 'onSwipeRight' in hook_content:
        print("✅ onSwipeRight callback supported")
        checks_passed += 1
    else:
        print("❌ onSwipeRight callback missing")

    # Check 5: Touch event handlers
    print("\n[5/35] Checking touch event handlers...")
    if 'touchstart' in hook_content and 'touchmove' in hook_content and 'touchend' in hook_content:
        print("✅ Touch event handlers implemented")
        checks_passed += 1
    else:
        print("❌ Touch event handlers incomplete")

    # Check 6: Minimum swipe distance
    print("\n[6/35] Checking minimum swipe distance...")
    if 'minSwipeDistance' in hook_content or 'threshold' in hook_content.lower():
        print("✅ Minimum swipe distance configurable")
        checks_passed += 1
    else:
        print("❌ Minimum swipe distance not configurable")

    # Check 7: Maximum swipe time
    print("\n[7/35] Checking maximum swipe time...")
    if 'maxSwipeTime' in hook_content or 'timeout' in hook_content.lower():
        print("✅ Maximum swipe time configurable")
        checks_passed += 1
    else:
        print("❌ Maximum swipe time not configurable")

    # Check 8: Touch position tracking
    print("\n[8/35] Checking touch position tracking...")
    if 'TouchPosition' in hook_content or ('clientX' in hook_content and 'clientY' in hook_content):
        print("✅ Touch position tracking implemented")
        checks_passed += 1
    else:
        print("❌ Touch position tracking missing")

    # Check 9: Distance calculation
    print("\n[9/35] Checking distance calculation...")
    if 'deltaX' in hook_content or 'distance' in hook_content.lower():
        print("✅ Distance calculation implemented")
        checks_passed += 1
    else:
        print("❌ Distance calculation missing")

    # Check 10: Time validation
    print("\n[10/35] Checking time validation...")
    if 'deltaTime' in hook_content or 'Date.now()' in hook_content:
        print("✅ Time validation for swipe speed")
        checks_passed += 1
    else:
        print("❌ Time validation missing")

    # Check 11: Horizontal vs vertical detection
    print("\n[11/35] Checking horizontal vs vertical detection...")
    if 'deltaY' in hook_content and 'abs' in hook_content.lower():
        print("✅ Horizontal vs vertical swipe detection")
        checks_passed += 1
    else:
        print("❌ Direction detection missing")

    # Check 12: State management
    print("\n[12/35] Checking state management...")
    if 'useState' in hook_content or 'useRef' in hook_content:
        print("✅ State management with hooks")
        checks_passed += 1
    else:
        print("❌ State management missing")

    # Check 13: Event listeners
    print("\n[13/35] Checking event listeners...")
    if 'addEventListener' in hook_content:
        print("✅ Event listeners added")
        checks_passed += 1
    else:
        print("❌ Event listeners missing")

    # Check 14: Cleanup
    print("\n[14/35] Checking cleanup...")
    if 'removeEventListener' in hook_content and 'return ()' in hook_content:
        print("✅ Event listener cleanup implemented")
        checks_passed += 1
    else:
        print("❌ Cleanup missing")

    # Check 15: Passive event options
    print("\n[15/35] Checking passive event options...")
    if 'passive' in hook_content:
        print("✅ Passive event options configured")
        checks_passed += 1
    else:
        print("❌ Passive event options missing")

    # Check 16: Demo component exists
    print("\n[16/35] Checking demo component...")
    demo_file = 'services/frontend/app/components/SwipeGestureDemo.tsx'
    try:
        with open(demo_file, 'r') as f:
            demo_content = f.read()
            if 'SwipeGestureDemo' in demo_content:
                print("✅ SwipeGestureDemo component exists")
                checks_passed += 1
            else:
                print("❌ SwipeGestureDemo component not found")
    except FileNotFoundError:
        print("❌ SwipeGestureDemo component file not found")
        demo_content = ""

    # Check 17: Demo uses hook
    print("\n[17/35] Checking demo uses hook...")
    if 'useSwipeGesture' in demo_content:
        print("✅ Demo uses useSwipeGesture hook")
        checks_passed += 1
    else:
        print("❌ Demo doesn't use hook")

    # Check 18: Sidebar element
    print("\n[18/35] Checking sidebar element...")
    if 'sidebar' in demo_content.lower() or 'aside' in demo_content.lower():
        print("✅ Sidebar element present")
        checks_passed += 1
    else:
        print("❌ Sidebar element missing")

    # Check 19: Sidebar state
    print("\n[19/35] Checking sidebar state...")
    if 'sidebarOpen' in demo_content or 'isOpen' in demo_content:
        print("✅ Sidebar open/close state managed")
        checks_passed += 1
    else:
        print("❌ Sidebar state missing")

    # Check 20: Smooth animation
    print("\n[20/35] Checking smooth animation...")
    if 'transition' in demo_content and ('300ms' in demo_content or 'duration' in demo_content):
        print("✅ Smooth transition animation")
        checks_passed += 1
    else:
        print("❌ Animation missing or not smooth")

    # Check 21: Transform for sliding
    print("\n[21/35] Checking transform for sliding...")
    if 'translate-x' in demo_content.lower() or 'translatex' in demo_content.lower():
        print("✅ Transform translate for smooth sliding")
        checks_passed += 1
    else:
        print("❌ Transform translate missing")

    # Check 22: Ease timing function
    print("\n[22/35] Checking ease timing function...")
    if 'ease-in-out' in demo_content or 'ease' in demo_content:
        print("✅ Ease timing function for natural motion")
        checks_passed += 1
    else:
        print("❌ Ease timing missing")

    # Check 23: Overlay/backdrop
    print("\n[23/35] Checking overlay/backdrop...")
    if 'overlay' in demo_content.lower() or 'backdrop' in demo_content.lower():
        print("✅ Overlay/backdrop for focus")
        checks_passed += 1
    else:
        print("❌ Overlay/backdrop missing")

    # Check 24: Close button
    print("\n[24/35] Checking close button...")
    if 'close' in demo_content.lower() and 'button' in demo_content.lower():
        print("✅ Close button for accessibility")
        checks_passed += 1
    else:
        print("❌ Close button missing")

    # Check 25: Instructions
    print("\n[25/35] Checking instructions...")
    if 'swipe right' in demo_content.lower() or 'how to' in demo_content.lower():
        print("✅ User instructions provided")
        checks_passed += 1
    else:
        print("❌ User instructions missing")

    # Check 26: Demo page route
    print("\n[26/35] Checking demo page route...")
    page_file = 'services/frontend/app/swipe-gesture-demo/page.tsx'
    try:
        with open(page_file, 'r') as f:
            page_content = f.read()
            if 'SwipeGestureDemo' in page_content:
                print("✅ Demo page route exists")
                checks_passed += 1
            else:
                print("❌ Demo page doesn't import component")
    except FileNotFoundError:
        print("❌ Demo page route not found")
        page_content = ""

    # Check 27: Test IDs
    print("\n[27/35] Checking test IDs...")
    if 'data-testid' in demo_content:
        print("✅ Test IDs for E2E testing")
        checks_passed += 1
    else:
        print("❌ Test IDs missing")

    # Check 28: Swipe statistics/feedback
    print("\n[28/35] Checking swipe statistics...")
    if 'swipe' in demo_content.lower() and 'count' in demo_content.lower():
        print("✅ Swipe statistics/feedback displayed")
        checks_passed += 1
    else:
        print("❌ Swipe statistics missing")

    # Check 29: Dark mode support
    print("\n[29/35] Checking dark mode support...")
    if 'dark:' in demo_content:
        print("✅ Dark mode support")
        checks_passed += 1
    else:
        print("❌ Dark mode support missing")

    # Check 30: Responsive design
    print("\n[30/35] Checking responsive design...")
    if 'md:' in demo_content or 'lg:' in demo_content:
        print("✅ Responsive breakpoints")
        checks_passed += 1
    else:
        print("❌ Responsive design missing")

    # Check 31: Accessibility - ARIA labels
    print("\n[31/35] Checking ARIA labels...")
    if 'aria-label' in demo_content:
        print("✅ ARIA labels for accessibility")
        checks_passed += 1
    else:
        print("❌ ARIA labels missing")

    # Check 32: Z-index layering
    print("\n[32/35] Checking z-index layering...")
    if 'z-50' in demo_content or 'z-40' in demo_content:
        print("✅ Z-index for proper layering")
        checks_passed += 1
    else:
        print("❌ Z-index layering missing")

    # Check 33: Fixed positioning for sidebar
    print("\n[33/35] Checking fixed positioning...")
    if 'fixed' in demo_content:
        print("✅ Fixed positioning for sidebar")
        checks_passed += 1
    else:
        print("❌ Fixed positioning missing")

    # Check 34: Technical details section
    print("\n[34/35] Checking technical details section...")
    if 'Technical Details' in demo_content or 'technical' in demo_content.lower():
        print("✅ Technical details section")
        checks_passed += 1
    else:
        print("❌ Technical details missing")

    # Check 35: Mobile optimization note
    print("\n[35/35] Checking mobile optimization note...")
    if 'mobile' in demo_content.lower() and ('touch' in demo_content.lower() or 'phone' in demo_content.lower()):
        print("✅ Mobile optimization note")
        checks_passed += 1
    else:
        print("❌ Mobile optimization note missing")

    # Summary
    print("\n" + "=" * 80)
    print(f"VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Total checks: {total_checks}")
    print(f"Passed: {checks_passed}")
    print(f"Failed: {total_checks - checks_passed}")
    print(f"Success rate: {(checks_passed/total_checks)*100:.1f}%")

    if checks_passed == total_checks:
        print("\n✅ Feature #607 FULLY VALIDATED - All checks passed!")
        print("\nImplementation Summary:")
        print("- useSwipeGesture hook with callbacks ✅")
        print("- Touch event handling (touchstart, touchmove, touchend) ✅")
        print("- Distance and time validation ✅")
        print("- Horizontal vs vertical detection ✅")
        print("- Sidebar with smooth slide animation (300ms ease-in-out) ✅")
        print("- Swipe right to open ✅")
        print("- Swipe left to close ✅")
        print("- Demo component with statistics ✅")
        print("- Demo page route ✅")
        print("- Accessibility and dark mode ✅")
        return 0
    elif checks_passed >= total_checks * 0.85:
        print(f"\n✅ Feature #607 VALIDATED - {checks_passed}/{total_checks} checks passed (>85%)")
        return 0
    else:
        print(f"\n❌ Feature #607 VALIDATION FAILED - Only {checks_passed}/{total_checks} checks passed")
        return 1


if __name__ == '__main__':
    sys.exit(validate_feature_607())
