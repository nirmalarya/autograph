#!/bin/bash

# Start Chrome with remote debugging for Puppeteer MCP testing

echo "Starting Chrome with remote debugging on port 9222..."

# Close existing Chrome instances (if any)
osascript -e 'quit app "Google Chrome"' 2>/dev/null || true
sleep 2

# Start Chrome with debugging enabled
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug-profile \
  --no-first-run \
  --no-default-browser-check \
  http://localhost:3000 &

# Wait for Chrome to start
sleep 3

# Verify it's running
if curl -s http://localhost:9222/json/version > /dev/null 2>&1; then
    echo "✅ Chrome debugging active on port 9222"
    curl -s http://localhost:9222/json/version | python3 -c "import json, sys; data=json.load(sys.stdin); print(f'Browser: {data.get(\"Browser\", \"Unknown\")}')"
else
    echo "❌ Chrome debugging not responding"
    echo "Please start Chrome manually with:"
    echo "/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug-profile http://localhost:3000"
fi
