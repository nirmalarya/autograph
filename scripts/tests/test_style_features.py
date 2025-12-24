#!/usr/bin/env python3
"""
Test Script for Style Features (Notifications and Video Tutorials)
Tests features #670-673
"""

import re
import sys
from pathlib import Path

def test_notification_system():
    """Test Feature: Notification System (Preferences, Center, Badges)"""
    print("\n" + "="*80)
    print("TESTING: Notification System Components")
    print("="*80)
    
    test_results = {
        'total': 0,
        'passed': 0,
        'failed': 0
    }
    
    # Test 1: NotificationSystem.tsx exists and has required components
    notification_system = Path('services/frontend/app/components/NotificationSystem.tsx')
    test_results['total'] += 1
    if not notification_system.exists():
        print("❌ NotificationSystem.tsx not found")
        test_results['failed'] += 1
        return test_results
    
    content = notification_system.read_text()
    
    # Test 2: Check for NotificationProvider
    test_results['total'] += 1
    if 'export function NotificationProvider' in content:
        print("✅ NotificationProvider component found")
        test_results['passed'] += 1
    else:
        print("❌ NotificationProvider component not found")
        test_results['failed'] += 1
    
    # Test 3: Check for NotificationCenter
    test_results['total'] += 1
    if 'export function NotificationCenter' in content:
        print("✅ NotificationCenter component found")
        test_results['passed'] += 1
    else:
        print("❌ NotificationCenter component not found")
        test_results['failed'] += 1
    
    # Test 4: Check for NotificationBellIcon
    test_results['total'] += 1
    if 'export function NotificationBellIcon' in content:
        print("✅ NotificationBellIcon component found")
        test_results['passed'] += 1
    else:
        print("❌ NotificationBellIcon component not found")
        test_results['failed'] += 1
    
    # Test 5: Check for useNotifications hook
    test_results['total'] += 1
    if 'export function useNotifications' in content:
        print("✅ useNotifications hook found")
        test_results['passed'] += 1
    else:
        print("❌ useNotifications hook not found")
        test_results['failed'] += 1
    
    # Test 6: Check for notification types
    test_results['total'] += 1
    notification_types = ['comment', 'mention', 'share', 'collaboration', 'system', 'export', 'version']
    has_all_types = all(t in content for t in notification_types)
    if has_all_types:
        print(f"✅ All 7 notification types found: {', '.join(notification_types)}")
        test_results['passed'] += 1
    else:
        print("❌ Missing some notification types")
        test_results['failed'] += 1
    
    # Test 7: Check for preferences
    test_results['total'] += 1
    if 'NotificationPreferences' in content and 'updatePreferences' in content:
        print("✅ Notification preferences system found")
        test_results['passed'] += 1
    else:
        print("❌ Notification preferences system not found")
        test_results['failed'] += 1
    
    # Test 8: Check for unread count
    test_results['total'] += 1
    if 'unreadCount' in content:
        print("✅ Unread count badge support found")
        test_results['passed'] += 1
    else:
        print("❌ Unread count badge support not found")
        test_results['failed'] += 1
    
    # Test 9: Check for localStorage persistence
    test_results['total'] += 1
    if 'localStorage' in content and 'autograph_notifications' in content:
        print("✅ localStorage persistence found")
        test_results['passed'] += 1
    else:
        print("❌ localStorage persistence not found")
        test_results['failed'] += 1
    
    # Test 10: Check for read/unread status
    test_results['total'] += 1
    if 'markAsRead' in content and 'markAllAsRead' in content:
        print("✅ Read/unread status management found")
        test_results['passed'] += 1
    else:
        print("❌ Read/unread status management not found")
        test_results['failed'] += 1
    
    # Test 11: Check for notification deletion
    test_results['total'] += 1
    if 'deleteNotification' in content and 'clearAll' in content:
        print("✅ Notification deletion found")
        test_results['passed'] += 1
    else:
        print("❌ Notification deletion not found")
        test_results['failed'] += 1
    
    # Test 12: Check for dark mode support
    test_results['total'] += 1
    dark_mode_count = content.count('dark:')
    if dark_mode_count >= 20:
        print(f"✅ Dark mode support found ({dark_mode_count} dark: classes)")
        test_results['passed'] += 1
    else:
        print(f"❌ Insufficient dark mode support ({dark_mode_count} dark: classes)")
        test_results['failed'] += 1
    
    # Test 13: Check for accessibility
    test_results['total'] += 1
    if 'aria-label' in content and 'role="dialog"' in content:
        print("✅ Accessibility attributes found")
        test_results['passed'] += 1
    else:
        print("❌ Missing accessibility attributes")
        test_results['failed'] += 1
    
    return test_results


