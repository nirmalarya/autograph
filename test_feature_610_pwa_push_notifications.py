#!/usr/bin/env python3
"""
Feature #610: PWA Push Notifications
Validation test for PWA push notification functionality

Requirements:
- Push notification permission request
- VAPID keys configured
- Service worker handles push events
- Push subscription management
- Notification display with icon and badge
"""

import os
import re

def test_push_notifications_component():
    """Check if PushNotifications component exists"""
    component_path = "services/frontend/app/components/PushNotifications.tsx"
    assert os.path.exists(component_path), "PushNotifications component not found"

    with open(component_path, 'r') as f:
        content = f.read()

    # Check for notification permission request
    assert "Notification.requestPermission" in content or \
           "requestPermission" in content, \
        "Missing notification permission request"

    # Check for push subscription
    assert "PushManager" in content or "pushManager" in content, \
        "Missing PushManager usage"

    assert "subscribe" in content, "Missing push subscription logic"

    # Check for VAPID key handling
    assert "VAPID" in content or "applicationServerKey" in content, \
        "Missing VAPID key configuration"

    print("✓ PushNotifications component exists and configured")
    print("  - Permission request logic")
    print("  - Push subscription management")
    print("  - VAPID key integration")
    return True

def test_service_worker_push_handler():
    """Verify service worker handles push events"""
    sw_path = "services/frontend/public/sw.js"
    assert os.path.exists(sw_path), "Service worker not found"

    with open(sw_path, 'r') as f:
        sw_content = f.read()

    # Check for push event listener
    assert "addEventListener('push'" in sw_content or \
           'addEventListener("push"' in sw_content, \
        "Service worker missing push event listener"

    # Check for showNotification
    assert "showNotification" in sw_content, \
        "Service worker missing showNotification"

    # Check for notification click handler
    assert "addEventListener('notificationclick'" in sw_content or \
           'addEventListener("notificationclick"' in sw_content, \
        "Service worker missing notificationclick handler"

    print("✓ Service worker handles push events")
    print("  - push event listener")
    print("  - showNotification implementation")
    print("  - notificationclick handler")
    return True

def test_push_notification_properties():
    """Verify push notifications have proper properties"""
    sw_path = "services/frontend/public/sw.js"
    with open(sw_path, 'r') as f:
        sw_content = f.read()

    # Check for notification properties
    notification_props = ['title', 'body', 'icon', 'badge']
    found_props = sum(1 for prop in notification_props if prop in sw_content)

    assert found_props >= 3, \
        f"Service worker missing notification properties (found {found_props}/4)"

    print(f"✓ Push notification properties configured")
    print(f"  - {found_props}/4 standard properties found")
    if 'icon' in sw_content:
        print("  - Icon for notification")
    if 'badge' in sw_content:
        print("  - Badge for notification")
    return True

def test_notification_click_handling():
    """Verify notification clicks are handled properly"""
    sw_path = "services/frontend/public/sw.js"
    with open(sw_path, 'r') as f:
        sw_content = f.read()

    # Check for notification close
    assert "notification.close" in sw_content, \
        "Missing notification.close() call"

    # Check for window/client management
    assert "clients.openWindow" in sw_content or \
           "client.focus" in sw_content, \
        "Missing client window management"

    print("✓ Notification click handling implemented")
    print("  - Notification closes on click")
    print("  - Opens/focuses app window")
    return True

def test_push_subscription_api_integration():
    """Check if push subscription integrates with backend API"""
    component_path = "services/frontend/app/components/PushNotifications.tsx"
    with open(component_path, 'r') as f:
        content = f.read()

    # Check for API calls
    assert "/api/push/subscribe" in content or "api/push" in content, \
        "Missing push subscription API integration"

    # Check for subscribe and unsubscribe endpoints
    has_subscribe = "/api/push/subscribe" in content or "/push/subscribe" in content
    has_unsubscribe = "/api/push/unsubscribe" in content or "/push/unsubscribe" in content

    assert has_subscribe, "Missing subscribe API endpoint"
    # Unsubscribe is optional but good to have

    print("✓ Push subscription API integration")
    print("  - Subscribe endpoint configured")
    if has_unsubscribe:
        print("  - Unsubscribe endpoint configured")
    return True

def test_vapid_key_configuration():
    """Verify VAPID keys are configured"""
    component_path = "services/frontend/app/components/PushNotifications.tsx"
    with open(component_path, 'r') as f:
        content = f.read()

    # Check for VAPID key usage
    assert "VAPID" in content, "Missing VAPID key reference"

    # Check for environment variable or hardcoded key
    has_env_var = "NEXT_PUBLIC_VAPID" in content or "process.env" in content
    has_key = re.search(r'["\'][A-Za-z0-9+/=-]{64,}["\']', content) is not None

    assert has_env_var or has_key, "VAPID key not configured (neither env var nor hardcoded)"

    # Check for base64 conversion function
    assert "urlBase64ToUint8Array" in content or "Uint8Array" in content, \
        "Missing VAPID key conversion function"

    print("✓ VAPID keys configured")
    if has_env_var:
        print("  - Environment variable for VAPID key")
    if has_key:
        print("  - VAPID key present")
    print("  - Base64 conversion implemented")
    return True

