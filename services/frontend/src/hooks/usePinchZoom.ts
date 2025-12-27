import { useEffect, useRef, useState, useCallback } from 'react';

interface PinchZoomOptions {
  minScale?: number;
  maxScale?: number;
  step?: number;
  onZoomChange?: (scale: number) => void;
  smoothing?: boolean;
  enableOnWheel?: boolean;
}

interface TouchInfo {
  identifier: number;
  clientX: number;
  clientY: number;
}

export function usePinchZoom(
  elementRef: React.RefObject<HTMLElement>,
  options: PinchZoomOptions = {}
) {
  const {
    minScale = 0.5,
    maxScale = 3,
    step = 0.1,
    onZoomChange,
    smoothing = true,
    enableOnWheel = true,
  } = options;

  const [scale, setScale] = useState(1);
  const [isPinching, setIsPinching] = useState(false);
  const initialDistance = useRef<number | null>(null);
  const initialScale = useRef(1);
  const touches = useRef<TouchInfo[]>([]);

  // Calculate distance between two touch points
  const getDistance = (touch1: TouchInfo, touch2: TouchInfo): number => {
    const dx = touch2.clientX - touch1.clientX;
    const dy = touch2.clientY - touch1.clientY;
    return Math.sqrt(dx * dx + dy * dy);
  };

  // Clamp scale within bounds
  const clampScale = (value: number): number => {
    return Math.max(minScale, Math.min(maxScale, value));
  };

  // Update scale with smoothing
  const updateScale = useCallback(
    (newScale: number) => {
      const clampedScale = clampScale(newScale);
      setScale(clampedScale);
      onZoomChange?.(clampedScale);
    },
    [minScale, maxScale, onZoomChange]
  );

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    // Handle touch start
    const handleTouchStart = (e: TouchEvent) => {
      if (e.touches.length === 2) {
        e.preventDefault();

        // Store touch info
        touches.current = Array.from(e.touches).map(touch => ({
          identifier: touch.identifier,
          clientX: touch.clientX,
          clientY: touch.clientY,
        }));

        // Calculate initial distance
        const [touch1, touch2] = touches.current;
        initialDistance.current = getDistance(touch1, touch2);
        initialScale.current = scale;
        setIsPinching(true);
      }
    };

    // Handle touch move (pinch zoom)
    const handleTouchMove = (e: TouchEvent) => {
      if (e.touches.length === 2 && initialDistance.current !== null) {
        e.preventDefault();

        // Get current touches
        const currentTouches = Array.from(e.touches).map(touch => ({
          identifier: touch.identifier,
          clientX: touch.clientX,
          clientY: touch.clientY,
        }));

        // Ensure we're tracking the same two fingers
        const touch1 = currentTouches.find(
          t => t.identifier === touches.current[0]?.identifier
        );
        const touch2 = currentTouches.find(
          t => t.identifier === touches.current[1]?.identifier
        );

        if (!touch1 || !touch2) return;

        // Calculate new distance
        const currentDistance = getDistance(touch1, touch2);

        // Calculate scale change
        const scaleChange = currentDistance / initialDistance.current;
        const newScale = initialScale.current * scaleChange;

        // Update scale
        updateScale(newScale);
      }
    };

    // Handle touch end
    const handleTouchEnd = (e: TouchEvent) => {
      if (e.touches.length < 2) {
        initialDistance.current = null;
        touches.current = [];
        setIsPinching(false);
      }
    };

    // Handle mouse wheel zoom (optional)
    const handleWheel = (e: WheelEvent) => {
      if (!enableOnWheel) return;

      // Check if Ctrl/Cmd is pressed (standard pinch-to-zoom gesture on trackpad)
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault();

        const delta = e.deltaY > 0 ? -step : step;
        const newScale = scale + delta;
        updateScale(newScale);
      }
    };

    // Add event listeners
    element.addEventListener('touchstart', handleTouchStart, { passive: false });
    element.addEventListener('touchmove', handleTouchMove, { passive: false });
    element.addEventListener('touchend', handleTouchEnd, { passive: true });

    if (enableOnWheel) {
      element.addEventListener('wheel', handleWheel, { passive: false });
    }

    // Cleanup
    return () => {
      element.removeEventListener('touchstart', handleTouchStart);
      element.removeEventListener('touchmove', handleTouchMove);
      element.removeEventListener('touchend', handleTouchEnd);
      if (enableOnWheel) {
        element.removeEventListener('wheel', handleWheel);
      }
    };
  }, [elementRef, scale, updateScale, enableOnWheel, step]);

  // Programmatic zoom controls
  const zoomIn = useCallback(() => {
    updateScale(scale + step);
  }, [scale, step, updateScale]);

  const zoomOut = useCallback(() => {
    updateScale(scale - step);
  }, [scale, step, updateScale]);

  const resetZoom = useCallback(() => {
    updateScale(1);
  }, [updateScale]);

  const setZoom = useCallback(
    (newScale: number) => {
      updateScale(newScale);
    },
    [updateScale]
  );

  return {
    scale,
    isPinching,
    zoomIn,
    zoomOut,
    resetZoom,
    setZoom,
  };
}