def test_notification_settings_page():
    """Test Feature: Notification Settings Page"""
    print("\n" + "="*80)
    print("TESTING: Notification Settings Page")
    print("="*80)
    
    test_results = {
        'total': 0,
        'passed': 0,
        'failed': 0
    }
    
    # Test 1: Settings page exists
    settings_page = Path('services/frontend/app/settings/notifications/page.tsx')
    test_results['total'] += 1
    if not settings_page.exists():
        print("❌ Notification settings page not found")
        test_results['failed'] += 1
        return test_results
    
    print("✅ Notification settings page found")
    test_results['passed'] += 1
    
    content = settings_page.read_text()
    
    # Test 2: Check for useNotifications hook usage
    test_results['total'] += 1
    if 'useNotifications' in content:
        print("✅ Uses useNotifications hook")
        test_results['passed'] += 1
    else:
        print("❌ Missing useNotifications hook")
        test_results['failed'] += 1
    
    # Test 3: Check for enable/disable toggles
    test_results['total'] += 1
    if 'toggle' in content.lower() or 'checkbox' in content:
        print("✅ Toggle switches found")
        test_results['passed'] += 1
    else:
        print("❌ Toggle switches not found")
        test_results['failed'] += 1
    
    # Test 4: Check for test notification feature
    test_results['total'] += 1
    if 'handleTestNotification' in content or 'test notification' in content.lower():
        print("✅ Test notification feature found")
        test_results['passed'] += 1
    else:
        print("❌ Test notification feature not found")
        test_results['failed'] += 1
    
    # Test 5: Check for enable all/disable all
    test_results['total'] += 1
    if 'handleEnableAll' in content and 'handleDisableAll' in content:
        print("✅ Enable all/disable all buttons found")
        test_results['passed'] += 1
    else:
        print("❌ Enable all/disable all buttons not found")
        test_results['failed'] += 1
    
    return test_results


def test_layout_integration():
    """Test Feature: Layout Integration"""
    print("\n" + "="*80)
    print("TESTING: Layout Integration")
    print("="*80)
    
    test_results = {
        'total': 0,
        'passed': 0,
        'failed': 0
    }
    
    # Test 1: Check layout.tsx for NotificationProvider
    layout = Path('services/frontend/app/layout.tsx')
    test_results['total'] += 1
    if not layout.exists():
        print("❌ layout.tsx not found")
        test_results['failed'] += 1
        return test_results
    
    content = layout.read_text()
    
    # Test 2: NotificationProvider import
    test_results['total'] += 1
    if 'NotificationProvider' in content and 'NotificationCenter' in content:
        print("✅ NotificationProvider and NotificationCenter imported")
        test_results['passed'] += 1
    else:
        print("❌ Missing NotificationProvider or NotificationCenter import")
        test_results['failed'] += 1
    
    # Test 3: NotificationProvider wrapping
    test_results['total'] += 1
    if '<NotificationProvider>' in content:
        print("✅ NotificationProvider wraps app")
        test_results['passed'] += 1
    else:
        print("❌ NotificationProvider not wrapping app")
        test_results['failed'] += 1
    
    # Test 4: NotificationCenter rendered
    test_results['total'] += 1
    if '<NotificationCenter' in content:
        print("✅ NotificationCenter rendered in layout")
        test_results['passed'] += 1
    else:
        print("❌ NotificationCenter not rendered")
        test_results['failed'] += 1
    
    return test_results


def test_dashboard_integration():
    """Test Feature: Dashboard Bell Icon"""
    print("\n" + "="*80)
    print("TESTING: Dashboard Bell Icon Integration")
    print("="*80)
    
    test_results = {
        'total': 0,
        'passed': 0,
        'failed': 0
    }
    
    # Test 1: Check dashboard for NotificationBellIcon
    dashboard = Path('services/frontend/app/dashboard/page.tsx')
    test_results['total'] += 1
    if not dashboard.exists():
        print("❌ dashboard/page.tsx not found")
        test_results['failed'] += 1
        return test_results
    
    content = dashboard.read_text()
    
    # Test 2: NotificationBellIcon import
    test_results['total'] += 1
    if 'NotificationBellIcon' in content:
        print("✅ NotificationBellIcon imported")
        test_results['passed'] += 1
    else:
        print("❌ NotificationBellIcon not imported")
        test_results['failed'] += 1
    
    # Test 3: NotificationBellIcon rendered
    test_results['total'] += 1
    if '<NotificationBellIcon' in content:
        print("✅ NotificationBellIcon rendered in header")
        test_results['passed'] += 1
    else:
        print("❌ NotificationBellIcon not rendered")
        test_results['failed'] += 1
    
    return test_results


