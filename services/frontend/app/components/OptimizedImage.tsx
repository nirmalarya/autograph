'use client';

import { useState, useEffect, useRef } from 'react';

/**
 * Optimized Image Component
 * 
 * Features:
 * - WebP format support with PNG/JPEG fallback
 * - Lazy loading (loads when scrolled into view)
 * - Loading placeholder
 * - Error handling with fallback
 * 
 * Implements:
 * - Feature #617: Image optimization with WebP format
 * - Feature #618: Lazy loading for images
 */

interface OptimizedImageProps {
  src: string;
  alt: string;
  className?: string;
  width?: number;
  height?: number;
  priority?: boolean; // If true, load immediately (no lazy loading)
  fallback?: React.ReactNode; // Custom fallback for errors
  placeholder?: React.ReactNode; // Custom loading placeholder
}

export default function OptimizedImage({
  src,
  alt,
  className = '',
  width,
  height,
  priority = false,
  fallback,
  placeholder,
}: OptimizedImageProps) {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isInView, setIsInView] = useState(priority);
  const [hasError, setHasError] = useState(false);
  const [imageSrc, setImageSrc] = useState<string>('');
  const imgRef = useRef<HTMLImageElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Check if browser supports WebP
  const supportsWebP = useRef<boolean | null>(null);

  useEffect(() => {
    // Check WebP support once
    if (supportsWebP.current === null) {
      const checkWebPSupport = () => {
        const canvas = document.createElement('canvas');
        if (canvas.getContext && canvas.getContext('2d')) {
          // Check if WebP is supported
          return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
        }
        return false;
      };
      supportsWebP.current = checkWebPSupport();
    }

    // Convert image URL to WebP if supported and not already WebP
    if (src && supportsWebP.current && !src.endsWith('.webp')) {
      // Try to convert PNG/JPG to WebP by changing extension
      const webpSrc = src.replace(/\.(png|jpg|jpeg)$/i, '.webp');
      setImageSrc(webpSrc);
    } else {
      setImageSrc(src);
    }
  }, [src]);

  // Intersection Observer for lazy loading
  useEffect(() => {
    if (priority || !containerRef.current) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsInView(true);
            observer.disconnect();
          }
        });
      },
      {
        rootMargin: '50px', // Start loading 50px before entering viewport
        threshold: 0.01,
      }
    );

    observer.observe(containerRef.current);

    return () => {
      observer.disconnect();
    };
  }, [priority]);

  const handleLoad = () => {
    setIsLoaded(true);
    setHasError(false);
  };

  const handleError = () => {
    // If WebP fails, try original format
    if (imageSrc.endsWith('.webp') && !src.endsWith('.webp')) {
      setImageSrc(src);
      setHasError(false);
    } else {
      setHasError(true);
      setIsLoaded(true);
    }
  };

  // Default loading placeholder
  const defaultPlaceholder = (
    <div className="w-full h-full bg-gray-200 dark:bg-gray-700 animate-pulse flex items-center justify-center">
      <svg
        className="w-12 h-12 text-gray-400 dark:text-gray-600"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
        />
      </svg>
    </div>
  );

  // Default error fallback
  const defaultFallback = (
    <div className="w-full h-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
      <div className="text-center text-gray-400 dark:text-gray-600">
        <svg
          className="w-12 h-12 mx-auto mb-2"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <p className="text-sm">Image unavailable</p>
      </div>
    </div>
  );

  return (
    <div
      ref={containerRef}
      className={`relative overflow-hidden ${className}`}
      style={{ width: width ? `${width}px` : undefined, height: height ? `${height}px` : undefined }}
    >
      {/* Show placeholder while loading or not in view */}
      {!isLoaded && !hasError && (placeholder || defaultPlaceholder)}

      {/* Show error fallback if image failed to load */}
      {hasError && (fallback || defaultFallback)}

      {/* Actual image - only render when in view or priority */}
      {isInView && imageSrc && !hasError && (
        <img
          ref={imgRef}
          src={imageSrc}
          alt={alt}
          className={`${className} ${isLoaded ? 'opacity-100' : 'opacity-0'} transition-opacity duration-300`}
          width={width}
          height={height}
          onLoad={handleLoad}
          onError={handleError}
          loading={priority ? 'eager' : 'lazy'}
          decoding="async"
        />
      )}
    </div>
  );
}

/**
 * Helper hook to preload critical images
 */
export function usePreloadImage(src: string) {
  useEffect(() => {
    if (!src) return;

    const link = document.createElement('link');
    link.rel = 'preload';
    link.as = 'image';
    link.href = src;
    document.head.appendChild(link);

    return () => {
      document.head.removeChild(link);
    };
  }, [src]);
}

/**
 * Helper function to convert image URL to WebP
 */
export function getWebPUrl(url: string): string {
  if (!url) return url;
  if (url.endsWith('.webp')) return url;
  return url.replace(/\.(png|jpg|jpeg)$/i, '.webp');
}

/**
 * Helper function to check if browser supports WebP
 */
export function checkWebPSupport(): Promise<boolean> {
  return new Promise((resolve) => {
    const webP = new Image();
    webP.onload = webP.onerror = () => {
      resolve(webP.height === 2);
    };
    webP.src = 'data:image/webp;base64,UklGRjoAAABXRUJQVlA4IC4AAACyAgCdASoCAAIALmk0mk0iIiIiIgBoSygABc6WWgAA/veff/0PP8bA//LwYAAA';
  });
}
