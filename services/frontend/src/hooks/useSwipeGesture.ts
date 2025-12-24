import { useEffect, useRef, useState } from 'react';

interface SwipeGestureOptions {
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  minSwipeDistance?: number;
  maxSwipeTime?: number;
}

interface TouchPosition {
  x: number;
  y: number;
  time: number;
}

export function useSwipeGesture(options: SwipeGestureOptions) {
  const {
    onSwipeLeft,
    onSwipeRight,
    minSwipeDistance = 50, // Minimum distance for swipe (pixels)
    maxSwipeTime = 300, // Maximum time for swipe (ms)
  } = options;

  const touchStart = useRef<TouchPosition | null>(null);
  const touchEnd = useRef<TouchPosition | null>(null);
  const [isSwiping, setIsSwiping] = useState(false);

  useEffect(() => {
    const handleTouchStart = (e: TouchEvent) => {
      const touch = e.touches[0];
      touchStart.current = {
        x: touch.clientX,
        y: touch.clientY,
        time: Date.now(),
      };
      touchEnd.current = null;
      setIsSwiping(false);
    };

    const handleTouchMove = (e: TouchEvent) => {
      if (!touchStart.current) return;

      const touch = e.touches[0];
      touchEnd.current = {
        x: touch.clientX,
        y: touch.clientY,
        time: Date.now(),
      };

      // Calculate swipe distance
      const deltaX = touchEnd.current.x - touchStart.current.x;
      const deltaY = Math.abs(touchEnd.current.y - touchStart.current.y);

      // Only consider horizontal swipes (deltaX > deltaY)
      if (Math.abs(deltaX) > minSwipeDistance && Math.abs(deltaX) > deltaY) {
        setIsSwiping(true);
      }
    };

    const handleTouchEnd = (e: TouchEvent) => {
      if (!touchStart.current || !touchEnd.current) {
        touchStart.current = null;
        touchEnd.current = null;
        setIsSwiping(false);
        return;
      }

      const deltaX = touchEnd.current.x - touchStart.current.x;
      const deltaY = Math.abs(touchEnd.current.y - touchStart.current.y);
      const deltaTime = touchEnd.current.time - touchStart.current.time;

      // Check if it's a valid swipe:
      // 1. Horizontal distance > minimum
      // 2. Horizontal distance > vertical distance (more horizontal than vertical)
      // 3. Time < maximum
      const isValidSwipe =
        Math.abs(deltaX) >= minSwipeDistance &&
        Math.abs(deltaX) > deltaY &&
        deltaTime <= maxSwipeTime;

      if (isValidSwipe) {
        if (deltaX > 0) {
          // Swipe right
          onSwipeRight?.();
        } else {
          // Swipe left
          onSwipeLeft?.();
        }
      }

      // Reset
      touchStart.current = null;
      touchEnd.current = null;
      setIsSwiping(false);
    };

    // Add event listeners
    document.addEventListener('touchstart', handleTouchStart, { passive: true });
    document.addEventListener('touchmove', handleTouchMove, { passive: true });
    document.addEventListener('touchend', handleTouchEnd, { passive: true });

    // Cleanup
    return () => {
      document.removeEventListener('touchstart', handleTouchStart);
      document.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('touchend', handleTouchEnd);
    };
  }, [onSwipeLeft, onSwipeRight, minSwipeDistance, maxSwipeTime]);

  return { isSwiping };
}
