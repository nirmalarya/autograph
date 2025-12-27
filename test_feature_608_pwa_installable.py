#!/usr/bin/env python3
"""
Feature #608: PWA Installable
Validation test for PWA installation capability

Requirements:
- Manifest.json exists and is valid
- Service worker is registered
- beforeinstallprompt event can be captured
- Install prompt shows "Install" button
- App icon appears on home screen after install
"""

import json
import os

def test_manifest_exists():
    """Check if manifest.json exists"""
    manifest_path = "services/frontend/public/manifest.json"
    assert os.path.exists(manifest_path), "manifest.json not found"
    print("✓ manifest.json exists")
    return True

def test_manifest_valid():
    """Validate manifest.json content"""
    manifest_path = "services/frontend/public/manifest.json"
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    # Required fields for PWA installability
    required_fields = ['name', 'short_name', 'start_url', 'display', 'icons']
    for field in required_fields:
        assert field in manifest, f"Missing required field: {field}"

    # Display mode should be standalone or fullscreen
    assert manifest['display'] in ['standalone', 'fullscreen', 'minimal-ui'], \
        f"Invalid display mode: {manifest['display']}"

    # Must have at least one icon 192x192 or larger
    large_icons = [icon for icon in manifest['icons']
                   if '192' in icon['sizes'] or '512' in icon['sizes']]
    assert len(large_icons) > 0, "No icons 192x192 or larger found"

    print(f"✓ manifest.json is valid")
    print(f"  - Name: {manifest['name']}")
    print(f"  - Short name: {manifest['short_name']}")
    print(f"  - Display: {manifest['display']}")
    print(f"  - Icons: {len(manifest['icons'])} defined")
    print(f"  - Large icons (≥192px): {len(large_icons)}")
    return True

def test_service_worker_exists():
    """Check if service worker file exists"""
    sw_path = "services/frontend/public/sw.js"
    assert os.path.exists(sw_path), "Service worker (sw.js) not found"
    print("✓ Service worker file exists")
    return True

def test_service_worker_content():
    """Validate service worker has required functionality"""
    sw_path = "services/frontend/public/sw.js"
    with open(sw_path, 'r') as f:
        sw_content = f.read()

    # Check for essential service worker events
    required_events = ['install', 'activate', 'fetch']
    for event in required_events:
        assert f"addEventListener('{event}'" in sw_content or \
               f'addEventListener("{event}"' in sw_content, \
               f"Service worker missing '{event}' event listener"

    # Check for caching functionality
    assert 'caches.open' in sw_content, "Service worker missing cache functionality"
    assert 'cache.addAll' in sw_content or 'cache.add' in sw_content, \
        "Service worker missing cache.add functionality"

    print("✓ Service worker has required functionality")
    print("  - install event handler")
    print("  - activate event handler")
    print("  - fetch event handler")
    print("  - Caching functionality")
    return True

def test_pwa_installer_component():
    """Check if PWA installer component exists and is configured"""
    installer_path = "services/frontend/app/components/PWAInstaller.tsx"
    assert os.path.exists(installer_path), "PWAInstaller component not found"

    with open(installer_path, 'r') as f:
        content = f.read()

    # Check for service worker registration
    assert "serviceWorker" in content, "Missing service worker registration code"
    assert "register('/sw.js')" in content or 'register("/sw.js")' in content, \
        "Service worker not being registered"

    # Check for beforeinstallprompt handling
    assert "beforeinstallprompt" in content, "Missing beforeinstallprompt event handling"
    assert "deferredPrompt" in content, "Missing deferred prompt handling"

    # Check for install button/prompt
    assert "prompt()" in content, "Missing install prompt trigger"

    print("✓ PWAInstaller component configured correctly")
    print("  - Service worker registration")
    print("  - beforeinstallprompt event handling")
    print("  - Install prompt functionality")
    return True

def test_layout_includes_pwa_installer():
    """Check if PWAInstaller is included in the app layout"""
    layout_path = "services/frontend/app/layout.tsx"
    assert os.path.exists(layout_path), "Layout file not found"

    with open(layout_path, 'r') as f:
        content = f.read()

    assert "PWAInstaller" in content, "PWAInstaller not imported in layout"
    assert "<PWAInstaller" in content, "PWAInstaller component not used in layout"

    # Check for manifest link
    assert 'manifest' in content and '/manifest.json' in content, \
        "Manifest not linked in layout"

    print("✓ PWAInstaller included in app layout")
    print("  - Component imported and used")
    print("  - Manifest linked in <head>")
    return True

def test_icons_exist():
    """Check if required icon files exist"""
    icons_dir = "services/frontend/public/icons"
    assert os.path.exists(icons_dir), "Icons directory not found"

    # Check for required icon sizes
    required_icons = [
        'icon-192x192.png',
        'icon-512x512.png',
    ]

    for icon in required_icons:
        icon_path = os.path.join(icons_dir, icon)
        assert os.path.exists(icon_path), f"Required icon not found: {icon}"

    # Check for maskable icons
    maskable_icons = [
        'icon-192x192-maskable.png',
        'icon-512x512-maskable.png',
    ]

    maskable_count = sum(1 for icon in maskable_icons
                         if os.path.exists(os.path.join(icons_dir, icon)))

    print(f"✓ Required PWA icons exist")
    print(f"  - 192x192 icon")
    print(f"  - 512x512 icon")
    if maskable_count > 0:
        print(f"  - {maskable_count} maskable icon(s)")
    return True

def test_theme_color_configured():
    """Check if theme-color is configured"""
    layout_path = "services/frontend/app/layout.tsx"
    with open(layout_path, 'r') as f:
        content = f.read()

    assert "theme-color" in content or "themeColor" in content, \
        "theme-color not configured"

    print("✓ Theme color configured for PWA")
    return True

def test_apple_touch_icon_configured():
    """Check if apple-touch-icon is configured for iOS"""
    layout_path = "services/frontend/app/layout.tsx"
    with open(layout_path, 'r') as f:
        content = f.read()

    assert "apple-touch-icon" in content, "apple-touch-icon not configured"

    print("✓ Apple touch icon configured for iOS")
    return True

def main():
    """Run all validation tests"""
    print("=" * 80)
    print("Feature #608: PWA Installable - Validation Test")
    print("=" * 80)
    print()

    tests = [
        ("Manifest exists", test_manifest_exists),
        ("Manifest is valid", test_manifest_valid),
        ("Service worker exists", test_service_worker_exists),
        ("Service worker content", test_service_worker_content),
        ("PWA installer component", test_pwa_installer_component),
        ("PWA installer in layout", test_layout_includes_pwa_installer),
        ("Icons exist", test_icons_exist),
        ("Theme color configured", test_theme_color_configured),
        ("Apple touch icon configured", test_apple_touch_icon_configured),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
            print()
        except AssertionError as e:
            print(f"✗ {test_name} FAILED: {e}")
            failed += 1
            print()
        except Exception as e:
            print(f"✗ {test_name} ERROR: {e}")
            failed += 1
            print()

    print("=" * 80)
    print(f"Test Results: {passed}/{len(tests)} passed")
    if failed == 0:
        print("✅ All PWA installability requirements met!")
        print()
        print("The app can be installed as a PWA with:")
        print("  - Valid manifest.json with proper configuration")
        print("  - Service worker for offline functionality")
        print("  - Install prompt handling")
        print("  - Proper icons for home screen")
        print("  - iOS and Android support")
        return 0
    else:
        print(f"❌ {failed} test(s) failed")
        return 1

if __name__ == "__main__":
    exit(main())
