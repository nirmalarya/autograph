import { useEffect, useRef, useState, useCallback } from 'react';

interface TwoFingerPanOptions {
  onPan?: (deltaX: number, deltaY: number) => void;
  onPanStart?: () => void;
  onPanEnd?: () => void;
  smoothing?: boolean;
  threshold?: number;
}

interface TouchPoint {
  identifier: number;
  clientX: number;
  clientY: number;
}

interface PanPosition {
  x: number;
  y: number;
}

export function useTwoFingerPan(
  elementRef: React.RefObject<HTMLElement>,
  options: TwoFingerPanOptions = {}
) {
  const {
    onPan,
    onPanStart,
    onPanEnd,
    smoothing = true,
    threshold = 5, // Minimum movement to trigger pan (pixels)
  } = options;

  const [isPanning, setIsPanning] = useState(false);
  const [panOffset, setPanOffset] = useState<PanPosition>({ x: 0, y: 0 });

  const lastMidpoint = useRef<PanPosition | null>(null);
  const touches = useRef<TouchPoint[]>([]);
  const startMidpoint = useRef<PanPosition | null>(null);
  const hasPanned = useRef(false);

  // Calculate midpoint between two touches
  const getMidpoint = (touch1: TouchPoint, touch2: TouchPoint): PanPosition => {
    return {
      x: (touch1.clientX + touch2.clientX) / 2,
      y: (touch1.clientY + touch2.clientY) / 2,
    };
  };

  // Calculate distance from start
  const getDistanceFromStart = (current: PanPosition): number => {
    if (!startMidpoint.current) return 0;
    const dx = current.x - startMidpoint.current.x;
    const dy = current.y - startMidpoint.current.y;
    return Math.sqrt(dx * dx + dy * dy);
  };

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

        // Calculate initial midpoint
        const [touch1, touch2] = touches.current;
        const midpoint = getMidpoint(touch1, touch2);

        lastMidpoint.current = midpoint;
        startMidpoint.current = midpoint;
        hasPanned.current = false;
        setIsPanning(true);
        onPanStart?.();
      }
    };

    // Handle touch move (pan)
    const handleTouchMove = (e: TouchEvent) => {
      if (e.touches.length === 2 && lastMidpoint.current !== null) {
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

        // Calculate new midpoint
        const currentMidpoint = getMidpoint(touch1, touch2);

        // Check if movement exceeds threshold
        const distanceFromStart = getDistanceFromStart(currentMidpoint);
        if (!hasPanned.current && distanceFromStart < threshold) {
          return; // Not enough movement yet
        }

        hasPanned.current = true;

        // Calculate delta
        const deltaX = currentMidpoint.x - lastMidpoint.current.x;
        const deltaY = currentMidpoint.y - lastMidpoint.current.y;

        // Update pan offset
        setPanOffset(prev => ({
          x: prev.x + deltaX,
          y: prev.y + deltaY,
        }));

        // Call onPan callback
        onPan?.(deltaX, deltaY);

        // Update last midpoint
        lastMidpoint.current = currentMidpoint;
      }
    };

    // Handle touch end
    const handleTouchEnd = (e: TouchEvent) => {
      if (e.touches.length < 2) {
        lastMidpoint.current = null;
        touches.current = [];
        startMidpoint.current = null;
        hasPanned.current = false;

        if (isPanning) {
          setIsPanning(false);
          onPanEnd?.();
        }
      }
    };

    // Add event listeners
    element.addEventListener('touchstart', handleTouchStart, { passive: false });
    element.addEventListener('touchmove', handleTouchMove, { passive: false });
    element.addEventListener('touchend', handleTouchEnd, { passive: true });
    element.addEventListener('touchcancel', handleTouchEnd, { passive: true });

    // Cleanup
    return () => {
      element.removeEventListener('touchstart', handleTouchStart);
      element.removeEventListener('touchmove', handleTouchMove);
      element.removeEventListener('touchend', handleTouchEnd);
      element.removeEventListener('touchcancel', handleTouchEnd);
    };
  }, [elementRef, onPan, onPanStart, onPanEnd, isPanning, threshold]);

  // Reset pan to origin
  const resetPan = useCallback(() => {
    setPanOffset({ x: 0, y: 0 });
  }, []);

  // Set pan to specific position
  const setPan = useCallback((x: number, y: number) => {
    setPanOffset({ x, y });
  }, []);

  return {
    isPanning,
    panOffset,
    resetPan,
    setPan,
  };
}