def test_video_tutorials():
    """Test Feature: Video Tutorials"""
    print("\n" + "="*80)
    print("TESTING: Video Tutorials Page")
    print("="*80)
    
    test_results = {
        'total': 0,
        'passed': 0,
        'failed': 0
    }
    
    # Test 1: Video tutorials page exists
    videos_page = Path('services/frontend/app/help/videos/page.tsx')
    test_results['total'] += 1
    if not videos_page.exists():
        print("❌ Video tutorials page not found")
        test_results['failed'] += 1
        return test_results
    
    print("✅ Video tutorials page found")
    test_results['passed'] += 1
    
    content = videos_page.read_text()
    
    # Test 2: Check for VIDEO_TUTORIALS array
    test_results['total'] += 1
    if 'VIDEO_TUTORIALS' in content and 'VideoTutorial' in content:
        print("✅ VIDEO_TUTORIALS data structure found")
        test_results['passed'] += 1
    else:
        print("❌ VIDEO_TUTORIALS data structure not found")
        test_results['failed'] += 1
    
    # Test 3: Count video tutorials
    test_results['total'] += 1
    video_count = content.count('id:')
    if video_count >= 15:
        print(f"✅ Found {video_count} video tutorials")
        test_results['passed'] += 1
    else:
        print(f"❌ Only found {video_count} video tutorials (expected 15+)")
        test_results['failed'] += 1
    
    # Test 4: Check for categories
    test_results['total'] += 1
    categories = ['getting-started', 'canvas', 'ai', 'mermaid', 'collaboration', 'export']
    has_categories = all(cat in content for cat in categories)
    if has_categories:
        print(f"✅ All {len(categories)} categories found")
        test_results['passed'] += 1
    else:
        print("❌ Missing some categories")
        test_results['failed'] += 1
    
    # Test 5: Check for search functionality
    test_results['total'] += 1
    if 'searchQuery' in content and 'Search' in content:
        print("✅ Search functionality found")
        test_results['passed'] += 1
    else:
        print("❌ Search functionality not found")
        test_results['failed'] += 1
    
    # Test 6: Check for video player
    test_results['total'] += 1
    if 'iframe' in content and 'videoUrl' in content:
        print("✅ Video player (iframe) found")
        test_results['passed'] += 1
    else:
        print("❌ Video player not found")
        test_results['failed'] += 1
    
    # Test 7: Check for difficulty levels
    test_results['total'] += 1
    difficulties = ['beginner', 'intermediate', 'advanced']
    has_difficulties = all(diff in content for diff in difficulties)
    if has_difficulties:
        print("✅ All difficulty levels found")
        test_results['passed'] += 1
    else:
        print("❌ Missing some difficulty levels")
        test_results['failed'] += 1
    
    # Test 8: Check for duration display
    test_results['total'] += 1
    if 'duration' in content and 'Clock' in content:
        print("✅ Duration display found")
        test_results['passed'] += 1
    else:
        print("❌ Duration display not found")
        test_results['failed'] += 1
    
    # Test 9: Check for progress tracking
    test_results['total'] += 1
    if 'completedVideos' in content or 'markCompleted' in content:
        print("✅ Progress tracking found")
        test_results['passed'] += 1
    else:
        print("❌ Progress tracking not found")
        test_results['failed'] += 1
    
    # Test 10: Check for related videos
    test_results['total'] += 1
    if 'relatedVideos' in content:
        print("✅ Related videos feature found")
        test_results['passed'] += 1
    else:
        print("❌ Related videos feature not found")
        test_results['failed'] += 1
    
    return test_results


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("STYLE FEATURES TEST SUITE - Session 141")
    print("Testing 4 features: Notification System + Video Tutorials")
    print("="*80)
    
    all_results = []
    
    # Run all tests
    all_results.append(test_notification_system())
    all_results.append(test_notification_settings_page())
    all_results.append(test_layout_integration())
    all_results.append(test_dashboard_integration())
    all_results.append(test_video_tutorials())
    
    # Calculate totals
    total_tests = sum(r['total'] for r in all_results)
    total_passed = sum(r['passed'] for r in all_results)
    total_failed = sum(r['failed'] for r in all_results)
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total tests:  {total_tests}")
    print(f"Passed:       {total_passed} ✅")
    print(f"Failed:       {total_failed} ❌")
    print(f"Success rate: {(total_passed/total_tests*100):.1f}%")
    print("="*80)
    
    if total_failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total_failed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
