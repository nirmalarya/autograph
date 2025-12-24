'use client';

/**
 * Skeleton Loader Component
 * 
 * Provides animated skeleton placeholders for loading states.
 * Implements Feature #623: Loading states with skeleton loaders
 */

interface SkeletonLoaderProps {
  variant?: 'card' | 'list' | 'text' | 'circle' | 'rectangle';
  count?: number;
  className?: string;
}

export function SkeletonCard({ className = '' }: { className?: string }) {
  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden ${className}`}>
      <div className="animate-pulse">
        {/* Thumbnail skeleton */}
        <div className="h-40 bg-gray-200 dark:bg-gray-700"></div>
        
        {/* Content skeleton */}
        <div className="p-4 space-y-3">
          {/* Title */}
          <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
          
          {/* Metadata */}
          <div className="space-y-2">
            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-2/3"></div>
          </div>
          
          {/* Footer */}
          <div className="flex items-center justify-between pt-2">
            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function SkeletonListItem({ className = '' }: { className?: string }) {
  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4 ${className}`}>
      <div className="animate-pulse flex items-center gap-4">
        {/* Icon/Thumbnail */}
        <div className="w-12 h-12 bg-gray-200 dark:bg-gray-700 rounded"></div>
        
        {/* Content */}
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
          <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
        </div>
        
        {/* Actions */}
        <div className="w-20 h-8 bg-gray-200 dark:bg-gray-700 rounded"></div>
      </div>
    </div>
  );
}

export function SkeletonText({ 
  lines = 3, 
  className = '' 
}: { 
  lines?: number; 
  className?: string;
}) {
  return (
    <div className={`space-y-2 ${className}`}>
      <div className="animate-pulse space-y-2">
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className="h-4 bg-gray-200 dark:bg-gray-700 rounded"
            style={{ width: i === lines - 1 ? '60%' : '100%' }}
          ></div>
        ))}
      </div>
    </div>
  );
}

export function SkeletonCircle({ 
  size = 'md',
  className = '' 
}: { 
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}) {
  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-12 h-12',
    lg: 'w-16 h-16',
    xl: 'w-24 h-24',
  };

  return (
    <div className={`animate-pulse ${sizeClasses[size]} bg-gray-200 dark:bg-gray-700 rounded-full ${className}`}></div>
  );
}

export function SkeletonRectangle({ 
  width = 'full',
  height = 'md',
  className = '' 
}: { 
  width?: 'sm' | 'md' | 'lg' | 'full';
  height?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}) {
  const widthClasses = {
    sm: 'w-1/4',
    md: 'w-1/2',
    lg: 'w-3/4',
    full: 'w-full',
  };

  const heightClasses = {
    sm: 'h-4',
    md: 'h-8',
    lg: 'h-16',
    xl: 'h-32',
  };

  return (
    <div className={`animate-pulse ${widthClasses[width]} ${heightClasses[height]} bg-gray-200 dark:bg-gray-700 rounded ${className}`}></div>
  );
}

export default function SkeletonLoader({ 
  variant = 'card', 
  count = 1,
  className = '' 
}: SkeletonLoaderProps) {
  const renderSkeleton = () => {
    switch (variant) {
      case 'card':
        return <SkeletonCard className={className} />;
      case 'list':
        return <SkeletonListItem className={className} />;
      case 'text':
        return <SkeletonText className={className} />;
      case 'circle':
        return <SkeletonCircle className={className} />;
      case 'rectangle':
        return <SkeletonRectangle className={className} />;
      default:
        return <SkeletonCard className={className} />;
    }
  };

  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i}>
          {renderSkeleton()}
        </div>
      ))}
    </>
  );
}

// Export all variants
export { SkeletonLoader };
