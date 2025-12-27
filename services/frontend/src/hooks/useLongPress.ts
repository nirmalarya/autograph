import { useEffect, useRef, useState, useCallback } from 'react';

interface LongPressOptions {
  onLongPress?: (event: TouchEvent | MouseEvent) => void;
  onLongPressStart?: () => void;
  onLongPressEnd?: () => void;
  delay?: number; // Time in ms before long-press is triggered
  moveThreshold?: number; // Maximum movement allowed during long-press (pixels)
}

interface Position {
  x: number;
  y: number;
}

export function useLongPress(options: LongPressOptions) {
  const {
    onLongPress,
    onLongPressStart,
    onLongPressEnd,
    delay = 500, // Default 500ms for long-press
    moveThreshold = 10, // Default 10px movement threshold
  } = options;

  const [isLongPressing, setIsLongPressing] = useState(false);
  const longPressTimer = useRef<NodeJS.Timeout | null>(null);
  const startPosition = useRef<Position | null>(null);
  const currentEvent = useRef<TouchEvent | MouseEvent | null>(null);
  const hasMoved = useRef(false);

  const clearTimer = useCallback(() => {
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
      longPressTimer.current = null;
    }
  }, []);

  const handleStart = useCallback(
    (e: TouchEvent | MouseEvent) => {
      // Store the event for later use
      currentEvent.current = e;

      // Get position
      let x: number, y: number;
      if ('touches' in e) {
        x = e.touches[0].clientX;
        y = e.touches[0].clientY;
      } else {
        x = e.clientX;
        y = e.clientY;
      }

      startPosition.current = { x, y };
      hasMoved.current = false;

      // Clear any existing timer
      clearTimer();

      // Start long-press timer
      longPressTimer.current = setTimeout(() => {
        if (!hasMoved.current && startPosition.current) {
          setIsLongPressing(true);
          onLongPressStart?.();
          onLongPress?.(e);
        }
      }, delay);
    },
    [delay, onLongPress, onLongPressStart, clearTimer]
  );

  const handleMove = useCallback(
    (e: TouchEvent | MouseEvent) => {
      if (!startPosition.current) return;

      // Get current position
      let x: number, y: number;
      if ('touches' in e) {
        x = e.touches[0].clientX;
        y = e.touches[0].clientY;
      } else {
        x = e.clientX;
        y = e.clientY;
      }

      // Calculate distance moved
      const deltaX = x - startPosition.current.x;
      const deltaY = y - startPosition.current.y;
      const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

      // If moved beyond threshold, cancel long-press
      if (distance > moveThreshold) {
        hasMoved.current = true;
        clearTimer();
        if (isLongPressing) {
          setIsLongPressing(false);
          onLongPressEnd?.();
        }
      }
    },
    [moveThreshold, isLongPressing, onLongPressEnd, clearTimer]
  );

  const handleEnd = useCallback(() => {
    clearTimer();
    if (isLongPressing) {
      setIsLongPressing(false);
      onLongPressEnd?.();
    }
    startPosition.current = null;
    currentEvent.current = null;
    hasMoved.current = false;
  }, [isLongPressing, onLongPressEnd, clearTimer]);

  useEffect(() => {
    const handleTouchStart = (e: TouchEvent) => handleStart(e);
    const handleTouchMove = (e: TouchEvent) => handleMove(e);
    const handleTouchEnd = () => handleEnd();
    const handleTouchCancel = () => handleEnd();

    const handleMouseDown = (e: MouseEvent) => handleStart(e);
    const handleMouseMove = (e: MouseEvent) => handleMove(e);
    const handleMouseUp = () => handleEnd();
    const handleMouseLeave = () => handleEnd();

    // Touch events
    document.addEventListener('touchstart', handleTouchStart, { passive: true });
    document.addEventListener('touchmove', handleTouchMove, { passive: true });
    document.addEventListener('touchend', handleTouchEnd, { passive: true });
    document.addEventListener('touchcancel', handleTouchCancel, { passive: true });

    // Mouse events (for desktop testing)
    document.addEventListener('mousedown', handleMouseDown);
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('mouseleave', handleMouseLeave);

    // Cleanup
    return () => {
      clearTimer();
      document.removeEventListener('touchstart', handleTouchStart);
      document.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('touchend', handleTouchEnd);
      document.removeEventListener('touchcancel', handleTouchCancel);
      document.removeEventListener('mousedown', handleMouseDown);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, [handleStart, handleMove, handleEnd, clearTimer]);

  return { isLongPressing };
}