def test_push_notifications_in_layout():
    """Check if PushNotifications component is included in layout"""
    layout_path = "services/frontend/app/layout.tsx"
    assert os.path.exists(layout_path), "Layout file not found"

    with open(layout_path, 'r') as f:
        content = f.read()

    assert "PushNotifications" in content, \
        "PushNotifications component not imported in layout"

    assert "<PushNotifications" in content, \
        "PushNotifications component not rendered in layout"

    print("✓ PushNotifications included in app layout")
    return True

def test_notification_permission_ui():
    """Verify notification permission request has good UX"""
    component_path = "services/frontend/app/components/PushNotifications.tsx"
    with open(component_path, 'r') as f:
        content = f.read()

    # Check for permission prompt UI
    assert "showPrompt" in content or "prompt" in content.lower(), \
        "Missing permission prompt state"

    # Check for buttons (Enable/Allow and Dismiss/Cancel)
    button_indicators = ["button", "onClick", "Enable", "Not Now"]
    found_buttons = sum(1 for indicator in button_indicators if indicator in content)

    assert found_buttons >= 3, "Permission UI incomplete (missing buttons)"

    # Check for delay before showing prompt (better UX)
    assert "setTimeout" in content or "delay" in content.lower(), \
        "Missing delayed prompt for better UX"

    print("✓ Notification permission UI implemented")
    print("  - Permission prompt state")
    print("  - Enable and dismiss buttons")
    print("  - Delayed prompt for better UX")
    return True

def test_notification_icons_configured():
    """Verify notification uses proper icons"""
    component_path = "services/frontend/app/components/PushNotifications.tsx"
    sw_path = "services/frontend/public/sw.js"

    # Check component
    with open(component_path, 'r') as f:
        component_content = f.read()

    # Check service worker
    with open(sw_path, 'r') as f:
        sw_content = f.read()

    # Look for icon references
    has_icon_in_component = "/icons/" in component_content
    has_icon_in_sw = "/icons/" in sw_content

    assert has_icon_in_component or has_icon_in_sw, \
        "No icon paths found for notifications"

    # Check for both icon and badge
    has_badge = "badge" in component_content or "badge" in sw_content

    print("✓ Notification icons configured")
    if has_icon_in_component:
        print("  - Icons in component")
    if has_icon_in_sw:
        print("  - Icons in service worker")
    if has_badge:
        print("  - Badge icon configured")
    return True

def test_browser_compatibility_checks():
    """Verify code checks for push notification support"""
    component_path = "services/frontend/app/components/PushNotifications.tsx"
    with open(component_path, 'r') as f:
        content = f.read()

    # Check for feature detection
    assert "'Notification' in window" in content or \
           '"Notification" in window' in content, \
        "Missing Notification API feature detection"

    assert "'serviceWorker' in navigator" in content or \
           '"serviceWorker" in navigator' in content, \
        "Missing Service Worker feature detection"

    assert "'PushManager' in window" in content or \
           '"PushManager" in window' in content, \
        "Missing PushManager feature detection"

    print("✓ Browser compatibility checks implemented")
    print("  - Notification API detection")
    print("  - Service Worker detection")
    print("  - PushManager detection")
    return True

def main():
    """Run all validation tests"""
    print("=" * 80)
    print("Feature #610: PWA Push Notifications - Validation Test")
    print("=" * 80)
    print()

    tests = [
        ("PushNotifications component", test_push_notifications_component),
        ("Service worker push handler", test_service_worker_push_handler),
        ("Notification properties", test_push_notification_properties),
        ("Notification click handling", test_notification_click_handling),
        ("API integration", test_push_subscription_api_integration),
        ("VAPID configuration", test_vapid_key_configuration),
        ("Component in layout", test_push_notifications_in_layout),
        ("Permission UI", test_notification_permission_ui),
        ("Notification icons", test_notification_icons_configured),
        ("Browser compatibility", test_browser_compatibility_checks),
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
        print("✅ All PWA push notification requirements met!")
        print()
        print("Push notifications configured with:")
        print("  - Permission request with good UX")
        print("  - VAPID keys for secure push")
        print("  - Service worker push event handling")
        print("  - Notification display with icons")
        print("  - Click handling to open/focus app")
        print("  - Backend API integration")
        print("  - Browser compatibility checks")
        return 0
    else:
        print(f"❌ {failed} test(s) failed")
        return 1

if __name__ == "__main__":
    exit(main())
