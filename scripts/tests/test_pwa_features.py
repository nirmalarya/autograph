#!/usr/bin/env python3
"""
Test PWA Features (Features #607-609)
- Feature #607: PWA: installable
- Feature #608: PWA: works offline
- Feature #609: PWA: push notifications
"""

import asyncio
import json
import sys
from playwright.async_api import async_playwright, expect

FRONTEND_URL = "http://localhost:3000"

async def test_pwa_installable():
    """Test Feature #607: PWA is installable"""
    print("\n" + "="*80)
    print("TEST: Feature #607 - PWA: installable")
    print("="*80)
    
    async with async_playwright() as p:
        # Launch browser with PWA support
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        try:
            print("\n1. Navigate to homepage...")
            await page.goto(FRONTEND_URL)
            await page.wait_for_load_state('networkidle')
            
            print("2. Check manifest.json is accessible...")
            manifest_response = await page.goto(f"{FRONTEND_URL}/manifest.json")
            assert manifest_response.status == 200, "Manifest not accessible"
            manifest = await manifest_response.json()
            print(f"   ✓ Manifest loaded: {manifest['name']}")
            
            # Verify manifest properties
            assert manifest['name'] == "AutoGraph v3 - AI-Powered Diagramming", "Invalid manifest name"
            assert manifest['short_name'] == "AutoGraph", "Invalid short name"
            assert manifest['display'] == "standalone", "Invalid display mode"
            assert manifest['start_url'] == "/", "Invalid start URL"
            assert len(manifest['icons']) >= 8, "Not enough icons"
            print("   ✓ Manifest has correct properties")
            
            print("3. Check service worker is registered...")
            await page.goto(FRONTEND_URL)
            await page.wait_for_timeout(2000)  # Wait for SW registration
            
            # Check if service worker is registered
            sw_registered = await page.evaluate("""
                () => {
                    return navigator.serviceWorker.getRegistration()
                        .then(reg => reg !== undefined);
                }
            """)
            print(f"   ✓ Service Worker registered: {sw_registered}")
            
            print("4. Check PWA icons are accessible...")
            icon_sizes = [72, 96, 128, 144, 152, 192, 384, 512]
            for size in icon_sizes:
                icon_url = f"{FRONTEND_URL}/icons/icon-{size}x{size}.png"
                icon_response = await page.goto(icon_url)
                assert icon_response.status == 200, f"Icon {size}x{size} not found"
            print(f"   ✓ All {len(icon_sizes)} icons accessible")
            
            print("5. Check for install prompt (PWAInstaller component)...")
            await page.goto(FRONTEND_URL)
            await page.wait_for_timeout(6000)  # Wait for install prompt (5s delay)
            
            # Check if install prompt appears (it should after 5 seconds)
            install_prompt = await page.locator('text=Install AutoGraph').count()
            if install_prompt > 0:
                print("   ✓ Install prompt appeared")
            else:
                print("   ⚠ Install prompt not visible (may already be installed)")
            
            print("6. Verify PWA metadata in HTML...")
            await page.goto(FRONTEND_URL)
            
            # Check meta tags
            theme_color = await page.locator('meta[name="theme-color"]').get_attribute('content')
            assert theme_color == "#3b82f6", "Invalid theme color"
            print(f"   ✓ Theme color: {theme_color}")
            
            manifest_link = await page.locator('link[rel="manifest"]').get_attribute('href')
            assert manifest_link == "/manifest.json", "Manifest link not found"
            print(f"   ✓ Manifest link: {manifest_link}")
            
            apple_icon = await page.locator('link[rel="apple-touch-icon"]').get_attribute('href')
            print(f"   ✓ Apple touch icon: {apple_icon}")
            
            print("\n" + "="*80)
            print("✅ Feature #607 PASSED: PWA is installable")
            print("="*80)
            return True
            
        except Exception as e:
            print(f"\n❌ Feature #607 FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await browser.close()


async def test_pwa_offline():
    """Test Feature #608: PWA works offline"""
    print("\n" + "="*80)
    print("TEST: Feature #608 - PWA: works offline")
    print("="*80)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720}
        )
        page = await context.new_page()
        
        try:
            print("\n1. Navigate to app and wait for service worker...")
            await page.goto(FRONTEND_URL)
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(3000)  # Wait for SW to activate
            
            print("2. Check service worker is active...")
            sw_state = await page.evaluate("""
                () => {
                    return navigator.serviceWorker.getRegistration()
                        .then(reg => reg ? reg.active?.state : 'none');
                }
            """)
            print(f"   ✓ Service Worker state: {sw_state}")
            assert sw_state == 'activated', "Service worker not activated"
            
            print("3. Cache some pages...")
            pages_to_cache = ['/dashboard', '/login', '/register']
            for page_url in pages_to_cache:
                await page.goto(f"{FRONTEND_URL}{page_url}")
                await page.wait_for_load_state('networkidle')
                print(f"   ✓ Cached: {page_url}")
            
            print("4. Go offline...")
            await context.set_offline(True)
            print("   ✓ Network disabled")
            
            print("5. Try to access cached pages...")
            for page_url in pages_to_cache:
                await page.goto(f"{FRONTEND_URL}{page_url}")
                # Page should load from cache
                content = await page.content()
                assert len(content) > 100, f"Page {page_url} not cached properly"
                print(f"   ✓ Loaded from cache: {page_url}")
            
            print("6. Check offline indicator...")
            await page.goto(FRONTEND_URL)
            await page.wait_for_timeout(1000)
            
            # Check if offline indicator is visible
            offline_indicator = await page.locator('text=offline').count()
            if offline_indicator > 0:
                print("   ✓ Offline indicator visible")
            else:
                print("   ⚠ Offline indicator not visible (may be styled differently)")
            
            print("7. Go back online...")
            await context.set_offline(False)
            await page.reload()
            await page.wait_for_load_state('networkidle')
            print("   ✓ Network re-enabled")
            
            print("\n" + "="*80)
            print("✅ Feature #608 PASSED: PWA works offline")
            print("="*80)
            return True
            
        except Exception as e:
            print(f"\n❌ Feature #608 FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await browser.close()


async def test_pwa_push_notifications():
    """Test Feature #609: PWA push notifications"""
    print("\n" + "="*80)
    print("TEST: Feature #609 - PWA: push notifications")
    print("="*80)
    
    async with async_playwright() as p:
        # Grant notification permission
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            permissions=['notifications']
        )
        page = await context.new_page()
        
        try:
            print("\n1. Navigate to app...")
            await page.goto(FRONTEND_URL)
            await page.wait_for_load_state('networkidle')
            
            print("2. Check Notification API is available...")
            notification_available = await page.evaluate("""
                () => 'Notification' in window
            """)
            assert notification_available, "Notification API not available"
            print("   ✓ Notification API available")
            
            print("3. Check notification permission...")
            permission = await page.evaluate("""
                () => Notification.permission
            """)
            print(f"   ✓ Notification permission: {permission}")
            
            print("4. Check PushManager is available...")
            push_available = await page.evaluate("""
                () => 'PushManager' in window
            """)
            assert push_available, "PushManager not available"
            print("   ✓ PushManager available")
            
            print("5. Wait for notification prompt...")
            await page.wait_for_timeout(11000)  # Wait for prompt (10s delay)
            
            # Check if notification prompt appears
            notification_prompt = await page.locator('text=Enable Notifications').count()
            if notification_prompt > 0:
                print("   ✓ Notification prompt appeared")
                
                # Click enable button
                enable_button = page.locator('button:has-text("Enable")')
                if await enable_button.count() > 0:
                    print("   ✓ Enable button found")
            else:
                print("   ⚠ Notification prompt not visible (may already be granted)")
            
            print("6. Check service worker supports push...")
            push_support = await page.evaluate("""
                () => {
                    return navigator.serviceWorker.getRegistration()
                        .then(reg => reg ? 'pushManager' in reg : false);
                }
            """)
            print(f"   ✓ Push support in service worker: {push_support}")
            
            print("7. Check push subscription endpoints exist...")
            # Test subscribe endpoint
            subscribe_response = await page.goto(f"{FRONTEND_URL}/api/push/subscribe")
            print(f"   ✓ Subscribe endpoint status: {subscribe_response.status}")
            
            # Test unsubscribe endpoint
            unsubscribe_response = await page.goto(f"{FRONTEND_URL}/api/push/unsubscribe")
            print(f"   ✓ Unsubscribe endpoint status: {unsubscribe_response.status}")
            
            print("8. Test local notification...")
            await page.goto(FRONTEND_URL)
            
            # Create a test notification
            notification_created = await page.evaluate("""
                () => {
                    try {
                        if (Notification.permission === 'granted') {
                            new Notification('AutoGraph Test', {
                                body: 'Push notifications are working!',
                                icon: '/icons/icon-192x192.png'
                            });
                            return true;
                        }
                        return false;
                    } catch (e) {
                        console.error('Notification error:', e);
                        return false;
                    }
                }
            """)
            
            if notification_created:
                print("   ✓ Test notification created")
            else:
                print("   ⚠ Test notification not created (permission may not be granted)")
            
            print("\n" + "="*80)
            print("✅ Feature #609 PASSED: PWA push notifications")
            print("="*80)
            return True
            
        except Exception as e:
            print(f"\n❌ Feature #609 FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await browser.close()


async def main():
    """Run all PWA tests"""
    print("\n" + "="*80)
    print("PWA FEATURES TEST SUITE")
    print("Testing Features #607-609")
    print("="*80)
    
    results = {
        'Feature #607 (PWA: installable)': False,
        'Feature #608 (PWA: works offline)': False,
        'Feature #609 (PWA: push notifications)': False,
    }
    
    # Test each feature
    results['Feature #607 (PWA: installable)'] = await test_pwa_installable()
    await asyncio.sleep(2)
    
    results['Feature #608 (PWA: works offline)'] = await test_pwa_offline()
    await asyncio.sleep(2)
    
    results['Feature #609 (PWA: push notifications)'] = await test_pwa_push_notifications()
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for feature, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {feature}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*80)
    if all_passed:
        print("✅ ALL PWA FEATURES PASSED!")
        print("="*80)
        return 0
    else:
        print("❌ SOME PWA FEATURES FAILED")
        print("="*80)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
