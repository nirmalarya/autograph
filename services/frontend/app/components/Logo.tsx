'use client';

import Image from 'next/image';
import { getLogoUrl, getProductName, isCustomBrandingEnabled } from '../../src/utils/branding';

interface LogoProps {
  className?: string;
  showText?: boolean;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

const sizeClasses = {
  sm: 'h-6 w-6',
  md: 'h-8 w-8',
  lg: 'h-10 w-10',
  xl: 'h-12 w-12',
};

const textSizeClasses = {
  sm: 'text-sm',
  md: 'text-base',
  lg: 'text-lg',
  xl: 'text-xl',
};

/**
 * Logo Component
 * 
 * Displays the application logo based on branding configuration.
 * Supports custom white-label branding via environment variables.
 * 
 * Features:
 * - Automatic branding switching via environment variables
 * - Responsive sizing (sm, md, lg, xl)
 * - Optional text display
 * - Optimized image loading
 * - Dark mode support
 */
export default function Logo({ className = '', showText = true, size = 'md' }: LogoProps) {
  const logoUrl = getLogoUrl();
  const productName = getProductName();
  const isCustom = isCustomBrandingEnabled();

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* Logo Image */}
      <div className={`relative ${sizeClasses[size]} flex-shrink-0`}>
        {isCustom && logoUrl.endsWith('.svg') ? (
          // For SVG logos, use img tag for better styling control
          <img
            src={logoUrl}
            alt={`${productName} logo`}
            className="h-full w-full object-contain"
          />
        ) : (
          // For PNG/other formats, use Next.js Image
          <Image
            src={logoUrl}
            alt={`${productName} logo`}
            fill
            className="object-contain"
            priority
          />
        )}
      </div>

      {/* Product Name Text */}
      {showText && (
        <span 
          className={`font-bold ${textSizeClasses[size]} text-gray-900 dark:text-gray-100 whitespace-nowrap`}
          style={isCustom ? { color: 'var(--brand-primary-color, #3b82f6)' } : undefined}
        >
          {productName}
        </span>
      )}
    </div>
  );
}
