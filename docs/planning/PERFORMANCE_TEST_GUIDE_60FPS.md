
================================================================================
MANUAL PERFORMANCE TESTING GUIDE - 60 FPS Canvas
================================================================================

To manually verify 60 FPS performance:

1. START THE APPLICATION:
   cd services/frontend
   npm run dev

2. OPEN BROWSER DEVTOOLS:
   - Open Chrome DevTools (F12)
   - Go to "Performance" tab
   - Enable "Show frames per second (FPS) meter"

3. CREATE TEST DIAGRAM:
   - Login to the application
   - Create a new diagram
   - Open the canvas editor

4. ADD 1000+ SHAPES:
   Option A - Manual (Quick Test):
   - Draw 50-100 rectangles
   - Select all (Ctrl+A)
   - Duplicate multiple times (Ctrl+D)
   - Continue until you have 1000+ shapes

   Option B - Programmatic (Accurate Test):
   - Open browser console
   - Run this script:
   
   ```javascript
   const editor = window.tldrawEditor;
   if (editor) {
     for (let i = 0; i < 1000; i++) {
       const x = (i % 50) * 100;
       const y = Math.floor(i / 50) * 100;
       editor.createShape({
         type: 'geo',
         x: x,
         y: y,
         props: {
           w: 80,
           h: 80,
           geo: 'rectangle',
         },
       });
     }
     console.log('Created 1000 rectangles');
   }
   ```

5. TEST PERFORMANCE:
   a) PAN TEST:
      - Hold spacebar + drag to pan
      - Move around the canvas smoothly
      - Check FPS meter stays at 60 FPS
   
   b) ZOOM TEST:
      - Use Ctrl+Scroll to zoom in/out
      - Zoom from 25% to 400%
      - Check FPS meter stays at 60 FPS
   
   c) SELECTION TEST:
      - Select all 1000 shapes (Ctrl+A)
      - Move the selection
      - Check FPS meter stays at 60 FPS
   
   d) DRAWING TEST:
      - Draw new shapes on top of existing ones
      - Check FPS meter stays at 60 FPS

6. VERIFY RESULTS:
   ✓ FPS meter shows 58-60 FPS consistently
   ✓ No stuttering or lag during pan/zoom
   ✓ Smooth selection and movement
   ✓ No frame drops during drawing

7. PERFORMANCE METRICS:
   - Target: 60 FPS (16.67ms per frame)
   - Acceptable: 55-60 FPS (16.67-18.18ms per frame)
   - Poor: < 50 FPS (> 20ms per frame)

================================================================================
EXPECTED RESULTS
================================================================================

TLDraw 2.4.0 includes built-in optimizations:
✓ Hardware-accelerated rendering
✓ Shape culling (only render visible shapes)
✓ Efficient hit testing
✓ Optimized update batching
✓ WebGL acceleration where available

With these optimizations, the canvas should maintain 60 FPS even with 1000+
elements during all operations (pan, zoom, select, draw).

================================================================================
TROUBLESHOOTING
================================================================================

If FPS drops below 55:
1. Check browser GPU acceleration is enabled
2. Close other browser tabs
3. Check system resources (CPU/GPU usage)
4. Try in Chrome (best performance)
5. Disable browser extensions
6. Check for console errors

================================================================================
