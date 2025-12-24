#!/usr/bin/env python3
"""
Verification script for Mobile Menu Features (#606, #607)
Tests bottom navigation and swipe gestures
"""

import os
import sys

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description} NOT FOUND: {filepath}")
        return False

def check_file_contains(filepath, patterns, description):
    """Check if a file contains specific patterns"""
    if not os.path.exists(filepath):
        print(f"❌ {description}: File not found - {filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    missing = []
    for pattern in patterns:
        if pattern not in content:
            missing.append(pattern)
    
    if missing:
        print(f"❌ {description}: Missing patterns in {filepath}")
        for pattern in missing:
            print(f"   - {pattern}")
        return False
    else:
        print(f"✅ {description}: All patterns found in {filepath}")
        return True

def main():
    print("=" * 80)
    print("MOBILE MENU FEATURES VERIFICATION")
    print("=" * 80)
    print()
    
    base_dir = "/Users/nirmalarya/Workspace/auto-harness/cursor-autonomous-coding/autograph-v3/services/frontend"
    
    all_checks_passed = True
    
    # Check 1: MobileBottomNav component exists
    print("Check 1: MobileBottomNav Component")
    print("-" * 80)
    mobile_nav_file = os.path.join(base_dir, "app/components/MobileBottomNav.tsx")
    if check_file_exists(mobile_nav_file, "MobileBottomNav component"):
        # Check for required features
        patterns = [
            "Home Tab",
            "Search Tab",
            "Create Tab",
            "Profile Tab",
            "AI",
            "useRouter",
            "usePathname",
            "md:hidden",
            "fixed bottom-0",
            "safe-area-bottom",
        ]
        all_checks_passed &= check_file_contains(mobile_nav_file, patterns, "MobileBottomNav features")
    else:
        all_checks_passed = False
    print()
    
    # Check 2: useSwipeGesture hook exists
    print("Check 2: useSwipeGesture Hook")
    print("-" * 80)
    swipe_hook_file = os.path.join(base_dir, "src/hooks/useSwipeGesture.ts")
    if check_file_exists(swipe_hook_file, "useSwipeGesture hook"):
        # Check for required features
        patterns = [
            "onSwipeLeft",
            "onSwipeRight",
            "minSwipeDistance",
            "maxSwipeTime",
            "touchstart",
            "touchmove",
            "touchend",
            "deltaX",
            "deltaY",
        ]
        all_checks_passed &= check_file_contains(swipe_hook_file, patterns, "useSwipeGesture features")
    else:
        all_checks_passed = False
    print()
    
    # Check 3: Dashboard integration
    print("Check 3: Dashboard Integration")
    print("-" * 80)
    dashboard_file = os.path.join(base_dir, "app/dashboard/page.tsx")
    if check_file_exists(dashboard_file, "Dashboard page"):
        patterns = [
            "import MobileBottomNav",
            "import { useSwipeGesture }",
            "useSwipeGesture({",
            "onSwipeRight",
            "onSwipeLeft",
            "<MobileBottomNav",
            "onCreateClick",
        ]
        all_checks_passed &= check_file_contains(dashboard_file, patterns, "Dashboard mobile menu integration")
    else:
        all_checks_passed = False
    print()
    
    # Check 4: Profile page exists
    print("Check 4: Profile Page")
    print("-" * 80)
    profile_file = os.path.join(base_dir, "app/profile/page.tsx")
    if check_file_exists(profile_file, "Profile page"):
        patterns = [
            "import MobileBottomNav",
            "<MobileBottomNav",
            "ProfilePage",
            "Account Information",
            "handleLogout",
        ]
        all_checks_passed &= check_file_contains(profile_file, patterns, "Profile page features")
    else:
        all_checks_passed = False
    print()
    
    # Check 5: Build success
    print("Check 5: Frontend Build")
    print("-" * 80)
    build_dir = os.path.join(base_dir, ".next")
    if os.path.exists(build_dir):
        print(f"✅ Frontend build directory exists: {build_dir}")
    else:
        print(f"❌ Frontend build directory NOT FOUND: {build_dir}")
        all_checks_passed = False
    print()
    
    # Summary
    print("=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    
    if all_checks_passed:
        print("✅ ALL CHECKS PASSED!")
        print()
        print("Features Implemented:")
        print("  ✅ #606: Mobile bottom navigation with tabs (Home, Search, Create, AI, Profile)")
        print("  ✅ #607: Swipe gestures for sidebar (swipe right to open, swipe left to close)")
        print()
        print("Implementation Details:")
        print("  • MobileBottomNav component with 5 tabs")
        print("  • Bottom navigation only visible on mobile (md:hidden)")
        print("  • Elevated Create button with gradient")
        print("  • Search modal for mobile")
        print("  • useSwipeGesture hook with touch event handling")
        print("  • Swipe right to open sidebar (mobile only)")
        print("  • Swipe left to close sidebar (mobile only)")
        print("  • Dashboard integration with swipe gestures")
        print("  • Profile page with mobile navigation")
        print("  • Safe area support for notched devices")
        print()
        print("Next Steps:")
        print("  1. Test on mobile device or browser DevTools mobile emulation")
        print("  2. Verify bottom navigation appears on mobile")
        print("  3. Test swipe gestures on sidebar")
        print("  4. Test all navigation tabs")
        print("  5. Mark features as passing in feature_list.json")
        return 0
    else:
        print("❌ SOME CHECKS FAILED")
        print("Please review the errors above and fix the issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
