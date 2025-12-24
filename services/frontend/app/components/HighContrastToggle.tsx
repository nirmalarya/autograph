'use client';

import { useTheme } from './ThemeProvider';
import Tooltip from './Tooltip';

/**
 * HighContrastToggle Component
 * 
 * Provides a toggle button for enabling/disabling high contrast mode.
 * High contrast mode meets WCAG AA compliance with 7:1 contrast ratios.
 * 
 * Features:
 * - Toggle high contrast mode on/off
 * - Visual indicator when enabled
 * - Persists preference to localStorage
 * - WCAG AA compliant colors
 */
export default function HighContrastToggle() {
  const { highContrast, setHighContrast } = useTheme();

  const toggleHighContrast = () => {
    setHighContrast(!highContrast);
  };

  const tooltipContent = (
    <div className="text-center">
      <div className="font-semibold">High Contrast: {highContrast ? 'On' : 'Off'}</div>
      <div className="text-xs mt-1 opacity-80">
        {highContrast ? 'Enhanced contrast for accessibility' : 'Click to enable'}
      </div>
    </div>
  );

  return (
    <Tooltip content={tooltipContent} position="bottom">
    <button
      onClick={toggleHighContrast}
      className={`p-2 rounded-lg transition-colors ${
        highContrast
          ? 'bg-blue-600 text-white hover:bg-blue-700'
          : 'hover:bg-gray-200 dark:hover:bg-gray-700'
      }`}
      aria-label="Toggle high contrast mode"
      aria-pressed={highContrast}
    >
      {/* High contrast icon */}
      <svg
        className="w-5 h-5"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
      >
        {highContrast ? (
          // Eye icon when enabled
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
          />
        ) : (
          // Contrast icon when disabled
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
          />
        )}
      </svg>
      {highContrast && (
        <span className="ml-1 text-xs font-semibold">HC</span>
      )}
    </button>
    </Tooltip>
  );
}
