'use client';

import { useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';

/**
 * PageTransition Component
 * 
 * Provides smooth fade transitions between page navigations.
 * Prevents content flickering and improves perceived performance.
 * 
 * Features:
 * - Fade in/out transitions
 * - Prevents layout shift
 * - Smooth state changes
 * - No content flash
 */
export default function PageTransition({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [displayChildren, setDisplayChildren] = useState(children);

  useEffect(() => {
    // Start transition
    setIsTransitioning(true);

    // Short delay to allow fade out
    const fadeOutTimer = setTimeout(() => {
      setDisplayChildren(children);
      setIsTransitioning(false);
    }, 150);

    return () => clearTimeout(fadeOutTimer);
  }, [pathname, children]);

  return (
    <div
      className={`page-transition ${isTransitioning ? 'page-transition-out' : 'page-transition-in'}`}
      style={{
        transition: 'opacity 150ms ease-in-out',
        opacity: isTransitioning ? 0 : 1,
      }}
    >
      {displayChildren}
    </div>
  );
}
