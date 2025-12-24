# PWA Features Manual Testing Guide

## Feature #607: PWA is installable

### Test Steps:
1. Open Chrome/Edge browser
2. Navigate to http://localhost:3000
3. Wait 5-10 seconds for install prompt
4. Look for "Install AutoGraph" prompt in bottom-right corner
5. Click "Install" button
6. Verify app installs and opens in standalone window
7. Check app icon appears on desktop/home screen

### Expected Results:
✅ Manifest.json accessible at /manifest.json
✅ Service worker registered (check DevTools > Application > Service Workers)
✅ Install prompt appears after 5 seconds
✅ App can be installed
✅ App opens in standalone mode (no browser UI)
✅ App icon visible on desktop

### Verification Commands:
```bash
# Check manifest
curl http://localhost:3000/manifest.json | python3 -m json.tool

# Check service worker
curl -I http://localhost:3000/sw.js

# Check icons
ls -lh services/frontend/public/icons/
```

## Feature #608: PWA works offline

### Test Steps:
1. Open app in browser
2. Navigate to a few pages (dashboard, login, etc.)
3. Open DevTools > Network tab
4. Enable "Offline" mode
5. Try to navigate to cached pages
6. Verify pages load from cache
7. Check offline indicator appears
8. Disable offline mode
9. Verify app reconnects

### Expected Results:
✅ Service worker caches pages on first visit
✅ Cached pages load when offline
✅ Offline indicator shows "You're offline" banner
✅ App works without network connection
✅ Changes sync when back online

### Verification in DevTools:
1. Open DevTools > Application
2. Check "Service Workers" - should show active worker
3. Check "Cache Storage" - should show cached resources
4. Network tab > Offline checkbox
5. Try loading pages - should work from cache

## Feature #609: PWA push notifications

### Test Steps:
1. Open app in browser
2. Wait 10 seconds for notification prompt
3. Look for "Enable Notifications" prompt
4. Click "Enable" button
5. Grant notification permission in browser
6. Verify subscription is created
7. Test notification by triggering an event

### Expected Results:
✅ Notification prompt appears after 10 seconds
✅ Browser asks for notification permission
✅ Permission can be granted
✅ Push subscription created
✅ Service worker can receive push events
✅ Notifications appear in system tray

### Verification in DevTools:
1. Open DevTools > Application
2. Check "Service Workers" - should have push event listener
3. Console should show: "[PWA] Service Worker registered"
4. Check browser notification settings

## Quick Verification Script

Run these commands to verify PWA setup:

```bash
# 1. Check manifest is valid
curl http://localhost:3000/manifest.json | python3 -c "import json, sys; data=json.load(sys.stdin); print('✅ Manifest valid' if data.get('name') else '❌ Invalid manifest')"

# 2. Check service worker exists
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/sw.js | grep -q 200 && echo "✅ Service worker accessible" || echo "❌ Service worker not found"

# 3. Check icons exist
ls services/frontend/public/icons/icon-192x192.png > /dev/null 2>&1 && echo "✅ PWA icons exist" || echo "❌ Icons missing"

# 4. Check PWA components exist
grep -q "PWAInstaller" services/frontend/app/layout.tsx && echo "✅ PWAInstaller registered" || echo "❌ PWAInstaller not found"

# 5. Check push notification support
grep -q "PushNotifications" services/frontend/app/layout.tsx && echo "✅ Push notifications registered" || echo "❌ Push notifications not found"
```

## Browser Testing

### Chrome/Edge:
1. Open http://localhost:3000
2. DevTools > Application tab
3. Check "Manifest" section - should show app details
4. Check "Service Workers" - should show registered worker
5. Look for install icon in address bar (⊕ or install icon)
6. Click to install

### Firefox:
1. Open http://localhost:3000
2. DevTools > Application tab
3. Check "Manifest" and "Service Workers"
4. May not show install prompt (Firefox has different PWA support)

### Safari (iOS):
1. Open http://localhost:3000
2. Tap Share button
3. Look for "Add to Home Screen"
4. Tap to install
5. App icon appears on home screen

## Success Criteria

All three features should pass:
- ✅ Feature #607: App is installable (manifest + SW + install prompt)
- ✅ Feature #608: App works offline (cached pages load without network)
- ✅ Feature #609: Push notifications work (permission + subscription + events)
