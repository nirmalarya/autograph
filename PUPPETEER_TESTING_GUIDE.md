# Puppeteer MCP Testing Guide

## Prerequisites

To use Puppeteer MCP for AutoGraph testing, you need:

1. **Chrome/Chromium with Remote Debugging Enabled**
2. **Frontend Service Running** (http://localhost:3000)
3. **Backend Services Healthy**

## Step 1: Start Chrome with Remote Debugging

### MacOS
```bash
# Close all Chrome instances first
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug-profile \
  http://localhost:3000 &
```

### Linux
```bash
google-chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug-profile \
  http://localhost:3000 &
```

### Windows
```powershell
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --user-data-dir=C:\temp\chrome-debug-profile ^
  http://localhost:3000
```

## Step 2: Verify Remote Debugging

```bash
curl http://localhost:9222/json/version
```

Should return JSON with browser version info.

## Step 3: Connect Puppeteer MCP

Use the MCP tool:
```
mcp__puppeteer__puppeteer_connect_active_tab(debugPort=9222)
```

## Step 4: Test Basic Navigation

```
1. Navigate to login:
   puppeteer_navigate(url="http://localhost:3000/login")

2. Take screenshot:
   puppeteer_screenshot(name="login-page")

3. Fill email:
   puppeteer_fill(selector='input[type="email"]', value="test@example.com")

4. Fill password:
   puppeteer_fill(selector='input[type="password"]', value="password123")

5. Click login button:
   puppeteer_click(selector='button[type="submit"]')

6. Wait a bit:
   Bash: sleep 2

7. Take screenshot of dashboard:
   puppeteer_screenshot(name="dashboard")
```

## Common Selectors for AutoGraph

### Authentication
- Email input: `input[type="email"]`
- Password input: `input[type="password"]`
- Submit button: `button[type="submit"]`

### Dashboard
- Diagram cards: `.diagram-card, [data-testid="diagram-card"]`
- Create button: `button:has-text("Create"), button:has-text("New")`
- Search input: `input[type="search"], input[placeholder*="Search"]`

### Canvas
- TLDraw container: `.tl-container, .tldraw`
- Canvas theme toggle: `button[title*="Canvas theme"]`
- Tool buttons: `button[data-tool]`

### Common Actions
- Click first diagram: `document.querySelector('.diagram-card')`
- Count diagrams: `document.querySelectorAll('.diagram-card').length`
- Get background color: `window.getComputedStyle(document.querySelector('.tl-container')).backgroundColor`

## Troubleshooting

### Chrome not responding
```bash
# Kill existing Chrome processes
pkill -f chrome
# Start fresh
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 ...
```

### Connection refused
- Check if port 9222 is open: `lsof -i :9222`
- Verify Chrome started with `--remote-debugging-port=9222`

### Element not found
- Use `puppeteer_screenshot()` to see current page
- Use `puppeteer_evaluate(script="document.querySelector('...')")` to test selectors
