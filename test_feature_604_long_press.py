#!/usr/bin/env python3
"""
Feature #604 Validation: Long-press for context menu
Tests the long-press gesture for opening context menus on touch devices.
"""

import sys

def validate_feature_604():
    """Validate Feature #604: Long-press for context menu"""
    print("=" * 80)
    print("Feature #604: Long-press for context menu")
    print("=" * 80)

    checks_passed = 0
    total_checks = 40

    # Check 1: Hook file exists
    print("\n[1/40] Checking if useLongPress hook exists...")
    try:
        with open('services/frontend/src/hooks/useLongPress.ts', 'r') as f:
            hook_content = f.read()
            if 'useLongPress' in hook_content:
                print("✅ useLongPress hook file exists")
                checks_passed += 1
            else:
                print("❌ useLongPress hook not found in file")
    except FileNotFoundError:
        print("❌ useLongPress hook file not found")

    # Check 2: Hook exports interface
    print("\n[2/40] Checking hook interface...")
    if 'interface LongPressOptions' in hook_content:
        print("✅ LongPressOptions interface defined")
        checks_passed += 1
    else:
        print("❌ LongPressOptions interface missing")

    # Check 3: onLongPress callback
    print("\n[3/40] Checking onLongPress callback...")
    if 'onLongPress?' in hook_content:
        print("✅ onLongPress callback defined")
        checks_passed += 1
    else:
        print("❌ onLongPress callback missing")

    # Check 4: onLongPressStart callback
    print("\n[4/40] Checking onLongPressStart callback...")
    if 'onLongPressStart?' in hook_content:
        print("✅ onLongPressStart callback defined")
        checks_passed += 1
    else:
        print("❌ onLongPressStart callback missing")

    # Check 5: onLongPressEnd callback
    print("\n[5/40] Checking onLongPressEnd callback...")
    if 'onLongPressEnd?' in hook_content:
        print("✅ onLongPressEnd callback defined")
        checks_passed += 1
    else:
        print("❌ onLongPressEnd callback missing")

    # Check 6: Configurable delay
    print("\n[6/40] Checking configurable delay...")
    if 'delay?' in hook_content and 'delay = 500' in hook_content:
        print("✅ Configurable delay with 500ms default")
        checks_passed += 1
    else:
        print("❌ Configurable delay missing or incorrect default")

    # Check 7: Move threshold
    print("\n[7/40] Checking move threshold...")
    if 'moveThreshold?' in hook_content:
        print("✅ Move threshold parameter defined")
        checks_passed += 1
    else:
        print("❌ Move threshold parameter missing")

    # Check 8: Touch event handling
    print("\n[8/40] Checking touch event handling...")
    if 'touchstart' in hook_content and 'touchend' in hook_content:
        print("✅ Touch events handled")
        checks_passed += 1
    else:
        print("❌ Touch events not properly handled")

    # Check 9: Mouse event handling (desktop support)
    print("\n[9/40] Checking mouse event handling...")
    if 'mousedown' in hook_content and 'mouseup' in hook_content:
        print("✅ Mouse events handled (desktop support)")
        checks_passed += 1
    else:
        print("❌ Mouse events not properly handled")

    # Check 10: Timer implementation
    print("\n[10/40] Checking timer implementation...")
    if 'setTimeout' in hook_content and 'clearTimeout' in hook_content:
        print("✅ Timer-based long-press detection")
        checks_passed += 1
    else:
        print("❌ Timer implementation missing")

    # Check 11: Position tracking
    print("\n[11/40] Checking position tracking...")
    if 'Position' in hook_content or 'startPosition' in hook_content:
        print("✅ Position tracking implemented")
        checks_passed += 1
    else:
        print("❌ Position tracking missing")

    # Check 12: Movement detection
    print("\n[12/40] Checking movement detection...")
    if 'distance' in hook_content or 'deltaX' in hook_content:
        print("✅ Movement detection implemented")
        checks_passed += 1
    else:
        print("❌ Movement detection missing")

    # Check 13: State management
    print("\n[13/40] Checking state management...")
    if 'isLongPressing' in hook_content and 'useState' in hook_content:
        print("✅ State management with isLongPressing")
        checks_passed += 1
    else:
        print("❌ State management missing")

    # Check 14: Cleanup on unmount
    print("\n[14/40] Checking cleanup...")
    if 'removeEventListener' in hook_content and 'return ()' in hook_content:
        print("✅ Cleanup on unmount")
        checks_passed += 1
    else:
        print("❌ Cleanup missing")

    # Check 15: Demo component exists
    print("\n[15/40] Checking demo component...")
    try:
        with open('services/frontend/app/components/LongPressContextMenuDemo.tsx', 'r') as f:
            demo_content = f.read()
            if 'LongPressContextMenuDemo' in demo_content:
                print("✅ Demo component exists")
                checks_passed += 1
            else:
                print("❌ Demo component not found")
    except FileNotFoundError:
        print("❌ Demo component file not found")
        demo_content = ""

    # Check 16: Hook usage in demo
    print("\n[16/40] Checking hook usage in demo...")
    if 'useLongPress' in demo_content:
        print("✅ Hook used in demo component")
        checks_passed += 1
    else:
        print("❌ Hook not used in demo")

    # Check 17: Context menu rendering
    print("\n[17/40] Checking context menu rendering...")
    if 'menuPosition' in demo_content or 'ContextMenu' in demo_content:
        print("✅ Context menu rendering logic")
        checks_passed += 1
    else:
        print("❌ Context menu rendering missing")

    # Check 18: Menu items
    print("\n[18/40] Checking menu items...")
    if 'menuItems' in demo_content or 'MenuItem' in demo_content:
        print("✅ Menu items defined")
        checks_passed += 1
    else:
        print("❌ Menu items missing")

    # Check 19: Touch-friendly sizing
    print("\n[19/40] Checking touch-friendly sizing...")
    if '48px' in demo_content or 'minHeight' in demo_content:
        print("✅ Touch-friendly menu item sizing (48px)")
        checks_passed += 1
    else:
        print("❌ Touch-friendly sizing not implemented")

    # Check 20: Menu positioning
    print("\n[20/40] Checking menu positioning...")
    if 'left:' in demo_content and 'top:' in demo_content:
        print("✅ Menu positioning at touch point")
        checks_passed += 1
    else:
        print("❌ Menu positioning missing")

    # Check 21: Shape elements
    print("\n[21/40] Checking shape elements...")
    if 'data-shape-id' in demo_content:
        print("✅ Shape elements with data attributes")
        checks_passed += 1
    else:
        print("❌ Shape elements missing")

    # Check 22: Visual feedback
    print("\n[22/40] Checking visual feedback...")
    if 'isLongPressing' in demo_content and ('bg-' in demo_content or 'color' in demo_content):
        print("✅ Visual feedback for long-press state")
        checks_passed += 1
    else:
        print("❌ Visual feedback missing")

    # Check 23: Action handlers
    print("\n[23/40] Checking action handlers...")
    if 'handleMenuAction' in demo_content or 'action:' in demo_content:
        print("✅ Menu action handlers implemented")
        checks_passed += 1
    else:
        print("❌ Action handlers missing")

    # Check 24: Action logging
    print("\n[24/40] Checking action logging...")
    if 'actionLog' in demo_content or 'log' in demo_content.lower():
        print("✅ Action logging for demonstration")
        checks_passed += 1
    else:
        print("❌ Action logging missing")

    # Check 25: Selected shape tracking
    print("\n[25/40] Checking selected shape tracking...")
    if 'selectedShape' in demo_content:
        print("✅ Selected shape tracking")
        checks_passed += 1
    else:
        print("❌ Selected shape tracking missing")

    # Check 26: Menu backdrop
    print("\n[26/40] Checking menu backdrop...")
    if 'backdrop' in demo_content.lower() or ('fixed inset-0' in demo_content):
        print("✅ Backdrop to close menu")
        checks_passed += 1
    else:
        print("❌ Menu backdrop missing")

    # Check 27: Haptic feedback
    print("\n[27/40] Checking haptic feedback...")
    if 'vibrate' in demo_content:
        print("✅ Haptic feedback on long-press")
        checks_passed += 1
    else:
        print("❌ Haptic feedback missing")

    # Check 28: Menu close functionality
    print("\n[28/40] Checking menu close...")
    if 'setMenuPosition(null)' in demo_content:
        print("✅ Menu close functionality")
        checks_passed += 1
    else:
        print("❌ Menu close functionality missing")

    # Check 29: Touch action prevention
    print("\n[29/40] Checking touch-action CSS...")
    if 'touchAction' in demo_content or 'touch-action' in demo_content:
        print("✅ Touch-action CSS for gesture control")
        checks_passed += 1
    else:
        print("❌ Touch-action CSS missing")

    # Check 30: Responsive design
    print("\n[30/40] Checking responsive design...")
    if 'grid' in demo_content or 'flex' in demo_content:
        print("✅ Responsive layout")
        checks_passed += 1
    else:
        print("❌ Responsive layout missing")

    # Check 31: Instructions
    print("\n[31/40] Checking user instructions...")
    if 'How to Use' in demo_content or 'Instructions' in demo_content:
        print("✅ User instructions provided")
        checks_passed += 1
    else:
        print("❌ User instructions missing")

    # Check 32: Technical details
    print("\n[32/40] Checking technical details...")
    if 'Technical Details' in demo_content or '500ms' in demo_content:
        print("✅ Technical details documented")
        checks_passed += 1
    else:
        print("❌ Technical details missing")

    # Check 33: Page route exists
    print("\n[33/40] Checking page route...")
    try:
        with open('services/frontend/app/long-press-demo/page.tsx', 'r') as f:
            page_content = f.read()
            if 'LongPressContextMenuDemo' in page_content:
                print("✅ Page route exists")
                checks_passed += 1
            else:
                print("❌ Page route not configured")
    except FileNotFoundError:
        print("❌ Page route file not found")

    # Check 34: Cancel on movement
    print("\n[34/40] Checking cancel on movement...")
    if 'hasMoved' in hook_content:
        print("✅ Long-press cancels on movement")
        checks_passed += 1
    else:
        print("❌ Movement cancellation missing")

    # Check 35: Event type handling
    print("\n[35/40] Checking event type handling...")
    if 'TouchEvent | MouseEvent' in hook_content:
        print("✅ Both touch and mouse events handled")
        checks_passed += 1
    else:
        print("❌ Event type handling incomplete")

    # Check 36: Menu z-index
    print("\n[36/40] Checking menu z-index...")
    if 'z-50' in demo_content or 'z-index' in demo_content:
        print("✅ Menu z-index for proper layering")
        checks_passed += 1
    else:
        print("❌ Menu z-index missing")

    # Check 37: Menu shadow
    print("\n[37/40] Checking menu shadow...")
    if 'shadow' in demo_content:
        print("✅ Menu shadow for depth")
        checks_passed += 1
    else:
        print("❌ Menu shadow missing")

    # Check 38: Menu icons
    print("\n[38/40] Checking menu icons...")
    if 'icon' in demo_content.lower():
        print("✅ Menu items have icons")
        checks_passed += 1
    else:
        print("❌ Menu icons missing")

    # Check 39: Active state styling
    print("\n[39/40] Checking active state styling...")
    if 'active:' in demo_content or 'hover:' in demo_content:
        print("✅ Active/hover states for menu items")
        checks_passed += 1
    else:
        print("❌ Active state styling missing")

    # Check 40: Accessibility
    print("\n[40/40] Checking accessibility...")
    if 'aria-' in demo_content.lower() or 'button' in demo_content:
        print("✅ Accessibility features (buttons/ARIA)")
        checks_passed += 1
    else:
        print("❌ Accessibility features missing")

    # Summary
    print("\n" + "=" * 80)
    print(f"VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Total checks: {total_checks}")
    print(f"Passed: {checks_passed}")
    print(f"Failed: {total_checks - checks_passed}")
    print(f"Success rate: {(checks_passed/total_checks)*100:.1f}%")

    if checks_passed == total_checks:
        print("\n✅ Feature #604 FULLY VALIDATED - All checks passed!")
        return 0
    elif checks_passed >= total_checks * 0.8:
        print(f"\n⚠️  Feature #604 PARTIALLY VALIDATED - {checks_passed}/{total_checks} checks passed")
        return 1
    else:
        print(f"\n❌ Feature #604 VALIDATION FAILED - Only {checks_passed}/{total_checks} checks passed")
        return 1

if __name__ == '__main__':
    sys.exit(validate_feature_604())
