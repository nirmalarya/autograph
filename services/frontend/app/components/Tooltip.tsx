'use client';

import React, { useState, useRef, useEffect } from 'react';

export type TooltipPosition = 'top' | 'bottom' | 'left' | 'right';
export type TooltipSize = 'sm' | 'md' | 'lg';

interface TooltipProps {
  content: React.ReactNode;
  children: React.ReactElement;
  position?: TooltipPosition;
  size?: TooltipSize;
  delay?: number; // Delay in ms before showing tooltip
  disabled?: boolean;
  className?: string;
}

export default function Tooltip({
  content,
  children,
  position = 'top',
  size = 'md',
  delay = 300,
  disabled = false,
  className = '',
}: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [coords, setCoords] = useState({ top: 0, left: 0 });
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const triggerRef = useRef<HTMLElement | null>(null);
  const tooltipRef = useRef<HTMLDivElement | null>(null);

  const showTooltip = () => {
    if (disabled || !content) return;
    
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
      calculatePosition();
    }, delay);
  };

  const hideTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    setIsVisible(false);
  };

  const calculatePosition = () => {
    if (!triggerRef.current || !tooltipRef.current) return;

    const triggerRect = triggerRef.current.getBoundingClientRect();
    const tooltipRect = tooltipRef.current.getBoundingClientRect();
    const gap = 8; // Gap between trigger and tooltip

    let top = 0;
    let left = 0;

    switch (position) {
      case 'top':
        top = triggerRect.top - tooltipRect.height - gap;
        left = triggerRect.left + (triggerRect.width - tooltipRect.width) / 2;
        break;
      case 'bottom':
        top = triggerRect.bottom + gap;
        left = triggerRect.left + (triggerRect.width - tooltipRect.width) / 2;
        break;
      case 'left':
        top = triggerRect.top + (triggerRect.height - tooltipRect.height) / 2;
        left = triggerRect.left - tooltipRect.width - gap;
        break;
      case 'right':
        top = triggerRect.top + (triggerRect.height - tooltipRect.height) / 2;
        left = triggerRect.right + gap;
        break;
    }

    // Keep tooltip within viewport
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    if (left < 0) left = gap;
    if (left + tooltipRect.width > viewportWidth) {
      left = viewportWidth - tooltipRect.width - gap;
    }
    if (top < 0) top = gap;
    if (top + tooltipRect.height > viewportHeight) {
      top = viewportHeight - tooltipRect.height - gap;
    }

    setCoords({ top, left });
  };

  useEffect(() => {
    if (isVisible) {
      calculatePosition();
      // Recalculate on scroll or resize
      window.addEventListener('scroll', calculatePosition, true);
      window.addEventListener('resize', calculatePosition);

      return () => {
        window.removeEventListener('scroll', calculatePosition, true);
        window.removeEventListener('resize', calculatePosition);
      };
    }
  }, [isVisible]);

  // Clone child and add event handlers
  const trigger = React.cloneElement(children, {
    ref: (node: HTMLElement) => {
      triggerRef.current = node;
      // Preserve original ref if exists
      const { ref } = children as any;
      if (typeof ref === 'function') {
        ref(node);
      } else if (ref) {
        ref.current = node;
      }
    },
    onMouseEnter: (e: React.MouseEvent) => {
      showTooltip();
      children.props.onMouseEnter?.(e);
    },
    onMouseLeave: (e: React.MouseEvent) => {
      hideTooltip();
      children.props.onMouseLeave?.(e);
    },
    onFocus: (e: React.FocusEvent) => {
      showTooltip();
      children.props.onFocus?.(e);
    },
    onBlur: (e: React.FocusEvent) => {
      hideTooltip();
      children.props.onBlur?.(e);
    },
    'aria-describedby': isVisible ? 'tooltip' : undefined,
  });

  const sizeClasses = {
    sm: 'text-xs px-2 py-1',
    md: 'text-sm px-3 py-1.5',
    lg: 'text-base px-4 py-2',
  };

  const arrowPositionClasses = {
    top: 'bottom-[-4px] left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-b-transparent',
    bottom: 'top-[-4px] left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-t-transparent',
    left: 'right-[-4px] top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-r-transparent',
    right: 'left-[-4px] top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-l-transparent',
  };

  return (
    <>
      {trigger}
      {isVisible && !disabled && content && (
        <div
          ref={tooltipRef}
          id="tooltip"
          role="tooltip"
          className={`
            fixed z-[9999] pointer-events-none
            bg-gray-900 dark:bg-gray-700 text-white
            rounded-md shadow-lg
            ${sizeClasses[size]}
            ${className}
            fade-in
          `}
          style={{
            top: `${coords.top}px`,
            left: `${coords.left}px`,
          }}
        >
          {content}
          {/* Arrow */}
          <div
            className={`
              absolute w-0 h-0
              border-4 border-gray-900 dark:border-gray-700
              ${arrowPositionClasses[position]}
            `}
          />
        </div>
      )}
    </>
  );
}

// Convenience wrapper for simple text tooltips
interface SimpleTooltipProps extends Omit<TooltipProps, 'content'> {
  text: string;
}

export function SimpleTooltip({ text, ...props }: SimpleTooltipProps) {
  return <Tooltip content={text} {...props} />;
}

// Hook for programmatic tooltip control
export function useTooltip() {
  const [isVisible, setIsVisible] = useState(false);
  const [content, setContent] = useState<React.ReactNode>(null);
  const [position, setPosition] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  const show = (content: React.ReactNode, x: number, y: number) => {
    setContent(content);
    setPosition({ x, y });
    setIsVisible(true);
  };

  const hide = () => {
    setIsVisible(false);
  };

  return { isVisible, content, position, show, hide };
}
