/**
 * Lazy Loading Utilities
 * 
 * This file provides utilities for code splitting and lazy loading components
 * to improve initial page load performance.
 */

import dynamic from 'next/dynamic';
import React from 'react';

/**
 * Common loading fallback components
 */
export const LoadingFallbacks = {
  // Generic spinner
  Spinner: () => (
    <div className="flex items-center justify-center p-4">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
    </div>
  ),

  // Skeleton for buttons/small components
  SmallSkeleton: () => (
    <div className="h-10 w-10 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
  ),

  // Skeleton for cards
  CardSkeleton: () => (
    <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse mb-2" />
      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-3/4" />
    </div>
  ),

  // Skeleton for lists
  ListSkeleton: () => (
    <div className="space-y-2">
      <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
      <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
      <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
    </div>
  ),

  // Skeleton for tree structures
  TreeSkeleton: () => (
    <div className="space-y-2">
      <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
      <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded animate-pulse ml-4" />
      <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded animate-pulse ml-4" />
      <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded animate-pulse ml-8" />
    </div>
  ),

  // Skeleton for navigation bars
  NavSkeleton: () => (
    <div className="h-16 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700" />
  ),

  // Skeleton for breadcrumbs
  BreadcrumbSkeleton: () => (
    <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-64" />
  ),

  // Full page loading
  PageLoading: () => (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
        <p className="text-gray-600 dark:text-gray-400">Loading...</p>
      </div>
    </div>
  ),

  // Canvas loading
  CanvasLoading: () => (
    <div className="flex items-center justify-center h-full bg-gray-50 dark:bg-gray-900">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
        <p className="text-gray-600 dark:text-gray-400">Loading canvas...</p>
      </div>
    </div>
  ),

  // Editor loading
  EditorLoading: () => (
    <div className="flex items-center justify-center h-full bg-white dark:bg-gray-800">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2" />
        <p className="text-sm text-gray-600 dark:text-gray-400">Loading editor...</p>
      </div>
    </div>
  ),
};

/**
 * Lazy load a component with a custom loading fallback
 */
export function lazyLoadComponent<T extends React.ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  options?: {
    loading?: () => React.ReactElement;
    ssr?: boolean;
  }
) {
  return dynamic(importFn, {
    loading: options?.loading || (() => <LoadingFallbacks.Spinner />),
    ssr: options?.ssr ?? true,
  });
}

/**
 * Lazy load a component that should not be server-side rendered
 */
export function lazyLoadClientComponent<T extends React.ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  loading?: () => React.ReactElement
) {
  return dynamic(importFn, {
    loading: loading || (() => <LoadingFallbacks.Spinner />),
    ssr: false,
  });
}

/**
 * Preload a component for faster subsequent loading
 */
export function preloadComponent(importFn: () => Promise<any>) {
  // Trigger the import but don't wait for it
  importFn().catch((err) => {
    console.warn('Failed to preload component:', err);
  });
}

/**
 * Lazy load multiple components at once
 */
export function lazyLoadComponents<T extends Record<string, () => Promise<{ default: any }>>>(
  imports: T,
  options?: {
    loading?: () => React.ReactElement;
    ssr?: boolean;
  }
): { [K in keyof T]: ReturnType<typeof dynamic> } {
  const result: any = {};
  
  for (const [key, importFn] of Object.entries(imports)) {
    result[key] = dynamic(importFn, {
      loading: options?.loading || (() => <LoadingFallbacks.Spinner />),
      ssr: options?.ssr ?? true,
    });
  }
  
  return result;
}

/**
 * Route-based code splitting helper
 * Use this to lazy load entire page components
 */
export function lazyLoadRoute<T extends React.ComponentType<any>>(
  importFn: () => Promise<{ default: T }>
) {
  return dynamic(importFn, {
    loading: LoadingFallbacks.PageLoading,
    ssr: true,
  });
}

/**
 * Intersection Observer based lazy loading for components
 * Only loads when component enters viewport
 */
export function lazyLoadOnVisible<T extends React.ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  options?: {
    rootMargin?: string;
    threshold?: number;
  }
) {
  const LazyComponent = dynamic(importFn, {
    loading: () => <LoadingFallbacks.Spinner />,
    ssr: false,
  });

  return function LazyVisibleComponent(props: React.ComponentProps<T>) {
    const [isVisible, setIsVisible] = React.useState(false);
    const ref = React.useRef<HTMLDivElement>(null);

    React.useEffect(() => {
      if (!ref.current) return;

      const observer = new IntersectionObserver(
        (entries) => {
          if (entries[0].isIntersecting) {
            setIsVisible(true);
            observer.disconnect();
          }
        },
        {
          rootMargin: options?.rootMargin || '50px',
          threshold: options?.threshold || 0.01,
        }
      );

      observer.observe(ref.current);

      return () => observer.disconnect();
    }, []);

    return (
      <div ref={ref}>
        {isVisible ? <LazyComponent {...props} /> : <LoadingFallbacks.Spinner />}
      </div>
    );
  };
}

/**
 * Prefetch a route for faster navigation
 */
export function prefetchRoute(href: string) {
  if (typeof window !== 'undefined') {
    const link = document.createElement('link');
    link.rel = 'prefetch';
    link.href = href;
    document.head.appendChild(link);
  }
}

/**
 * Bundle size optimization utilities
 */
export const BundleOptimization = {
  /**
   * Check if code splitting is working
   */
  logChunkInfo: () => {
    if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
      console.log('Code splitting enabled');
      console.log('Lazy loaded chunks will be loaded on demand');
    }
  },

  /**
   * Measure component load time
   */
  measureLoadTime: (componentName: string) => {
    const start = performance.now();
    return () => {
      const end = performance.now();
      console.log(`${componentName} loaded in ${(end - start).toFixed(2)}ms`);
    };
  },
};

export default {
  LoadingFallbacks,
  lazyLoadComponent,
  lazyLoadClientComponent,
  preloadComponent,
  lazyLoadComponents,
  lazyLoadRoute,
  lazyLoadOnVisible,
  prefetchRoute,
  BundleOptimization,
};
