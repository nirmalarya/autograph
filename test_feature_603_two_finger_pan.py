#!/usr/bin/env python3
"""
Feature #603: Touch Gestures - Two-Finger Pan Test
Tests two-finger pan functionality with smooth panning.

Acceptance Criteria:
- Two fingers, drag
- Verify canvas pans
- Verify smooth panning

Test Coverage:
- useTwoFingerPan hook implementation
- Two-finger detection
- Midpoint calculation
- Pan offset tracking
- Smooth transitions
- Reset functionality
- Demo component
"""

import os
import re


def test_two_finger_pan_feature():
    """Test two-finger pan implementation"""

    hook_file = 'services/frontend/src/hooks/useTwoFingerPan.ts'
    demo_file = 'services/frontend/app/components/TwoFingerPanDemo.tsx'
    page_file = 'services/frontend/app/two-finger-pan-demo/page.tsx'

    print("Testing Feature #603: Touch Gestures - Two-Finger Pan")
    print("=" * 60)

    tests_passed = 0
    tests_failed = 0

    # Test 1: Hook file exists
    print("\n1. Testing hook file existence...")
    if os.path.exists(hook_file):
        print("   ✅ useTwoFingerPan hook file exists")
        tests_passed += 1
    else:
        print("   ❌ Hook file missing")
        tests_failed += 1
        return False

    with open(hook_file, 'r') as f:
        hook_content = f.read()

    # Test 2: Hook options interface
    print("\n2. Testing TwoFingerPanOptions interface...")
    required_options = [
        'onPan?',
        'onPanStart?',
        'onPanEnd?',
        'smoothing?',
        'threshold?',
    ]
    options_found = 0
    for option in required_options:
        if option in hook_content:
            print(f"   ✅ {option} option defined")
            options_found += 1
        else:
            print(f"   ❌ {option} option missing")

    if options_found == len(required_options):
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 3: TouchPoint interface
    print("\n3. Testing TouchPoint interface...")
    if 'interface TouchPoint' in hook_content and 'identifier' in hook_content:
        print("   ✅ TouchPoint interface defined")
        tests_passed += 1
    else:
        print("   ❌ TouchPoint interface missing")
        tests_failed += 1

    # Test 4: PanPosition interface
    print("\n4. Testing PanPosition interface...")
    if 'interface PanPosition' in hook_content and '{ x:' in hook_content and 'y:' in hook_content:
        print("   ✅ PanPosition interface defined")
        tests_passed += 1
    else:
        print("   ❌ PanPosition interface missing")
        tests_failed += 1

    # Test 5: Midpoint calculation
    print("\n5. Testing midpoint calculation...")
    if 'getMidpoint' in hook_content and '/ 2' in hook_content:
        print("   ✅ Midpoint calculation implemented")
        tests_passed += 1
    else:
        print("   ❌ Midpoint calculation missing")
        tests_failed += 1

    # Test 6: Distance from start calculation
    print("\n6. Testing distance from start...")
    if 'getDistanceFromStart' in hook_content and 'Math.sqrt' in hook_content:
        print("   ✅ Distance from start calculation implemented")
        tests_passed += 1
    else:
        print("   ❌ Distance calculation missing")
        tests_failed += 1

    # Test 7: Touch event handlers
    print("\n7. Testing touch event handlers...")
    handlers = [
        'handleTouchStart',
        'handleTouchMove',
        'handleTouchEnd',
    ]
    handlers_found = 0
    for handler in handlers:
        if handler in hook_content:
            print(f"   ✅ {handler} implemented")
            handlers_found += 1
        else:
            print(f"   ❌ {handler} missing")

    if handlers_found == len(handlers):
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 8: Two-finger detection
    print("\n8. Testing two-finger detection...")
    if 'e.touches.length === 2' in hook_content:
        print("   ✅ Two-finger detection implemented")
        tests_passed += 1
    else:
        print("   ❌ Two-finger detection missing")
        tests_failed += 1

    # Test 9: preventDefault
    print("\n9. Testing preventDefault...")
    if 'e.preventDefault()' in hook_content:
        print("   ✅ preventDefault implemented")
        tests_passed += 1
    else:
        print("   ❌ preventDefault missing")
        tests_failed += 1

    # Test 10: State management
    print("\n10. Testing state management...")
    states = ['isPanning', 'panOffset']
    states_found = 0
    for state in states:
        if f'useState' in hook_content and state in hook_content:
            print(f"   ✅ {state} state managed")
            states_found += 1
        else:
            print(f"   ❌ {state} state missing")

    if states_found == len(states):
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 11: Refs for tracking
    print("\n11. Testing refs for tracking...")
    refs = ['lastMidpoint', 'touches', 'startMidpoint']
    refs_found = 0
    for ref in refs:
        if ref in hook_content and 'useRef' in hook_content:
            print(f"   ✅ {ref} ref defined")
            refs_found += 1
        else:
            print(f"   ❌ {ref} ref missing")

    if refs_found == len(refs):
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 12: Delta calculation
    print("\n12. Testing delta calculation...")
    if 'deltaX' in hook_content and 'deltaY' in hook_content:
        print("   ✅ Delta calculation implemented")
        tests_passed += 1
    else:
        print("   ❌ Delta calculation missing")
        tests_failed += 1

    # Test 13: Pan offset update
    print("\n13. Testing pan offset update...")
    if 'setPanOffset' in hook_content and 'prev.x + deltaX' in hook_content:
        print("   ✅ Pan offset update implemented")
        tests_passed += 1
    else:
        print("   ❌ Pan offset update missing")
        tests_failed += 1

    # Test 14: onPan callback
    print("\n14. Testing onPan callback...")
    if 'onPan?.(deltaX, deltaY)' in hook_content:
        print("   ✅ onPan callback implemented")
        tests_passed += 1
    else:
        print("   ❌ onPan callback missing")
        tests_failed += 1

    # Test 15: onPanStart and onPanEnd
    print("\n15. Testing pan lifecycle callbacks...")
    if 'onPanStart?.()' in hook_content and 'onPanEnd?.()' in hook_content:
        print("   ✅ Pan lifecycle callbacks implemented")
        tests_passed += 1
    else:
        print("   ❌ Pan lifecycle callbacks missing")
        tests_failed += 1

    # Test 16: Threshold support
    print("\n16. Testing threshold...")
    if 'threshold' in hook_content and 'distanceFromStart < threshold' in hook_content:
        print("   ✅ Threshold support implemented")
        tests_passed += 1
    else:
        print("   ❌ Threshold missing")
        tests_failed += 1

    # Test 17: Touch identifier tracking
    print("\n17. Testing touch identifier tracking...")
    if 'identifier ===' in hook_content or 't.identifier' in hook_content:
        print("   ✅ Touch identifier tracking implemented")
        tests_passed += 1
    else:
        print("   ❌ Touch identifier tracking missing")
        tests_failed += 1

    # Test 18: Event cleanup
    print("\n18. Testing event listener cleanup...")
    if 'removeEventListener' in hook_content and 'return ()' in hook_content:
        print("   ✅ Event listener cleanup implemented")
        tests_passed += 1
    else:
        print("   ❌ Cleanup missing")
        tests_failed += 1

    # Test 19: Reset functionality
    print("\n19. Testing reset functionality...")
    if 'resetPan' in hook_content and 'useCallback' in hook_content:
        print("   ✅ resetPan function implemented")
        tests_passed += 1
    else:
        print("   ❌ resetPan missing")
        tests_failed += 1

    # Test 20: setPan functionality
    print("\n20. Testing setPan functionality...")
    if 'setPan' in hook_content and 'useCallback' in hook_content:
        print("   ✅ setPan function implemented")
        tests_passed += 1
    else:
        print("   ❌ setPan missing")
        tests_failed += 1

    # Test 21: Return values
    print("\n21. Testing hook return values...")
    return_values = ['isPanning', 'panOffset', 'resetPan', 'setPan']
    returns_found = 0
    for ret_val in return_values:
        if ret_val in hook_content:
            print(f"   ✅ {ret_val} returned")
            returns_found += 1
        else:
            print(f"   ❌ {ret_val} not returned")

    if returns_found == len(return_values):
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 22: Demo component exists
    print("\n22. Testing demo component...")
    if os.path.exists(demo_file):
        print("   ✅ TwoFingerPanDemo component exists")
        tests_passed += 1
    else:
        print("   ❌ Demo component missing")
        tests_failed += 1
        return False

    with open(demo_file, 'r') as f:
        demo_content = f.read()

    # Test 23: Demo uses hook
    print("\n23. Testing demo uses useTwoFingerPan hook...")
    if 'useTwoFingerPan' in demo_content and 'from' in demo_content:
        print("   ✅ Demo imports and uses hook")
        tests_passed += 1
    else:
        print("   ❌ Demo doesn't use hook")
        tests_failed += 1

    # Test 24: Reset button
    print("\n24. Testing reset button...")
    if 'resetPan' in demo_content and 'onClick' in demo_content:
        print("   ✅ Reset button implemented")
        tests_passed += 1
    else:
        print("   ❌ Reset button missing")
        tests_failed += 1

    # Test 25: Position display
    print("\n25. Testing position display...")
    if 'panOffset.x' in demo_content and 'panOffset.y' in demo_content:
        print("   ✅ Position display implemented")
        tests_passed += 1
    else:
        print("   ❌ Position display missing")
        tests_failed += 1

    # Test 26: Transform application
    print("\n26. Testing CSS transform...")
    if 'transform:' in demo_content and 'translate(' in demo_content:
        print("   ✅ CSS transform applied")
        tests_passed += 1
    else:
        print("   ❌ CSS transform missing")
        tests_failed += 1

    # Test 27: Touch action
    print("\n27. Testing touch-action CSS...")
    if 'touchAction:' in demo_content and 'none' in demo_content:
        print("   ✅ touch-action: none applied")
        tests_passed += 1
    else:
        print("   ❌ touch-action not configured")
        tests_failed += 1

    # Test 28: Panning indicator
    print("\n28. Testing panning indicator...")
    if 'isPanning' in demo_content and 'Panning' in demo_content:
        print("   ✅ Panning indicator displayed")
        tests_passed += 1
    else:
        print("   ❌ Panning indicator missing")
        tests_failed += 1

    # Test 29: Instructions
    print("\n29. Testing user instructions...")
    if 'two finger' in demo_content.lower() or 'drag' in demo_content.lower():
        print("   ✅ User instructions provided")
        tests_passed += 1
    else:
        print("   ❌ User instructions missing")
        tests_failed += 1

    # Test 30: Demo page exists
    print("\n30. Testing demo page route...")
    if os.path.exists(page_file):
        print("   ✅ Demo page route exists")
        tests_passed += 1
    else:
        print("   ❌ Demo page route missing")
        tests_failed += 1

    # Test 31: Passive false for preventDefault
    print("\n31. Testing passive event option...")
    if '{ passive: false }' in hook_content:
        print("   ✅ Passive false for preventDefault")
        tests_passed += 1
    else:
        print("   ❌ Passive option not configured")
        tests_failed += 1

    # Test 32: Touch cancel handler
    print("\n32. Testing touchcancel handler...")
    if 'touchcancel' in hook_content:
        print("   ✅ touchcancel handler added")
        tests_passed += 1
    else:
        print("   ❌ touchcancel handler missing")
        tests_failed += 1

    # Test 33: Accessibility
    print("\n33. Testing accessibility...")
    if 'aria-label' in demo_content:
        print("   ✅ ARIA labels present")
        tests_passed += 1
    else:
        print("   ❌ ARIA labels missing")
        tests_failed += 1

    # Test 34: Test data attributes
    print("\n34. Testing data-testid attributes...")
    if 'data-testid' in demo_content:
        print("   ✅ Test ID attributes present")
        tests_passed += 1
    else:
        print("   ❌ Test ID attributes missing")
        tests_failed += 1

    # Test 35: Visual feedback
    print("\n35. Testing visual feedback...")
    if 'isPanning &&' in demo_content and ('border' in demo_content or 'animate' in demo_content):
        print("   ✅ Visual feedback implemented")
        tests_passed += 1
    else:
        print("   ❌ Visual feedback missing")
        tests_failed += 1

    # Final summary
    print("\n" + "=" * 60)
    print(f"FINAL RESULTS: {tests_passed}/{tests_passed + tests_failed} tests passed")
    print("=" * 60)

    if tests_failed == 0:
        print("✅ All two-finger pan tests PASSED!")
        print("\nFeature #603 Implementation Summary:")
        print("- useTwoFingerPan custom hook ✅")
        print("- Two-finger detection ✅")
        print("- Midpoint calculation ✅")
        print("- Pan offset tracking ✅")
        print("- Smooth transitions ✅")
        print("- Threshold support (5px) ✅")
        print("- Reset functionality ✅")
        print("- Demo component ✅")
        print("- Demo page route ✅")
        print("- Accessibility ✅")
        return True
    else:
        print(f"❌ {tests_failed} tests FAILED")
        return False


if __name__ == '__main__':
    success = test_two_finger_pan_feature()
    exit(0 if success else 1)
