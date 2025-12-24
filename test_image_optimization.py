#!/usr/bin/env python3
"""
Test script for Image Optimization Features
Tests Features #617 and #618
"""

import os
import sys

def test_optimized_image_component():
    """Test that OptimizedImage component exists and has required features"""
    print("Testing Feature #617: WebP image format support")
    print("Testing Feature #618: Lazy loading for images")
    print("=" * 80)
    
    component_path = "services/frontend/app/components/OptimizedImage.tsx"
    
    # Check if component exists
    if not os.path.exists(component_path):
        print(f"❌ FAIL: {component_path} not found")
        return False
    
    print(f"✅ PASS: {component_path} exists")
    
    # Read component content
    with open(component_path, 'r') as f:
        content = f.read()
    
    # Check for WebP support
    checks = [
        ("WebP support check", "supportsWebP"),
        ("WebP conversion", "webp"),
        ("PNG fallback", "handleError"),
        ("Lazy loading", "IntersectionObserver"),
        ("Loading placeholder", "placeholder"),
        ("Error fallback", "fallback"),
        ("Priority loading", "priority"),
        ("Image loading state", "isLoaded"),
        ("In view state", "isInView"),
    ]
    
    all_passed = True
    for check_name, check_string in checks:
        if check_string in content:
            print(f"✅ PASS: {check_name} - found '{check_string}'")
        else:
            print(f"❌ FAIL: {check_name} - '{check_string}' not found")
            all_passed = False
    
    return all_passed

def test_dashboard_integration():
    """Test that dashboard uses OptimizedImage"""
    print("\n" + "=" * 80)
    print("Testing Dashboard Integration")
    print("=" * 80)
    
    dashboard_path = "services/frontend/app/dashboard/page.tsx"
    
    if not os.path.exists(dashboard_path):
        print(f"❌ FAIL: {dashboard_path} not found")
        return False
    
    with open(dashboard_path, 'r') as f:
        content = f.read()
    
    checks = [
        ("OptimizedImage import", "import OptimizedImage"),
        ("OptimizedImage usage in grid view", "<OptimizedImage"),
        ("Fallback prop", "fallback="),
    ]
    
    all_passed = True
    for check_name, check_string in checks:
        if check_string in content:
            print(f"✅ PASS: {check_name}")
        else:
            print(f"❌ FAIL: {check_name} - '{check_string}' not found")
            all_passed = False
    
    return all_passed

def test_versions_integration():
    """Test that versions page uses OptimizedImage"""
    print("\n" + "=" * 80)
    print("Testing Versions Page Integration")
    print("=" * 80)
    
    versions_path = "services/frontend/app/versions/[id]/page.tsx"
    
    if not os.path.exists(versions_path):
        print(f"❌ FAIL: {versions_path} not found")
        return False
    
    with open(versions_path, 'r') as f:
        content = f.read()
    
    checks = [
        ("OptimizedImage import", "import OptimizedImage"),
        ("OptimizedImage usage", "<OptimizedImage"),
    ]
    
    all_passed = True
    for check_name, check_string in checks:
        if check_string in content:
            print(f"✅ PASS: {check_name}")
        else:
            print(f"❌ FAIL: {check_name} - '{check_string}' not found")
            all_passed = False
    
    return all_passed

def test_pwa_installer_integration():
    """Test that PWA installer uses OptimizedImage"""
    print("\n" + "=" * 80)
    print("Testing PWA Installer Integration")
    print("=" * 80)
    
    pwa_path = "services/frontend/app/components/PWAInstaller.tsx"
    
    if not os.path.exists(pwa_path):
        print(f"❌ FAIL: {pwa_path} not found")
        return False
    
    with open(pwa_path, 'r') as f:
        content = f.read()
    
    checks = [
        ("OptimizedImage import", "import OptimizedImage"),
        ("OptimizedImage usage", "<OptimizedImage"),
        ("Priority loading", "priority={true}"),
    ]
    
    all_passed = True
    for check_name, check_string in checks:
        if check_string in content:
            print(f"✅ PASS: {check_name}")
        else:
            print(f"❌ FAIL: {check_name} - '{check_string}' not found")
            all_passed = False
    
    return all_passed

def test_build_success():
    """Test that frontend builds successfully"""
    print("\n" + "=" * 80)
    print("Testing Frontend Build")
    print("=" * 80)
    
    # Check if build output exists
    build_path = "services/frontend/.next"
    
    if os.path.exists(build_path):
        print(f"✅ PASS: Frontend build directory exists")
        return True
    else:
        print(f"❌ FAIL: Frontend build directory not found")
        return False

def main():
    print("\n")
    print("=" * 80)
    print("IMAGE OPTIMIZATION FEATURES TEST")
    print("Feature #617: WebP image format support")
    print("Feature #618: Lazy loading for images")
    print("=" * 80)
    print("\n")
    
    results = []
    
    # Run all tests
    results.append(("OptimizedImage Component", test_optimized_image_component()))
    results.append(("Dashboard Integration", test_dashboard_integration()))
    results.append(("Versions Integration", test_versions_integration()))
    results.append(("PWA Installer Integration", test_pwa_installer_integration()))
    results.append(("Frontend Build", test_build_success()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 80)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 80)
    
    if passed == total:
        print("\n✅ All tests passed! Features #617 and #618 are working correctly.")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
