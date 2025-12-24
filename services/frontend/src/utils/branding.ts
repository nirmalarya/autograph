/**
 * Bayer Branding Configuration
 * 
 * This utility manages Bayer-specific branding including:
 * - Corporate logo display
 * - Corporate colors (Bayer Blue: #00A0E3, #0066B2)
 * - Product name customization
 * - Theme customization
 */

export interface BrandingConfig {
  enabled: boolean;
  logoUrl: string;
  productName: string;
  tagline: string;
  primaryColor: string;
  secondaryColor: string;
  companyName: string;
}

/**
 * Get the current branding configuration
 * Reads from environment variables to support white-label deployments
 * 
 * Note: This function can be called both server-side and client-side.
 * Client-side only sees NEXT_PUBLIC_* variables.
 */
export function getBrandingConfig(): BrandingConfig {
  // Check if running in browser
  const isBrowser = typeof window !== 'undefined';
  
  // For server-side, we need to check process.env
  // For client-side, only NEXT_PUBLIC_* vars are available
  const enableBayerBranding = isBrowser 
    ? (window as any).__NEXT_PUBLIC_ENABLE_BAYER_BRANDING === 'true' || process.env.NEXT_PUBLIC_ENABLE_BAYER_BRANDING === 'true'
    : process.env.NEXT_PUBLIC_ENABLE_BAYER_BRANDING === 'true';
  
  if (enableBayerBranding) {
    return {
      enabled: true,
      logoUrl: process.env.NEXT_PUBLIC_BAYER_LOGO_URL || '/bayer-logo.svg',
      productName: 'AutoGraph v3 for Bayer',
      tagline: 'AI-Powered Diagramming Platform',
      primaryColor: process.env.NEXT_PUBLIC_BAYER_PRIMARY_COLOR || '#00A0E3',
      secondaryColor: process.env.NEXT_PUBLIC_BAYER_SECONDARY_COLOR || '#0066B2',
      companyName: 'Bayer',
    };
  }
  
  // Default AutoGraph branding
  return {
    enabled: false,
    logoUrl: '/icons/icon-192x192.png',
    productName: 'AutoGraph v3',
    tagline: 'AI-Powered Diagramming Platform',
    primaryColor: '#3b82f6',
    secondaryColor: '#2563eb',
    companyName: 'AutoGraph',
  };
}

/**
 * Check if Bayer branding is enabled
 */
export function isBayerBrandingEnabled(): boolean {
  return getBrandingConfig().enabled;
}

/**
 * Get the logo URL
 */
export function getLogoUrl(): string {
  return getBrandingConfig().logoUrl;
}

/**
 * Get the product name
 */
export function getProductName(): string {
  return getBrandingConfig().productName;
}

/**
 * Get the tagline
 */
export function getTagline(): string {
  return getBrandingConfig().tagline;
}

/**
 * Get primary brand color (Bayer Blue or default blue)
 */
export function getPrimaryColor(): string {
  return getBrandingConfig().primaryColor;
}

/**
 * Get secondary brand color
 */
export function getSecondaryColor(): string {
  return getBrandingConfig().secondaryColor;
}

/**
 * Get company name
 */
export function getCompanyName(): string {
  return getBrandingConfig().companyName;
}
