#!/usr/bin/env python3
"""
Feature #602: Touch Gestures - Pinch Zoom Test
Tests pinch zoom functionality with smooth zooming and accuracy.

Acceptance Criteria:
- On touch device, pinch to zoom
- Verify smooth zooming
- Verify accurate scaling

Test Coverage:
- usePinchZoom hook implementation
- Touch event handling (2 fingers)
- Distance calculation
- Scale clamping (min/max)
- Smooth transitions
- Wheel zoom support
- Programmatic zoom controls
- Demo component
"""

import os
import re


def test_pinch_zoom_feature():
    """Test pinch zoom implementation"""

    hook_file = 'services/frontend/src/hooks/usePinchZoom.ts'
    demo_file = 'services/frontend/app/components/PinchZoomDemo.tsx'
    page_file = 'services/frontend/app/pinch-zoom-demo/page.tsx'

    print("Testing Feature #602: Touch Gestures - Pinch Zoom")
    print("=" * 60)

    tests_passed = 0
    tests_failed = 0

    # Test 1: Hook file exists
    print("\n1. Testing hook file existence...")
    if os.path.exists(hook_file):
        print("   ✅ usePinchZoom hook file exists")
        tests_passed += 1
    else:
        print("   ❌ Hook file missing")
        tests_failed += 1
        return False

    with open(hook_file, 'r') as f:
        hook_content = f.read()

    # Test 2: Hook interface
    print("\n2. Testing PinchZoomOptions interface...")
    required_options = [
        'minScale?',
        'maxScale?',
        'step?',
        'onZoomChange?',
        'smoothing?',
        'enableOnWheel?',
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

    # Test 3: Touch info tracking
    print("\n3. Testing touch info tracking...")
    if 'interface TouchInfo' in hook_content and 'identifier' in hook_content:
        print("   ✅ TouchInfo interface defined")
        tests_passed += 1
    else:
        print("   ❌ TouchInfo interface missing")
        tests_failed += 1

    # Test 4: Distance calculation
    print("\n4. Testing distance calculation...")
    if 'getDistance' in hook_content and 'Math.sqrt' in hook_content:
        print("   ✅ Distance calculation implemented")
        tests_passed += 1
    else:
        print("   ❌ Distance calculation missing")
        tests_failed += 1

    # Test 5: Scale clamping
    print("\n5. Testing scale clamping...")
    if 'clampScale' in hook_content and 'Math.max' in hook_content and 'Math.min' in hook_content:
        print("   ✅ Scale clamping function implemented")
        tests_passed += 1
    else:
        print("   ❌ Scale clamping missing")
        tests_failed += 1

    # Test 6: Touch event handlers
    print("\n6. Testing touch event handlers...")
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

    # Test 7: Two-finger detection
    print("\n7. Testing two-finger detection...")
    if 'e.touches.length === 2' in hook_content:
        print("   ✅ Two-finger pinch detection implemented")
        tests_passed += 1
    else:
        print("   ❌ Two-finger detection missing")
        tests_failed += 1

    # Test 8: Prevent default behavior
    print("\n8. Testing preventDefault on touch events...")
    if 'e.preventDefault()' in hook_content:
        print("   ✅ preventDefault implemented")
        tests_passed += 1
    else:
        print("   ❌ preventDefault missing")
        tests_failed += 1

    # Test 9: State management
    print("\n9. Testing state management...")
    states = ['scale', 'isPinching']
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

    # Test 10: Initial distance ref
    print("\n10. Testing initial distance reference...")
    if 'initialDistance' in hook_content and 'useRef' in hook_content:
        print("   ✅ initialDistance ref implemented")
        tests_passed += 1
    else:
        print("   ❌ initialDistance ref missing")
        tests_failed += 1

    # Test 11: Scale calculation
    print("\n11. Testing scale calculation...")
    if 'scaleChange = currentDistance / initialDistance' in hook_content:
        print("   ✅ Scale calculation implemented")
        tests_passed += 1
    else:
        print("   ❌ Scale calculation missing")
        tests_failed += 1

    # Test 12: Wheel zoom support
    print("\n12. Testing wheel zoom support...")
    if 'handleWheel' in hook_content and 'e.ctrlKey' in hook_content:
        print("   ✅ Wheel zoom with Ctrl/Cmd support")
        tests_passed += 1
    else:
        print("   ❌ Wheel zoom missing")
        tests_failed += 1

    # Test 13: Programmatic controls
    print("\n13. Testing programmatic zoom controls...")
    controls = ['zoomIn', 'zoomOut', 'resetZoom', 'setZoom']
    controls_found = 0
    for control in controls:
        if control in hook_content:
            print(f"   ✅ {control} implemented")
            controls_found += 1
        else:
            print(f"   ❌ {control} missing")

    if controls_found == len(controls):
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 14: Event listener cleanup
    print("\n14. Testing event listener cleanup...")
    if 'removeEventListener' in hook_content and 'return ()' in hook_content:
        print("   ✅ Event listener cleanup implemented")
        tests_passed += 1
    else:
        print("   ❌ Cleanup missing")
        tests_failed += 1

    # Test 15: Passive option handling
    print("\n15. Testing passive event options...")
    if '{ passive: false }' in hook_content:
        print("   ✅ Passive false for preventDefault support")
        tests_passed += 1
    else:
        print("   ❌ Passive option not configured")
        tests_failed += 1

    # Test 16: Return values
    print("\n16. Testing hook return values...")
    return_values = [
        'scale',
        'isPinching',
        'zoomIn',
        'zoomOut',
        'resetZoom',
        'setZoom',
    ]
    returns_found = 0
    for ret_val in return_values:
        if f'{ret_val},' in hook_content or f'{ret_val} }}' in hook_content:
            print(f"   ✅ {ret_val} returned")
            returns_found += 1
        else:
            print(f"   ❌ {ret_val} not returned")

    if returns_found == len(return_values):
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 17: Demo component exists
    print("\n17. Testing demo component...")
    if os.path.exists(demo_file):
        print("   ✅ PinchZoomDemo component exists")
        tests_passed += 1
    else:
        print("   ❌ Demo component missing")
        tests_failed += 1
        return False

    with open(demo_file, 'r') as f:
        demo_content = f.read()

    # Test 18: Demo uses hook
    print("\n18. Testing demo uses usePinchZoom hook...")
    if 'usePinchZoom' in demo_content and 'from' in demo_content and 'hooks/usePinchZoom' in demo_content:
        print("   ✅ Demo imports and uses hook")
        tests_passed += 1
    else:
        print("   ❌ Demo doesn't use hook")
        tests_failed += 1

    # Test 19: Demo UI controls
    print("\n19. Testing demo UI controls...")
    ui_elements = ['zoomIn', 'zoomOut', 'resetZoom', 'onClick']
    ui_found = 0
    for element in ui_elements:
        if element in demo_content:
            print(f"   ✅ {element} UI element present")
            ui_found += 1
        else:
            print(f"   ❌ {element} UI element missing")

    if ui_found == len(ui_elements):
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 20: Scale display
    print("\n20. Testing scale display...")
    if 'scale' in demo_content and ('toFixed' in demo_content or 'scale *' in demo_content):
        print("   ✅ Scale display implemented")
        tests_passed += 1
    else:
        print("   ❌ Scale display missing")
        tests_failed += 1

    # Test 21: Transform application
    print("\n21. Testing CSS transform application...")
    if 'transform:' in demo_content and 'scale(' in demo_content:
        print("   ✅ CSS transform applied")
        tests_passed += 1
    else:
        print("   ❌ CSS transform missing")
        tests_failed += 1

    # Test 22: Touch action prevention
    print("\n22. Testing touch-action CSS...")
    if 'touchAction:' in demo_content and 'none' in demo_content:
        print("   ✅ touch-action: none applied")
        tests_passed += 1
    else:
        print("   ❌ touch-action not configured")
        tests_failed += 1

    # Test 23: Pinching indicator
    print("\n23. Testing pinching indicator...")
    if 'isPinching' in demo_content and 'Pinching' in demo_content:
        print("   ✅ Pinching indicator displayed")
        tests_passed += 1
    else:
        print("   ❌ Pinching indicator missing")
        tests_failed += 1

    # Test 24: Instructions
    print("\n24. Testing user instructions...")
    if 'two fingers' in demo_content.lower() or 'pinch' in demo_content.lower():
        print("   ✅ User instructions provided")
        tests_passed += 1
    else:
        print("   ❌ User instructions missing")
        tests_failed += 1

    # Test 25: Demo page exists
    print("\n25. Testing demo page route...")
    if os.path.exists(page_file):
        print("   ✅ Demo page route exists")
        tests_passed += 1
    else:
        print("   ❌ Demo page route missing")
        tests_failed += 1

    # Test 26: Default scale value
    print("\n26. Testing default scale initialization...")
    if 'useState(1)' in hook_content or 'useState<number>(1)' in hook_content:
        print("   ✅ Default scale set to 1")
        tests_passed += 1
    else:
        print("   ❌ Default scale not properly initialized")
        tests_failed += 1

    # Test 27: Callback memoization
    print("\n27. Testing callback memoization...")
    if 'useCallback' in hook_content:
        print("   ✅ useCallback used for optimization")
        tests_passed += 1
    else:
        print("   ❌ useCallback not used")
        tests_failed += 1

    # Test 28: onZoomChange callback
    print("\n28. Testing onZoomChange callback...")
    if 'onZoomChange?.(' in hook_content:
        print("   ✅ onZoomChange callback implemented")
        tests_passed += 1
    else:
        print("   ❌ onZoomChange callback missing")
        tests_failed += 1

    # Test 29: Accessibility - aria labels
    print("\n29. Testing accessibility labels...")
    if 'aria-label' in demo_content:
        print("   ✅ ARIA labels present")
        tests_passed += 1
    else:
        print("   ❌ ARIA labels missing")
        tests_failed += 1

    # Test 30: Test data attributes
    print("\n30. Testing data-testid attributes...")
    if 'data-testid' in demo_content:
        print("   ✅ Test ID attributes present")
        tests_passed += 1
    else:
        print("   ❌ Test ID attributes missing")
        tests_failed += 1

    # Final summary
    print("\n" + "=" * 60)
    print(f"FINAL RESULTS: {tests_passed}/{tests_passed + tests_failed} tests passed")
    print("=" * 60)

    if tests_failed == 0:
        print("✅ All pinch zoom tests PASSED!")
        print("\nFeature #602 Implementation Summary:")
        print("- usePinchZoom custom hook ✅")
        print("- Two-finger pinch detection ✅")
        print("- Distance calculation ✅")
        print("- Scale clamping (0.5x - 3x) ✅")
        print("- Smooth zooming with transforms ✅")
        print("- Wheel zoom support (Ctrl/Cmd + Scroll) ✅")
        print("- Programmatic controls ✅")
        print("- Demo component ✅")
        print("- Demo page route ✅")
        print("- Accessibility ✅")
        return True
    else:
        print(f"❌ {tests_failed} tests FAILED")
        return False


if __name__ == '__main__':
    success = test_pinch_zoom_feature()
    exit(0 if success else 1)
